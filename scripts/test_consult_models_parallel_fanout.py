#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import time
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "consult_models.py"


def load_module():
    spec = importlib.util.spec_from_file_location("consult_models_under_test", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_fanout_calls_planners_concurrently_with_bounded_workers(tmp_path, monkeypatch):
    m = load_module()
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"question": "parallel fanout smoke"}), encoding="utf-8")

    planners = ["model-a", "model-b", "model-c"]
    monkeypatch.setattr(m, "HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.setattr(m, "load_quorum", lambda: {"degradation": {}})
    monkeypatch.setattr(m, "load_config", lambda: {"multimodel": {"max_model_workers_per_task": 3}})
    monkeypatch.setattr(m, "get_tier_planners", lambda quorum, tier, skip: (planners, 3, 2))
    monkeypatch.setattr(m, "select_planners_for_fanout", lambda planners, q_count, config=None: (list(planners), [], {}))
    monkeypatch.setattr(m, "quota_observability_summary", lambda snapshot: {"status": "test"})
    monkeypatch.setattr(m, "cleanup_old_ticks", lambda: None)
    monkeypatch.setattr(m, "build_evidence_bundle", lambda state: {"claims": []})
    monkeypatch.setattr(m, "evaluate_truth_gate", lambda evidence: {"can_certify_truth": True, "truth_status": "grounded"})
    planner_done_order = []

    def fake_emit_phase_event(phase, chain_id, actor_id, verdict, summary, extensions):
        if phase == "planner_done":
            planner_done_order.append(extensions["model"])

    monkeypatch.setattr(m, "emit_phase_event", fake_emit_phase_event)
    monkeypatch.setattr(m, "build_planner_prompt", lambda state, state_hash, model, tier: f"prompt:{model}")

    def fake_call_planner_model(*, model, prompt, state_hash, tier, chain_id, config, timeout):
        time.sleep(0.30 if model == "model-a" else 0.05)
        return {"meta": {"planner_model": model}, "patches": []}, {"ok": True, "adapter": "test"}

    monkeypatch.setattr(m, "call_planner_model", fake_call_planner_model)

    class Completed:
        returncode = 0
        stdout = json.dumps({"merged": True})
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Completed())

    started = time.perf_counter()
    result = m.run_fanout(str(state_file), tier="T2", timeout=5)
    elapsed = time.perf_counter() - started

    assert elapsed < 0.55, f"planner calls appear serial; elapsed={elapsed:.3f}s"
    assert result["success_count"] == 3
    assert result["fail_count"] == 0
    assert result["models_used"] == planners
    assert planner_done_order == planners
    plan_files = sorted(Path(result["plans_dir"]).glob("*.json"))
    assert len(plan_files) == 3


def test_run_fanout_handles_non_dict_multimodel_config_and_writes_failed_plan(tmp_path, monkeypatch):
    m = load_module()
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"question": "failure artifact smoke"}), encoding="utf-8")

    planners = ["model-a", "model-b"]
    monkeypatch.setattr(m, "HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.setattr(m, "load_quorum", lambda: {"degradation": {}})
    monkeypatch.setattr(m, "load_config", lambda: {"multimodel": None})
    monkeypatch.setattr(m, "get_tier_planners", lambda quorum, tier, skip: (planners, 2, 1))
    monkeypatch.setattr(m, "select_planners_for_fanout", lambda planners, q_count, config=None: (list(planners), [], {}))
    monkeypatch.setattr(m, "quota_observability_summary", lambda snapshot: {"status": "test"})
    monkeypatch.setattr(m, "cleanup_old_ticks", lambda: None)
    monkeypatch.setattr(m, "build_evidence_bundle", lambda state: {"claims": []})
    monkeypatch.setattr(m, "evaluate_truth_gate", lambda evidence: {"can_certify_truth": True, "truth_status": "grounded"})
    monkeypatch.setattr(m, "emit_phase_event", lambda *args, **kwargs: None)

    def fake_prompt(state, state_hash, model, tier):
        if model == "model-b":
            raise RuntimeError("prompt failed")
        return f"prompt:{model}"

    monkeypatch.setattr(m, "build_planner_prompt", fake_prompt)
    monkeypatch.setattr(
        m,
        "call_planner_model",
        lambda **kwargs: ({"meta": {"planner_model": kwargs["model"]}, "patches": []}, {"ok": True, "adapter": "test"}),
    )

    class Completed:
        returncode = 0
        stdout = json.dumps({"merged": True})
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Completed())

    result = m.run_fanout(str(state_file), tier="T2", timeout=5)

    assert result["success_count"] == 1
    assert result["fail_count"] == 1
    failed_plan = Path(result["plans_dir"]) / "model-b.json"
    payload = json.loads(failed_plan.read_text(encoding="utf-8"))
    assert payload["error"] == "planner_exception"
    assert "prompt failed" in payload["detail"]


