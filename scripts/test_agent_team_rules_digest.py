#!/usr/bin/env python3
"""Regression tests for taskpool execution-worker rule digest injection."""
import argparse
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
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_orchestrator_module():
    sys.path.insert(0, str(SCRIPTS_DIR))
    path = SCRIPTS_DIR / "brain_task_orchestrator.py"
    spec = importlib.util.spec_from_file_location("brain_task_orchestrator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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


def test_task_spec_section_includes_objective_and_acceptance_evidence_fallbacks():
    module = load_module()

    section = module.build_task_spec_section(
        {
            "id": "task-ssot",
            "title": "SSOT completeness",
            "objective": "Capture chat requirement once into the task record.",
            "acceptance_evidence": "worker proof maps acceptance atoms to deterministic evidence",
            "mission_objective": "Mission objective is also machine-readable.",
            "body": "body fallback remains available for legacy notes",
        }
    )

    assert "OBJECTIVE" in section
    assert "Capture chat requirement once" in section
    assert "ACCEPTANCE_EVIDENCE" in section
    assert "worker proof maps acceptance atoms" in section
    assert "MISSION_OBJECTIVE" in section


def test_worker_prompt_requires_acceptance_and_red_line_proof_mapping():
    module = load_module()

    prompt = module.build_worker_context(
        {
            "id": "task-proof-contract",
            "title": "closeout proof contract",
            "project": "hermes",
            "acceptance_criteria": ["criterion must be mapped"],
            "red_lines": ["no fake done"],
        },
        conflict_group="hermes-control-plane",
        profile={},
    )

    assert "acceptance_criteria_covered" in prompt
    assert "red_lines_status" in prompt
    assert "no_red_line_violations" in prompt
    assert "BLOCKED instead of done" in prompt


def test_worker_done_proof_without_acceptance_mapping_is_rejected():
    module = load_module()

    result = module.validate_worker_proof_against_task(
        {"acceptance_criteria": ["worker prompt includes task acceptance criteria"]},
        {"status": "done", "summary": "implemented", "files_changed": [], "tests_passed": 1},
    )

    assert result["status"] == "FAIL"
    assert "acceptance_criteria_covered_missing" in result["violations"]


def test_worker_done_proof_with_red_line_unknown_is_rejected():
    module = load_module()

    result = module.validate_worker_proof_against_task(
        {"red_lines": ["do not fake evidence"]},
        {"status": "done", "summary": "done", "no_red_line_violations": False, "red_lines_status": "unknown"},
    )

    assert result["status"] == "FAIL"
    assert any(v.startswith("red_line") for v in result["violations"])


def test_worker_blocked_proof_can_report_missing_evidence_without_done_closeout():
    module = load_module()

    result = module.validate_worker_proof_against_task(
        {"acceptance_criteria": ["needs real browser proof"], "red_lines": ["no mock evidence"]},
        {"status": "blocked", "summary": "browser auth missing", "blockers": ["HUMAN_INPUT_NEEDED"]},
    )

    assert result["status"] == "PASS"
    assert result["proof_status"] == "blocked"


def test_worker_done_proof_with_acceptance_and_red_line_mapping_passes():
    module = load_module()

    result = module.validate_worker_proof_against_task(
        {
            "acceptance_criteria": ["worker prompt includes task acceptance criteria"],
            "red_lines": ["do not fake evidence"],
        },
        {
            "status": "done",
            "summary": "implemented",
            "acceptance_criteria_covered": [
                {"criterion": "worker prompt includes task acceptance criteria", "status": "covered", "evidence": ["command:pytest PASS"]}
            ],
            "red_lines_status": {"do not fake evidence": "safe"},
            "no_red_line_violations": True,
            "evidence": ["command:pytest PASS"],
        },
    )

    assert result["status"] == "PASS"


def test_worker_done_proof_with_junk_acceptance_mapping_is_rejected():
    module = load_module()

    result = module.validate_worker_proof_against_task(
        {"acceptance_criteria": ["real browser proof covers the task"]},
        {
            "status": "done",
            "acceptance_criteria_covered": [
                {"criterion": "unrelated criterion", "status": "covered", "evidence": ["command:echo ok"]}
            ],
        },
    )

    assert result["status"] == "FAIL"
    assert any(v.startswith("acceptance_criterion_not_evidence_covered") for v in result["violations"])


def test_worker_done_proof_uses_acceptance_evidence_fallback_gate():
    module = load_module()

    result = module.validate_worker_proof_against_task(
        {"acceptance_evidence": "artifact:proof.json records browser verification"},
        {
            "status": "done",
            "acceptance_criteria_covered": [
                {"criterion": "artifact:proof.json records browser verification", "status": "covered", "evidence": ["artifact:proof.json"]}
            ],
        },
    )

    assert result["status"] == "PASS"


def test_delegate_done_with_inconsistent_proof_returns_blocked(monkeypatch):
    module = load_module()

    class FakeCompleted:
        returncode = 0
        stdout = 'worker output\nPROOF_JSON: {"status":"done"}'
        stderr = ""

    monkeypatch.setattr(module._sp if hasattr(module, "_sp") else subprocess, "run", lambda *args, **kwargs: FakeCompleted(), raising=False)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: FakeCompleted())
    monkeypatch.setattr(module, "collect_proof", lambda task_id, output: {"status": "done", "summary": "claimed"})

    result = module.delegate_to_worker(
        {
            "id": "proof-fail-task",
            "title": "must not fake done",
            "project": "hermes",
            "acceptance_criteria": ["criterion must be evidenced"],
        },
        "hermes-control-plane",
        "envelope-proof-fail",
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "proof_consistency_failed"


def test_command_add_persists_structured_task_spec_fields(monkeypatch, tmp_path):
    module = load_orchestrator_module()
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(module, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(module, "refresh_derived_task_views", lambda reason: {"status": "SKIP"})
    monkeypatch.setattr(module, "maybe_fire_taskpool_event_hook", lambda *args, **kwargs: {"status": "SKIP"})
    monkeypatch.setattr(module, "architecture_alignment_missing", lambda fm: [])
    monkeypatch.setattr(module, "obsidian_link", lambda path: f"obsidian://test/{Path(path).name}")

    args = argparse.Namespace(
        title="structured spec intake",
        status="pending",
        lane="work",
        priority="P2",
        priority_layer="P2",
        dependency_order="implementation",
        multimodel_triage_result="P2:test",
        layer="L3",
        project="hermes",
        workflow_contract="evidence-first",
        workspace="",
        parallel_boundary="scripts/agent_team_controller.py",
        concepts="task",
        architecture_target="",
        capability_delta="",
        anti_drift_check="",
        acceptance_evidence="artifact:proof.json",
        requires_multimodel=False,
        multimodel_reason="",
        expected_participants="",
        truth_gate="local-proof",
        evidence_bundle="artifact:bundle.json",
        expires_at="",
        expires_days=1,
        objective="structured objective",
        accept="structured acceptance criterion",
        red_line=["do not fake evidence"],
        non_goal=["do not sync raw chat"],
        evidence_ref=["artifact:source.json"],
        json=True,
    )

    result = module.command_add(args)
    created = Path(result["created"])
    text = created.read_text(encoding="utf-8")

    assert "mission_objective: structured objective" in text
    assert "acceptance_criteria:" in text
    assert "structured acceptance criterion" in text
    assert "red_lines:" in text
    assert "do not fake evidence" in text
    assert "non_goals:" in text
    assert "do not sync raw chat" in text
    assert "evidence_refs:" in text
    assert "artifact:source.json" in text


def test_task_row_exposes_structured_spec_to_worker_and_proof_gate(monkeypatch, tmp_path):
    orchestrator = load_orchestrator_module()
    controller = load_module()

    monkeypatch.setattr(orchestrator, "load_project_profile", lambda project: {"status": "ok"})
    monkeypatch.setattr(orchestrator, "task_brain_contract", lambda task: {})
    monkeypatch.setattr(orchestrator, "obsidian_link", lambda path: f"obsidian://test/{Path(path).name}")
    monkeypatch.setattr(orchestrator, "task_dependency_status", lambda task: {})
    monkeypatch.setattr(orchestrator, "project_profile_failures", lambda task: [])
    monkeypatch.setattr(orchestrator.Task, "architecture_aligned", lambda self: True)
    monkeypatch.setattr(orchestrator.Task, "is_dispatchable", lambda self: True)

    task = orchestrator.Task(
        tmp_path / "2026-05-25-row-ssot.md",
        {
            "status": "pending",
            "priority": "P2",
            "project": "hermes",
            "mission_objective": "row carries objective",
            "acceptance_criteria": ["row acceptance must reach proof gate"],
            "red_lines": ["row red line must reach proof gate"],
            "non_goals": ["do not use chat history"],
            "evidence_refs": ["artifact:source.json"],
            "acceptance_evidence": "artifact:proof.json",
            "workflow_contract": {"proof": "PROOF_JSON"},
        },
        "# Row SSOT task\nBody requirement must also be available.\n",
    )

    row = task.row()
    section = controller.build_task_spec_section(row)
    failed_gate = controller.validate_worker_proof_against_task(row, {"status": "done", "summary": "claimed without mapping"})

    assert row["acceptance_criteria"] == ["row acceptance must reach proof gate"]
    assert row["red_lines"] == ["row red line must reach proof gate"]
    assert "row carries objective" in section
    assert "row acceptance must reach proof gate" in section
    assert "row red line must reach proof gate" in section
    assert failed_gate["status"] == "FAIL"
    assert "acceptance_criteria_covered_missing" in failed_gate["violations"]


def test_environment_capability_pack_carries_skills_mcp_and_brain_refs(tmp_path):
    module = load_module()
    config = tmp_path / "config.yaml"
    config.write_text(
        "mcp_servers:\n"
        "  time:\n"
        "    command: uvx\n"
        "    env:\n"
        "      API_KEY: super-secret-value\n"
        "  filesystem:\n"
        "    command: npx\n"
        "    auth:\n"
        "      token: nested-token-value\n",
        encoding="utf-8",
    )

    pack = module.build_environment_capability_pack(
        {
            "required_skills": "taskpool-control-plane,native-mcp",
            "skills": '["taskpool-control-plane", "hermes-agent"]',
            "required_mcp_tools": {"mcp_time_get_current_time": True, "mcp_secret_disabled": False},
            "brain": "local-brain",
            "brain_contract": {"red_lines": ["真实证据闭环"]},
            "brain_context": "只注入检索快照，不同步全量 memory。",
        },
        profile={"required_skills": ["hermes-agent"], "required_mcp_tools": ["mcp_filesystem_read_text_file"]},
        config_path=config,
    )

    assert "ENVIRONMENT CAPABILITY PACK" in pack
    assert "taskpool-control-plane" in pack
    assert "native-mcp" in pack
    assert "hermes-agent" in pack
    assert pack.count("taskpool-control-plane") == 1
    assert "mcp_time_get_current_time" in pack
    assert "mcp_secret_disabled" not in pack
    assert "mcp_filesystem_read_text_file" in pack
    assert "time" in pack
    assert "filesystem" in pack
    assert "super-secret-value" not in pack
    assert "nested-token-value" not in pack
    assert "API_KEY" not in pack
    assert "auth" not in pack
    assert "local-brain" in pack
    assert "真实证据闭环" in pack
    assert "全量 memory" in pack


def test_environment_capability_pack_empty_without_explicit_context(tmp_path):
    module = load_module()
    config = tmp_path / "config.yaml"
    config.write_text("mcp_servers:\n  time:\n    command: uvx\n", encoding="utf-8")

    assert module.build_environment_capability_pack({}, profile={}, config_path=config) == ""
    assert module.collect_worker_required_skills({}, {}) == []


def test_environment_capability_pack_truncates_brain_context(tmp_path):
    module = load_module()
    config = tmp_path / "config.yaml"
    config.write_text("{}\n", encoding="utf-8")
    long_context = "脑" * 80

    pack = module.build_environment_capability_pack(
        {"brain_context": long_context},
        profile={},
        config_path=config,
        max_field_chars=20,
    )

    assert "LOCAL_BRAIN_CONTEXT_PACK" in pack
    assert "[truncated" in pack
    assert long_context not in pack


def test_delegate_worker_injects_digest_task_spec_and_environment_while_preserving_ignore_rules(monkeypatch, tmp_path):
    module = load_module()
    captured = {}

    monkeypatch.setattr(
        module,
        "load_project_profile",
        lambda project: {"required_skills": ["hermes-agent"], "required_mcp_tools": ["mcp_time_get_current_time"]},
    )
    monkeypatch.setattr(module, "can_continue", lambda task_id: (False, 0))
    monkeypatch.setattr(module, "build_execution_rules_digest", lambda: "CANONICAL EXECUTION RULES DIGEST\n- shared red line")

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="PROOF_JSON {\"ok\": true}", stderr="")

    monkeypatch.setattr(module._sp if hasattr(module, "_sp") else subprocess, "run", fake_run, raising=False)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        module,
        "collect_proof",
        lambda task_id, output: {
            "status": "done",
            "acceptance_criteria_covered": [
                {"criterion": "不需要重复在 chat 再说一次", "status": "covered", "evidence": ["command:pytest PASS"]}
            ],
            "red_lines_status": {"不得丢失任务级验收": "safe"},
            "no_red_line_violations": True,
            "evidence": ["command:pytest PASS"],
        },
    )

    result = module.delegate_to_worker(
        {
            "id": "task-1",
            "title": "实现 Hermes worker 规则收敛",
            "project": "hermes",
            "parallel_boundary": "scripts/agent_team_controller.py",
            "body": "用户要求：任务池继承 chat 中已表达的验收标准。",
            "acceptance_criteria": ["不需要重复在 chat 再说一次"],
            "red_lines": ["不得丢失任务级验收"],
            "required_skills": ["taskpool-control-plane"],
            "brain_context": "本地大脑提示：使用 brainctl 证据优先。",
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
    assert "ENVIRONMENT CAPABILITY PACK" in prompt
    assert "taskpool-control-plane" in prompt
    assert "hermes-agent" in prompt
    assert "mcp_time_get_current_time" in prompt
    assert "本地大脑提示" in prompt
    assert cmd.count("--skills") == 2
    assert "taskpool-control-plane" in cmd
    assert "hermes-agent" in cmd


def test_hermes_cli_loads_explicit_skills_outside_ignore_rules_gate():
    cli_path = SCRIPTS_DIR.parent / "hermes-agent" / "cli.py"
    source = cli_path.read_text(encoding="utf-8", errors="replace")

    ignore_setup = source.index("self.ignore_rules = ignore_rules")
    agent_skip_files = source.index("skip_context_files=self.ignore_rules")
    explicit_skill_gate = source.index("if parsed_skills:")
    preload_call = source.index("build_preloaded_skills_prompt", explicit_skill_gate)
    system_prompt_merge = source.index("cli.system_prompt", preload_call)

    assert ignore_setup < agent_skip_files
    assert explicit_skill_gate < preload_call < system_prompt_merge
    assert "skip_context_files=self.ignore_rules" in source
    assert "skip_memory=self.ignore_rules" in source


def test_configured_mcp_servers_fallback_excludes_nested_secret_keys(monkeypatch, tmp_path):
    module = load_module()
    config = tmp_path / "config.yaml"
    config.write_text(
        "mcp_servers:\n"
        "  alpha:\n"
        "    command: uvx\n"
        "    env:\n"
        "      TOKEN: should-not-render\n"
        "  beta:\n"
        "    auth:\n"
        "      api_key: also-secret\n"
        "other_section:\n"
        "  gamma:\n",
        encoding="utf-8",
    )
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("force fallback")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert module._configured_mcp_servers(config) == ["alpha", "beta"]
