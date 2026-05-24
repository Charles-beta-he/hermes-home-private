#!/usr/bin/env python3
"""Regression tests for taskpool execution-worker rule digest injection."""
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "agent_team_controller.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("agent_team_controller_under_test", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_execution_rules_digest_includes_local_constitution(tmp_path):
    module = load_module()
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "AGENTS.md").write_text(
        "# Local Constitution\nPolicy: proof gates, fail-closed default.\n",
        encoding="utf-8",
    )

    digest = module.build_execution_rules_digest(hermes_home=hermes_home)

    assert "CANONICAL EXECUTION RULES DIGEST" in digest
    assert "proof gates" in digest
    assert "fail-closed" in digest
    assert "--ignore-rules only skips chat context" in digest


def test_delegate_worker_injects_digest_while_preserving_ignore_rules(monkeypatch, tmp_path):
    module = load_module()
    captured = {}

    monkeypatch.setattr(module, "load_project_profile", lambda project: {})
    monkeypatch.setattr(module, "can_continue", lambda task_id: (False, 0))
    monkeypatch.setattr(module, "build_execution_rules_digest", lambda: "CANONICAL EXECUTION RULES DIGEST\n- shared red line")

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="PROOF_JSON {\"ok\": true}", stderr="")

    monkeypatch.setattr(module._sp if hasattr(module, "_sp") else subprocess, "run", fake_run, raising=False)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(module, "collect_proof", lambda task_id, output: {"ok": True})

    result = module.delegate_to_worker(
        {
            "id": "task-1",
            "title": "实现 Hermes worker 规则收敛",
            "project": "hermes",
            "parallel_boundary": "scripts/agent_team_controller.py",
        },
        conflict_group="hermes-control-plane",
        eid="abcdef123456",
    )

    assert result["status"] == "done"
    cmd = captured["cmd"]
    assert "--ignore-rules" in cmd
    prompt = cmd[cmd.index("-q") + 1]
    assert "CANONICAL EXECUTION RULES DIGEST" in prompt
    assert "shared red line" in prompt
