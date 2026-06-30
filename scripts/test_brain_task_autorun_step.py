#!/usr/bin/env python3
"""Tests for bounded local-brain autorun step.
Run with: python3 ~/.hermes/scripts/test_brain_task_autorun_step.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
ORCH = HOME / ".hermes" / "scripts" / "brain_task_orchestrator.py"
STEP = HOME / ".hermes" / "scripts" / "brain_task_autorun_step.py"


def run(cmd, env, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"command failed {cmd}\nstdout={r.stdout}\nstderr={r.stderr}")
    return r


def make_env_and_vault():
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    vault = root / "brain"
    (vault / "05-实践与项目" / "tasks").mkdir(parents=True)
    (vault / "07-仪表盘").mkdir(parents=True)
    env = os.environ.copy()
    env["HERMES_HOME"] = str(HOME / ".hermes")
    env["HERMES_BRAIN_VAULT"] = str(vault)
    env["HERMES_BRAIN_AUTORUN_STATE_DIR"] = str(root / "autorun-state")
    env["HERMES_AUTONOMY_WRITE_ALLOWLIST"] = str(root / "autonomy-write-allowlist.json")
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN", None)
    return td, vault, env


def add_task(env, title="bounded autorun task"):
    r = run([
        sys.executable,
        str(ORCH),
        "add",
        title,
        "--priority",
        "P1",
        "--project",
        "local-brain-task-orchestration",
        "--expires-at",
        "2099-01-01",
        "--priority-layer",
        "P1",
        "--dependency-order",
        "[]",
        "--multimodel-triage-result",
        "not_required",
        "--json",
    ], env)
    data = json.loads(r.stdout)
    return data["id"], Path(data["created"])


def task_row(env, task_id):
    rows = json.loads(run([sys.executable, str(ORCH), "list", "--json"], env).stdout)["rows"]
    return next(r for r in rows if r["id"] == task_id)


def write_allowlists_and_policy(env, task_id, command_ids):
    state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")
    Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool", "kanban-worker"], ensure_ascii=False), encoding="utf-8")
    (state_dir / "auto_run_policy.json").write_text(json.dumps({
        "version": 1,
        "profiles": {
            "test": {
                "task_ids": [task_id],
                "lanes": ["work"],
                "workspace_roots": [str(HOME / ".hermes")],
                "command_ids": command_ids,
                "max_seconds": 30,
                "close_mode": "review_only"
            }
        }
    }, ensure_ascii=False), encoding="utf-8")


def test_autorun_step_default_disabled_returns_summary_without_claiming():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _ = add_task(env)
        payload = json.loads(run([sys.executable, str(STEP), "--json", "--profile", "test"], env).stdout)
        assert payload["status"] == "PASS", payload
        assert payload["claimed"] is False, payload
        assert payload["advanced"] is False, payload
        assert "autorun_disabled" in payload["reasons"], payload
        assert task_row(env, task_id)["status"] == "pending"


def test_autorun_step_requires_policy_before_claiming():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _ = add_task(env)
        run([sys.executable, str(ORCH), "dashboard", "--write", "--json"], env)
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool", "kanban-worker"], ensure_ascii=False), encoding="utf-8")
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        payload = json.loads(run([sys.executable, str(STEP), "--json", "--profile", "missing"], env).stdout)
        assert payload["claimed"] is False, payload
        assert "policy_missing" in payload["reasons"] or "policy_profile_missing" in payload["reasons"], payload
        assert task_row(env, task_id)["status"] == "pending"


def test_autorun_step_does_not_execute_markdown_body_and_advances_to_review():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env)
        run([sys.executable, str(ORCH), "dashboard", "--write", "--json"], env)
        sentinel = Path(tempfile.gettempdir()) / f"hermes-markdown-body-should-not-run-{task_id}"
        if sentinel.exists():
            sentinel.unlink()
        task_path.write_text(task_path.read_text(encoding="utf-8") + f"\n```bash\ntouch {sentinel}\n```\n", encoding="utf-8")
        write_allowlists_and_policy(env, task_id, ["noop"])
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"

        payload = json.loads(run([sys.executable, str(STEP), "--json", "--profile", "test"], env).stdout)
        assert payload["status"] == "OK", payload
        assert payload["claimed"] is True, payload
        assert payload["advanced"] is True, payload
        assert payload["to_status"] == "review", payload
        assert payload["proof_hash"].startswith("sha256:"), payload
        assert not sentinel.exists(), payload
        row = task_row(env, task_id)
        assert row["status"] == "review", row
        note = task_path.read_text(encoding="utf-8")
        assert f"proof:{payload['proof_hash']}" in note
        assert "command:noop PASS" in note


def test_autorun_step_failure_moves_to_retry_not_claimed():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _ = add_task(env)
        run([sys.executable, str(ORCH), "dashboard", "--write", "--json"], env)
        write_allowlists_and_policy(env, task_id, ["fail"])
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        payload = json.loads(run([sys.executable, str(STEP), "--json", "--profile", "test"], env).stdout)
        assert payload["status"] == "OK", payload
        assert payload["claimed"] is True, payload
        assert payload["advanced"] is False, payload
        assert payload["to_status"] == "retry", payload
        row = task_row(env, task_id)
        assert row["status"] == "retry", row
        assert row["claimed_by"] == "", row


def test_autorun_step_fails_closed_when_eligibility_unavailable():
    import argparse
    import importlib.util

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    calls = []
    old_run_json = module.run_json
    try:
        def fake_run_json(cmd, timeout=120):
            calls.append(list(cmd))
            return {"status": "ERROR", "reason": "subprocess_timeout", "returncode": "timeout"}
        module.run_json = fake_run_json
        payload = module.command_autorun_step(argparse.Namespace(actor="tester", task="", profile="test", ttl_minutes=10))
    finally:
        module.run_json = old_run_json

    assert payload["status"] == "PASS", payload
    assert payload["claimed"] is False, payload
    assert payload["advanced"] is False, payload
    assert "eligibility_unavailable" in payload["reasons"], payload
    assert any("eligibility-check" in cmd and "--no-reconcile" in cmd and "--skip-selfcheck" in cmd for cmd in calls), calls


def test_run_json_timeout_returns_structured_error():
    import importlib.util

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    payload = module.run_json([sys.executable, "-c", "import time; print('partial out'); time.sleep(10)"], timeout=1)

    assert payload["status"] == "ERROR", payload
    assert payload["returncode"] == "timeout", payload
    assert payload["reason"] == "subprocess_timeout", payload
    assert payload["timeout_seconds"] == 1, payload


def test_run_json_uses_configurable_default_timeout():
    import importlib.util
    import subprocess as subprocess_module

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    old_popen = module.subprocess.Popen
    old_env = os.environ.get("HERMES_BRAIN_AUTORUN_STEP_COMMAND_TIMEOUT_SECONDS")
    try:
        seen = {}
        class FakeProc:
            pid = 999999
            returncode = 0
            def __init__(self, *args, **kwargs):
                seen["kwargs"] = kwargs
            def communicate(self, timeout=None):
                seen["timeout"] = timeout
                return '{"status":"OK"}', ""
        module.subprocess.Popen = FakeProc
        os.environ["HERMES_BRAIN_AUTORUN_STEP_COMMAND_TIMEOUT_SECONDS"] = "345"
        payload = module.run_json(["ok"])
    finally:
        module.subprocess.Popen = old_popen
        if old_env is None:
            os.environ.pop("HERMES_BRAIN_AUTORUN_STEP_COMMAND_TIMEOUT_SECONDS", None)
        else:
            os.environ["HERMES_BRAIN_AUTORUN_STEP_COMMAND_TIMEOUT_SECONDS"] = old_env

    assert payload["status"] == "OK", payload
    assert seen["timeout"] == 345, seen
    assert seen["kwargs"].get("start_new_session") is True, seen
    assert seen["kwargs"].get("env", {}).get("HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN") == "1", seen


def test_autorun_step_skips_selfcheck_until_policy_allows_claim():
    import argparse
    import importlib.util

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    calls = []
    old_run_json = module.run_json
    old_load_orchestrator = module.load_orchestrator
    old_find_row = module.find_row
    old_load_policy = module.load_policy
    try:
        class FakeOrchestrator:
            pass
        def fake_run_json(cmd, timeout=None):
            calls.append(list(cmd))
            if "eligibility-check" in cmd:
                return {"status": "PASS", "eligible": True, "task_id": "task-1", "reasons": []}
            raise AssertionError(f"unexpected run_json call after policy denial: {cmd}")
        module.load_orchestrator = lambda: FakeOrchestrator()
        module.run_json = fake_run_json
        module.find_row = lambda task_id, orch_module=None: {"id": task_id, "lane": "evolution", "project": "", "architecture_target": "", "brain": ""}
        module.load_policy = lambda profile: ({
            "task_ids": ["task-1"],
            "lanes": ["work"],
            "workspace": str(HOME / ".hermes"),
            "workspace_roots": [str(HOME / ".hermes")],
            "command_ids": ["noop"],
            "close_mode": "review_only",
        }, [])

        payload = module.command_autorun_step(argparse.Namespace(actor="tester", task="", profile="test", ttl_minutes=10, retry_delay_minutes=10))
    finally:
        module.run_json = old_run_json
        module.load_orchestrator = old_load_orchestrator
        module.find_row = old_find_row
        module.load_policy = old_load_policy

    assert payload["status"] == "PASS", payload
    assert payload["claimed"] is False, payload
    assert payload["advanced"] is False, payload
    assert "policy_lane_miss" in payload["reasons"], payload
    assert any("eligibility-check" in cmd and "--skip-selfcheck" in cmd for cmd in calls), calls
    assert not any("selfcheck" in cmd for cmd in calls), calls
    assert not any("auto-claim-and-handoff" in cmd for cmd in calls), calls


def test_autorun_step_falls_back_to_policy_allowed_dispatchable_when_default_lane_denied():
    import argparse
    import importlib.util

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    calls = []
    old_run_json = module.run_json
    old_load_orchestrator = module.load_orchestrator
    old_find_row = module.find_row
    old_load_policy = module.load_policy
    try:
        class FakeTask:
            def __init__(self, task_id, lane):
                self.id = task_id
                self.lane = lane
            def row(self):
                return {"id": self.id, "lane": self.lane, "project": "hermes", "architecture_target": "", "brain": ""}
        class FakeOrchestrator:
            @staticmethod
            def dispatchable_tasks():
                return [FakeTask("task-advisory", "advisory"), FakeTask("task-work", "work")]
        def fake_run_json(cmd, timeout=None):
            calls.append(list(cmd))
            if "eligibility-check" in cmd:
                return {"status": "PASS", "eligible": True, "task_id": "task-advisory", "reasons": []}
            if "selfcheck" in cmd:
                return {"status": "ERROR", "failures": ["stop_before_claim"]}
            raise AssertionError(f"unexpected command: {cmd}")
        module.load_orchestrator = lambda: FakeOrchestrator()
        module.run_json = fake_run_json
        module.find_row = lambda task_id, orch_module=None: {"id": task_id, "lane": "advisory", "project": "hermes", "architecture_target": "", "brain": ""}
        module.load_policy = lambda profile: ({
            "projects": ["project:hermes"],
            "lanes": ["work"],
            "workspace": str(HOME / ".hermes"),
            "workspace_roots": [str(HOME / ".hermes")],
            "command_ids": ["noop"],
            "close_mode": "review_only",
        }, [])

        payload = module.command_autorun_step(argparse.Namespace(actor="tester", task="", profile="test", ttl_minutes=10, retry_delay_minutes=10))
    finally:
        module.run_json = old_run_json
        module.load_orchestrator = old_load_orchestrator
        module.find_row = old_find_row
        module.load_policy = old_load_policy

    assert payload["task_id"] == "task-work", payload
    assert payload.get("selected_after_policy_skip") == "task-advisory", payload
    assert payload["reasons"] == ["selfcheck_failed"], payload
    assert any("selfcheck" in cmd for cmd in calls), calls
    assert not any("auto-claim-and-handoff" in cmd for cmd in calls), calls



def test_autorun_step_runs_selfcheck_after_policy_before_claiming():
    import argparse
    import importlib.util

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    calls = []
    old_run_json = module.run_json
    old_load_orchestrator = module.load_orchestrator
    old_find_row = module.find_row
    old_load_policy = module.load_policy
    try:
        class FakeOrchestrator:
            pass
        def fake_run_json(cmd, timeout=None):
            calls.append(list(cmd))
            if "eligibility-check" in cmd:
                return {"status": "PASS", "eligible": True, "task_id": "task-1", "reasons": []}
            if "selfcheck" in cmd:
                return {"status": "ERROR", "failures": ["synthetic_selfcheck_failure"]}
            raise AssertionError(f"claim/transition must not run when selfcheck fails: {cmd}")
        module.load_orchestrator = lambda: FakeOrchestrator()
        module.run_json = fake_run_json
        module.find_row = lambda task_id, orch_module=None: {"id": task_id, "lane": "work", "project": "", "architecture_target": "", "brain": ""}
        module.load_policy = lambda profile: ({
            "task_ids": ["task-1"],
            "lanes": ["work"],
            "workspace": str(HOME / ".hermes"),
            "workspace_roots": [str(HOME / ".hermes")],
            "command_ids": ["noop"],
            "close_mode": "review_only",
        }, [])

        payload = module.command_autorun_step(argparse.Namespace(actor="tester", task="", profile="test", ttl_minutes=10, retry_delay_minutes=10))
    finally:
        module.run_json = old_run_json
        module.load_orchestrator = old_load_orchestrator
        module.find_row = old_find_row
        module.load_policy = old_load_policy

    assert payload["status"] == "PASS", payload
    assert payload["claimed"] is False, payload
    assert payload["advanced"] is False, payload
    assert payload["reasons"] == ["selfcheck_failed"], payload
    assert calls[0].count("eligibility-check") == 1 and "--skip-selfcheck" in calls[0], calls
    assert any("selfcheck" in cmd for cmd in calls), calls
    assert not any("auto-claim-and-handoff" in cmd for cmd in calls), calls


def test_autorun_step_claim_uses_prechecked_fast_gate_flags():
    import argparse
    import importlib.util

    spec = importlib.util.spec_from_file_location("brain_task_autorun_step", STEP)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    calls = []
    old_run_json = module.run_json
    old_load_orchestrator = module.load_orchestrator
    old_find_row = module.find_row
    old_load_policy = module.load_policy
    try:
        class FakeOrchestrator:
            pass
        def fake_run_json(cmd, timeout=None):
            calls.append(list(cmd))
            if "eligibility-check" in cmd:
                return {"status": "PASS", "eligible": True, "task_id": "task-1", "reasons": []}
            if "selfcheck" in cmd:
                return {"status": "PASS", "failures": []}
            if "auto-claim-and-handoff" in cmd:
                return {"status": "PASS", "claimed": False, "eligible": False, "reasons": ["synthetic_claim_denied"]}
            raise AssertionError(f"unexpected command before claim denial: {cmd}")
        module.load_orchestrator = lambda: FakeOrchestrator()
        module.run_json = fake_run_json
        module.find_row = lambda task_id, orch_module=None: {"id": task_id, "lane": "work", "project": "", "architecture_target": "", "brain": ""}
        module.load_policy = lambda profile: ({
            "task_ids": ["task-1"],
            "lanes": ["work"],
            "workspace": str(HOME / ".hermes"),
            "workspace_roots": [str(HOME / ".hermes")],
            "command_ids": ["noop"],
            "close_mode": "review_only",
        }, [])

        payload = module.command_autorun_step(argparse.Namespace(actor="tester", task="", profile="test", ttl_minutes=10, retry_delay_minutes=10))
    finally:
        module.run_json = old_run_json
        module.load_orchestrator = old_load_orchestrator
        module.find_row = old_find_row
        module.load_policy = old_load_policy

    assert payload["claimed"] is False, payload
    claim_calls = [cmd for cmd in calls if "auto-claim-and-handoff" in cmd]
    assert len(claim_calls) == 1, calls
    assert "--no-reconcile" in claim_calls[0], claim_calls
    assert "--skip-selfcheck" in claim_calls[0], claim_calls


if __name__ == "__main__":
    test_autorun_step_default_disabled_returns_summary_without_claiming()
    test_autorun_step_requires_policy_before_claiming()
    test_autorun_step_does_not_execute_markdown_body_and_advances_to_review()
    test_autorun_step_failure_moves_to_retry_not_claimed()
    test_autorun_step_fails_closed_when_eligibility_unavailable()
    test_run_json_timeout_returns_structured_error()
    test_run_json_uses_configurable_default_timeout()
    test_autorun_step_skips_selfcheck_until_policy_allows_claim()
    test_autorun_step_falls_back_to_policy_allowed_dispatchable_when_default_lane_denied()
    test_autorun_step_runs_selfcheck_after_policy_before_claiming()
    test_autorun_step_claim_uses_prechecked_fast_gate_flags()
    print("PASS")
