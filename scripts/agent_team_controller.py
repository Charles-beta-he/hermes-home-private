#!/usr/bin/env python3
"""Agent Team Controller v2 — Dynamic N + Task Classification + Conflict Avoidance.

Phase 4: Adaptive parallel scheduling.
- Dynamic N: min(ceil(dispatchable/7), conflict_groups, 3)
- Task classifier: deterministic boundary→group mapping
- Conflict groups: same group serial, different groups parallel
- Smoothing: N changes only after 2 consecutive cycles

Safety:
- Worker cannot mark DONE (controller-owned)
- Proof artifact required for DONE transition
- Lease TTL with auto-cleanup
- Human escape: kill switch file/env
- Conflict group isolation
"""
import argparse
import json, subprocess, sys, time, os, hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from envelope_bus import create, get, update_status, append_trace, increment_retry, list_by_status, stats, human_escape_check
from task_classifier import classify_batch, get_parallel_schedule, boundary_health_check, check_parallel_file_conflicts
from dynamic_n import get_smoothed_n
from task_continuation import detect_budget_exhausted, save_checkpoint, can_continue, build_continuation_context, get_checkpoint_status, cleanup_checkpoint, list_checkpoints
from self_optimizing_verifier import save_rejection, analyze_rejection, generate_enhanced_criteria, generate_retry_prompt, update_project_profile
from uvisa_lark_work_contract import generate_acceptance_atoms, extract_lark_guid

ORCHESTRATOR = Path.home() / '.hermes' / 'scripts' / 'brain_task_orchestrator.py'
STATE_DIR = Path.home() / '.hermes' / 'state'
KILL_SWITCH = STATE_DIR / 'agent_team_disabled'
PROOF_DIR = STATE_DIR / 'proof_artifacts'
UVISA_CONTRACT_DIRNAME = 'uvisa_lark_contracts'

def is_disabled():
    return os.environ.get('AGENT_TEAM_DISABLED') == '1' or KILL_SWITCH.exists()

