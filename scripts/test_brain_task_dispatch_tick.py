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

HOME = Path.home()
ORCH = HOME / ".hermes" / "scripts" / "brain_task_orchestrator.py"
TICK = HOME / ".hermes" / "scripts" / "brain_task_dispatch_tick.py"


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
    hermes_home = root / "hermes-home"
    scripts_dir = hermes_home / "scripts"
    scripts_dir.mkdir(parents=True)
    real_scripts = Path.home() / ".hermes" / "scripts"
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
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN", None)
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL", None)
    return td, vault, env


def add_task(env):
    r = run([
        sys.executable,
        str(ORCH),
        "add",
        "验证 safe tick autorun bridge",
        "--priority",
        "P1",
        "--project",
        "local-brain-task-orchestration",
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


def task_row(env, task_id):
    rows = json.loads(run([sys.executable, str(ORCH), "list", "--json"], env).stdout)["rows"]
    return next(r for r in rows if r["id"] == task_id)


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


if __name__ == "__main__":
    test_tick_autorun_bridge_is_opt_in_and_fail_closed()
    test_tick_print_always_records_no_agent_observability_policy()
    test_tick_summary_outputs_compact_no_agent_heartbeat_without_autorun()
    test_tick_summary_autorun_step_denial_is_visible_and_non_mutating()
    test_tick_summary_surfaces_multimodel_intervention_hint()
    test_tick_summary_ambient_multimodel_env_does_not_run_expensive_step()
    test_tick_multimodel_step_requires_explicit_flag_and_env()
    test_run_cmd_json_timeout_is_structured_and_kills_process_group()
    print("PASS")
