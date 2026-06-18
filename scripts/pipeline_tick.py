#!/usr/bin/env python3
"""Pipeline Tick — Connects brain_task_orchestrator with envelope_bus.

Reads brain tasks, creates envelopes, manages lifecycle.
Run via cron or manually.
"""
import json, subprocess, sys, time, os
from pathlib import Path

# Import envelope bus
sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))
from envelope_bus import create, get, update_status, append_trace, increment_retry, list_by_status, stats, check_timeout, human_escape_check

ORCHESTRATOR = Path.home() / '.hermes' / 'scripts' / 'brain_task_orchestrator.py'
MAX_NEW_PER_TICK = 5

def get_dispatchable_tasks():
    """Get tasks from brain orchestrator that are dispatchable."""
    r = subprocess.run(
        ['python3', str(ORCHESTRATOR), 'list', '--json'],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        raise RuntimeError(f'orchestrator list failed: {r.stderr[:200]}')
    data = json.loads(r.stdout)
    rows = data.get('rows', [])
    # Filter: dispatchable, not already in envelope bus
    return [t for t in rows if t.get('dispatchable', False)]

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


def build_payload_from_task(task, priority):
    """Preserve task acceptance/proof contract when creating an envelope."""
    acceptance_criteria = _as_list(task.get('acceptance_criteria'))
    evidence_refs = _as_list(task.get('evidence_refs'))
    non_goals = _as_list(task.get('non_goals'))
    red_lines = _as_list(task.get('red_lines'))
    workflow_contract = task.get('workflow_contract') if isinstance(task.get('workflow_contract'), dict) else {}
    payload = {
        'brain_id': task.get('id', ''),
        'priority': priority,
        'lane': task.get('lane', ''),
        'parallel_boundary': task.get('parallel_boundary', ''),
    }
    if acceptance_criteria:
        payload['acceptance_criteria'] = acceptance_criteria
    if evidence_refs:
        payload['evidence_refs'] = evidence_refs
        payload['acceptance_evidence'] = evidence_refs
    if non_goals:
        payload['non_goals'] = non_goals
    if red_lines:
        payload['red_lines'] = red_lines
    if workflow_contract:
        payload['workflow_contract'] = workflow_contract
    if acceptance_criteria or evidence_refs or workflow_contract:
        payload['harness_contract'] = {
            'map': {
                'state_source': 'brain_task_orchestrator',
                'repo_or_surface': task.get('project', ''),
                'forbidden_changes': red_lines,
            },
            'goal': {
                'user_intent': task.get('title', ''),
                'desired_state': task.get('description') or task.get('body') or task.get('title', ''),
                'non_goals': non_goals,
            },
            'acceptance': {
                'observable_results': acceptance_criteria,
            },
            'evidence': {
                'evidence_refs': evidence_refs,
                'minimum_done_proof': evidence_refs or acceptance_criteria,
            },
            'gates': {
                'risk_level': 'high' if priority in ('P0', 'P1') else 'medium',
                'dry_run_first': True,
            },
        }
    return payload


def sync_envelopes():
    """Sync brain tasks to envelope bus."""
    tasks = get_dispatchable_tasks()
    existing = {e['title'] for e in list_by_status('PENDING', limit=500)}
    existing.update(e['title'] for e in list_by_status('RUNNING', limit=500))

    created = 0
    for task in tasks[:MAX_NEW_PER_TICK]:
        title = task.get('title', 'untitled')
        if title in existing:
            continue

        # Determine appetite based on priority
        priority = task.get('priority', 'P2')
        appetite_map = {'P0': 3600, 'P1': 1800, 'P2': 1800, 'P3': 900}
        appetite = appetite_map.get(priority, 1800)

        eid = create(
            type='TASK',
            title=title,
            project=task.get('project', ''),
            assignee=task.get('claimed_by', ''),
            payload=build_payload_from_task(task, priority),
            appetite_seconds=appetite,
        )
        append_trace(eid, {'event': 'created_from_brain', 'brain_id': task.get('id', '')})
        created += 1

    return created

def check_and_handle_timeouts():
    """Handle timed-out envelopes."""
    timeouts = check_timeout()
    for env in timeouts:
        eid = env['id']
        retry_count, max_retries = increment_retry(eid)
        if retry_count >= max_retries:
            update_status(eid, 'FAILED', error=f'Appetite timeout after {retry_count} retries')
            append_trace(eid, {'event': 'timeout_final', 'retry_count': retry_count})
        else:
            update_status(eid, 'PENDING')
            append_trace(eid, {'event': 'timeout_retry', 'retry_count': retry_count})
    return len(timeouts)

def check_escape():
    """Check human escape threshold."""
    triggered, info = human_escape_check()
    if triggered:
        print(f'⚠ HUMAN ESCAPE TRIGGERED: {info}')
        return True
    return False

def run_tick():
    """Full pipeline tick."""
    result = {
        'tick_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'new_envelopes': 0,
        'timeouts_handled': 0,
        'escape_triggered': False,
        'stats': {},
    }

    # Check escape first
    result['escape_triggered'] = check_escape()
    if result['escape_triggered']:
        result['stats'] = stats()
        return result

    # Sync new tasks
    result['new_envelopes'] = sync_envelopes()

    # Handle timeouts
    result['timeouts_handled'] = check_and_handle_timeouts()

    # Stats
    result['stats'] = stats()

    return result

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'tick':
        result = run_tick()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == 'stats':
        print(json.dumps(stats(), indent=2))
    else:
        print('Usage: pipeline_tick.py [tick|stats]')