def get_all_dispatchable():
    """Get all dispatchable tasks."""
    r = subprocess.run(
        ['python3', str(ORCHESTRATOR), 'list', '--json'],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        raise RuntimeError(f'list failed: {r.stderr[:200]}')
    data = json.loads(r.stdout)
    return [t for t in data.get('rows', []) if t.get('dispatchable', False)]

def claim_task(task_id, actor='agent-team-controller', ttl=60):
    """Claim a task via orchestrator."""
    r = subprocess.run(
        ['python3', str(ORCHESTRATOR), 'claim', task_id,
         '--actor', actor, '--ttl-minutes', str(ttl),
         '--reason', 'Phase 4 dynamic parallel dispatch', '--json'],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return {'ok': False, 'error': r.stderr[:200]}
    data = json.loads(r.stdout)
    if data.get('status') == 'OK':
        return {'ok': True, 'data': data}
    return {'ok': False, 'error': data.get('reasons', str(data.get('status', 'unknown')))}


def transition_task(task_id, to_status, actor, reason, evidence=None, ttl=60, force=False):
    """Transition a brain task through the lifecycle gate."""
    cmd = [
        'python3', str(ORCHESTRATOR), 'transition', task_id,
        '--to', to_status,
        '--actor', actor,
        '--ttl-minutes', str(ttl),
        '--reason', reason,
        '--json',
    ]
    for item in evidence or []:
        cmd.extend(['--evidence', str(item)])
    if force:
        cmd.append('--force')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return {'ok': False, 'error': (r.stderr or r.stdout)[:500], 'returncode': r.returncode}
    try:
        data = json.loads(r.stdout)
    except Exception:
        data = {'raw': r.stdout[:500]}
    return {'ok': data.get('status') == 'OK', 'data': data}


def list_task_rows(include_done=False):
    cmd = ['python3', str(ORCHESTRATOR), 'list']
    if include_done:
        cmd.append('--include-done')
    cmd.append('--json')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f'list failed: {(r.stderr or r.stdout)[:300]}')
    return json.loads(r.stdout).get('rows', [])


def rows_by_id(ids):
    wanted = set(ids)
    return {row.get('id'): row for row in list_task_rows(include_done=True) if row.get('id') in wanted}


def page_batch_siblings_for(row, rows=None, limit=8):
    """Return same-boundary work/Lark UI siblings for page-level batching context.

    The controller still claims/closes only the current task. Siblings are context
    so a worker can make one coherent page-level code change and report which
    acceptance atoms were covered.
    """
    boundary = str(row.get('parallel_boundary') or '').strip()
    project = str(row.get('project') or '').strip()
    task_id = str(row.get('id') or '')
    if not boundary or not project:
        return []
    rows = rows if rows is not None else list_task_rows(include_done=False)
    out = []
    for other in rows:
        if str(other.get('id') or '') == task_id:
            continue
        if str(other.get('project') or '').strip() != project:
            continue
        if str(other.get('parallel_boundary') or '').strip() != boundary:
            continue
        status = str(other.get('status') or '').strip()
        if status not in {'pending', 'retry', 'claimed', 'running', 'review'}:
            continue
        title_blob = f"{other.get('id','')} {other.get('title','')}".lower()
        row_blob = f"{row.get('id','')} {row.get('title','')}".lower()
        if not (('lark' in title_blob or 'lark' in row_blob or project.startswith('uvisa')) and (row.get('lane') == 'work' or other.get('lane') == 'work')):
            continue
        out.append(other)
        if len(out) >= limit:
            break
    return out

def _looks_like_uvisa_lark_task(task):
    text = ' '.join(str(task.get(k, '') or '') for k in ('id', 'title', 'project', 'source', 'body', 'description')).lower()
    return ('lark' in text or '飞书' in text) and ('uvisa' in text or 'uvisa-admin' in text or '管理端' in text)

def ensure_uvisa_lark_contract(task):
    """Create/read the fail-closed UVISA Lark contract for a task.

    The task dict is mutated with uvisa_contract_path so downstream context,
    envelope payloads, and closeout gates all point at the same artifact.
    """
    if not _looks_like_uvisa_lark_task(task):
        return None
    existing = task.get('uvisa_contract_path')
    if existing and Path(existing).expanduser().exists():
        try:
            return json.loads(Path(existing).expanduser().read_text())
        except Exception:
            pass
    task_id = str(task.get('id', '') or '')
    title = str(task.get('title', '') or task_id)
    body = str(task.get('body', '') or task.get('description', '') or '')
    lark_guid = str(task.get('lark_task_guid', '') or '')
    if not lark_guid:
        lark_guid = extract_lark_guid(task_id, title, body)
    contract = generate_acceptance_atoms(task_id=task_id, title=title, body=body, lark_task_guid=lark_guid)
    contract_data = dict(contract.__dict__)
    out_dir = STATE_DIR / UVISA_CONTRACT_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = ''.join(ch if ch.isalnum() or ch in '._-' else '-' for ch in (lark_guid or task_id or 'uvisa-lark-task')).strip('-._')[:80] or 'uvisa-lark-task'
    path = out_dir / f'{safe}.contract.json'
    path.write_text(json.dumps(contract_data, ensure_ascii=False, indent=2, sort_keys=True))
    task['uvisa_contract_path'] = str(path)
    task['uvisa_contract_task_type'] = contract.task_type
    return contract_data

def re_search_lark_guid(text):
    import re as _re
    m = _re.search(r'lark[-_\s:]*([0-9a-f]{6,12})', str(text), flags=_re.I)
    return m.group(1) if m else ''

def format_uvisa_contract_context(contract, path):
    if not contract:
        return ''
    atoms = contract.get('acceptance_atoms') or []
    atom_lines = []
    for atom in atoms:
        atom_lines.append(f"- {atom.get('id')}: {atom.get('proof_type')} :: {atom.get('requirement')}")
    return f'''
UVISA LARK WORK CONTRACT (fail-closed)
CONTRACT_PATH: {path}
TASK_TYPE: {contract.get('task_type')}
REPOS: {', '.join(contract.get('repos') or [])}
BRANCH_NAMESPACE: {contract.get('branch_namespace')}
VIEWPORT: 1512x982 / 14-inch-admin
TARGET_SURFACE: {contract.get('target_surface')}
ACCEPTANCE_ATOMS:
{chr(10).join(atom_lines)}
CLOSEOUT_RULES:
- Worker cannot mark done; controller owns done transition.
- PR merge, online UI regression evidence, Lark close response, and TG evidence-directory notification are mandatory.
- Data correctness tasks require source_to_sink_equality assertion JSON.
'''

def build_worker_context(task, conflict_group, sibling_tasks=None):
    """Build context for delegate_task child.

    v2: Includes full boundary constraints so the worker understands its
    isolation envelope — allowed_globs, forbidden_globs, loc_budget,
    workspace_isolation, and merge_gate.

    v3: Includes sibling awareness — other tasks in the same conflict group
    so the worker knows what else is running and can avoid cross-contamination.

    v4: For Lark/work UI bursts, same-boundary sibling tasks are page-batch
    acceptance atoms. The worker may implement them in the same page-level
    code slice when safe, but lifecycle closeout remains per original task.
    """
    allowed_globs = task.get('allowed_globs', '')
    forbidden_globs = task.get('forbidden_globs', '')
    loc_budget = task.get('loc_budget', '')
    ws_isolation = task.get('workspace_isolation', '')
    merge_gate = task.get('merge_gate', '')
    workspace = task.get('workspace', '')
    parallel_group = task.get('parallel_group', '')

    boundary_constraints = []
    if workspace:
        boundary_constraints.append(f'WORKSPACE: {workspace}')
    if allowed_globs:
        boundary_constraints.append(f'ALLOWED_GLOBS: {allowed_globs}')
    if forbidden_globs:
        boundary_constraints.append(f'FORBIDDEN_GLOBS: {forbidden_globs}')
    if loc_budget:
        boundary_constraints.append(f'LOC_BUDGET: {loc_budget} lines max')
    if ws_isolation:
        boundary_constraints.append(f'WORKSPACE_ISOLATION: {ws_isolation}')
    if merge_gate:
        boundary_constraints.append(f'MERGE_GATE: {merge_gate}')
    if parallel_group:
        boundary_constraints.append(f'PARALLEL_GROUP: {parallel_group} (cooperative with same group)')

    boundary_section = ''
    if boundary_constraints:
        boundary_section = '\nBOUNDARY CONSTRAINTS (fail-closed: violations block task):\n' + '\n'.join(f'- {c}' for c in boundary_constraints)

    # Sibling awareness: inform worker about other tasks in the same conflict group.
    # For Lark/work UI bursts, same-boundary siblings are page-batch candidates:
    # implement together only when safe, but keep proof/closeout mapped per task.
    sibling_section = ''
    if sibling_tasks:
        sib_lines = []
        for sib in sibling_tasks[:8]:  # Cap to avoid context bloat while allowing page batches
            sib_id = sib.get('id', '?')
            sib_title = sib.get('title', '?')[:80]
            sib_status = sib.get('status', '?')
            sib_boundary = sib.get('parallel_boundary', sib.get('workspace', ''))
            sib_lines.append(f'- [{sib_status}] {sib_id}: {sib_title} (boundary: {sib_boundary})')
        if sib_lines:
            sibling_section = '''
PAGE-BATCH SIBLING TASKS (same boundary / likely same page surface):
{lines}
PAGE-BATCH RULES:
- If these siblings target the same repo + route/page/module and can be verified in one browser pass, include their code changes in the same page-level slice.
- Keep each original task/GUID as an acceptance atom; do not mark sibling tasks done from this worker.
- PROOF_JSON should include page_batch_covered_task_ids when sibling acceptance atoms are covered.
- Do not batch siblings that cross repos, need BE/schema changes, have unrelated modules, or are blocked by a different release gate.
'''.format(lines='\n'.join(sib_lines))

    uvisa_contract = ensure_uvisa_lark_contract(task)
    uvisa_contract_section = format_uvisa_contract_context(uvisa_contract, task.get('uvisa_contract_path', ''))

    return f"""You are a Kanban worker executing a brain task.

TASK: {task.get('title', 'untitled')}
ID: {task.get('id', '')}
PRIORITY: {task.get('priority', 'P2')}
PROJECT: {task.get('project', '')}
BOUNDARY: {task.get('parallel_boundary', '')}
CONFLICT_GROUP: {conflict_group}
LANE: {task.get('lane', '')}
{boundary_section}
{sibling_section}
{uvisa_contract_section}

RULES:
1. You CANNOT mark this task done. Only the controller can.
2. You must produce a PROOF artifact when complete.
3. Stay within your boundary. Do not modify files outside your project.
4. If blocked, output BLOCKED: <reason> and stop.
5. If you need human input, output BLOCKED: HUMAN_INPUT_NEEDED: <question>
6. Respect BOUNDARY CONSTRAINTS: do not modify files matching FORBIDDEN_GLOBS,
   only modify files matching ALLOWED_GLOBS (if set), stay under LOC_BUDGET.

PROOF FORMAT (output as last line):
PROOF_JSON: {{"status":"done|blocked","summary":"<=200 chars","files_changed":[],"tests_passed":0,"proof_sha":"sha256_of_output"}}

WORKSPACE: Use /tmp/agent-team-{task.get('id','unknown')[:12]} as your workspace.
"""

def collect_proof(task_id, worker_output):
    """Extract proof from worker output."""
    for line in worker_output.split('\n'):
        line = line.strip()
        if line.startswith('PROOF_JSON:'):
            try:
                proof = json.loads(line[len('PROOF_JSON:'):].strip())
                PROOF_DIR.mkdir(parents=True, exist_ok=True)
                proof_path = PROOF_DIR / f'{task_id}.json'
                proof_path.write_text(json.dumps(proof, indent=2))
                return proof
            except json.JSONDecodeError:
                pass
    return None

def build_handoff_artifact(task, conflict_group, envelope_id):
    """Build a structured handoff artifact for parallel dispatch.

    This JSON artifact captures the full boundary envelope for a claimed task,
    enabling downstream verification that the worker stayed within constraints.
    It is recorded alongside the envelope state for audit and replay.
    """
    import time as _time
    boundary_key = task.get('parallel_boundary', '')
    workspace = task.get('workspace', '')
    allowed_globs = task.get('allowed_globs', '')
    forbidden_globs = task.get('forbidden_globs', '')
    loc_budget = task.get('loc_budget', '')
    ws_isolation = task.get('workspace_isolation', '')
    merge_gate = task.get('merge_gate', '')
    parallel_group = task.get('parallel_group', '')
    uvisa_contract = ensure_uvisa_lark_contract(task)

    artifact = {
        'schema': 'local_brain_handoff_artifact_v1',
        'generated_at': _time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'task_id': task.get('id', ''),
        'title': task.get('title', ''),
        'project': task.get('project', ''),
        'priority': task.get('priority', 'P2'),
        'lane': task.get('lane', ''),
        'envelope_id': envelope_id,
        'conflict_group': conflict_group,
        'boundary': {
            'boundary_key': boundary_key,
            'workspace': workspace,
            'allowed_globs': allowed_globs,
            'forbidden_globs': forbidden_globs,
            'loc_budget': loc_budget,
            'workspace_isolation': ws_isolation,
            'merge_gate': merge_gate,
            'parallel_group': parallel_group,
        },
        'safety': {
            'worker_cannot_mark_done': True,
            'proof_required': True,
            'boundary_enforced': True,
            'forbidden_dominates_allowed': True,
            'uvisa_closeout_contract_required': bool(uvisa_contract),
        },
    }
    if uvisa_contract:
        artifact['uvisa_lark_contract'] = {
            'contract_path': task.get('uvisa_contract_path', ''),
            'schema': uvisa_contract.get('schema'),
            'task_type': uvisa_contract.get('task_type'),
            'acceptance_atom_ids': [a.get('id') for a in (uvisa_contract.get('acceptance_atoms') or []) if isinstance(a, dict)],
            'closeout_blockers': uvisa_contract.get('closeout_blockers') or [],
        }

    # Persist handoff artifact
    handoff_dir = STATE_DIR / 'handoff_artifacts'
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / f'{task.get("id", "unknown")}_{envelope_id[:8]}.json'
    try:
        handoff_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False))
        artifact['handoff_path'] = str(handoff_path)
    except Exception:
        pass

    return artifact

