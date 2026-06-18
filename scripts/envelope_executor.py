#!/usr/bin/env python3
"""Envelope Executor — Consumes PENDING envelopes and delegates to workers.

This is the missing link: pipeline_tick creates PENDING envelopes,
this executor claims them → RUNNING → delegates to delegate_task workers.
"""
import json, subprocess, sys, time, os, hashlib, signal, calendar
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from envelope_bus import get, update_status, append_trace, list_by_status, increment_retry, human_escape_check, stats
from task_continuation import detect_budget_exhausted, save_checkpoint, can_continue, build_continuation_context

MAX_CONCURRENT = int(os.environ.get('ENVELOPE_EXECUTOR_MAX', '1'))
STALE_PENDING_DAYS = float(os.environ.get('ENVELOPE_EXECUTOR_STALE_PENDING_DAYS', '1'))
STALE_RUNNING_GRACE_SECONDS = int(os.environ.get('ENVELOPE_EXECUTOR_STALE_RUNNING_GRACE_SECONDS', '300'))
# Cron jobs time out at the scheduler boundary. Keep this legacy executor's
# worker call comfortably inside that wall clock so cron reports a classified
# retry/failure instead of an unstructured script timeout.
WORKER_TIMEOUT_SECONDS = int(os.environ.get('ENVELOPE_EXECUTOR_WORKER_TIMEOUT_SECONDS', '90'))
WALL_BUDGET_SECONDS = int(os.environ.get('ENVELOPE_EXECUTOR_WALL_BUDGET_SECONDS', '105'))
ORCHESTRATOR = Path.home() / '.hermes' / 'scripts' / 'brain_task_orchestrator.py'
_ACTIVE_WORKER_PGID = None


def _kill_worker_group(pgid, grace=5):
    if not pgid:
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except Exception:
        pass
    deadline = time.time() + grace
    while time.time() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return
        except Exception:
            break
        time.sleep(0.2)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except Exception:
        pass


def _shutdown_handler(signum, frame):
    _kill_worker_group(_ACTIVE_WORKER_PGID, grace=1)
    raise SystemExit(128 + signum)


for _sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(_sig, _shutdown_handler)
    except Exception:
        pass


def run_worker_command(cmd, timeout=600, cwd=None):
    """Run worker in its own process group and clean up the whole tree.

    `hermes chat` can spawn nested processes.  Killing only the direct child can
    leave orphan workers that keep editing after the envelope has been retried or
    failed, so timeout/shutdown must terminate the process group.  When the
    envelope is tied to a source repository, run the worker with that repository
    as cwd so Hermes exposes the correct working tree and project instructions.
    """
    global _ACTIVE_WORKER_PGID
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        cwd=str(cwd) if cwd else None,
    )
    _ACTIVE_WORKER_PGID = proc.pid
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        _kill_worker_group(proc.pid)
        proc.wait(timeout=5)
        raise
    finally:
        _ACTIVE_WORKER_PGID = None


def claim_envelope(eid):
    """Move envelope PENDING → RUNNING."""
    env = get(eid)
    if not env or env['status'] != 'PENDING':
        return False
    update_status(eid, 'RUNNING')
    append_trace(eid, {'event': 'executor_claimed'})
    return True

def _strip_json_fence(text):
    text = (text or '').strip()
    if not text.startswith('```'):
        return text
    lines = text.splitlines()
    if lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith('```'):
        lines = lines[:-1]
    return '\n'.join(lines).strip()


def _first_json_object(text):
    text = _strip_json_fence(text)
    start = text.find('{')
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for offset, ch in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:offset + 1]
    return None


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    return []


def _payload_harness_contract(payload):
    if not isinstance(payload, dict):
        return {}
    for key in ('harness_contract', 'intake_contract', 'contract'):
        contract = payload.get(key)
        if isinstance(contract, dict):
            return contract
    confirm_plan = payload.get('confirm_plan')
    if isinstance(confirm_plan, dict) and isinstance(confirm_plan.get('contract'), dict):
        return confirm_plan['contract']
    return {}


def _contract_acceptance_items(contract):
    if not isinstance(contract, dict):
        return []
    raw_acceptance = contract.get('acceptance')
    raw_evidence = contract.get('evidence')
    acceptance = raw_acceptance if isinstance(raw_acceptance, dict) else {}
    evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
    items = []
    for key in ('observable_results', 'required_commands', 'required_artifacts', 'screenshots_or_logs', 'precision_rules', 'regression_boundaries'):
        items.extend(_as_list(acceptance.get(key)))
    items.extend(_as_list(evidence.get('minimum_done_proof')))
    return items


