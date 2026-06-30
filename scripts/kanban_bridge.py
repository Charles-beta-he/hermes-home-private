#!/usr/bin/env python3
"""Brain → Kanban One-Way Bridge (Observability Only)

Mirrors selected brain tasks to Hermes Kanban for watch observability.
One-way: brain is source-of-truth, Kanban is mirror only.
Kill switch: set env KANBAN_BRIDGE_DISABLED=1 or touch ~/.hermes/state/kanban_bridge_disabled
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

STATE_DIR = Path.home() / '.hermes' / 'state'
BRIDGE_STATE = STATE_DIR / 'kanban_bridge_state.json'
KILL_SWITCH_FILE = STATE_DIR / 'kanban_bridge_disabled'
ORCHESTRATOR = Path.home() / '.hermes' / 'scripts' / 'brain_task_orchestrator.py'
KANBAN_DB = Path.home() / '.hermes' / 'kanban.db'

STATUS_MAP = {
    'pending': 'todo',
    'ready': 'ready',
    'claimed': 'running',
    'running': 'running',
    'review': 'review',
    'retry': 'ready',
    'blocked': 'blocked',
    'done': 'done',
    'completed': 'done',
    'cancelled': 'archived',
    'archived': 'archived',
}


def is_disabled():
    if os.environ.get('KANBAN_BRIDGE_DISABLED') == '1':
        return True
    if KILL_SWITCH_FILE.exists():
        return True
    return False


def load_state():
    if BRIDGE_STATE.exists():
        return json.loads(BRIDGE_STATE.read_text())
    return {'mirrored': {}, 'last_sync': None, 'errors': []}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state['last_sync'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    BRIDGE_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def get_brain_tasks():
    """Get tasks from brain orchestrator."""
    r = subprocess.run(
        ['python3', str(ORCHESTRATOR), 'list', '--json'],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(f'orchestrator list failed: {r.stderr[:300]}')
    return json.loads(r.stdout)


def get_kanban_tasks():
    """Get existing Kanban tasks."""
    r = subprocess.run(
        ['hermes', 'kanban', 'stats', '--json'],
        capture_output=True, text=True, timeout=15,
    )
    if r.returncode != 0:
        return {}
    return json.loads(r.stdout)


def task_hash(task):
    """Stable hash fallback for old/anonymous tasks. Do not include status."""
    key = f"{task.get('title','')}{task.get('priority','')}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def task_key(task):
    """Stable source key. Prefer local-brain task id; never include status."""
    return str(task.get('id') or task_hash(task))


def kanban_status_for(task):
    return STATUS_MAP.get(str(task.get('status') or 'pending'), 'todo')


def _now():
    return int(time.time())


def _kanban_conn():
    conn = sqlite3.connect(str(KANBAN_DB))
    conn.row_factory = sqlite3.Row
    return conn


def _event(conn, task_id, kind, payload):
    conn.execute(
        'INSERT INTO task_events(task_id,run_id,kind,payload,created_at) VALUES(?,?,?,?,?)',
        (task_id, None, kind, json.dumps(payload, ensure_ascii=False), _now()),
    )


def _find_existing_mirror(task, state):
    key = task_key(task)
    entry = state.get('mirrored', {}).get(key)
    if isinstance(entry, dict) and entry.get('kanban_id'):
        return entry['kanban_id']
    title = task.get('title', 'untitled')
    if not KANBAN_DB.exists():
        return None
    with _kanban_conn() as conn:
        row = conn.execute(
            "SELECT id FROM tasks WHERE assignee='brain-mirror' AND title=? AND status!='archived' ORDER BY created_at DESC LIMIT 1",
            (title,),
        ).fetchone()
        return row['id'] if row else None


def _mirror_body(task):
    status = task.get('status', 'pending')
    priority = task.get('priority', 'medium')
    body = task.get('body', task.get('description', ''))[:500]
    return f'[brain-mirror] {body}\n\nSource: brain_task_orchestrator\nSource-ID: {task_key(task)}\nStatus: {status}\nPriority: {priority}'


def _sync_kanban_task(kanban_id, task):
    """Keep the mirror projection aligned with source task status/body."""
    if not KANBAN_DB.exists():
        return {'updated': False, 'reason': 'kanban_db_missing'}
    target_status = kanban_status_for(task)
    target_body = _mirror_body(task)
    with _kanban_conn() as conn:
        row = conn.execute(
            "SELECT status, body FROM tasks WHERE id=? AND assignee='brain-mirror'",
            (kanban_id,),
        ).fetchone()
        if not row:
            return {'updated': False, 'reason': 'mirror_missing'}
        updates: dict[str, Any] = {}
        if row['status'] != target_status:
            updates['status'] = {'from': row['status'], 'to': target_status}
        if (row['body'] or '') != target_body:
            updates['body'] = 'refreshed'
        if updates:
            conn.execute(
                "UPDATE tasks SET status=?, body=?, completed_at=CASE WHEN ?='done' THEN COALESCE(completed_at, ?) ELSE completed_at END WHERE id=?",
                (target_status, target_body, target_status, _now(), kanban_id),
            )
            _event(conn, kanban_id, 'brain_mirror_sync', {
                'source_id': task_key(task),
                'source_status': task.get('status'),
                'mirror_status': target_status,
                'updated': updates,
            })
        conn.commit()
    return {'updated': bool(updates), 'updates': updates, 'status': target_status}


def _append_source_provenance(task, kanban_id):
    path = task.get('path')
    if not path:
        return False
    p = Path(path)
    if not p.exists() or not p.is_file():
        return False
    text = p.read_text(encoding='utf-8', errors='ignore')
    if kanban_id in text or 'kanban_projection_exempt' in text:
        return False
    marker = (
        '\n\n## Kanban Projection\n\n'
        f'- Mirror: {kanban_id}\n'
        f'- Workspace: ~/.hermes/kanban/workspaces/{kanban_id}\n'
        '- Source: brain_task_orchestrator\n'
    )
    p.write_text(text.rstrip() + marker + '\n', encoding='utf-8')
    return True


def mirror_task(task, state):
    """Create or update a Kanban task mirroring brain task."""
    title = task.get('title', 'untitled')
    status = task.get('status', 'pending')
    key = task_key(task)

    existing_id = _find_existing_mirror(task, state)
    if existing_id:
        sync = _sync_kanban_task(existing_id, task)
        provenance_written = _append_source_provenance(task, existing_id)
        state['mirrored'][key] = {
            'kanban_id': existing_id,
            'brain_id': key,
            'brain_title': title,
            'brain_status': status,
            'mirror_status': sync.get('status'),
            'mirrored_at': state.get('mirrored', {}).get(key, {}).get('mirrored_at') or time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'last_synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'provenance_written': provenance_written,
        }
        return state['mirrored'][key]

    cmd = [
        'hermes', 'kanban', 'create', title,
        '--assignee', 'brain-mirror',
        '--body', _mirror_body(task),
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            output = r.stdout.strip()
            task_id = 'unknown'
            m = re.search(r'Created\s+(t_[a-f0-9]+)', output)
            if m:
                task_id = m.group(1)
            _sync_kanban_task(task_id, task)
            provenance_written = _append_source_provenance(task, task_id)
            state['mirrored'][key] = {
                'kanban_id': task_id,
                'brain_id': key,
                'brain_title': title,
                'brain_status': status,
                'mirror_status': kanban_status_for(task),
                'mirrored_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'last_synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'provenance_written': provenance_written,
            }
            return state['mirrored'][key]
        state['errors'].append(f'create failed for {title}: {r.stderr[:100]}')
    except Exception as e:
        state['errors'].append(f'create error for {title}: {str(e)[:100]}')

    return None


def run_bridge():
    """Main bridge logic."""
    if is_disabled():
        print('Bridge disabled (kill switch active)')
        return {'status': 'disabled'}

    state = load_state()

    try:
        tasks = get_brain_tasks()
    except Exception as e:
        state['errors'].append(f'brain list failed: {str(e)[:200]}')
        save_state(state)
        return {'status': 'error', 'error': str(e)[:200]}

    task_list = tasks if isinstance(tasks, list) else tasks.get('rows', tasks.get('tasks', []))

    # Mirror active tasks and sync recently completed source tasks so stale
    # blocked Kanban cards do not survive after the source note is done.
    active = [t for t in task_list if t.get('status') not in ('cancelled', 'archived')]

    mirrored_count = 0
    skipped_count = 0

    for task in active[:100]:  # bounded but enough for the active local-brain set
        before = state.get('mirrored', {}).get(task_key(task))
        result = mirror_task(task, state)
        if result:
            if before:
                skipped_count += 1
            else:
                mirrored_count += 1

    # Cleanup old errors (keep last 10)
    state['errors'] = state['errors'][-10:]

    save_state(state)

    return {
        'status': 'ok',
        'active_tasks': len(active),
        'mirrored_new': mirrored_count,
        'skipped_existing': skipped_count,
        'total_mirrored': len(state['mirrored']),
        'errors': len(state['errors']),
    }


if __name__ == '__main__':
    result = run_bridge()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get('status') == 'error':
        sys.exit(1)