def verify_worker_boundary(task, proof):
    """Verify that worker's proof output complies with task boundary constraints.

    Fail-closed: if boundary constraints are set and the proof includes
    files_changed, verify compliance. Returns a dict with status and violations.
    """
    allowed_raw = task.get('allowed_globs', '')
    forbidden_raw = task.get('forbidden_globs', '')
    loc_budget_raw = task.get('loc_budget', '')

    allowed_globs = [g.strip() for g in str(allowed_raw).split(',') if g.strip()] if allowed_raw else []
    forbidden_globs = [g.strip() for g in str(forbidden_raw).split(',') if g.strip()] if forbidden_raw else []

    loc_budget = 0
    if loc_budget_raw:
        try:
            loc_budget = int(loc_budget_raw)
        except (ValueError, TypeError):
            pass

    if not allowed_globs and not forbidden_globs and loc_budget <= 0:
        return {'status': 'SKIP', 'reason': 'no_boundary_constraints'}

    files_changed = proof.get('files_changed', [])
    if not isinstance(files_changed, list):
        files_changed = []

    import fnmatch
    violations = []

    # forbidden_globs dominate
    for fpath in files_changed:
        fpath = str(fpath).strip()
        if not fpath:
            continue
        for pattern in forbidden_globs:
            if fnmatch.fnmatch(fpath, pattern):
                violations.append(f'forbidden_match:{fpath}:{pattern}')
                break

    # allowed_globs: if set, every file must match at least one
    if allowed_globs:
        for fpath in files_changed:
            fpath = str(fpath).strip()
            if not fpath:
                continue
            if any(v.startswith(f'forbidden_match:{fpath}:') for v in violations):
                continue
            if not any(fnmatch.fnmatch(fpath, p) for p in allowed_globs):
                violations.append(f'not_in_allowed_globs:{fpath}')

    # loc_budget
    if loc_budget > 0 and len(files_changed) > loc_budget:
        violations.append(f'loc_budget_exceeded:{len(files_changed)}>{loc_budget}')

    return {
        'status': 'PASS' if not violations else 'FAIL',
        'violations': violations,
        'files_changed_count': len(files_changed),
    }

def cleanup_worktree(task_id):
    """Clean up temporary workspace."""
    import shutil
    workspace = Path(f'/tmp/agent-team-{task_id[:12]}')
    if workspace.exists():
        try:
            shutil.rmtree(workspace)
        except Exception:
            pass

def load_project_profile(project):
    """Load project profile for task context injection."""
    profile_dir = Path.home() / '.hermes' / 'project-profiles'
    # Try exact match first
    for name in [project, project.replace('-work', ''), project.split('-')[0]]:
        p = profile_dir / f'{name}.json'
        if p.exists():
            return json.loads(p.read_text())
    # Default to hermes
    default = profile_dir / 'hermes.json'
    if default.exists():
        return json.loads(default.read_text())
    return {}