def _payload_acceptance_items(payload):
    if not isinstance(payload, dict):
        return []
    items = []
    items.extend(_as_list(payload.get('acceptance_criteria')))
    items.extend(_as_list(payload.get('acceptance_evidence')))
    items.extend(_contract_acceptance_items(_payload_harness_contract(payload)))
    # Stable de-duplication keeps prompts compact while preserving order.
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _proof_acceptance_entries(proof):
    entries = proof.get('acceptance_criteria_covered') if isinstance(proof, dict) else None
    return entries if isinstance(entries, list) else []


def validate_done_proof_against_payload(proof, payload):
    """Fail closed when a task declared acceptance but proof did not cover it."""
    if not isinstance(proof, dict) or proof.get('status') != 'done':
        return None
    expected = _payload_acceptance_items(payload)
    if not expected:
        return None
    entries = _proof_acceptance_entries(proof)
    if len(entries) < len(expected):
        return f'acceptance_criteria_covered_incomplete:{len(entries)}<{len(expected)}'
    missing_evidence = []
    for idx, entry in enumerate(entries[:len(expected)]):
        if not isinstance(entry, dict):
            missing_evidence.append(str(idx))
            continue
        status = entry.get('status')
        evidence = entry.get('evidence')
        if status not in ('covered', 'blocked') or not isinstance(evidence, list) or not evidence:
            missing_evidence.append(str(idx))
    if missing_evidence:
        return 'acceptance_criteria_covered_missing_evidence:' + ','.join(missing_evidence)
    return None


def build_harness_contract_section(payload, contract_path=''):
    """Build a compact intake-contract section for the worker prompt."""
    contract = _payload_harness_contract(payload)
    acceptance_items = _payload_acceptance_items(payload)
    lines = [
        'HARNESS INTAKE CONTRACT:',
        '- Use map → goal → acceptance → division → evidence → gates as the execution contract.',
        '- If required map/acceptance/proof facts are missing, stop at status=blocked and name the missing contract fields.',
        '- If an external acceptance contract path is missing but inline contract JSON or payload acceptance exists, continue from the inline/payload contract instead of blocking on the missing file.',
        '- Do not invent acceptance; satisfy only stated acceptance and produce deterministic evidence.',
    ]
    if contract_path:
        lines.append(f'- External acceptance contract path, if present: {contract_path}')
    if contract:
        compact = json.dumps(contract, ensure_ascii=False, sort_keys=True)
        lines.append(f'- Inline contract JSON: {compact[:3000]}')
    if acceptance_items:
        lines.append('- Acceptance/proof items that must be covered in PROOF_JSON.acceptance_criteria_covered:')
        for i, item in enumerate(acceptance_items, 1):
            lines.append(f'  {i}. {item}')
    else:
        lines.append('- No explicit acceptance items found in the envelope payload; derive only from task text and external contract path if it exists, and use status=blocked if insufficient.')
    return '\n'.join(lines)


