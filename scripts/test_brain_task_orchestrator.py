#!/usr/bin/env python3
"""Tests for brain_task_orchestrator.py.
Run with: python3 ~/.hermes/scripts/test_brain_task_orchestrator.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "brain_task_orchestrator.py"


def run(env, *args, check=True):
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"command failed {cmd}\nstdout={r.stdout}\nstderr={r.stderr}")
    return r


def test_add_list_claim_release_dashboard_inbox_selfcheck():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td) / "brain"
        (vault / "05-实践与项目" / "tasks").mkdir(parents=True)
        (vault / "07-仪表盘").mkdir(parents=True)
        env = os.environ.copy()
        env["HERMES_BRAIN_VAULT"] = str(vault)

        r = run(env, "add", "完成本地大脑任务控制台", "--priority", "P1", "--project", "local-brain", "--expires-at", "2099-01-01", "--json")
        created = json.loads(r.stdout)
        assert created["status"] == "OK"
        task_id = created["id"]

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        assert rows and rows[0]["id"] == task_id
        assert rows[0]["priority"] == "P1"

        claim = json.loads(run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json").stdout)
        assert claim["claimed_by"] == "tester"

        denied = run(env, "release", task_id, "--actor", "other", "--json", check=False)
        assert denied.returncode != 0

        rel = json.loads(run(env, "release", task_id, "--actor", "tester", "--to-status", "pending", "--json").stdout)
        assert rel["to_status"] == "pending"

        dash = json.loads(run(env, "dashboard", "--write", "--json").stdout)
        assert Path(dash["dashboard"]).exists()
        assert Path(dash["control_center"]).exists()
        assert Path(dash["sorted_pool"]).exists()
        assert "处理本地大脑任务收件箱" in Path(dash["control_center"]).read_text(encoding="utf-8")

        inbox = vault / "05-实践与项目" / "tasks" / "任务收件箱.md"
        inbox.write_text(inbox.read_text(encoding="utf-8") + "\n- [ ] 新增收件箱任务 | priority:P0 | project:inbox-test | due:2099-02-01 | concepts:task,test\n", encoding="utf-8")
        ing = json.loads(run(env, "ingest-inbox", "--write", "--json").stdout)
        assert ing["created_count"] >= 1
        assert "<!-- ingested:" in inbox.read_text(encoding="utf-8")

        done = json.loads(run(env, "done", task_id, "--actor", "tester", "--evidence", "unit-test", "--json").stdout)
        assert done["status"] == "OK"

        selfcheck = json.loads(run(env, "selfcheck", "--json").stdout)
        assert selfcheck["status"] == "PASS", selfcheck


def main():
    test_add_list_claim_release_dashboard_inbox_selfcheck()
    print("PASS")


if __name__ == "__main__":
    main()