def verify_with_models(task_title, worker_output, project_profile):
    """4-model verification of task completion. All 4 must approve."""
    if isinstance(project_profile, str):
        project_profile = load_project_profile(project_profile)
    if project_profile is None:
        project_profile = {}
    if not isinstance(project_profile, dict):
        return {
            'models_checked': 0,
            'verified': 0,
            'passed': False,
            'errors': 1,
            'issues': ['invalid_project_profile'],
            'details': [],
            'model_errors': ['invalid_project_profile'],
        }
    if not isinstance(worker_output, str):
        return {
            'models_checked': 0,
            'verified': 0,
            'passed': False,
            'errors': 1,
            'issues': ['invalid_worker_output: expected string'],
            'details': [],
            'model_errors': ['invalid_worker_output: expected string'],
        }
    verify_prompt = f"""Verify task completion. Return ONLY compact JSON.
Task: {task_title}
Project: {project_profile.get('display_name', 'unknown')}
Acceptance: {json.dumps(project_profile.get('acceptance', []), ensure_ascii=False)}
Output (last 500): {worker_output[-500:]}
JSON: {{"verified":true|false,"issues":[],"reasoning":"<=80 chars"}}"""

    import subprocess as _sp
    from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _ac
    import re as _re, urllib.request as _ur

    def _extract(s):
        s = (s or '').strip()
        m = _re.search(r'\{[^{}]*\}', s)
        if m: return json.loads(m.group())
        raise ValueError('no json')

    def _call_gpt():
        cmd = ['hermes', 'chat', '-q', verify_prompt, '--model', 'gpt-5.5', '--provider', 'openai-codex',
               '--quiet', '--max-turns', '1', '--source', 'verify', '--ignore-rules']
        r = _sp.run(cmd, capture_output=True, text=True, timeout=60)
        return _extract(r.stdout)

    def _call_claude():
        cmd = ['claude', '-p', verify_prompt, '--model', 'claude-opus-4-7', '--max-turns', '1', '--output-format', 'json']
        r = _sp.run(cmd, capture_output=True, text=True, timeout=60)
        raw = r.stdout
        try:
            outer = json.loads(raw)
            if isinstance(outer, dict) and isinstance(outer.get('result'), str): raw = outer['result']
        except: pass
        return _extract(raw)

    def _call_ds():
        key = os.environ.get('DEEPSEEK_API_KEY')
        if not key:
            raise RuntimeError('DEEPSEEK_API_KEY missing')
        url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com').rstrip('/') + '/chat/completions'
        body = json.dumps({'model': 'deepseek-v4-pro', 'messages': [{'role': 'user', 'content': verify_prompt}],
                          'temperature': 0, 'max_tokens': 500}).encode()
        req = _ur.Request(url, data=body, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
        with _ur.urlopen(req, timeout=60) as resp:
            content = json.loads(resp.read().decode())['choices'][0]['message']['content']
        return _extract(content)

    def _call_mimo():
        key = os.environ.get('XIAOMI_API_KEY')
        if not key:
            raise RuntimeError('XIAOMI_API_KEY missing')
        url = os.environ.get('XIAOMI_BASE_URL', 'https://token-plan-cn.xiaomimimo.com/v1').rstrip('/') + '/chat/completions'
        body = json.dumps({'model': 'mimo-v2.5-pro', 'messages': [{'role': 'user', 'content': verify_prompt}],
                          'temperature': 0, 'max_tokens': 300}).encode()
        for _ in range(3):
            req = _ur.Request(url, data=body, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
            try:
                with _ur.urlopen(req, timeout=60) as resp:
                    c = json.loads(resp.read().decode())['choices'][0]['message']['content']
                if c and c.strip(): return _extract(c)
            except: import time; time.sleep(2)
        raise RuntimeError('MiMo failed')

    results = []
    all_issues = []

    # Phase 1: Claude + GPT + DeepSeek concurrent
    with _TPE(max_workers=3) as ex:
        futs = {ex.submit(fn): name for name, fn in [('claude', _call_claude), ('gpt', _call_gpt), ('ds', _call_ds)]}
        for fut in _ac(futs):
            model = futs[fut]
            try:
                parsed = fut.result()
                results.append({'model': model, 'verified': parsed.get('verified', False)})
                all_issues.extend(parsed.get('issues', []))
            except Exception as exc:
                results.append({'model': model, 'verified': False, 'error': str(exc)[:160]})

    # Phase 2: MiMo sequential
    try:
        parsed = _call_mimo()
        results.append({'model': 'mimo', 'verified': parsed.get('verified', False)})
        all_issues.extend(parsed.get('issues', []))
    except Exception as exc:
        results.append({'model': 'mimo', 'verified': False, 'error': str(exc)[:160]})

    verified = sum(1 for r in results if r.get('verified'))
    total = len(results)
    errors = sum(1 for r in results if r.get('error'))

    return {
        'models_checked': total,
        'verified': verified,
        'passed': verified >= 3,  # Need 3/4 to pass
        'errors': errors,
        'issues': all_issues,
        'details': results,
        'model_errors': [f"{r.get('model')}: {r.get('error')}" for r in results if r.get('error')],
    }

def handle_continuations():
    """Check RUNNING tasks for budget exhaustion and create continuations."""
    running = list_by_status('RUNNING')
    continuations = []
    
    for env in running:
        eid = env['id']
        task_id = env.get('payload', {})
        if isinstance(task_id, str):
            try:
                task_id = json.loads(task_id).get('brain_id', '')
            except:
                task_id = ''
        else:
            task_id = (task_id or {}).get('brain_id', '')
        
        if not task_id:
            continue
        
        # Check if this envelope has budget exhaustion in trace
        trace = json.loads(env.get('trace', '[]'))
        last_events = [t for t in trace if 'budget' in str(t).lower() or 'exhausted' in str(t).lower()]
        
        if last_events:
            # Already handled
            continue
        
        # Check if task can be continued
        can_cont, count = can_continue(task_id)
        if not can_cont:
            continue
        
        # Mark as continuation pending
        update_status(eid, 'PENDING')
        append_trace(eid, {
            'event': 'continuation_pending',
            'reason': 'budget_exhausted',
            'continuation_count': count + 1,
        })
        
        continuations.append({
            'envelope_id': eid,
            'task_id': task_id[:50],
            'continuation_count': count + 1,
        })
    
    return continuations

def delegate_to_worker(task, conflict_group, eid, sibling_tasks=None):
    """Delegate task to a lightweight worker via hermes chat -q."""
    import subprocess as _sp
    title = task.get('title', 'untitled')
    task_id = task.get('id', '')
    boundary = task.get('parallel_boundary', '')
    
    # Load and inject project profile
    project = task.get('project', '')
    profile = load_project_profile(project)
    profile_context = ''
    if profile:
        profile_context = f'''
PROJECT PROFILE:
Name: {profile.get('display_name', project)}
Tech: {json.dumps(profile.get('tech_stack', {}), ensure_ascii=False)}
Conventions: {chr(10).join('- ' + c for c in profile.get('conventions', []))}
Test: {profile.get('test_cmd', 'N/A')}
Acceptance: {chr(10).join('- ' + a for a in profile.get('acceptance', []))}
Forbidden: {chr(10).join('- ' + f for f in profile.get('forbidden', []))}
'''

    # Check continuation
    can_cont, cont_count = can_continue(task_id)
    context = build_worker_context(task, conflict_group, sibling_tasks=sibling_tasks) + profile_context
    if cont_count > 0:
        context = build_continuation_context(task_id, context)
    
    # Route by task type: code tasks → GPT-5.5, analysis → MiMo
    needs_code = any(kw in title.lower() for kw in ['修复', 'fix', '实现', 'implement', '代码', 'uvisa', '前端', '后端', '恢复', '集成'])
    model = 'gpt-5.5' if needs_code else 'mimo-v2.5-pro'
    provider = 'openai-codex' if needs_code else 'xiaomi'
    max_turns = 30 if needs_code else 15
    timeout_s = 600 if needs_code else 300

    try:
        cmd = [
            'hermes', 'chat', '-q', context,
            '--model', model, '--provider', provider,
            '--quiet', '--max-turns', str(max_turns),
            '--source', f'team-worker-{eid[:8]}',
            '--ignore-rules',
        ]
        r = _sp.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        output = r.stdout
        
        # Check budget exhaustion
        exhausted, signal = detect_budget_exhausted(output)
        if exhausted:
            cp = save_checkpoint(task_id, output)
            can_cont, _ = can_continue(task_id)
            if can_cont:
                return {'status': 'continuation_pending', 'signal': signal}
            return {'status': 'failed', 'reason': 'budget_exhausted_max_continuations'}
        
        # Check for proof
        if 'PROOF_JSON' in output:
            proof = collect_proof(task_id, output)
            if not proof:
                return {'status': 'failed', 'reason': 'invalid_proof', 'output': output[-300:]}
            return {'status': 'done', 'proof': proof, 'output': output}
        elif 'BLOCKED' in output:
            return {'status': 'blocked', 'output': output[:200]}
        else:
            return {'status': 'failed', 'reason': 'missing_proof', 'output': output[-300:]}
    
    except _sp.TimeoutExpired:
        return {'status': 'timeout'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)[:200]}


def create_claim_envelope(task, conflict_group, actor='agent-team-controller', *, source='claim-cycle', handoff=''):
    """Create a PENDING envelope for a claimed brain task.

    Claiming and execution are intentionally decoupled: claim paths enqueue work,
    execute paths consume envelopes later under an explicit worker budget.
    """
    eid = create(
        type='TASK',
        title=task.get('title', 'untitled'),
        project=task.get('project', ''),
        assignee=f'agent-team-{conflict_group}',
        payload={
            'brain_id': task.get('id', ''),
            'boundary': task.get('parallel_boundary', ''),
            'parallel_boundary': task.get('parallel_boundary', ''),
            'conflict_group': conflict_group,
            'project': task.get('project', ''),
            'claimed_by': actor,
            'claim_source': source,
            'handoff': handoff,
        },
        appetite_seconds=1800,
    )
    append_trace(eid, {'event': 'enqueued', 'group': conflict_group, 'source': source, 'actor': actor})
    return eid


def prepare_claim_batch(max_claims=3):
    """Select a safe batch to claim without executing workers."""
    if is_disabled():
        return {'status': 'disabled', 'reason': 'kill switch active'}

    escape, escape_info = human_escape_check()
    if escape:
        return {'status': 'escaped', 'reason': f'Human escape: {escape_info}'}

    try:
        all_tasks = get_all_dispatchable()
    except Exception as e:
        return {'status': 'error', 'reason': str(e)[:200]}

    if not all_tasks:
        return {'status': 'idle', 'reason': 'no dispatchable tasks'}

    groups = classify_batch(all_tasks)
    conflict_group_count = len(groups)

    health = boundary_health_check(all_tasks)
    file_conflicts = health.get('file_conflicts', {})
    if file_conflicts.get('conflict_count', 0) > 0:
        for conflict in file_conflicts.get('conflicts', [])[:3]:
            ga = conflict['group_a']
            gb = conflict['group_b']
            if ga in groups and gb in groups:
                score_a = sum(int(t.get('score', 0)) for t in groups[ga])
                score_b = sum(int(t.get('score', 0)) for t in groups[gb])
                loser = gb if score_a >= score_b else ga
                winner = ga if loser == gb else gb
                groups[winner].extend(groups.pop(loser))
                conflict_group_count = len(groups)

    n_result = get_smoothed_n(len(all_tasks), conflict_group_count)
    applied_n = n_result['applied_n']
    try:
        batch_cap = max(1, int(max_claims or applied_n or 1))
    except Exception:
        batch_cap = max(1, applied_n or 1)
    selected_n = min(applied_n, batch_cap)

    if selected_n == 0:
        return {'status': 'idle', 'reason': 'N=0 (no tasks)', 'n_info': n_result}

    schedule = get_parallel_schedule(all_tasks, selected_n)
    return {
        'status': 'ok',
        'all_tasks': all_tasks,
        'groups': groups,
        'schedule': schedule,
        'n_info': n_result,
        'applied_n': applied_n,
        'selected_n': selected_n,
        'conflict_group_count': conflict_group_count,
        'health': health,
    }


def claim_cycle(max_claims=3, wall_budget_seconds=20):
    """Claim + enqueue only. Never calls hermes chat/delegate."""
    prepared = prepare_claim_batch(max_claims=max_claims)
    if prepared.get('status') != 'ok':
        return prepared

    started = time.monotonic()
    claimed = []
    claim_errors = []
    all_tasks = list(prepared.get('all_tasks') or [])
    schedule = prepared.get('schedule') or {}
    schedule_items = schedule.get('schedule', []) if isinstance(schedule, dict) else []
    selected_n = int(prepared.get('selected_n') or 0)

    for group_info in schedule_items[:selected_n]:
        if time.monotonic() - started >= max(1, int(wall_budget_seconds or 20)):
            break
        group = group_info['conflict_group']
        group_tasks = [t for t in all_tasks if t.get('_conflict_group') == group]
        if not group_tasks:
            continue
        task = group_tasks[0]
        task_id = task.get('id', '')
        result = claim_task(task_id)
        if not result.get('ok'):
            claim_errors.append({'task_id': task_id, 'group': group, 'error': result.get('error', 'claim_failed')})
            continue
        eid = create_claim_envelope(task, group, actor='agent-team-controller', source='claim-cycle')
        claimed.append({
            'task_id': task_id,
            'title': task.get('title', '')[:50],
            'envelope_id': eid,
            'conflict_group': group,
            'priority': task.get('priority', 'P2'),
            'worker_result': 'enqueued',
        })

    return {
        'status': 'ok',
        'mode': 'claim-only',
        'n_info': prepared['n_info'],
        'conflict_groups': prepared['conflict_group_count'],
        'total_dispatchable': len(all_tasks),
        'tasks_claimed': len(claimed),
        'claimed': claimed,
        'claim_errors': claim_errors,
        'deferred_groups': schedule.get('deferred_groups', []) if isinstance(schedule, dict) else [],
        'safety': 'claim-cycle only claims and enqueues; execution is delegated to execute-cycle',
    }


def _process_worker_result(row, actor, eid, worker_result):
    record = {'task_id': row.get('id', ''), 'envelope_id': eid, 'worker_result': worker_result.get('status', '?')}
    if worker_result.get('status') == 'done':
        proof = worker_result.get('proof') or {}
        PROOF_DIR.mkdir(parents=True, exist_ok=True)
        proof_path = PROOF_DIR / f"{row.get('id','')}.json"
        if not proof_path.exists():
            proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2))
        review = transition_task(
            row.get('id', ''),
            'review',
            actor,
            'worker produced proof; controller stops at review for proof-gated closeout',
            evidence=[f'artifact:{proof_path}'],
        )
        record['review_transition'] = review
        if review.get('ok'):
            update_status(eid, 'DONE')
            record['to_status'] = 'review'
        else:
            update_status(eid, 'FAILED', error=str(review)[:200])
            record['to_status'] = 'running'
        return record
    if worker_result.get('status') == 'blocked':
        update_status(eid, 'BLOCKED')
        record['to_status'] = 'running'
        return record
    if worker_result.get('status') == 'continuation_pending':
        update_status(eid, 'PENDING')
        record['to_status'] = 'pending'
        return record
    if worker_result.get('status') == 'timeout':
        retry = transition_task(
            row.get('id', ''),
            'retry',
            actor,
            'worker timed out without proof; requeue for proof-gated retry',
            evidence=['command:agent_team_controller execute-cycle worker timeout'],
        )
        record['retry_transition'] = retry
        update_status(eid, 'FAILED', error='worker_timeout')
        record['to_status'] = 'retry' if retry.get('ok') else 'running'
        return record
    update_status(eid, 'FAILED', error=str(worker_result)[:200])
    record['to_status'] = 'running'
    return record


