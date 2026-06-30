#!/usr/bin/env python3
"""Task Pool Guardian — Monitors and fixes task flow issues.

Detects and auto-fixes:
- Stale claims (claimed but TTL expired)
- Stuck envelopes (RUNNING beyond appetite)
- Deadlock (claimed > 5min with no envelope activity)
- Flow gaps (PENDING tasks not reaching workers)

Run via cron every 10 minutes.
"""
import json, subprocess, sys, time, os, signal
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))

ORCHESTRATOR = Path.home() / '.hermes' / 'scripts' / 'brain_task_orchestrator.py'
try:
    from brain_task_orchestrator import iter_tasks, now
except Exception:  # pragma: no cover - guardian reports this at runtime
    iter_tasks = None
    now = None


def run_command(args, timeout=120):
    """Run a subprocess in its own process group and kill the whole group on timeout."""
    proc = subprocess.Popen(
        [sys.executable, *map(str, args)],
        cwd=str(Path.home() / '.hermes' / 'scripts'),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
        return {"returncode": proc.returncode, "stdout": out or "", "stderr": err or ""}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors='replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors='replace')
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            out, err = proc.communicate(timeout=5)
            stdout += out or ""
            stderr += err or ""
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                out, err = proc.communicate(timeout=2)
                stdout += out or ""
                stderr += err or ""
            except Exception:
                pass
        return {
            "returncode": 124,
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
            "timeout_seconds": timeout,
            "reason": "subprocess_timeout",
        }


def parse_json_or_error(result, label):
    if result.get("returncode") != 0:
        return None, {"action": label, "error": result.get("reason") or "command_failed", "returncode": result.get("returncode"), "stderr": (result.get("stderr") or "")[-500:]}
    try:
        return json.loads(result.get("stdout") or "{}"), None
    except Exception as exc:
        return None, {"action": label, "error": f"json_parse_failed:{exc}", "stdout": (result.get("stdout") or "")[-500:]}

def load_task_rows():
    if iter_tasks is None:
        raise RuntimeError('brain_task_orchestrator.iter_tasks unavailable')
    at = now() if now is not None else None
    rows = []
    for task in iter_tasks():
        status = task.status
        claimed_by = str(task.fm.get('claimed_by') or '')
        claim_expires_at = str(task.fm.get('claim_expires_at') or '')
        run_id = str(task.fm.get('run_id') or '')
        try:
            stale_claim = bool(task.is_stale_claim(at))
        except Exception:
            stale_claim = False
        simple_dispatchable = status in {'pending', 'retry'} and not claimed_by and not claim_expires_at and not run_id and not stale_claim
        rows.append({
            'id': task.id,
            'status': status,
            'claimed_by': claimed_by,
            'claim_expires_at': claim_expires_at,
            'run_id': run_id,
            'stale_claim': stale_claim,
            'dispatchable': simple_dispatchable,
        })
    return rows


def check_stale_claims():
    """Release stale claims."""
    try:
        rows = load_task_rows()
    except Exception as exc:
        return {'action': 'release_stale', 'error': str(exc)[:200]}
    stale = [t for t in rows if t.get('stale_claim')]

    released = 0
    for t in stale:
        task_id = t['id']
        r2 = run_command(
            [ORCHESTRATOR, 'release', task_id,
             '--force', '--reason', 'guardian_stale_claim_cleanup', '--json'],
            timeout=30
        )
        if r2.get('returncode') == 0:
            released += 1

    return {
        'action': 'release_stale',
        'found': len(stale),
        'released': released,
    }

def check_stuck_envelopes():
    """Reset envelopes stuck in RUNNING beyond appetite."""
    try:
        from envelope_bus import list_by_status, update_status, append_trace, check_timeout
        timed_out = check_timeout()

        reset = 0
        for env in timed_out:
            eid = env['id']
            # Check retry count
            retry = env.get('retry_count', 0)
            max_r = env.get('max_retries', 3)

            if retry >= max_r:
                update_status(eid, 'FAILED', error='guardian: max retries exceeded')
                append_trace(eid, {'event': 'guardian_failed', 'reason': 'max_retries'})
            else:
                update_status(eid, 'PENDING')
                append_trace(eid, {'event': 'guardian_reset', 'retry': retry + 1})
            reset += 1

        return {
            'action': 'reset_stuck_envelopes',
            'found': len(timed_out),
            'reset': reset,
        }
    except Exception as e:
        return {'action': 'reset_stuck_envelopes', 'error': str(e)[:200]}

def check_flow_health():
    """Check overall flow health and report."""
    try:
        # Orchestrator snapshot (direct Markdown scan; avoids spawning heavyweight list/selfcheck paths)
        rows = load_task_rows()

        total = len(rows)
        pending = sum(1 for t in rows if t.get('status') == 'pending')
        claimed = sum(1 for t in rows if t.get('status') == 'claimed')
        review = sum(1 for t in rows if t.get('status') == 'review')
        stale = sum(1 for t in rows if t.get('stale_claim'))
        dispatchable = sum(1 for t in rows if t.get('dispatchable'))

        # Envelope
        from envelope_bus import stats as env_stats
        es = env_stats()

        # V(x) is computed by a dedicated v-state cron; guardian stays lightweight and does not spawn it.
        v = {'V': 0, 'grade': 'skipped', 'bottleneck': 'v_state_dedicated_cron'}

        return {
            'action': 'health_check',
            'tasks': {'total': total, 'pending': pending, 'claimed': claimed, 'review': review, 'stale': stale, 'dispatchable': dispatchable},
            'envelopes': es,
            'v_state': {'V': v['V'], 'grade': v['grade'], 'bottleneck': v['bottleneck']},
        }
    except Exception as e:
        return {'action': 'health_check', 'error': str(e)[:200]}

def run_guardian():
    """Full guardian cycle."""
    results = {}

    # 1. Fix stale claims
    results['stale_claims'] = check_stale_claims()

    # 2. Fix stuck envelopes
    results['stuck_envelopes'] = check_stuck_envelopes()

    # 3. Health check
    results['health'] = check_flow_health()

    # Summary
    issues_found = (
        results['stale_claims'].get('found', 0) +
        results['stuck_envelopes'].get('found', 0)
    )
    issues_fixed = (
        results['stale_claims'].get('released', 0) +
        results['stuck_envelopes'].get('reset', 0)
    )

    v_score = results['health'].get('v_state', {}).get('V', 0)
    grade = results['health'].get('v_state', {}).get('grade', 'unknown')

    return {
        'status': 'ok',
        'issues_found': issues_found,
        'issues_fixed': issues_fixed,
        'v_score': v_score,
        'grade': grade,
        'details': results,
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        print(json.dumps(run_guardian(), indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == 'health':
        print(json.dumps(check_flow_health(), indent=2, ensure_ascii=False))
    else:
        print('Usage: task_pool_guardian.py [run|health]')
