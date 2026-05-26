#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
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


def test_compute_parallel_max_agents_uses_boundary_probe_ceiling_not_configured_floor(monkeypatch=None):
    m = load_module()
    calls = []

    def fake_load_taskpool_config():
        return {"max_parallel_agents": 3}

    def fake_run(cmd, timeout=None, env=None):
        calls.append(cmd)
        return {"returncode": 0, "stdout": json.dumps({"selected_count": 7, "dispatchable": True, "status": "OK"})}

    old_cfg, old_run = getattr(m, "load_taskpool_config"), getattr(m, "run")
    setattr(m, "load_taskpool_config", fake_load_taskpool_config)
    setattr(m, "run", fake_run)
    try:
        result = m.compute_parallel_max_agents({})
    finally:
        setattr(m, "load_taskpool_config", old_cfg)
        setattr(m, "run", old_run)

    assert result["configured"] == 3
    assert result["ceiling"] == 24
    assert result["selected_count"] == 7
    assert result["recommended"] == 24
    assert "24" in calls[0]


def test_compute_parallel_max_agents_keeps_configured_floor_when_no_boundary_safe_slots():
    m = load_module()

    def fake_load_taskpool_config():
        return {"max_parallel_agents": 3}

    def fake_run(cmd, timeout=None, env=None):
        return {"returncode": 0, "stdout": json.dumps({"selected_count": 0, "dispatchable": True, "status": "OK"})}

    old_cfg, old_run = getattr(m, "load_taskpool_config"), getattr(m, "run")
    setattr(m, "load_taskpool_config", fake_load_taskpool_config)
    setattr(m, "run", fake_run)
    try:
        result = m.compute_parallel_max_agents({})
    finally:
        setattr(m, "load_taskpool_config", old_cfg)
        setattr(m, "run", old_run)

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
        assert len(calls) == 1
        assert calls[0][-2:] == ["--summary", "--no-state"], calls[0]
        event = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert event["autorun_skipped_reason"] == "human_escape_active_preclaim"
        assert event["human_escape"]["triggered"] is True


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
        with contextlib.redirect_stdout(io.StringIO()):
            rc = m.main()
        assert rc == 0
        saved = json.loads(state.read_text(encoding="utf-8"))
        assert saved["last_summary"]["status"] == "OK"
        assert saved["last_summary"]["next_task_id"] == "task-123"
        event = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert event["summary"]["status"] == "OK"
        assert event["summary"]["next_task_id"] == "task-123"
        assert event["multimodel_dynamic"]["returncode"] == 0


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} tests")