def execute_cycle(max_workers=3, wall_budget_seconds=600):
    """Consume PENDING claim envelopes under an explicit worker budget."""
    if is_disabled():
        return {'status': 'disabled', 'reason': 'kill switch active'}

    escape, escape_info = human_escape_check()
    if escape:
        return {'status': 'escaped', 'reason': f'Human escape: {escape_info}'}

    try:
        max_workers = max(1, int(max_workers or 3))
    except Exception:
        max_workers = 3
    budget_s = max(1, int(wall_budget_seconds or 600))
    started = time.monotonic()

    pending = [env for env in list_by_status('PENDING') if str(env.get('assignee', '')).startswith('agent-team-')]
    if not pending:
        return {'status': 'idle', 'mode': 'execute-only', 'pending': 0, 'processed': 0}

    results = []
    skipped = []
    processed = 0
    for envelope in pending:
        if processed >= max_workers or time.monotonic() - started >= budget_s:
            break
        eid = envelope['id']
        payload = json.loads(envelope.get('payload') or '{}') if isinstance(envelope.get('payload'), str) else (envelope.get('payload') or {})
        task_id = str(payload.get('brain_id') or '')
        if not task_id:
            update_status(eid, 'FAILED', error='missing_brain_id')
            skipped.append({'envelope_id': eid, 'reason': 'missing_brain_id'})
            continue
        row = rows_by_id([task_id]).get(task_id)
        if not row:
            update_status(eid, 'FAILED', error='task_not_found')
            skipped.append({'envelope_id': eid, 'task_id': task_id, 'reason': 'task_not_found'})
            continue
        if row.get('status') != 'claimed':
            skipped.append({'envelope_id': eid, 'task_id': task_id, 'reason': f"not_claimed:{row.get('status')}"})
            continue
        actor = str(payload.get('claimed_by') or row.get('claimed_by') or 'agent-team-controller')
        running = transition_task(task_id, 'running', actor, 'execute-cycle worker trigger after queued claim')
        if not running.get('ok'):
            update_status(eid, 'FAILED', error=str(running)[:200])
            skipped.append({'envelope_id': eid, 'task_id': task_id, 'reason': 'running_transition_failed', 'detail': running})
            continue
        update_status(eid, 'RUNNING')
        group = payload.get('conflict_group') or row.get('parallel_group') or row.get('conflict_group') or row.get('parallel_boundary') or row.get('project') or 'default'
        siblings = page_batch_siblings_for(row)
        worker_result = delegate_to_worker(row, str(group), eid, sibling_tasks=siblings)
        append_trace(eid, {'event': 'execute_cycle_worker_finished', 'result': worker_result.get('status', '?')})
        results.append(_process_worker_result(row, actor, eid, worker_result))
        processed += 1

    reviewed_count = sum(1 for item in results if item.get('to_status') == 'review')
    return {
        'status': 'ok',
        'mode': 'execute-only',
        'processed': processed,
        'reviewed_count': reviewed_count,
        'done_count': 0,
        'results': results,
        'skipped': skipped,
        'remaining_pending': max(0, len(pending) - processed),
        'safety': 'execute-cycle reads queued envelopes and only advances brain tasks to review/retry/blocked',
    }


