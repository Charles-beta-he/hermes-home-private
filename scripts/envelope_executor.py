#!/usr/bin/env python3
"""Envelope Executor — Consumes PENDING envelopes and delegates to workers.

This is the missing link: pipeline_tick creates PENDING envelopes,
this executor claims them → RUNNING → delegates to delegate_task workers.
"""
import json, subprocess, sys, time, os, hashlib, signal
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from envelope_bus import get, update_status, append_trace, list_by_status, increment_retry, human_escape_check, stats
from task_continuation import detect_budget_exhausted, save_checkpoint, can_continue, build_continuation_context

MAX_CONCURRENT = int(os.environ.get('ENVELOPE_EXECUTOR_MAX', '1'))
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

def extract_proof(output):
    """Extract and validate the last PROOF_JSON line from worker output.

    Returns (proof_dict, proof_sha, error_reason).  DONE is fail-closed: a
    literal marker is not enough; the proof must be parseable structured JSON.
    """
    saw_marker = False
    for line in reversed((output or '').splitlines()):
        text = line.strip()
        if not text.startswith('PROOF_JSON:'):
            continue
        saw_marker = True
        raw = text.split(':', 1)[1].strip()
        try:
            proof = json.loads(raw)
        except Exception:
            return None, None, 'invalid_proof'
        if not isinstance(proof, dict):
            return None, None, 'invalid_proof'
        if proof.get('status') not in ('done', 'blocked'):
            return None, None, 'invalid_proof'
        canonical = json.dumps(proof, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        proof_sha = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        return proof, proof_sha, None
    return None, None, 'invalid_proof' if saw_marker else 'missing_proof'


def delegate_to_worker(envelope):
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

    # Build prompt
    prompt = f"""Execute this task to the highest safe boundary and output a PROOF_JSON on the last line.

TASK: {title}
ID: {brain_id}
PROJECT: {project}
WORKSPACE: {cwd or '[unset]'}
BOUNDARY: {boundary}
ACCEPTANCE_CONTRACT: {contract_path}
EVIDENCE_DIR: {evidence_dir}

UVISA ADMIN WORKFLOW RULES:
1. Before editing, run git fetch and verify the current branch/status in WORKSPACE.
2. Stay within PROJECT/BOUNDARY. Do not touch unrelated repos or unrelated product surfaces.
3. If ACCEPTANCE_CONTRACT exists, satisfy its acceptance_atoms and write evidence files under EVIDENCE_DIR.
4. Run the relevant tests/build (at minimum npm run build for uvisa-admin frontend changes unless blocked by existing environment issues) and save logs under EVIDENCE_DIR.
5. Create/keep a scoped git commit. If the repo remote/auth allows it, push a task branch, open a PR, and merge it automatically after verification. Record PR URL/number in evidence.
6. Do not paste or persist secrets. Redact credentials as [REDACTED].
7. Do NOT mark brain/Lark task done yourself unless you have also produced verifiable evidence; the executor will collect PROOF_JSON.
8. Output PROOF_JSON on the LAST line exactly.

PROOF_JSON schema:
{{"status":"done|blocked","summary":"<=200 chars","files_changed":[],"tests_passed":0,"evidence_dir":"{evidence_dir}","pr_url":"","merged":false,"lark_guid":"{brain_id}"}}

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
        r = run_worker_command(cmd, timeout=600, cwd=cwd)
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

def run_executor(max_concurrent=None):
    """Execute one cycle: claim PENDING → delegate → collect result."""
    max_n = max_concurrent or MAX_CONCURRENT
    
    # Check human escape
    escape, info = human_escape_check()
    if escape:
        return {'status': 'escaped', 'reason': str(info)}
    
    pending = list_by_status('PENDING')
    if not pending:
        return {'status': 'idle', 'pending': 0}
    
    results = []
    for envelope in pending[:max_n]:
        eid = envelope['id']
        title = envelope.get('title', '')[:50]
        
        # Claim
        if not claim_envelope(eid):
            continue
        
        # Delegate
        result = delegate_to_worker(envelope)
        results.append({
            'envelope_id': eid,
            'title': title,
            'result': result.get('status', 'unknown'),
        })
    
    return {
        'status': 'ok',
        'processed': len(results),
        'remaining_pending': len(pending) - len(results),
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