def extract_proof(output):
    """Extract and validate the last PROOF_JSON marker from worker output.

    Returns (proof_dict, proof_sha, error_reason).  DONE is fail-closed: a
    literal marker is not enough; the proof must be parseable structured JSON.
    Supports both single-line and fenced/multiline PROOF_JSON payloads because
    model workers often wrap JSON despite the prompt requesting a last line.
    """
    marker = 'PROOF_JSON:'
    output = output or ''
    candidates = []
    pos = output.rfind(marker)
    if pos >= 0:
        candidates.append(output[pos + len(marker):])
    for line in reversed(output.splitlines()):
        text = line.strip()
        if text.startswith(marker):
            candidates.append(text.split(':', 1)[1].strip())
    saw_marker = bool(candidates)
    for raw in candidates:
        json_text = _first_json_object(raw)
        if not json_text:
            continue
        try:
            proof = json.loads(json_text)
        except Exception:
            continue
        if not isinstance(proof, dict):
            return None, None, 'invalid_proof'
        if proof.get('status') not in ('done', 'blocked'):
            return None, None, 'invalid_proof'
        canonical = json.dumps(proof, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        proof_sha = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return proof, proof_sha, None
    return None, None, 'invalid_proof' if saw_marker else 'missing_proof'


def delegate_to_worker(envelope, timeout=None):
    """Delegate envelope to a worker via hermes chat -q."""
    eid = envelope['id']
    payload = json.loads(envelope.get('payload', '{}')) if isinstance(envelope.get('payload'), str) else envelope.get('payload', {})
    title = envelope.get('title', 'untitled')
    brain_id = payload.get('brain_id', '')
    
    project = envelope.get('project') or payload.get('project') or ''
    boundary = payload.get('boundary') or payload.get('parallel_boundary') or ''
    workspace_map = {
        # Use clean shared task-loop worktrees, not the user's main working copies.
        # The main work/ repos often contain human/WIP branches; envelope workers
        # must be isolated to avoid overwriting or mixing unrelated changes.
        'uvisa-admin': '/Users/charles/Desktop/folder/work/.agent-team-worktrees/uvisa-admin-task-loop',
        'uvisa-admin-work': '/Users/charles/Desktop/folder/work/.agent-team-worktrees/uvisa-admin-task-loop',
        'uvisa-app-2.0': '/Users/charles/Desktop/folder/work/.agent-team-worktrees/uvisa-app-task-loop',
        'uvisa-app-2.0-work': '/Users/charles/Desktop/folder/work/.agent-team-worktrees/uvisa-app-task-loop',
        'uvisa-backend': '/Users/charles/Desktop/folder/work/.agent-team-worktrees/uvisa-backend-task-loop',
        'uvisa-backend-work': '/Users/charles/Desktop/folder/work/.agent-team-worktrees/uvisa-backend-task-loop',
    }
    cwd = workspace_map.get(project)
    if not cwd and boundary.startswith('workspace:'):
        cwd = boundary.split(':', 1)[1].strip() or None
    evidence_dir = f"/Users/charles/.hermes/evidence/envelopes/{eid}"
    contract_dir = '/Users/charles/.hermes/state/uvisa_lark_contracts/current'
    contract_path = str(Path(contract_dir) / f"{brain_id}.json") if brain_id else ''
    harness_section = build_harness_contract_section(payload, contract_path)

    # Build prompt
    prompt = f"""Execute this task to the highest safe boundary and output a PROOF_JSON on the last line.

TASK: {title}
ID: {brain_id}
PROJECT: {project}
WORKSPACE: {cwd or '[unset]'}
BOUNDARY: {boundary}
ACCEPTANCE_CONTRACT: {contract_path}
EVIDENCE_DIR: {evidence_dir}

{harness_section}

UVISA ADMIN WORKFLOW RULES:
1. Before editing, run git fetch and verify the current branch/status in WORKSPACE.
2. Stay within PROJECT/BOUNDARY. Do not touch unrelated repos or unrelated product surfaces.
3. If ACCEPTANCE_CONTRACT exists, satisfy its acceptance_atoms and write evidence files under EVIDENCE_DIR.
4. Run the relevant tests/build (at minimum npm run build for uvisa-admin frontend changes unless blocked by existing environment issues) and save logs under EVIDENCE_DIR.
5. Create/keep a scoped git commit. If the repo remote/auth allows it, push a task branch, open a PR, and merge it automatically after verification. Record PR URL/number in evidence.
6. Do not paste or persist secrets. Redact credentials as [REDACTED].
7. Do NOT mark brain/Lark task done yourself unless you have also produced verifiable evidence; the executor will collect PROOF_JSON.
8. Output PROOF_JSON on the LAST line exactly.
9. For proof-only validation tasks, no tool call or file edit is required; immediately return the final PROOF_JSON if the acceptance can be covered by the final proof itself.
10. Do not write explanatory text after PROOF_JSON. The final line must begin with `PROOF_JSON:` and contain parseable JSON.

FINAL OUTPUT CONTRACT:
- The final answer MUST contain a line starting exactly with `PROOF_JSON:`.
- For status=done, include acceptance_criteria_covered with one entry per stated acceptance/proof item.
- Each covered entry needs non-empty evidence such as `artifact:worker-final-proof-json`, `command:...`, `file:...`, or `log:...`.
- If you cannot satisfy the contract, output status=blocked with blockers; do not omit PROOF_JSON.

PROOF_JSON schema:
{{"status":"done|blocked","summary":"<=200 chars","files_changed":[],"tests_passed":0,"evidence_dir":"{evidence_dir}","pr_url":"","merged":false,"lark_guid":"{brain_id}","acceptance_criteria_covered":[{{"criterion":"...","status":"covered|blocked","evidence":["command:...|file:...|artifact:..."],"blocker":""}}]}}

If blocked, still output PROOF_JSON with status=blocked and a concise summary of the concrete blocker.
"""
    
    # Check for continuation context
    if brain_id:
        can_cont, count = can_continue(brain_id)
        if count > 0:
            prompt = build_continuation_context(brain_id, prompt)
    
    # Run via hermes chat -q
    try:
        cmd = [
            'hermes', 'chat', '-q', prompt,
            '--model', 'mimo-v2.5-pro', '--provider', 'xiaomi',
            '--quiet', '--max-turns', '30', '--source', f'envelope-exec-{eid[:8]}',
            '--ignore-rules',
        ]
        r = run_worker_command(cmd, timeout=timeout or WORKER_TIMEOUT_SECONDS, cwd=cwd)
        output = r.stdout
        if r.returncode != 0:
            update_status(eid, 'FAILED', error=(r.stderr or output or f'worker exited {r.returncode}')[:200])
            append_trace(eid, {'event': 'worker_failed', 'returncode': r.returncode, 'stderr': (r.stderr or '')[:200]})
            return {'status': 'failed', 'reason': 'worker_nonzero', 'returncode': r.returncode, 'output': output[:500]}
        
        # Check for budget exhaustion
        exhausted, signal = detect_budget_exhausted(output)
        if exhausted:
            checkpoint = save_checkpoint(brain_id, output)
            append_trace(eid, {'event': 'budget_exhausted', 'signal': signal, 'continuation': checkpoint.get('continuation_count', 0)})
            can_cont, _ = can_continue(brain_id)
            if can_cont:
                update_status(eid, 'PENDING')  # Re-queue for continuation
                return {'status': 'continuation_pending', 'output': output[:500]}
            else:
                update_status(eid, 'FAILED', error=f'Budget exhausted, max continuations reached')
                return {'status': 'failed', 'reason': 'max_continuations'}
        
        # Check for structured proof before allowing terminal completion.
        proof, proof_sha, proof_error = extract_proof(output)
        if proof:
            proof_contract_error = validate_done_proof_against_payload(proof, payload)
            if proof_contract_error:
                update_status(eid, 'FAILED', error=proof_contract_error)
                append_trace(eid, {'event': proof_contract_error, 'output_len': len(output), 'proof_sha': proof_sha, 'proof': proof})
                return {'status': 'failed', 'reason': proof_contract_error, 'output': output[:500]}
            if proof.get('status') == 'done':
                update_status(eid, 'DONE', proof_sha=proof_sha)
                append_trace(eid, {'event': 'completed', 'output_len': len(output), 'proof_sha': proof_sha, 'proof': proof})
                return {'status': 'done', 'output': output[:500], 'proof_sha': proof_sha}
            update_status(eid, 'BLOCKED', proof_sha=proof_sha)
            append_trace(eid, {'event': 'blocked', 'output': output[:200], 'proof_sha': proof_sha, 'proof': proof})
            return {'status': 'blocked', 'output': output[:500], 'proof_sha': proof_sha}
        elif 'BLOCKED' in output:
            update_status(eid, 'BLOCKED')
            append_trace(eid, {'event': 'blocked_no_proof', 'output': output[:200]})
            return {'status': 'blocked', 'reason': 'blocked_no_proof', 'output': output[:500]}
        else:
            update_status(eid, 'FAILED', error=proof_error)
            append_trace(eid, {'event': proof_error, 'output_len': len(output), 'output': output[:200]})
            return {'status': 'failed', 'reason': proof_error, 'output': output[:500]}
    
    except subprocess.TimeoutExpired:
        retry_count, max_retries = increment_retry(eid)
        if retry_count >= max_retries:
            update_status(eid, 'FAILED', error='Worker timeout, max retries')
            return {'status': 'failed', 'reason': 'timeout_max_retries'}
        else:
            update_status(eid, 'PENDING')
            append_trace(eid, {'event': 'timeout_retry', 'retry': retry_count})
            return {'status': 'retry', 'retry': retry_count}
    except Exception as e:
        update_status(eid, 'FAILED', error=str(e)[:200])
        append_trace(eid, {'event': 'error', 'error': str(e)[:200]})
        return {'status': 'error', 'error': str(e)[:200]}

def _parse_iso_z(value):
    if not value:
        return None
    try:
        return calendar.timegm(time.strptime(value, '%Y-%m-%dT%H:%M:%SZ'))
    except Exception:
        return None


def _age_seconds(envelope, field='created_at'):
    ts = _parse_iso_z(envelope.get(field))
    if ts is None:
        return None
    return time.time() - ts


def cleanup_stale_running():
    """Fail stale RUNNING envelopes before considering new work.

    Cron ticks must be bounded and quiet.  A previous killed/timeout executor can
    leave RUNNING envelopes behind; retrying unrelated PENDING work while stale
    RUNNING rows exist creates user-visible noise and duplicate work.
    """
    cleaned = []
    for env in list_by_status('RUNNING'):
        age = _age_seconds(env, 'started_at')
        appetite = int(env.get('appetite_seconds') or 1800) + STALE_RUNNING_GRACE_SECONDS
        if age is None or age <= appetite:
            continue
        update_status(env['id'], 'FAILED', error=f'stale RUNNING exceeded appetite+grace ({int(age)}s)')
        append_trace(env['id'], {'event': 'stale_running_cleanup', 'age_seconds': int(age), 'appetite_plus_grace': appetite})
        cleaned.append(env['id'])
    return cleaned


def skip_stale_pending(envelopes):
    """Quarantine stale pending envelopes instead of unexpectedly launching LLM workers.

    The envelope bus is a legacy escape lane; current taskpool state is the SSOT.
    Old PENDING envelopes should not suddenly wake up after a scheduler repair and
    start editing projects or spamming providers.  They remain auditable as
    SKIPPED with trace evidence.
    """
    if STALE_PENDING_DAYS <= 0:
        return envelopes, []
    cutoff = STALE_PENDING_DAYS * 86400
    fresh = []
    skipped = []
    for env in envelopes:
        age = _age_seconds(env, 'created_at')
        if age is not None and age > cutoff:
            update_status(env['id'], 'SKIPPED', error=f'stale pending envelope older than {STALE_PENDING_DAYS:g}d')
            append_trace(env['id'], {'event': 'stale_pending_quarantine', 'age_seconds': int(age), 'threshold_days': STALE_PENDING_DAYS})
            skipped.append(env['id'])
        else:
            fresh.append(env)
    return fresh, skipped


def run_executor(max_concurrent=None):
    """Execute one cycle: claim PENDING → delegate → collect result."""
    started = time.monotonic()
    max_n = max_concurrent or MAX_CONCURRENT
    cleaned_running = cleanup_stale_running()
    
    # Check human escape
    escape, info = human_escape_check()
    if escape:
        return {'status': 'escaped', 'reason': str(info)}
    
    pending = list_by_status('PENDING')
    pending, skipped_stale = skip_stale_pending(pending)
    if not pending:
        return {
            'status': 'idle',
            'pending': 0,
            'stale_pending_quarantined': len(skipped_stale),
            'stale_running_cleaned': len(cleaned_running),
            'envelope_stats': stats(),
        }
    
    results = []
    for envelope in pending[:max_n]:
        remaining_budget = WALL_BUDGET_SECONDS - (time.monotonic() - started)
        if remaining_budget < 30:
            return {
                'status': 'deferred_budget',
                'processed': len(results),
                'remaining_pending': len(pending) - len(results),
                'stale_pending_quarantined': len(skipped_stale),
                'stale_running_cleaned': len(cleaned_running),
                'reason': 'insufficient wall budget for another worker',
                'envelope_stats': stats(),
            }
        eid = envelope['id']
        title = envelope.get('title', '')[:50]
        
        # Claim
        if not claim_envelope(eid):
            continue
        
        # Delegate
        worker_timeout = max(20, min(WORKER_TIMEOUT_SECONDS, int(remaining_budget) - 10))
        result = delegate_to_worker(envelope, timeout=worker_timeout)
        results.append({
            'envelope_id': eid,
            'title': title,
            'result': result.get('status', 'unknown'),
        })
    
    return {
        'status': 'ok',
        'processed': len(results),
        'remaining_pending': len(pending) - len(results),
        'stale_pending_quarantined': len(skipped_stale),
        'stale_running_cleaned': len(cleaned_running),
        'results': results,
        'envelope_stats': stats(),
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        print(json.dumps(run_executor(n), indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == 'stats':
        print(json.dumps(stats(), indent=2))
    else:
        print('Usage: envelope_executor.py [run [N]|stats]')