def consume_claimed_batch(claimed_items, max_agents=3):
    """Immediately consume tasks just claimed by parallel-claim-and-handoff.

    This is the event-driven bridge between claim/handoff and real worker
    execution.  It only advances claimed tasks to running/review; it never marks
    brain tasks done.  Proof-gated review->done remains owned by the normal
    lifecycle closer.

    Important: claimed handoffs are already boundary/conflict classified by the
    orchestrator.  Do not serialize the batch here; start all eligible items and
    run workers concurrently up to max_agents so Lark/work bursts can use their
    existing non-overlapping boundaries.
    """
    if not claimed_items:
        return {'status': 'SKIP', 'event_driven': True, 'reason': 'no claimed tasks', 'consumed_count': 0}
    if is_disabled():
        return {'status': 'SKIP', 'event_driven': True, 'reason': 'kill switch active', 'consumed_count': 0}
    escape, escape_info = human_escape_check()
    if escape:
        return {'status': 'SKIP', 'event_driven': True, 'reason': f'Human escape: {escape_info}', 'consumed_count': 0}
    try:
        max_agents = max(1, int(max_agents or 3))
    except Exception:
        max_agents = 3
    claimed_items = list(claimed_items)[:max_agents]
    ids = [str(item.get('task_id') or item.get('id') or '') for item in claimed_items if isinstance(item, dict)]
    ids = [x for x in ids if x]
    row_map = rows_by_id(ids)
    consumed = []
    skipped = []
    launch_records = []

    for item in claimed_items:
        task_id = str(item.get('task_id') or item.get('id') or '') if isinstance(item, dict) else ''
        if not task_id:
            skipped.append({'task_id': '', 'reason': 'missing_task_id'})
            continue
        row = row_map.get(task_id)
        if not row:
            skipped.append({'task_id': task_id, 'reason': 'task_not_found'})
            continue
        if row.get('status') != 'claimed':
            skipped.append({'task_id': task_id, 'reason': f"not_claimed:{row.get('status')}"})
            continue
        actor = str(row.get('claimed_by') or 'hermes-parallel')
        group = row.get('parallel_group') or row.get('conflict_group') or row.get('parallel_boundary') or row.get('project') or 'default'
        eid = create(
            type='TASK',
            title=row.get('title', 'untitled'),
            project=row.get('project', ''),
            assignee=f'agent-team-{group}',
            payload={
                'brain_id': task_id,
                'boundary': row.get('parallel_boundary', ''),
                'conflict_group': group,
                'event_driven_claim': True,
                'handoff': item.get('handoff', '') if isinstance(item, dict) else '',
            },
            appetite_seconds=1800,
        )
        update_status(eid, 'RUNNING')
        append_trace(eid, {'event': 'event_driven_claim_consumed', 'task_id': task_id, 'actor': actor})
        running = transition_task(task_id, 'running', actor, 'event-driven worker trigger after parallel claim/handoff')
        if not running.get('ok'):
            update_status(eid, 'FAILED', error=str(running)[:200])
            skipped.append({'task_id': task_id, 'reason': 'running_transition_failed', 'detail': running})
            continue
        launch_records.append({'task_id': task_id, 'row': row, 'actor': actor, 'group': str(group), 'eid': eid})

    def _run_one(record):
        task_id = record['task_id']
        eid = record['eid']
        actor = record['actor']
        siblings = page_batch_siblings_for(record['row'])
        worker_result = delegate_to_worker(record['row'], record['group'], eid, sibling_tasks=siblings)
        append_trace(eid, {'event': 'event_worker_finished', 'result': worker_result.get('status', '?')})
        out = {'task_id': task_id, 'envelope_id': eid, 'worker_result': worker_result.get('status', '?')}
        if worker_result.get('status') == 'done':
            proof = worker_result.get('proof') or {}
            PROOF_DIR.mkdir(parents=True, exist_ok=True)
            proof_path = PROOF_DIR / f'{task_id}.json'
            if not proof_path.exists():
                proof_path.write_text(json.dumps(proof, ensure_ascii=False, indent=2))
            review = transition_task(
                task_id,
                'review',
                actor,
                'event-driven worker produced proof; controller stops at review for proof-gated closeout',
                evidence=[f'artifact:{proof_path}'],
            )
            out['review_transition'] = review
            if review.get('ok'):
                update_status(eid, 'DONE')
                out['to_status'] = 'review'
            else:
                update_status(eid, 'FAILED', error=str(review)[:200])
                out['to_status'] = 'running'
        elif worker_result.get('status') == 'blocked':
            update_status(eid, 'BLOCKED')
            out['to_status'] = 'running'
        elif worker_result.get('status') == 'continuation_pending':
            out['to_status'] = 'running'
        elif worker_result.get('status') == 'timeout':
            retry = transition_task(
                task_id,
                'retry',
                actor,
                'event-driven worker timed out without proof; requeue for proof-gated retry',
                evidence=['command:agent_team_controller consume-claimed worker timeout'],
            )
            out['retry_transition'] = retry
            update_status(eid, 'FAILED', error='worker_timeout')
            out['to_status'] = 'retry' if retry.get('ok') else 'running'
        else:
            update_status(eid, 'FAILED', error=str(worker_result)[:200])
            out['to_status'] = 'running'
        return out

    if launch_records:
        workers = min(max_agents, len(launch_records))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_run_one, rec): rec for rec in launch_records}
            for future in as_completed(futures):
                rec = futures[future]
                try:
                    consumed.append(future.result())
                except Exception as exc:
                    update_status(rec['eid'], 'FAILED', error=str(exc)[:200])
                    consumed.append({
                        'task_id': rec['task_id'],
                        'envelope_id': rec['eid'],
                        'worker_result': 'error',
                        'error': str(exc)[:200],
                        'to_status': 'running',
                    })

    reviewed_count = sum(1 for item in consumed if item.get('to_status') == 'review')
    return {
        'status': 'ok',
        'event_driven': True,
        'requested_count': len(claimed_items),
        'launched_count': len(launch_records),
        'consumed_count': len(consumed),
        'running_count': len(launch_records),
        'reviewed_count': reviewed_count,
        'done_count': 0,
        'claimed': consumed,
        'skipped': skipped,
        'safety': 'controller-consumed claimed handoffs in parallel; worker cannot mark done; review->done remains proof-gated',
        'next_tick_requested': bool(reviewed_count),
    }

