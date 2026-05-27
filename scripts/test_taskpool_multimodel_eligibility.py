#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ORCH = Path("/Users/charles/.hermes/scripts/brain_task_orchestrator.py")


def load_orch():
    spec = importlib.util.spec_from_file_location("brain_task_orchestrator", ORCH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_task(orch, fm: dict, title: str = "示例任务"):
    return orch.Task(Path(f"/tmp/{title}.md"), fm, f"# {title}\n\nbody")


def test_work_product_task_ignores_weak_multimodel_sidecar_fields():
    orch = load_orch()
    task = make_task(
        orch,
        {
            "status": "pending",
            "priority": "P1",
            "lane": "work",
            "project": "uvisa-app-2.0",
            "architecture_target": "frontend",
            "concepts": ["uvisa", "frontend"],
            "multimodel_reason": "sidecar asserted",
            "expected_participants": "gpt-5.5,deepseek-v4-pro",
            "truth_gate": "report-evidence-present",
            "evidence_bundle": "/tmp/report.md",
        },
        "修复 UVISA 页面问题",
    )
    assert orch.task_multimodel_eligible(task) is False
    reasons = orch.task_multimodel_intervention_reasons(task)
    assert "explicit_multimodel_reason" not in reasons
    assert "expected_participants_contract" not in reasons
    assert "truth_gate_contract" not in reasons
    assert reasons == []


def test_retrying_work_product_task_does_not_trigger_automatic_panel():
    orch = load_orch()
    task = make_task(
        orch,
        {
            "status": "retry",
            "priority": "P1",
            "lane": "work",
            "project": "uvisa-admin",
            "architecture_target": "L3",
            "retry_count": 2,
            "truth_gate": "deterministic_tests_build_online_ui_evidence_pr_merged_lark_closed_tg_sent",
            "evidence_bundle": "/tmp/uvisa-admin-lark-work",
        },
        "Task - [Lark] 普通 work 自动闭环重试任务",
    )
    assert orch.task_multimodel_eligible(task) is False
    assert orch.task_multimodel_intervention_reasons(task) == []


def test_evolution_control_plane_task_accepts_weak_contract_and_keywords():
    orch = load_orch()
    task = make_task(
        orch,
        {
            "status": "pending",
            "priority": "P1",
            "lane": "evolution",
            "project": "hermes-agent",
            "architecture_target": "taskpool",
            "priority_layer": "daily-report:p1:external-signal-ingest",
            "concepts": ["taskpool", "self-strengthening"],
            "multimodel_reason": "external repo gap analysis",
            "expected_participants": "claude-code,gpt-5.5",
            "truth_gate": "report-evidence-present",
            "evidence_bundle": "/tmp/report.md",
        },
        "完善 taskpool 自动触发流程",
    )
    assert orch.task_multimodel_eligible(task) is True
    reasons = orch.task_multimodel_intervention_reasons(task)
    assert "explicit_multimodel_reason" in reasons
    assert "expected_participants_contract" in reasons
    assert "truth_gate_contract" in reasons
    assert "evidence_bundle_contract" in reasons


def test_explicit_requires_multimodel_remains_strong_trigger_for_work_task():
    orch = load_orch()
    task = make_task(
        orch,
        {
            "status": "pending",
            "priority": "P1",
            "lane": "work",
            "project": "uvisa-app-2.0",
            "architecture_target": "frontend",
            "requires_multimodel": True,
        },
        "需要人工指定多模型的产品任务",
    )
    reasons = orch.task_multimodel_intervention_reasons(task)
    assert "explicit_requires_multimodel" in reasons


def test_reading_advisory_negative_contract_consumes_weak_multimodel_signals():
    orch = load_orch()
    task = make_task(
        orch,
        {
            "status": "review",
            "priority": "P2",
            "lane": "advisory",
            "project": "reading-programming-books",
            "architecture_target": "skill-graph",
            "mission_schema_version": "mission_task_v1",
            "mission_id": "reading-http",
            "mission_objective": "bounded reading tranche",
            "mission_constraints": ["source-grounded notes only"],
            "red_lines": ["do not close without artifact"],
            "non_goals": ["not implementation"],
            "evidence_refs": ["url:https://example.test/book.pdf"],
            "acceptance_criteria": ["artifact:notes"],
            "dag_nodes": ["read", "note"],
            "checkpoint_states": ["artifact_ready"],
            "permission_gates": ["proof_check"],
            "handoff_artifacts": ["artifact:notes"],
            "proof_artifacts": ["artifact:notes"],
            "requires_multimodel": False,
            "retry_count": 3,
            "multimodel_triage_result": "fixed intake triage: Some-Many-Books is a reading backlog, no per-book multimodel execution required; priority derived from user career relevance",
        },
        "Task - 精读书籍：《HTTP权威指南》",
    )
    assert orch.task_has_explicit_negative_multimodel_contract(task) is True
    assert orch.task_multimodel_intervention_reasons(task) == []


def main() -> int:
    test_work_product_task_ignores_weak_multimodel_sidecar_fields()
    test_retrying_work_product_task_does_not_trigger_automatic_panel()
    test_evolution_control_plane_task_accepts_weak_contract_and_keywords()
    test_explicit_requires_multimodel_remains_strong_trigger_for_work_task()
    test_reading_advisory_negative_contract_consumes_weak_multimodel_signals()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
