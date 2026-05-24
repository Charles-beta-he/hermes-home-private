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


def test_task_spec_section_preserves_task_level_requirements():
    module = load_module()

    section = module.build_task_spec_section(
        {
            "id": "task-1",
            "title": "实现 Hermes worker 规则收敛",
            "body": "用户已经在 chat 里说过一次：任务池 worker 必须继承验收标准，不要让用户重复描述。",
            "acceptance_criteria": [
                "worker prompt includes task acceptance criteria",
                "chat-to-task requirements remain the single source of truth",
            ],
            "red_lines": ["不得要求用户在 chat 和 taskpool 各说一遍"],
            "non_goals": ["不要取消 --ignore-rules 隔离"],
            "workflow_contract": {"proof": "PROOF_JSON required"},
            "evidence_refs": ["plans/taskpool-chat-rules.md"],
        }
    )

    assert "TASK-SPEC REQUIREMENTS SNAPSHOT" in section
    assert "用户已经在 chat 里说过一次" in section
    assert "worker prompt includes task acceptance criteria" in section
    assert "不得要求用户在 chat 和 taskpool 各说一遍" in section
    assert "不要取消 --ignore-rules 隔离" in section
    assert "PROOF_JSON required" in section


def test_delegate_worker_injects_digest_and_task_spec_while_preserving_ignore_rules(monkeypatch, tmp_path):
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
            "body": "用户要求：任务池继承 chat 中已表达的验收标准。",
            "acceptance_criteria": ["不需要重复在 chat 再说一次"],
            "red_lines": ["不得丢失任务级验收"],
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
    assert "TASK-SPEC REQUIREMENTS SNAPSHOT" in prompt
    assert "不需要重复在 chat 再说一次" in prompt
    assert "不得丢失任务级验收" in prompt