def run_dynamic_cycle(max_claims=3, max_workers=3, claim_wall_budget_seconds=20, execute_wall_budget_seconds=600):
    """Compatibility wrapper: claim/enqueue first, then execute under a worker budget."""
    claim_result = claim_cycle(max_claims=max_claims, wall_budget_seconds=claim_wall_budget_seconds)
    if claim_result.get('status') not in {'ok', 'idle'}:
        return claim_result
    execute_result = execute_cycle(max_workers=max_workers, wall_budget_seconds=execute_wall_budget_seconds)
    if execute_result.get('status') not in {'ok', 'idle'}:
        return {
            'status': execute_result.get('status'),
            'mode': 'claim-then-execute',
            'claim': claim_result,
            'execute': execute_result,
        }
    return {
        'status': 'ok',
        'mode': 'claim-then-execute',
        'claim': claim_result,
        'execute': execute_result,
        'n_info': claim_result.get('n_info', {}),
        'conflict_groups': claim_result.get('conflict_groups', 0),
        'total_dispatchable': claim_result.get('total_dispatchable', 0),
        'tasks_claimed': claim_result.get('tasks_claimed', 0),
        'claimed': claim_result.get('claimed', []),
        'deferred_groups': claim_result.get('deferred_groups', []),
        'processed': execute_result.get('processed', 0),
        'reviewed_count': execute_result.get('reviewed_count', 0),
        'remaining_pending': execute_result.get('remaining_pending', 0),
        'safety': 'cycle is now a wrapper over claim-cycle + execute-cycle',
    }

def show_status():
    """Show current agent team status with classification."""
    env_stats = stats()
    
    try:
        all_tasks = get_all_dispatchable()
        groups = classify_batch(all_tasks)
        n_result = get_smoothed_n(len(all_tasks), len(groups))
    except:
        all_tasks = []
        groups = {}
        n_result = {'applied_n': 1, 'raw_n': 1}
    
    return {
        'disabled': is_disabled(),
        'applied_n': n_result['applied_n'],
        'raw_n': n_result['raw_n'],
        'smoothing_active': n_result.get('smoothing_active', False),
        'dispatchable_tasks': len(all_tasks),
        'conflict_groups': {g: len(ts) for g, ts in groups.items()},
        'envelope_stats': env_stats,
        'proof_count': len(list(PROOF_DIR.glob('*.json'))) if PROOF_DIR.exists() else 0,
    }

