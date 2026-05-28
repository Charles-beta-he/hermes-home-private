#!/usr/bin/env python3
"""Tests for brain_task_dispatch_tick.py autorun bridge.
Run with: python3 ~/.hermes/scripts/test_brain_task_dispatch_tick.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HERMES_ROOT = SCRIPT_DIR.parent
ORCH = SCRIPT_DIR / "brain_task_orchestrator.py"
TICK = SCRIPT_DIR / "brain_task_dispatch_tick.py"
AGENT_TEAM = SCRIPT_DIR / "agent_team_controller.py"


def load_agent_team_module():
    spec = importlib.util.spec_from_file_location("agent_team_controller", AGENT_TEAM)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run(cmd, env, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        try:
            payload = json.loads(r.stdout)
        except Exception:
            payload = {}
        status = payload.get("status")
        has_outputs = any(bool(payload.get(k)) for k in ["ingest", "reconcile", "dashboard", "proof_check", "evidence_spine", "multimodel_intervention", "multimodel_step", "dispatch"])
        if status != "ERROR" or not has_outputs:
            raise AssertionError(f"command failed {cmd}\nstdout={r.stdout}\nstderr={r.stderr}")
    return r


def make_env_and_vault():
    td = tempfile.TemporaryDirectory()
    root = Path(td.name)
    vault = root / "brain"
    (vault / "05-实践与项目" / "tasks").mkdir(parents=True)
    (vault / "07-仪表盘").mkdir(parents=True)
    hermes_home = root / "hermes-home"
    scripts_dir = hermes_home / "scripts"
    scripts_dir.mkdir(parents=True)
    real_scripts = SCRIPT_DIR
    for name in ("brain_task_orchestrator.py", "autonomy-write-guard.py", "autonomy-precondition.py", "permission_taxonomy.py"):
        shutil.copy2(real_scripts / name, scripts_dir / name)
    fake_p10 = scripts_dir / "p10-health.sh"
    fake_p10.write_text(
        "#!/usr/bin/env bash\n"
        "cat <<'JSON'\n"
        '{"grade":"A","components":{"self_test":1.0},"warnings":[],"details":{"test_fixture":true}}\n'
        "JSON\n",
        encoding="utf-8",
    )
    fake_p10.chmod(0o755)
    env = os.environ.copy()
    env["HERMES_HOME"] = str(hermes_home)
    env["HERMES_BRAIN_VAULT"] = str(vault)
    env["HERMES_BRAIN_AUTORUN_STATE_DIR"] = str(root / "autorun-state")
    env["HERMES_BRAIN_DISPATCH_TICK_STATE_DIR"] = str(root / "tick-state")
    env["HERMES_BRAIN_DISPATCH_TICK_LOG_DIR"] = str(root / "tick-logs")
    env["HERMES_AUTONOMY_WRITE_ALLOWLIST"] = str(root / "autonomy-write-allowlist.json")
    env["HERMES_CRON_JOBS_PATH"] = str(root / "cron" / "jobs.json")
    cron_path = Path(env["HERMES_CRON_JOBS_PATH"])
    cron_path.parent.mkdir(parents=True, exist_ok=True)
    cron_path.write_text(json.dumps({"jobs": [
        {"id": "guardian", "name": "task-pool-guardian-10m", "enabled": True, "schedule_display": "every 10m", "last_status": "ok"},
        {"id": "pipeline", "name": "pipeline-tick-hourly", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
        {"id": "agent-team", "name": "agent-team-cycle-hourly", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
        {"id": "envelope", "name": "envelope-executor-cycle", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
        {"id": "multimodel", "name": "multimodel-intervention-step", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
        {"id": "auto-completer", "name": "local-brain-taskpool-auto-completer", "enabled": True, "schedule_display": "every 120m", "last_status": "ok"},
    ]}, ensure_ascii=False), encoding="utf-8")
    profiles_dir = hermes_home / "project-profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "hermes.json").write_text(json.dumps({
        "project": "hermes",
        "display_name": "Default Hermes taskpool profile",
        "tech_stack": {"runtime": "Python", "taskpool": "Obsidian Markdown"},
        "conventions": ["load profile before worker execution", "fail closed when profile is missing"],
        "acceptance": ["focused tests pass", "p10-health remains A"],
        "forbidden": ["start worker without project profile context"],
    }, ensure_ascii=False), encoding="utf-8")
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN", None)
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL", None)
    return td, vault, env


def add_task(env, title="验证 safe tick autorun bridge"):
    r = run([
        sys.executable,
        str(ORCH),
        "add",
        title,
        "--priority",
        "P1",
        "--project",
        "local-brain-task-orchestration",
        "--priority-layer",
        "P1",
        "--dependency-order",
        "1",
        "--multimodel-triage-result",
        "P3-local-only",
        "--expires-at",
        "2099-01-01",
        "--json",
    ], env)
    data = json.loads(r.stdout)
    return data["id"]


def add_multimodel_task(env):
    r = run([
        sys.executable,
        str(ORCH),
        "add",
        "pua-loop 自动触发介入与多模型任务池分解",
        "--priority",
        "P0",
        "--project",
        "self-improvement",
        "--lane",
        "evolution",
        "--priority-layer",
        "P0",
        "--dependency-order",
        "1",
        "--multimodel-triage-result",
        "P2-evolution-multimodel-required",
        "--architecture-target",
        "taskpool",
        "--capability-delta",
        "automatic multimodel intervention",
        "--anti-drift-check",
        "ratification gate decides loop done or continue",
        "--acceptance-evidence",
        "ratification-gate PASS plus deterministic gates",
        "--expires-at",
        "2099-01-01",
        "--json",
    ], env)
    data = json.loads(r.stdout)
    return data["id"]


def load_tick_module():
    spec = importlib.util.spec_from_file_location("brain_task_dispatch_tick", TICK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def task_row(env, task_id, include_done=False):
    cmd = [sys.executable, str(ORCH), "list"]
    if include_done:
        cmd.append("--include-done")
    cmd.append("--json")
    rows = json.loads(run(cmd, env).stdout)["rows"]
    return next(r for r in rows if r["id"] == task_id)


def add_review_evolution_task(env):
    r = run([
        sys.executable,
        str(ORCH),
        "add",
        "验证 review 自动进入 done",
        "--priority",
        "P1",
        "--project",
        "self-improvement",
        "--lane",
        "evolution",
        "--priority-layer",
        "P1",
        "--dependency-order",
        "1",
        "--multimodel-triage-result",
        "P2-evolution-review",
        "--architecture-target",
        "taskpool",
        "--capability-delta",
        "automatic review to done closeout",
        "--anti-drift-check",
        "normal lifecycle done gate remains enforced",
        "--acceptance-evidence",
        "selfcheck PASS closes review safely",
        "--expires-at",
        "2099-01-01",
        "--json",
    ], env)
    task_id = json.loads(r.stdout)["id"]
    run([sys.executable, str(ORCH), "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json"], env)
    run([sys.executable, str(ORCH), "transition", task_id, "--to", "running", "--actor", "tester", "--json"], env)
    run([sys.executable, str(ORCH), "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: selfcheck PASS", "--json"], env)
    return task_id


def add_claim_state_fixture(env):
    task_ids = [add_task(env, title=f"claim-state fixture #{i}") for i in range(1, 5)]
    for task_id in task_ids[:3]:
        run([sys.executable, str(ORCH), "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json"], env)
    run([sys.executable, str(ORCH), "transition", task_ids[0], "--to", "running", "--actor", "tester", "--json"], env)
    return {
        "running": task_ids[0],
        "claimed": task_ids[1:3],
        "pending": task_ids[3],
    }


def test_tick_autorun_bridge_is_opt_in_and_fail_closed():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id = add_task(env)
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")

        default_tick = json.loads(run([sys.executable, str(TICK), "--print-always", "--no-state"], env).stdout)
        assert default_tick["status"] == "OK", default_tick
        assert "autorun" not in default_tick
        assert task_row(env, task_id)["status"] == "pending"

        disabled_tick = json.loads(run([sys.executable, str(TICK), "--print-always", "--no-state", "--autorun"], env).stdout)
        assert disabled_tick["status"] == "OK", disabled_tick
        assert disabled_tick["autorun"]["claimed"] is False
        assert "autorun_disabled" in disabled_tick["autorun"]["reasons"]
        assert task_row(env, task_id)["status"] == "pending"

        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")
        enabled_tick = json.loads(run([sys.executable, str(TICK), "--print-always", "--no-state", "--autorun"], env).stdout)
        assert enabled_tick["status"] == "OK", enabled_tick
        assert enabled_tick["autorun"]["status"] == "OK"
        assert enabled_tick["autorun"]["claimed"] is True
        assert enabled_tick["autorun"]["task"] == task_id
        assert task_row(env, task_id)["status"] == "claimed"


def test_tick_print_always_records_no_agent_observability_policy():
    td, _vault, env = make_env_and_vault()
    with td:
        payload = json.loads(run([sys.executable, str(TICK), "--print-always", "--no-state"], env).stdout)
        assert payload["observability"]["schema"] == "brain_task_dispatch_tick_observability_v1", payload
        assert payload["observability"]["stdout_policy"] == "print_always", payload
        assert payload["observability"]["printed"] is True, payload
        assert payload["observability"]["log_file"], payload
        assert "--print-always" in payload["observability"]["recovery_command"], payload


def test_tick_summary_outputs_compact_no_agent_heartbeat_without_autorun():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id = add_task(env)
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state"], env).stdout)
        assert payload["schema"] == "brain_task_dispatch_tick_summary_v1", payload
        assert payload["status"] == "OK", payload
        assert payload["evidence_spine"]["status"] == "OK", payload
        assert payload["evidence_spine"]["summary"]["counts"]["active"] >= 1, payload
        assert payload["stdout_policy"] == "summary", payload
        assert "log_file" in payload and payload["log_file"], payload
        assert "autorun" not in payload, payload
        assert payload["dispatch_hint"]["task_id"] == task_id, payload
        assert payload["dispatch_hint"]["safety"] == "hint_only", payload
        assert task_row(env, task_id)["status"] == "pending"


def test_tick_summary_autorun_step_denial_is_visible_and_non_mutating():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id = add_task(env)
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state", "--autorun-step"], env).stdout)
        assert payload["schema"] == "brain_task_dispatch_tick_summary_v1", payload
        assert payload["status"] == "OK", payload
        assert payload["dispatch_hint"]["task_id"] == task_id, payload
        assert payload["autorun"]["requested"] is True, payload
        assert payload["autorun"]["claimed"] is False, payload
        assert payload["autorun"]["advanced"] is False, payload
        assert "autorun_disabled" in payload["autorun"]["reasons"], payload
        assert task_row(env, task_id)["status"] == "pending"


def test_tick_autorun_step_auto_closes_review_tasks_with_done_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id = add_review_evolution_task(env)
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state", "--autorun-step"], env).stdout)
        assert payload["status"] == "OK", payload
        assert payload["auto_close_review"]["closed_count"] == 1, payload
        assert payload["auto_close_review"]["closed"][0]["task_id"] == task_id, payload
        assert task_row(env, task_id, include_done=True)["status"] == "done"


def test_tick_summary_claim_state_surfaces_execution_starvation_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        fixture = add_claim_state_fixture(env)
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state"], env).stdout)
        claim_state = payload["claim_state"]
        assert payload["status"] == "OK", payload
        assert claim_state["claimed_total"] == 2, payload
        assert claim_state["running_total"] == 1, payload
        assert claim_state["review_total"] == 0, payload
        assert claim_state["pending_total"] == 1, payload
        assert claim_state["stale_claim_count"] == 0, payload
        assert claim_state["unsafe_unknown_claim_count"] == 0, payload
        assert claim_state["claimed_running_ratio"] == 2.0, payload
        assert claim_state["parallel_selected_count"] == 0, payload
        assert claim_state["proof_gate_status"] == "PASS", payload
        assert claim_state["execution_starvation"] is True, payload
        assert claim_state["concurrency_raise_gate"]["status"] == "DENY", payload
        assert claim_state["concurrency_raise_gate"]["raise_allowed"] is False, payload
        assert "execution_starvation" in claim_state["concurrency_raise_gate"]["reasons"], payload
        assert task_row(env, fixture["running"])["status"] == "running"
        assert all(task_row(env, task_id)["status"] == "claimed" for task_id in fixture["claimed"])
        assert task_row(env, fixture["pending"])["status"] == "pending"


def test_tick_summary_surfaces_multimodel_intervention_hint():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id = add_multimodel_task(env)
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state"], env).stdout)
        assert payload["schema"] == "brain_task_dispatch_tick_summary_v1", payload
        assert payload["status"] == "OK", payload
        mm = payload["multimodel_intervention"]
        assert mm["intervention_required"] is True, payload
        assert mm["task_id"] == task_id, payload
        assert "accuracy" in mm["criteria"], payload
        assert "p0_evolution_blast_radius" in mm["trigger_reasons"], payload
        assert "ratification-gate" in mm["gate_command_template"], payload
        assert task_row(env, task_id)["status"] == "pending"


def test_tick_summary_ambient_multimodel_env_does_not_run_expensive_step():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id = add_multimodel_task(env)
        env["HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL"] = "1"
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state"], env).stdout)
        assert payload["status"] == "OK", payload
        assert payload["multimodel_step"] == {}, payload
        assert payload["multimodel_intervention"]["task_id"] == task_id, payload
        assert task_row(env, task_id)["status"] == "pending"


def test_tick_multimodel_step_requires_explicit_flag_and_env():
    td, _vault, env = make_env_and_vault()
    with td:
        add_multimodel_task(env)
        payload = json.loads(run([sys.executable, str(TICK), "--summary", "--no-state", "--multimodel-step"], env).stdout)
        assert payload["status"] == "OK", payload
        assert payload["multimodel_step"]["status"] == "SKIP", payload
        assert payload["multimodel_step"]["reason"] == "autorun_multimodel_disabled", payload


def test_tick_multimodel_task_argument_routes_to_targeted_step():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(list(args))
        step = args[0]
        if step == "multimodel-intervention-step":
            return {"status": "OK", "task_id": "task-1"}
        if step == "evidence-spine":
            return {"status": "OK", "gate_status": "PASS"}
        if step == "dispatch-dry-run":
            return {"status": "OK", "dispatchable": False, "next": None}
        if step == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 0, "selected": []}
        return {"status": "OK"}

    old_argv = sys.argv[:]
    old_run_json = module.run_json
    old_append_log = module.append_log
    old_save_state = module.save_state
    old_load_state = module.load_state
    old_env = os.environ.get("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL")
    try:
        module.run_json = fake_run_json
        module.append_log = lambda event: None
        module.save_state = lambda state: None
        module.load_state = lambda: {}
        os.environ["HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL"] = "1"
        sys.argv = [str(TICK), "--summary", "--no-state", "--multimodel-step", "--multimodel-task", "task-1"]
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = module.main()
        assert rc == 0
        payload = json.loads(buf.getvalue())
    finally:
        sys.argv = old_argv
        module.run_json = old_run_json
        module.append_log = old_append_log
        module.save_state = old_save_state
        module.load_state = old_load_state
        if old_env is None:
            os.environ.pop("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL", None)
        else:
            os.environ["HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL"] = old_env

    assert payload["multimodel_step"]["status"] == "OK", payload
    assert ["multimodel-intervention-step", "--task", "task-1", "--background", "--json"] in calls, calls


def test_parallel_autorun_spawns_async_worker_consumer_summary_without_foreground_wait():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(("run_json", list(args)))
        step = args[0]
        if step == "parallel-claim-and-handoff":
            return {
                "status": "OK",
                "claimed": True,
                "claimed_count": 1,
                "batch_id": "parallel-test-batch",
                "claimed_tasks": [{"task_id": "task-1", "handoff": "/tmp/task-1.md", "run_id": "r1"}],
                "safety": "parallel-claimed-and-handoff-only; does not execute task bodies or mark done",
            }
        if step == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 1, "selected": [{"id": "task-1"}]}
        if step == "dispatch-dry-run":
            return {"status": "OK", "dispatchable": True, "next": {"id": "task-1", "title": "Task 1"}}
        if step == "evidence-spine":
            return {"status": "OK", "gate_status": "PASS", "summary": {}}
        if step == "auto-close-review":
            return {"status": "OK", "closed_count": 1, "safety": "proof-gated review closer"}
        return {"status": "OK"}

    def fake_run_cmd_json(cmd, timeout=None):
        calls.append(("run_cmd_json", list(cmd), timeout))
        assert "agent_team_controller.py" in " ".join(map(str, cmd)), cmd
        if "worker-jobs" in cmd:
            return {"status": "OK", "job_count": 0, "alive_count": 0, "jobs": []}
        assert "consume-claimed" in cmd, cmd
        assert "--background" in cmd, cmd
        assert "--batch-id" in cmd and cmd[cmd.index("--batch-id") + 1] == "parallel-test-batch", cmd
        assert timeout is not None and timeout < 900, timeout
        return {
            "status": "OK",
            "event_driven": True,
            "async_worker": True,
            "started": True,
            "job_id": "job-1",
            "pid": 12345,
            "requested_count": 1,
            "consumed_count": 0,
            "running_count": 0,
            "reviewed_count": 0,
            "done_count": 0,
            "next_tick_requested": False,
            "safety": "taskpool worker spawned as durable async job; parent tick does not wait for hermes chat workers",
        }

    old_argv = sys.argv[:]
    old_run_json = module.run_json
    old_run_cmd_json = module.run_cmd_json
    old_append_log = module.append_log
    old_save_state = module.save_state
    old_load_state = module.load_state
    try:
        module.run_json = fake_run_json
        module.run_cmd_json = fake_run_cmd_json
        module.append_log = lambda event: None
        module.save_state = lambda state: None
        module.load_state = lambda: {}
        sys.argv = [str(TICK), "--summary", "--no-state", "--parallel-autorun", "--max-agents", "2"]
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = module.main()
        assert rc == 0
        payload = json.loads(buf.getvalue())
    finally:
        sys.argv = old_argv
        module.run_json = old_run_json
        module.run_cmd_json = old_run_cmd_json
        module.append_log = old_append_log
        module.save_state = old_save_state
        module.load_state = old_load_state

    assert any(call[0] == "run_cmd_json" and "consume-claimed" in call[1] for call in calls), calls
    assert payload["autorun"]["step_mode"] == "parallel_claim_and_async_worker"
    assert payload["autorun"]["claimed"] is True
    assert payload["autorun"]["worker_trigger"]["async_worker"] is True
    assert payload["autorun"]["worker_trigger"]["started"] is True
    assert payload["autorun"]["worker_trigger"]["job_id"] == "job-1"
    assert payload["autorun"]["worker_trigger"]["done_count"] == 0
    assert payload["autorun"]["event_next_tick"]["status"] == "SKIP"
    assert payload["autorun"]["event_next_tick"]["reason"] == "not_requested"
    assert not any(call[0] == "run_json" and call[1][:1] == ["auto-close-review"] for call in calls), calls


def test_parallel_autorun_timeout_releases_claimed_batch_to_retry():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(("run_json", list(args)))
        step = args[0]
        if step == "parallel-claim-and-handoff":
            return {
                "status": "OK",
                "claimed": True,
                "claimed_count": 2,
                "batch_id": "parallel-timeout-batch",
                "claimed_tasks": [
                    {"task_id": "task-1", "handoff": "/tmp/task-1.md", "run_id": "r1"},
                    {"task_id": "task-2", "handoff": "/tmp/task-2.md", "run_id": "r2"},
                ],
            }
        if step == "transition":
            return {"ok": True, "status": "OK", "task": args[1], "to_status": "retry"}
        if step == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 2, "selected": [{"id": "task-1"}, {"id": "task-2"}]}
        if step == "dispatch-dry-run":
            return {"status": "OK", "dispatchable": True, "next": {"id": "task-1", "title": "Task 1"}}
        if step == "evidence-spine":
            return {"status": "OK", "gate_status": "PASS", "summary": {}}
        return {"status": "OK"}

    def fake_run_cmd_json(cmd, timeout=None):
        calls.append(("run_cmd_json", list(cmd), timeout))
        if "worker-jobs" in cmd:
            return {"status": "OK", "job_count": 0, "alive_count": 0, "jobs": []}
        assert "consume-claimed" in cmd, cmd
        assert "--background" not in cmd, cmd
        return {"status": "ERROR", "reason": "subprocess_timeout", "returncode": "timeout"}

    old_argv = sys.argv[:]
    old_run_json = module.run_json
    old_run_cmd_json = module.run_cmd_json
    old_append_log = module.append_log
    old_save_state = module.save_state
    old_load_state = module.load_state
    try:
        module.run_json = fake_run_json
        module.run_cmd_json = fake_run_cmd_json
        module.append_log = lambda event: None
        module.save_state = lambda state: None
        module.load_state = lambda: {}
        sys.argv = [str(TICK), "--summary", "--no-state", "--parallel-autorun", "--parallel-worker-foreground", "--max-agents", "2"]
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = module.main()
        assert rc == 2
        payload = json.loads(buf.getvalue())
    finally:
        sys.argv = old_argv
        module.run_json = old_run_json
        module.run_cmd_json = old_run_cmd_json
        module.append_log = old_append_log
        module.save_state = old_save_state
        module.load_state = old_load_state

    transition_calls = [call for call in calls if call[0] == "run_json" and call[1][:1] == ["transition"]]
    assert len(transition_calls) == 2, calls
    for _, args in transition_calls:
        assert "--to" in args and args[args.index("--to") + 1] == "retry", args
        assert "--force" in args, args
        assert "event_worker_trigger_timeout_cleanup" in " ".join(args), args
    cleanup = payload["autorun"]["worker_timeout_cleanup"]
    assert cleanup["released_count"] == 2, cleanup
    assert payload["errors"][0]["timeout_cleanup"]["released_count"] == 2, payload


def test_event_next_tick_depth_zero_skips_without_claiming_or_closing():
    module = load_tick_module()
    calls = []
    old_run_json = module.run_json
    try:
        module.run_json = lambda args: calls.append(list(args)) or {"status": "OK"}
        result = module.event_next_tick_follow_through(
            worker_trigger={"next_tick_requested": True, "reviewed_count": 1},
            review_close_max_tasks=50,
            max_depth=0,
        )
    finally:
        module.run_json = old_run_json
    assert result["status"] == "SKIP"
    assert result["reason"] == "depth_limit_zero"
    assert result["skip_reasons"] == ["depth_limit_zero"]
    assert result["depth_used"] == 0
    assert calls == []


def test_event_next_tick_not_requested_skips_without_side_effects():
    module = load_tick_module()
    calls = []
    old_run_json = module.run_json
    try:
        module.run_json = lambda args: calls.append(list(args)) or {"status": "OK"}
        result = module.event_next_tick_follow_through(
            worker_trigger={"next_tick_requested": False, "reviewed_count": 0},
            review_close_max_tasks=50,
            max_depth=1,
        )
    finally:
        module.run_json = old_run_json
    assert result["status"] == "SKIP"
    assert result["reason"] == "not_requested"
    assert result["skip_reasons"] == ["not_requested"]
    assert calls == []



def test_api_quota_capacity_probe_caps_on_hard_blockers_not_unknowns():
    module = load_tick_module()
    old_run_cmd_json = module.run_cmd_json
    try:
        def fake_run_cmd_json(cmd, timeout=None):
            assert "model_quota.py" in " ".join(map(str, cmd)), cmd
            return {
                "status": "FAIL_CLOSED",
                "pass_count": 1,
                "failure_count": 3,
                "failures": [
                    {"model": "claude-opus-4-7", "provider": "claude-code", "status": "unobservable", "reasons": ["status_unobservable"]},
                    {"model": "deepseek-v4-pro", "provider": "deepseek", "status": "exhausted", "reasons": ["quota_exhausted"]},
                    {"model": "mimo-v2.5-pro", "provider": "xiaomi", "status": "unknown", "reasons": ["status_unknown"]},
                ],
            }
        module.run_cmd_json = fake_run_cmd_json
        probe = module.api_quota_capacity_probe(dynamic_ceiling=6)
    finally:
        module.run_cmd_json = old_run_cmd_json
    assert probe["status"] == "OK", probe
    assert probe["api_slots"] == 5, probe
    assert probe["hard_blocker_count"] == 1, probe
    assert probe["soft_unknown_count"] == 2, probe


def test_api_quota_capacity_probe_unavailable_error_does_not_echo_stdout_stderr():
    module = load_tick_module()
    old_run_cmd_json = module.run_cmd_json
    try:
        module.run_cmd_json = lambda cmd, timeout=None: {
            "status": "ERROR",
            "reason": "subprocess_failed",
            "returncode": 2,
            "stdout": "token=SECRET",
            "stderr": "Authorization: bearer ***",
        }
        probe = module.api_quota_capacity_probe(dynamic_ceiling=6)
    finally:
        module.run_cmd_json = old_run_cmd_json
    assert probe["status"] == "SKIP", probe
    error = probe["confidence_gate_error"]
    assert error["status"] == "ERROR", error
    assert "stdout" not in error and "stderr" not in error, error
    assert probe["api_slots"] == 6, probe


def test_api_quota_capacity_probe_env_cap_overrides_slots():
    module = load_tick_module()
    old_run_cmd_json = module.run_cmd_json
    old_env = os.environ.get("HERMES_TASKPOOL_API_CAP")
    try:
        os.environ["HERMES_TASKPOOL_API_CAP"] = "2"
        module.run_cmd_json = lambda cmd, timeout=None: {"status": "PASS", "pass_count": 4, "failure_count": 0, "failures": []}
        probe = module.api_quota_capacity_probe(dynamic_ceiling=6)
    finally:
        module.run_cmd_json = old_run_cmd_json
        if old_env is None:
            os.environ.pop("HERMES_TASKPOOL_API_CAP", None)
        else:
            os.environ["HERMES_TASKPOOL_API_CAP"] = old_env
    assert probe["api_slots"] == 2, probe
    assert probe["env_api_cap"] == 2, probe


def test_scheduler_decision_classifies_boundary_headroom_and_batch_candidates():
    module = load_tick_module()
    event = {
        "task_list": {"status": "OK", "rows": [
            {"id": "running-1", "status": "running"},
            {"id": "pending-1", "status": "pending"},
        ]},
        "parallel_dispatch": {
            "status": "OK",
            "dispatchable": True,
            "selected_count": 0,
            "skipped": [
                {"id": "t1", "reason": "parallel_boundary_conflict", "boundary_key": "boundary:repo-a"},
                {"id": "t2", "reason": "parallel_boundary_conflict", "boundary_key": "boundary:repo-a"},
                {"id": "t3", "reason": "parallel_boundary_conflict", "boundary_key": "boundary:repo-a"},
            ],
        },
    }
    decision = module.scheduler_decision_snapshot(
        event=event,
        resource_probe={"effective_resource_ceiling": 4},
        threshold=3,
    )
    assert decision["action"] == "boundary_refinement_or_batch_merge", decision
    assert "boundary_conflict_with_resource_headroom" in decision["reasons"], decision
    assert decision["batch_merge_candidate_count"] == 1, decision
    assert decision["batch_merge_candidates"][0]["merge_policy"] == "propose_only", decision


def test_drain_first_consumes_only_uncovered_claimed_tasks():
    module = load_tick_module()
    calls = []

    def fake_run_agent_team_json(args, timeout=None):
        calls.append((list(args), timeout))
        if args[:1] == ["worker-jobs"]:
            return {"status": "OK", "job_count": 1, "alive_count": 1, "jobs": [{"alive": True, "task_ids": ["claimed-covered"]}]}
        assert args[0] == "consume-claimed", args
        payload = json.loads(args[args.index("--claimed-json") + 1])
        assert [row["id"] for row in payload] == ["claimed-open"], payload
        assert "--background" in args, args
        return {"status": "OK", "async_worker": True, "started": True, "task_ids": ["claimed-open"]}

    old_run_agent_team_json = module.run_agent_team_json
    old_run_json = module.run_json
    rows = [
        {"id": "claimed-covered", "status": "claimed", "claimed_by": "hermes-parallel", "claim_expires_at": "2099", "run_id": "r1"},
        {"id": "claimed-open", "status": "claimed", "claimed_by": "hermes-parallel", "claim_expires_at": "2099", "run_id": "r2"},
        {"id": "human-claimed", "status": "claimed", "claimed_by": "human", "claim_expires_at": "2099", "run_id": "r3", "stale_claim": True},
        {"id": "pending-1", "status": "pending"},
    ]
    try:
        module.run_agent_team_json = fake_run_agent_team_json
        module.run_json = lambda args: {"status": "OK", "rows": rows} if args[:1] == ["list"] else {"status": "OK"}
        result = module.trigger_claimed_drain_first(
            task_list={"rows": rows},
            max_agents=4,
            foreground=False,
        )
    finally:
        module.run_agent_team_json = old_run_agent_team_json
        module.run_json = old_run_json
    assert result["status"] == "OK", result
    assert result["drainable_count"] == 1, result
    assert result["drained_task_ids"] == ["claimed-open"], result
    assert len(calls) == 2, calls


def test_event_next_tick_refill_is_bounded_and_explicit():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(("run_json", list(args)))
        step = args[0]
        if step == "auto-close-review":
            return {"status": "OK", "closed_count": 1}
        if step == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 1, "selected": [{"id": "task-2"}]}
        if step == "parallel-claim-and-handoff":
            return {
                "status": "OK",
                "claimed": True,
                "batch_id": "follow-batch",
                "claimed_tasks": [{"task_id": "task-2", "run_id": "r2"}],
            }
        return {"status": "OK"}

    def fake_run_agent_team_json(args, timeout=None):
        calls.append(("run_agent_team_json", list(args), timeout))
        assert args[0] == "consume-claimed", args
        assert "--background" in args, args
        return {"status": "OK", "async_worker": True, "started": True}

    old_run_json = module.run_json
    old_run_agent_team_json = module.run_agent_team_json
    try:
        module.run_json = fake_run_json
        module.run_agent_team_json = fake_run_agent_team_json
        result = module.event_next_tick_follow_through(
            worker_trigger={"next_tick_requested": True, "reviewed_count": 1},
            review_close_max_tasks=50,
            max_depth=3,
            refill_enabled=True,
            max_agents=7,
            worker_foreground=False,
        )
    finally:
        module.run_json = old_run_json
        module.run_agent_team_json = old_run_agent_team_json

    assert result["status"] == "OK", result
    assert result["depth_used"] == 1, result
    assert result["refill"]["batch_id"] == "follow-batch", result
    assert result["refill_worker_trigger"]["started"] is True, result
    assert [c for c in calls if c[0] == "run_json" and c[1][:1] == ["parallel-claim-and-handoff"]], calls
    assert len([c for c in calls if c[0] == "run_agent_team_json"]) == 1, calls


def test_event_next_tick_refill_timeout_releases_claimed_tasks():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(("run_json", list(args)))
        step = args[0]
        if step == "auto-close-review":
            return {"status": "OK", "closed_count": 1}
        if step == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 1, "selected": [{"id": "task-2"}]}
        if step == "parallel-claim-and-handoff":
            return {"status": "OK", "claimed": True, "batch_id": "follow-batch", "claimed_tasks": [{"task_id": "task-2", "run_id": "r2"}]}
        if step == "transition":
            return {"status": "OK", "ok": True, "task": args[1], "to_status": "retry"}
        return {"status": "OK"}

    def fake_run_agent_team_json(args, timeout=None):
        calls.append(("run_agent_team_json", list(args), timeout))
        return {"status": "ERROR", "reason": "subprocess_timeout", "returncode": "timeout"}

    old_run_json = module.run_json
    old_run_agent_team_json = module.run_agent_team_json
    try:
        module.run_json = fake_run_json
        module.run_agent_team_json = fake_run_agent_team_json
        result = module.event_next_tick_follow_through(
            worker_trigger={"next_tick_requested": True, "reviewed_count": 1},
            review_close_max_tasks=50,
            max_depth=3,
            refill_enabled=True,
            max_agents=7,
        )
    finally:
        module.run_json = old_run_json
        module.run_agent_team_json = old_run_agent_team_json

    assert result["status"] == "ERROR", result
    assert result["reason"] == "refill_worker_trigger_failed", result
    cleanup = result["refill_worker_failure_cleanup"]
    assert cleanup["released_count"] == 1, cleanup
    assert result["refill_worker_timeout_cleanup"]["released_count"] == 1, result
    transition_calls = [call for call in calls if call[0] == "run_json" and call[1][:1] == ["transition"]]
    assert transition_calls and "hermes-parallel-follow-through" in " ".join(transition_calls[0][1]), transition_calls


def test_event_next_tick_refill_non_timeout_failure_releases_claimed_tasks():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(("run_json", list(args)))
        if args[0] == "auto-close-review":
            return {"status": "OK", "closed_count": 1}
        if args[0] == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 1}
        if args[0] == "parallel-claim-and-handoff":
            return {"status": "OK", "claimed": True, "batch_id": "follow-batch", "claimed_tasks": [{"task_id": "task-2", "run_id": "r2"}]}
        if args[0] == "transition":
            return {"status": "OK", "ok": True, "task": args[1], "to_status": "retry"}
        return {"status": "OK"}

    old_run_json = module.run_json
    old_run_agent_team_json = module.run_agent_team_json
    try:
        module.run_json = fake_run_json
        module.run_agent_team_json = lambda args, timeout=None: {"status": "ERROR", "reason": "spawn_failed"}
        result = module.event_next_tick_follow_through(
            worker_trigger={"next_tick_requested": True, "reviewed_count": 1},
            review_close_max_tasks=50,
            max_depth=3,
            refill_enabled=True,
            max_agents=7,
        )
    finally:
        module.run_json = old_run_json
        module.run_agent_team_json = old_run_agent_team_json

    assert result["status"] == "ERROR", result
    assert result["refill_worker_failure_cleanup"]["released_count"] == 1, result
    transition_calls = [call for call in calls if call[0] == "run_json" and call[1][:1] == ["transition"]]
    assert transition_calls, calls


def test_event_next_tick_refill_default_off_does_not_claim():
    module = load_tick_module()
    calls = []

    def fake_run_json(args):
        calls.append(list(args))
        if args[0] == "auto-close-review":
            return {"status": "OK", "closed_count": 1}
        if args[0] == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 1, "selected": [{"id": "task-2"}]}
        raise AssertionError(f"unexpected side effect: {args}")

    old_run_json = module.run_json
    try:
        module.run_json = fake_run_json
        result = module.event_next_tick_follow_through(
            worker_trigger={"next_tick_requested": True, "reviewed_count": 1},
            review_close_max_tasks=50,
            max_depth=3,
        )
    finally:
        module.run_json = old_run_json

    assert result["status"] == "OK", result
    assert result["next_dispatch_selected_count"] == 1, result
    assert not any(call[:1] == ["parallel-claim-and-handoff"] for call in calls), calls

def test_tick_evidence_spine_warn_is_visible_but_not_fatal():
    module = load_tick_module()

    def fake_run_json(args):
        step = args[0]
        if step == "evidence-spine":
            return {
                "status": "FAIL",
                "gate_status": "WARN",
                "summary": {"auto_completer_semantic_status": "error"},
            }
        if step == "dispatch-dry-run":
            return {"status": "OK", "dispatchable": False, "next": None}
        if step == "parallel-dispatch-dry-run":
            return {"status": "OK", "selected_count": 0, "selected": []}
        return {"status": "OK"}

    old_argv = sys.argv[:]
    old_run_json = module.run_json
    old_append_log = module.append_log
    old_save_state = module.save_state
    old_load_state = module.load_state
    try:
        module.run_json = fake_run_json
        module.append_log = lambda event: None
        module.save_state = lambda state: None
        module.load_state = lambda: {}
        sys.argv = [str(TICK), "--summary", "--no-state", "--parallel-autorun", "--max-agents", "2"]
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = module.main()
        assert rc == 0
        payload = json.loads(buf.getvalue())
    finally:
        sys.argv = old_argv
        module.run_json = old_run_json
        module.append_log = old_append_log
        module.save_state = old_save_state
        module.load_state = old_load_state

    assert payload["status"] == "WARN", payload
    assert payload["error_count"] == 0, payload
    assert payload["warning_count"] == 1, payload
    assert payload["warnings"][0]["step"] == "evidence_spine", payload
    assert payload["evidence_spine"]["gate_status"] == "WARN", payload
    assert payload["autorun"]["present"] is True, payload


def test_run_cmd_json_preserves_structured_nonzero_stdout_for_diagnostics():
    module = load_tick_module()
    result = module.run_cmd_json([
        sys.executable,
        "-c",
        "import json, sys; print(json.dumps({'status':'FAIL','gate_status':'FAIL','summary':{'selfcheck':'FAIL'}})); sys.exit(2)",
    ])
    assert result["status"] == "ERROR", result
    assert result["reported_status"] == "FAIL", result
    assert result["gate_status"] == "FAIL", result
    assert result["summary"]["selfcheck"] == "FAIL", result
    assert result["returncode"] == 2, result
    assert result["cmd"], result


def test_run_cmd_json_forces_nonzero_ok_stdout_to_error():
    module = load_tick_module()
    result = module.run_cmd_json([
        sys.executable,
        "-c",
        "import json, sys; print(json.dumps({'status':'OK'})); sys.exit(2)",
    ])
    assert result["status"] == "ERROR", result
    assert result["reported_status"] == "OK", result
    assert result["returncode"] == 2, result


def test_run_cmd_json_timeout_is_structured_and_kills_process_group():
    module = load_tick_module()
    marker = "hermes-pgid-timeout-fixture"
    old_timeout = module.os.environ.get("HERMES_BRAIN_DISPATCH_TICK_COMMAND_TIMEOUT_SECONDS")
    old_grace = module.os.environ.get("HERMES_BRAIN_DISPATCH_TICK_TERMINATE_GRACE_SECONDS")
    module.os.environ["HERMES_BRAIN_DISPATCH_TICK_COMMAND_TIMEOUT_SECONDS"] = "0.05"
    module.os.environ["HERMES_BRAIN_DISPATCH_TICK_TERMINATE_GRACE_SECONDS"] = "0.05"
    try:
        result = module.run_cmd_json([
            sys.executable,
            "-c",
            (
                "import signal, subprocess, sys, time; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "subprocess.Popen([sys.executable, '-c', 'import signal, time, sys; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)', 'hermes-pgid-timeout-fixture']); "
                "time.sleep(30)"
            ),
            marker,
        ])
    finally:
        if old_timeout is None:
            module.os.environ.pop("HERMES_BRAIN_DISPATCH_TICK_COMMAND_TIMEOUT_SECONDS", None)
        else:
            module.os.environ["HERMES_BRAIN_DISPATCH_TICK_COMMAND_TIMEOUT_SECONDS"] = old_timeout
        if old_grace is None:
            module.os.environ.pop("HERMES_BRAIN_DISPATCH_TICK_TERMINATE_GRACE_SECONDS", None)
        else:
            module.os.environ["HERMES_BRAIN_DISPATCH_TICK_TERMINATE_GRACE_SECONDS"] = old_grace
    assert result["status"] == "ERROR", result
    assert result["returncode"] == "timeout", result
    assert result["reason"] == "subprocess_timeout", result
    assert result["process_group_terminated"] is True, result
    assert result["process_group_killed"] is True, result
    time.sleep(0.2)
    ps = subprocess.check_output(["ps", "-axo", "command"], text=True)
    leftovers = [line for line in ps.splitlines() if marker in line and "ps -axo" not in line]
    assert leftovers == [], leftovers


def test_agent_team_background_worker_job_records_and_dedupes_alive_batches():
    module = load_agent_team_module()
    td = tempfile.TemporaryDirectory()
    with td:
        root = Path(td.name)
        module.WORKER_JOB_DIR = root / "jobs"
        module.WORKER_LOG_DIR = root / "logs"
        module.human_escape_check = lambda: (False, {})
        module.is_disabled = lambda: False
        module.process_alive = lambda pid: True

        popen_calls = []

        class FakePopen:
            def __init__(self, cmd, **kwargs):
                self.pid = 4242
                popen_calls.append((list(cmd), kwargs))

        old_popen = module.subprocess.Popen
        try:
            module.subprocess.Popen = FakePopen
            claimed = [{"task_id": "task-1", "handoff": "/tmp/task-1.md", "run_id": "r1"}]
            first = module.start_consume_claimed_background(claimed, max_agents=2, batch_id="batch-1")
            second = module.start_consume_claimed_background(claimed, max_agents=2, batch_id="batch-1")
            jobs = module.command_worker_jobs()
        finally:
            module.subprocess.Popen = old_popen

    assert first["status"] == "OK", first
    assert first["async_worker"] is True and first["started"] is True, first
    assert first["job"]["batch_id"] == "batch-1", first
    assert first["job"]["task_ids"] == ["task-1"], first
    assert "--background" not in popen_calls[0][0], popen_calls
    assert second["status"] == "OK" and second["already_running"] is True, second
    assert len(popen_calls) == 1, popen_calls
    assert jobs["job_count"] == 1 and jobs["alive_count"] == 1, jobs


if __name__ == "__main__":
    test_tick_autorun_bridge_is_opt_in_and_fail_closed()
    test_tick_print_always_records_no_agent_observability_policy()
    test_tick_summary_outputs_compact_no_agent_heartbeat_without_autorun()
    test_tick_summary_autorun_step_denial_is_visible_and_non_mutating()
    test_tick_autorun_step_auto_closes_review_tasks_with_done_gate()
    test_tick_summary_surfaces_multimodel_intervention_hint()
    test_tick_summary_ambient_multimodel_env_does_not_run_expensive_step()
    test_tick_multimodel_step_requires_explicit_flag_and_env()
    test_tick_multimodel_task_argument_routes_to_targeted_step()
    test_parallel_autorun_spawns_async_worker_consumer_summary_without_foreground_wait()
    test_parallel_autorun_timeout_releases_claimed_batch_to_retry()
    test_event_next_tick_depth_zero_skips_without_claiming_or_closing()
    test_event_next_tick_not_requested_skips_without_side_effects()
    test_api_quota_capacity_probe_caps_on_hard_blockers_not_unknowns()
    test_api_quota_capacity_probe_unavailable_error_does_not_echo_stdout_stderr()
    test_api_quota_capacity_probe_env_cap_overrides_slots()
    test_scheduler_decision_classifies_boundary_headroom_and_batch_candidates()
    test_drain_first_consumes_only_uncovered_claimed_tasks()
    test_event_next_tick_refill_is_bounded_and_explicit()
    test_event_next_tick_refill_timeout_releases_claimed_tasks()
    test_event_next_tick_refill_non_timeout_failure_releases_claimed_tasks()
    test_event_next_tick_refill_default_off_does_not_claim()
    test_run_cmd_json_preserves_structured_nonzero_stdout_for_diagnostics()
    test_run_cmd_json_forces_nonzero_ok_stdout_to_error()
    test_run_cmd_json_timeout_is_structured_and_kills_process_group()
    test_agent_team_background_worker_job_records_and_dedupes_alive_batches()
    print("PASS")