def test_run_fanout_single_worker_converts_worker_exception_to_failure_artifact(tmp_path, monkeypatch):
    m = load_module()
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"question": "single worker failure artifact"}), encoding="utf-8")

    planners = ["model-a"]
    monkeypatch.setattr(m, "HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.setattr(m, "load_quorum", lambda: {"degradation": {}})
    monkeypatch.setattr(m, "load_config", lambda: {"multimodel": {"max_model_workers_per_task": 1}})
    monkeypatch.setattr(m, "get_tier_planners", lambda quorum, tier, skip: (planners, 1, 1))
    monkeypatch.setattr(m, "select_planners_for_fanout", lambda planners, q_count, config=None: (list(planners), [], {}))
    monkeypatch.setattr(m, "quota_observability_summary", lambda snapshot: {"status": "test"})
    monkeypatch.setattr(m, "cleanup_old_ticks", lambda: None)
    monkeypatch.setattr(m, "build_evidence_bundle", lambda state: {"claims": []})
    monkeypatch.setattr(m, "evaluate_truth_gate", lambda evidence: {"can_certify_truth": True, "truth_status": "grounded"})
    monkeypatch.setattr(m, "emit_phase_event", lambda *args, **kwargs: None)

    def fail_shadow_plan(model, state_hash, tier, chain_id):
        raise RuntimeError("shadow exploded")

    monkeypatch.setattr(m, "generate_shadow_plan", fail_shadow_plan)

    result = m.run_fanout(str(state_file), tier="T2", timeout=5, shadow=True)

    assert result["error"] == "all_failed"
    failed_plan = Path(result["tick_dir"]) / "plans" / "model-a.json"
    payload = json.loads(failed_plan.read_text(encoding="utf-8"))
    assert payload["error"] == "planner_worker_exception"
    assert "shadow exploded" in payload["detail"]
    assert "diagnosis" in payload


def test_run_fanout_partial_failure_artifacts_are_valid_for_real_consensus(tmp_path, monkeypatch):
    m = load_module()
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"question": "real consensus partial failure"}), encoding="utf-8")

    planners = ["model-a", "model-b"]
    monkeypatch.setattr(m, "HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.setattr(m, "load_quorum", lambda: {"degradation": {}})
    monkeypatch.setattr(m, "load_config", lambda: {"multimodel": {"max_model_workers_per_task": 2}})
    monkeypatch.setattr(m, "get_tier_planners", lambda quorum, tier, skip: (planners, 2, 1))
    monkeypatch.setattr(m, "select_planners_for_fanout", lambda planners, q_count, config=None: (list(planners), [], {}))
    monkeypatch.setattr(m, "quota_observability_summary", lambda snapshot: {"status": "test"})
    monkeypatch.setattr(m, "cleanup_old_ticks", lambda: None)
    monkeypatch.setattr(m, "build_evidence_bundle", lambda state: {"claims": []})
    monkeypatch.setattr(m, "evaluate_truth_gate", lambda evidence: {"can_certify_truth": True, "truth_status": "grounded"})
    monkeypatch.setattr(m, "emit_phase_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(m, "build_planner_prompt", lambda state, state_hash, model, tier: f"prompt:{model}")

    def fake_call_planner_model(*, model, prompt, state_hash, tier, chain_id, config, timeout):
        if model == "model-b":
            raise RuntimeError("planner invoke failed")
        return {
            "meta": {"planner_model": model, "confidence": 0.8},
            "diagnosis": {"root_cause_class": "no_action", "summary": "success"},
            "patches": [{"id": "noop", "op": "noop", "rationale": "test"}],
        }, {"ok": True, "adapter": "test"}

    monkeypatch.setattr(m, "call_planner_model", fake_call_planner_model)

    result = m.run_fanout(str(state_file), tier="T2", timeout=5)

    assert "error" not in result
    assert result["success_count"] == 1
    assert result["fail_count"] == 1
    assert result["merged_plan"]["meta"]["planner_model"] == "ensemble:2"
    failed_payload = json.loads((Path(result["plans_dir"]) / "model-b.json").read_text(encoding="utf-8"))
    assert failed_payload["error"] == "planner_exception"
    assert failed_payload["diagnosis"]["root_cause_class"] == "planner_failure"


def test_run_fanout_uses_distinct_artifacts_for_colliding_safe_model_names(tmp_path, monkeypatch):
    m = load_module()
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"question": "safe name collision"}), encoding="utf-8")

    planners = ["model/a", "model_a", "model_a-2", "model a"]
    monkeypatch.setattr(m, "HERMES_HOME", str(tmp_path / "hermes-home"))
    monkeypatch.setattr(m, "load_quorum", lambda: {"degradation": {}})
    monkeypatch.setattr(m, "load_config", lambda: {"multimodel": {"max_model_workers_per_task": 3}})
    monkeypatch.setattr(m, "get_tier_planners", lambda quorum, tier, skip: (planners, 3, 2))
    monkeypatch.setattr(m, "select_planners_for_fanout", lambda planners, q_count, config=None: (list(planners), [], {}))
    monkeypatch.setattr(m, "quota_observability_summary", lambda snapshot: {"status": "test"})
    monkeypatch.setattr(m, "cleanup_old_ticks", lambda: None)
    monkeypatch.setattr(m, "build_evidence_bundle", lambda state: {"claims": []})
    monkeypatch.setattr(m, "evaluate_truth_gate", lambda evidence: {"can_certify_truth": True, "truth_status": "grounded"})
    monkeypatch.setattr(m, "emit_phase_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(m, "build_planner_prompt", lambda state, state_hash, model, tier: f"prompt:{model}")

    def fake_call_planner_model(*, model, prompt, state_hash, tier, chain_id, config, timeout):
        return {
            "meta": {"planner_model": model, "confidence": 0.8},
            "diagnosis": {"root_cause_class": "no_action", "summary": model},
            "patches": [{"id": "noop", "op": "noop", "rationale": "test"}],
        }, {"ok": True, "adapter": "test"}

    monkeypatch.setattr(m, "call_planner_model", fake_call_planner_model)

    result = m.run_fanout(str(state_file), tier="T2", timeout=5)

    plan_files = sorted(Path(result["plans_dir"]).glob("*.json"))
    assert len(plan_files) == len(planners)
    assert {path.name for path in plan_files} == {"model_a.json", "model_a-2.json", "model_a-2-2.json", "model_a-3.json"}
    payload_models = [json.loads(path.read_text(encoding="utf-8"))["meta"]["planner_model"] for path in plan_files]
    assert set(payload_models) == set(planners)
    assert result["success_count"] == len(planners)
