import importlib.util
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path('/Users/charles/.hermes/scripts/kanban_bridge.py')


def load_module():
    spec = importlib.util.spec_from_file_location('kanban_bridge_under_test', SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_default_run_fails_closed_before_reading_or_writing(monkeypatch, tmp_path):
    mod = load_module()
    monkeypatch.setattr(mod, 'STATE_DIR', tmp_path / 'state')
    monkeypatch.setattr(mod, 'BRIDGE_STATE', tmp_path / 'state' / 'bridge.json')
    monkeypatch.setattr(mod, 'get_brain_tasks', lambda: (_ for _ in ()).throw(AssertionError('must not read')))

    result = mod.run_bridge(execute=False)

    assert result['status'] == 'DENIED'
    assert result['reason'] == 'explicit_execute_required'
    assert not mod.BRIDGE_STATE.exists()


def test_source_provenance_is_read_only_by_default(monkeypatch, tmp_path):
    mod = load_module()
    note = tmp_path / 'task.md'
    note.write_text('canonical\n', encoding='utf-8')
    before = note.read_bytes()
    monkeypatch.delenv('KANBAN_BRIDGE_WRITE_PROVENANCE', raising=False)

    written = mod._append_source_provenance({'path': str(note)}, 't_abc')

    assert written is False
    assert note.read_bytes() == before


def test_create_without_parseable_id_fails_closed(monkeypatch, tmp_path):
    mod = load_module()
    state = {'mirrored': {}, 'errors': []}
    monkeypatch.setattr(mod, 'KANBAN_DB', tmp_path / 'missing.db')
    monkeypatch.setattr(mod.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout='created but no id', stderr=''))

    result = mod.mirror_task({'id': 'brain-1', 'title': 'test', 'status': 'pending'}, state)

    assert result is None
    assert state['mirrored'] == {}
    assert any('unparseable task id' in error for error in state['errors'])


def _create_mirror_db(path, *, with_events=True):
    conn = sqlite3.connect(path)
    conn.execute('CREATE TABLE tasks(id TEXT PRIMARY KEY, assignee TEXT, title TEXT, status TEXT, body TEXT, created_at INTEGER, completed_at INTEGER)')
    if with_events:
        conn.execute('CREATE TABLE task_events(task_id TEXT, run_id TEXT, kind TEXT, payload TEXT, created_at INTEGER)')
    conn.execute("INSERT INTO tasks VALUES('t_abc','brain-mirror','Task','todo','old',1,NULL)")
    conn.commit()
    conn.close()


def test_bridge_lock_blocks_overlapping_projection_before_source_read(monkeypatch, tmp_path):
    first = load_module()
    second = load_module()
    lock = tmp_path / "bridge.lock"
    for mod in (first, second):
        monkeypatch.setattr(mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(mod, "BRIDGE_LOCK", lock)
        monkeypatch.setattr(mod, "is_disabled", lambda: False)
    lock_fd = first.acquire_bridge_lock()
    assert lock_fd is not None
    monkeypatch.setattr(second, "get_brain_tasks", lambda: (_ for _ in ()).throw(AssertionError("source read during overlap")))
    try:
        result = second.run_bridge(execute=True)
    finally:
        first.release_bridge_lock(lock_fd)
    assert result["status"] == "busy"
    assert result["reason"] == "bridge_already_running"


def test_subprocess_crash_releases_bridge_lock(monkeypatch, tmp_path):
    lock = tmp_path / "bridge.lock"
    code = f"""
import importlib.util
import pathlib
import time
spec = importlib.util.spec_from_file_location('bridge_child', {str(SCRIPT)!r})
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.STATE_DIR = pathlib.Path({str(tmp_path)!r})
mod.BRIDGE_LOCK = pathlib.Path({str(lock)!r})
fd = mod.acquire_bridge_lock()
assert fd is not None
print('READY', flush=True)
time.sleep(30)
"""
    child = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "READY"
        mod = load_module()
        monkeypatch.setattr(mod, "STATE_DIR", tmp_path)
        monkeypatch.setattr(mod, "BRIDGE_LOCK", lock)
        assert mod.acquire_bridge_lock() is None
        child.kill()
        child.wait(timeout=5)
        recovered_fd = mod.acquire_bridge_lock()
        assert recovered_fd is not None
        mod.release_bridge_lock(recovered_fd)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)


def test_existing_mirror_sync_is_idempotent_and_records_one_event(monkeypatch, tmp_path):
    mod = load_module()
    db = tmp_path / 'kanban.db'
    _create_mirror_db(db)
    monkeypatch.setattr(mod, 'KANBAN_DB', db)
    task = {'id': 'brain-1', 'title': 'Task', 'status': 'claimed', 'priority': 'P1', 'body': 'work'}

    first = mod._sync_kanban_task('t_abc', task)
    second = mod._sync_kanban_task('t_abc', task)

    assert first['updated'] is True
    assert first['status'] == 'running'
    assert second['updated'] is False
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status FROM tasks WHERE id='t_abc'").fetchone()[0] == 'running'
        assert conn.execute("SELECT count(*) FROM task_events").fetchone()[0] == 1


def test_sync_event_failure_rolls_back_task_update(monkeypatch, tmp_path):
    mod = load_module()
    db = tmp_path / 'kanban.db'
    _create_mirror_db(db, with_events=False)
    monkeypatch.setattr(mod, 'KANBAN_DB', db)

    try:
        mod._sync_kanban_task('t_abc', {'id': 'brain-1', 'title': 'Task', 'status': 'done'})
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError('missing event table must fail the transaction')

    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status, body FROM tasks WHERE id='t_abc'").fetchone() == ('todo', 'old')


def test_execute_honors_kill_switch_before_reading_brain(monkeypatch, tmp_path):
    mod = load_module()
    kill = tmp_path / 'disabled'
    kill.write_text('disabled', encoding='utf-8')
    monkeypatch.setattr(mod, 'KILL_SWITCH_FILE', kill)
    monkeypatch.setattr(mod, 'get_brain_tasks', lambda: (_ for _ in ()).throw(AssertionError('must not read')))

    result = mod.run_bridge(execute=True)

    assert result['status'] == 'disabled'


def test_sync_selection_prioritizes_existing_terminal_mirrors_over_new_tasks(monkeypatch, tmp_path):
    mod = load_module()
    monkeypatch.setattr(mod, 'KANBAN_DB', tmp_path / 'missing.db')
    tasks = [
        {'id': f'new-{index:03d}', 'title': 'new', 'status': 'pending'}
        for index in range(120)
    ]
    tasks.append({'id': 'existing-done', 'title': 'old', 'status': 'done'})
    state = {'mirrored': {'existing-done': {'kanban_id': 't_old'}}, 'errors': []}

    selected = mod._select_tasks_for_sync(tasks, state, limit=100)

    assert selected[0]['id'] == 'existing-done'
    assert len(selected) == 100


def test_sync_duplicate_legacy_mirrors_by_title(monkeypatch, tmp_path):
    mod = load_module()
    db = tmp_path / 'kanban.db'
    _create_mirror_db(db)
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO tasks VALUES('t_dup','brain-mirror','Task','blocked','legacy',2,NULL)")
        conn.commit()
    monkeypatch.setattr(mod, 'KANBAN_DB', db)
    task = {'id': 'brain-1', 'title': 'Task', 'status': 'done'}

    updated = mod._sync_duplicate_mirrors(task, 't_abc')

    assert updated == 1
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status FROM tasks WHERE id='t_dup'").fetchone()[0] == 'done'
