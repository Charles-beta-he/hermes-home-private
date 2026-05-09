#!/usr/bin/env python3
"""Tests for brain_task_dispatch_tick.py autorun bridge.
Run with: python3 ~/.hermes/scripts/test_brain_task_dispatch_tick.py
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
    env = os.environ.copy()
    env["HERMES_BRAIN_VAULT"] = str(vault)
    env["HERMES_BRAIN_AUTORUN_STATE_DIR"] = str(root / "autorun-state")
    env["HERMES_BRAIN_DISPATCH_TICK_STATE_DIR"] = str(root / "tick-state")
    env["HERMES_BRAIN_DISPATCH_TICK_LOG_DIR"] = str(root / "tick-logs")
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN", None)
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
        enabled_tick = json.loads(run([sys.executable, str(TICK), "--print-always", "--no-state", "--autorun"], env).stdout)
        assert enabled_tick["status"] == "OK", enabled_tick
        assert enabled_tick["autorun"]["status"] == "OK"
        assert enabled_tick["autorun"]["claimed"] is True
        assert enabled_tick["autorun"]["task"] == task_id
        assert task_row(env, task_id)["status"] == "claimed"


if __name__ == "__main__":
    test_tick_autorun_bridge_is_opt_in_and_fail_closed()
    print("PASS")
