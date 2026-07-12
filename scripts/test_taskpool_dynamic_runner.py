#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "taskpool_dynamic_runner.py"


def load_module():
    spec = importlib.util.spec_from_file_location("taskpool_dynamic_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_lock_creation_is_atomic_and_owner_only(tmp_path):
    m = load_module()
    m.LOCK = tmp_path / "runner.lock"

    assert m.acquire_lock() is True
    assert m.LOCK.read_text(encoding="utf-8") == str(os.getpid())
    assert (m.LOCK.stat().st_mode & 0o777) == 0o600
    assert m.acquire_lock() is False
    m.release_lock()
    assert m.LOCK.exists()
    assert m.acquire_lock() is True
    m.release_lock()


def test_separate_runner_instances_cannot_share_lock(tmp_path):
    first = load_module()
    second = load_module()
    lock = tmp_path / "runner.lock"
    first.LOCK = lock
    second.LOCK = lock

    assert first.acquire_lock() is True
    assert second.acquire_lock() is False
    first.release_lock()
    assert second.acquire_lock() is True
    second.release_lock()


def test_stale_lock_is_replaced_atomically(tmp_path, monkeypatch):
    m = load_module()
    m.LOCK = tmp_path / "runner.lock"
    m.LOCK.write_text("99999999", encoding="utf-8")
    monkeypatch.setattr(m, "alive", lambda pid: pid == os.getpid())

    assert m.acquire_lock() is True
    assert m.LOCK.read_text(encoding="utf-8") == str(os.getpid())
    m.release_lock()


def test_signature_changes_on_next_task():
    m = load_module()
    a = {"status": "OK", "next_task_id": "a", "dispatchable": True, "multimodel_intervention": {"task_id": "m", "queued_count": 1}, "auto_close_review": {"closed_count": 0, "error_count": 0}}
    b = {"status": "OK", "next_task_id": "b", "dispatchable": True, "multimodel_intervention": {"task_id": "m", "queued_count": 1}, "auto_close_review": {"closed_count": 0, "error_count": 0}}
    c = {"status": "OK", "next_task_id": "b", "dispatchable": True, "multimodel_intervention": {"task_id": "m", "queued_count": 1}, "auto_close_review": {"closed_count": 1, "error_count": 0}}
    assert m.signature(a) != m.signature(b)
    assert m.signature(b) != m.signature(c)


def test_parse_json_tail_empty_is_safe():
    m = load_module()
    assert m.parse_json_tail("") == {}
    assert m.parse_json_tail(json.dumps({"ok": True}))["ok"] is True


def test_run_preserves_full_stdout_for_large_summary_json():
    m = load_module()
    payload = {
        "padding": "x" * 5000,
        "status": "OK",
        "next_task_id": "task-123",
        "dispatchable": True,
        "error_count": 0,
        "reconcile_action_count": 0,
        "ingested_count": 0,
        "multimodel_intervention": {"intervention_required": True, "task_id": "mm-task", "queued_count": 15},
    }
    code = "import json; print(json.dumps(%r))" % payload
    result = m.run([sys.executable, "-c", code], timeout=10)
    parsed = m.parse_json_tail(result["stdout"])
    assert parsed["status"] == "OK"
    assert parsed["next_task_id"] == "task-123"
    assert parsed["multimodel_intervention"]["queued_count"] == 15
    assert len(result["stdout"]) > 5000
    assert result["stdout_tail"].endswith("}\n")


def test_compute_parallel_max_agents_uses_clean_utc_ack_recovery_ceiling(monkeypatch=None):
    m = load_module()
    calls = []

    def fake_load_taskpool_config():
        return {
            "max_parallel_agents": 3,
            "dynamic_recovery_min_agents": 3,
            "dynamic_recovery_max_agents": 24,
            "dynamic_recovery_step_agents": 2,
            "dynamic_recovery_stable_window_seconds": 900,
        }

    def fake_run(cmd, timeout=None, env=None):
        calls.append(cmd)
        return {"returncode": 0, "stdout": json.dumps({"selected_count": 7, "dispatchable": True, "status": "OK"})}

    old_cfg, old_run, old_time, old_escape = getattr(m, "load_taskpool_config"), getattr(m, "run"), m.time.time, m.human_escape_status
    setattr(m, "load_taskpool_config", fake_load_taskpool_config)
    setattr(m, "run", fake_run)
    m.time.time = lambda: m.datetime(2026, 5, 28, 8, 47, 1, tzinfo=m.timezone.utc).timestamp()
    m.human_escape_status = lambda: {"status": "OK", "triggered": False, "info": {"since_ack": {"failures": 0, "blocks": 0, "invalid_timestamps": 0}, "ack": {"acked_at": "2026-05-28T08:32:01Z"}}}
    try:
        result = m.compute_parallel_max_agents({})
    finally:
        setattr(m, "load_taskpool_config", old_cfg)
        setattr(m, "run", old_run)
        m.time.time = old_time
        m.human_escape_status = old_escape

    assert result["configured"] == 3
    assert result["ceiling"] == 5
    assert result["selected_count"] == 7
    assert result["recommended"] == 5
    assert "5" in calls[0]


def test_parse_iso_z_treats_z_as_utc_not_local_time():
    m = load_module()
    assert m._parse_iso_z("2026-05-28T08:32:01Z") == m.datetime(2026, 5, 28, 8, 32, 1, tzinfo=m.timezone.utc).timestamp()


def test_compute_parallel_max_agents_keeps_configured_floor_when_no_boundary_safe_slots():
    m = load_module()

    def fake_load_taskpool_config():
        return {"max_parallel_agents": 3, "dynamic_recovery_max_agents": 24}

    def fake_run(cmd, timeout=None, env=None):
        return {"returncode": 0, "stdout": json.dumps({"selected_count": 0, "dispatchable": True, "status": "OK"})}

    old_cfg, old_run, old_time, old_escape = getattr(m, "load_taskpool_config"), getattr(m, "run"), m.time.time, m.human_escape_status
    setattr(m, "load_taskpool_config", fake_load_taskpool_config)
    setattr(m, "run", fake_run)
    m.time.time = lambda: m.datetime(2026, 5, 28, 8, 47, 1, tzinfo=m.timezone.utc).timestamp()
    m.human_escape_status = lambda: {"status": "OK", "triggered": False, "info": {"since_ack": {"failures": 0, "blocks": 0, "invalid_timestamps": 0}, "ack": {"acked_at": "2026-05-28T00:00:00Z"}}}
    try:
        result = m.compute_parallel_max_agents({})
    finally:
        setattr(m, "load_taskpool_config", old_cfg)
        setattr(m, "run", old_run)
        m.time.time = old_time
        m.human_escape_status = old_escape

    assert result["configured"] == 3
    assert result["ceiling"] == 24
    assert result["selected_count"] == 0
    assert result["recommended"] == 3
    assert result["reason"] == "configured_cap_sufficient"


def test_main_skips_autorun_preclaim_when_human_escape_active():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        state = root / "state.json"
        log = root / "log.jsonl"
        lock = root / "lock.pid"
        calls = []

        summary = {
            "status": "OK",
            "next_task_id": "",
            "dispatchable": True,
            "error_count": 0,
            "reconcile_action_count": 0,
            "ingested_count": 0,
            "auto_close_review": {"closed_count": 0, "error_count": 0},
            "multimodel_intervention": {},
        }

        def fake_run(cmd, timeout=240, env=None):
            calls.append(list(cmd))
            assert "--parallel-autorun" not in cmd, cmd
            assert "--autorun-step" not in cmd, cmd
            return {"returncode": 0, "stdout": json.dumps(summary), "stderr": "", "stdout_tail": json.dumps(summary), "stderr_tail": ""}

        def fake_compute_parallel_max_agents(env):
            raise AssertionError("parallel cap probe must not run while human_escape is active")

        old_state, old_log, old_lock = m.STATE, m.LOG, m.LOCK
        old_run = m.run
        old_dispatch_mode = m.load_taskpool_dispatch_mode
        old_escape = m.human_escape_status
        old_compute = m.compute_parallel_max_agents
        try:
            m.STATE = state
            m.LOG = log
            m.LOCK = lock
            m.run = fake_run
            m.load_taskpool_dispatch_mode = lambda: "parallel"
            m.human_escape_status = lambda: {"status": "OK", "triggered": True, "info": {"failures": 3}}
            m.compute_parallel_max_agents = fake_compute_parallel_max_agents
            with contextlib.redirect_stdout(io.StringIO()):
                rc = m.main()
        finally:
            m.STATE = old_state
            m.LOG = old_log
            m.LOCK = old_lock
            m.run = old_run
            m.load_taskpool_dispatch_mode = old_dispatch_mode
            m.human_escape_status = old_escape
            m.compute_parallel_max_agents = old_compute

        assert rc == 0
        assert len(calls) == 0
        event = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert event["autorun_skipped_reason"] == "human_escape_active_preclaim"
        assert event["human_escape"]["triggered"] is True
        assert event["summary"]["status"] == "OK"
        assert event["autorun"]["claimed"] is False


def test_main_parses_large_summary_and_invokes_multimodel_probe_without_silent_nulls():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tick = root / "tick.py"
        mm = root / "mm.py"
        state = root / "state.json"
        log = root / "log.jsonl"
        lock = root / "lock.pid"
        payload = {
            "padding": "x" * 5000,
            "status": "OK",
            "next_task_id": "task-123",
            "dispatchable": True,
            "error_count": 0,
            "reconcile_action_count": 0,
            "ingested_count": 0,
            "multimodel_intervention": {"intervention_required": True, "task_id": "mm-task", "queued_count": 15},
        }
        tick.write_text("import json\nprint(json.dumps(%r))\n" % payload, encoding="utf-8")
        mm.write_text("print('{\"status\":\"OK\",\"action\":\"started_worker\"}')\n", encoding="utf-8")
        m.TICK = tick
        m.MM_DYNAMIC = mm
        m.STATE = state
        m.LOG = log
        m.LOCK = lock
        old_dispatch_mode = m.load_taskpool_dispatch_mode
        old_escape = m.human_escape_status
        try:
            m.load_taskpool_dispatch_mode = lambda: "single"
            m.human_escape_status = lambda: {"status": "OK", "triggered": False, "info": {}}
            with contextlib.redirect_stdout(io.StringIO()):
                rc = m.main()
        finally:
            m.load_taskpool_dispatch_mode = old_dispatch_mode
            m.human_escape_status = old_escape
        assert rc == 0
        saved = json.loads(state.read_text(encoding="utf-8"))
        assert saved["last_summary"]["status"] == "OK"
        assert saved["last_summary"]["next_task_id"] == "task-123"
        event = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert event["summary"]["status"] == "OK"
        assert event["summary"]["next_task_id"] == "task-123"
        assert event["multimodel_dynamic"]["returncode"] == 0


def test_main_honors_no_multimodel_spawn_env_gate():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tick = root / "tick.py"
        mm = root / "mm.py"
        state = root / "state.json"
        log = root / "log.jsonl"
        lock = root / "lock.pid"
        payload = {
            "status": "OK",
            "next_task_id": "task-123",
            "dispatchable": True,
            "error_count": 0,
            "reconcile_action_count": 0,
            "ingested_count": 0,
            "multimodel_intervention": {"intervention_required": True, "task_id": "mm-task", "queued_count": 1},
        }
        tick.write_text("import json\nprint(json.dumps(%r))\n" % payload, encoding="utf-8")
        mm.write_text("raise SystemExit('multimodel worker must not be invoked')\n", encoding="utf-8")
        m.TICK = tick
        m.MM_DYNAMIC = mm
        m.STATE = state
        m.LOG = log
        m.LOCK = lock
        old_dispatch_mode = m.load_taskpool_dispatch_mode
        old_escape = m.human_escape_status
        old_env = dict(os.environ)
        try:
            os.environ[m.NO_MULTIMODEL_SPAWN_ENV_FLAG] = "1"
            m.load_taskpool_dispatch_mode = lambda: "single"
            m.human_escape_status = lambda: {"status": "OK", "triggered": False, "info": {}}
            with contextlib.redirect_stdout(io.StringIO()):
                rc = m.main()
        finally:
            os.environ.clear()
            os.environ.update(old_env)
            m.load_taskpool_dispatch_mode = old_dispatch_mode
            m.human_escape_status = old_escape
        assert rc == 0
        event = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert event["multimodel_dynamic"]["status"] == "SKIP"
        assert event["multimodel_dynamic"]["action"] == "spawn_disabled_by_env"
        assert event["multimodel_dynamic"]["env_flag"] == m.NO_MULTIMODEL_SPAWN_ENV_FLAG


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} tests")