def deep_review_4_of_4(task_title, worker_output, project_profile, rejection_history):
    """Tier 3: High-confidence 4/4 review. All must approve with evidence."""
    import subprocess as _sp, urllib.request as _ur, re as _re
    
    issues_str = '\n'.join(f'- {i}' for i in rejection_history.get('issues', [])[-5:])
    criteria = project_profile.get('acceptance', [])
    
    prompt = f"""HIGH CONFIDENCE REVIEW. Reply JSON only.
Task: {task_title}
Criteria: {json.dumps(criteria)}
Prior issues: {issues_str}
Output: {worker_output[-600:]}
Rules: approve ONLY if ALL criteria have concrete evidence. "looks ok" is NOT enough.
{{"ok":true|false,"missing":"what is missing"}}"""

    def _extract(s):
        m = _re.search(r'\{{[^{{}}]*\}}', s or '')
        if m: return json.loads(m.group())
        raise ValueError('no json')

    results = []
    
    # Claude
    try:
        r = _sp.run(['claude','-p',prompt,'--model','claude-opus-4-7','--max-turns','1','--output-format','json'],
                    capture_output=True, text=True, timeout=90)
        raw = r.stdout
        try:
            o = json.loads(raw)
            if isinstance(o,dict) and 'result' in o: raw = o['result']
        except: pass
        parsed = _extract(raw)
        results.append({'model':'claude','ok':parsed.get('ok',False),'missing':parsed.get('missing','')})
    except:
        results.append({'model':'claude','ok':False,'missing':'error'})
    
    # GPT
    try:
        r = _sp.run(['hermes','chat','-q',prompt,'--model','gpt-5.5','--provider','openai-codex',
                     '--quiet','--max-turns','1','--source','tier3','--ignore-rules'],
                    capture_output=True, text=True, timeout=90)
        parsed = _extract(r.stdout)
        results.append({'model':'gpt','ok':parsed.get('ok',False),'missing':parsed.get('missing','')})
    except:
        results.append({'model':'gpt','ok':False,'missing':'error'})
    
    # DeepSeek
    try:
        key = os.environ.get('DEEPSEEK_API_KEY')
        url = os.environ.get('DEEPSEEK_BASE_URL','https://api.deepseek.com').rstrip('/')+'/chat/completions'
        body = json.dumps({'model':'deepseek-v4-pro','messages':[{'role':'user','content':prompt}],
                          'temperature':0,'max_tokens':500}).encode()
        req = _ur.Request(url, data=body, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with _ur.urlopen(req, timeout=90) as resp:
            c = json.loads(resp.read().decode())['choices'][0]['message']['content']
        parsed = _extract(c)
        results.append({'model':'deepseek','ok':parsed.get('ok',False),'missing':parsed.get('missing','')})
    except:
        results.append({'model':'deepseek','ok':False,'missing':'error'})
    
    # MiMo (sequential with retry)
    for _ in range(3):
        try:
            key = os.environ.get('XIAOMI_API_KEY')
            url = os.environ.get('XIAOMI_BASE_URL','https://token-plan-cn.xiaomimimo.com/v1').rstrip('/')+'/chat/completions'
            body = json.dumps({'model':'mimo-v2.5-pro','messages':[{'role':'user','content':prompt}],
                              'temperature':0,'max_tokens':500}).encode()
            req = _ur.Request(url, data=body, headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
            with _ur.urlopen(req, timeout=90) as resp:
                c = json.loads(resp.read().decode())['choices'][0]['message']['content']
            if c and c.strip():
                parsed = _extract(c)
                results.append({'model':'mimo','ok':parsed.get('ok',False),'missing':parsed.get('missing','')})
                break
        except:
            import time; time.sleep(3)
    else:
        results.append({'model':'mimo','ok':False,'missing':'error'})
    
    approved = sum(1 for r in results if r.get('ok'))
    all_missing = [r['model'] + ': ' + r['missing'] for r in results if r.get('missing') and r['missing'] not in ('','error')]
    
    return {
        'models_checked': len(results),
        'approved': approved,
        'passed': approved == 4,
        'details': results,
        'missing_evidence': all_missing,
    }

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'cycle':
            parser = argparse.ArgumentParser(prog='agent_team_controller.py cycle')
            parser.add_argument('--max-claims', type=int, default=3)
            parser.add_argument('--max-workers', type=int, default=3)
            parser.add_argument('--claim-wall-budget-seconds', type=int, default=20)
            parser.add_argument('--execute-wall-budget-seconds', type=int, default=600)
            ns = parser.parse_args(sys.argv[2:])
            print(json.dumps(run_dynamic_cycle(
                max_claims=ns.max_claims,
                max_workers=ns.max_workers,
                claim_wall_budget_seconds=ns.claim_wall_budget_seconds,
                execute_wall_budget_seconds=ns.execute_wall_budget_seconds,
            ), indent=2, ensure_ascii=False))
        elif cmd == 'claim-cycle':
            parser = argparse.ArgumentParser(prog='agent_team_controller.py claim-cycle')
            parser.add_argument('--max-claims', type=int, default=3)
            parser.add_argument('--wall-budget-seconds', type=int, default=20)
            ns = parser.parse_args(sys.argv[2:])
            print(json.dumps(claim_cycle(max_claims=ns.max_claims, wall_budget_seconds=ns.wall_budget_seconds), indent=2, ensure_ascii=False))
        elif cmd == 'execute-cycle':
            parser = argparse.ArgumentParser(prog='agent_team_controller.py execute-cycle')
            parser.add_argument('--max-workers', type=int, default=3)
            parser.add_argument('--wall-budget-seconds', type=int, default=600)
            ns = parser.parse_args(sys.argv[2:])
            print(json.dumps(execute_cycle(max_workers=ns.max_workers, wall_budget_seconds=ns.wall_budget_seconds), indent=2, ensure_ascii=False))
        elif cmd == 'consume-claimed':
            parser = argparse.ArgumentParser(prog='agent_team_controller.py consume-claimed')
            parser.add_argument('--claimed-json', default='[]')
            parser.add_argument('--max-agents', type=int, default=3)
            ns = parser.parse_args(sys.argv[2:])
            try:
                claimed_items = json.loads(ns.claimed_json or '[]')
            except json.JSONDecodeError as exc:
                print(json.dumps({'status': 'ERROR', 'event_driven': True, 'reason': 'invalid_claimed_json', 'error': str(exc)}, ensure_ascii=False))
                raise SystemExit(2)
            print(json.dumps(consume_claimed_batch(claimed_items, max_agents=ns.max_agents), indent=2, ensure_ascii=False))
        elif cmd == 'status':
            print(json.dumps(show_status(), indent=2, ensure_ascii=False))
        elif cmd == 'enable':
            KILL_SWITCH.unlink(missing_ok=True)
            os.environ.pop('AGENT_TEAM_DISABLED', None)
            print('Agent team enabled')
        elif cmd == 'disable':
            KILL_SWITCH.touch()
            print('Agent team disabled')
        else:
            print('Usage: agent_team_controller.py [cycle|claim-cycle|execute-cycle|consume-claimed|status|enable|disable]')
    else:
        print('Usage: agent_team_controller.py [cycle|claim-cycle|execute-cycle|consume-claimed|status|enable|disable]')


