#!/usr/bin/env python3
"""Evidence-complete, local-only Workflow Kernel Loop implementation."""

from __future__ import annotations

import importlib.util
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIDE_EFFECTS = {"external": False, "cron": False, "taskpool": False, "agentos": False}
KILL_SWITCH = "HERMES_WORKFLOW_LOOP_DISABLE"
BUDGETS = {"max_iterations": 3, "max_runtime_seconds": 120, "max_retries": 2, "max_evidence_files": 64}
STAGES = ("observe", "orient", "compile", "simulate", "execute", "verify", "ratchet", "monitor", "cleanup")
CONTROL_MOVES = ("discovery", "handoff", "verification", "persistence", "scheduling")
SYSTEM_PARTS = ("automations", "worktrees", "skills", "connectors", "subagents", "memory")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_script(name: str):
    path = Path.home() / ".hermes" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _paths(root: Path) -> dict[str, Path]:
    return {
        "runs": root / "runs",
        "assets": root / "assets",
        "registry": root / "module-pool" / "module_registry.json",
        "ledger": root / "module-pool" / "usage_ledger.jsonl",
    }


def _stage(stage_id: str, path: Path, passed: bool = True) -> dict[str, Any]:
    return {"id": stage_id, "status": "PASS" if passed else "FAIL", "evidence_refs": [str(path)]}


def _coverage(count: int, total: int) -> dict[str, Any]:
    return {"covered": count, "total": total, "percent": round(100.0 * count / total, 1)}


def _run_dir(root: Path, seed: str) -> Path:
    decision = _load_script("workflow_asset_decision")
    unique = f"{seed}|{utc_now()}|{uuid.uuid4().hex}"
    return root / "runs" / decision.stable_id(unique, "wfl")


def _system_parts(parts_path: Path, decision_path: Path, plan_path: Path, scheduling_path: Path) -> dict[str, Any]:
    return {
        "automations": {"status": "disabled", "reason": "run-once only; no scheduler authority", "evidence_refs": [str(parts_path), str(scheduling_path)]},
        "worktrees": {"status": "not_applicable", "reason": "asset scaffold does not edit a source repository", "evidence_refs": [str(parts_path)]},
        "skills": {"status": "enabled", "reason": "local decision and module capabilities are loaded", "evidence_refs": [str(decision_path), str(plan_path)]},
        "connectors": {"status": "disabled", "reason": "external connectors are outside local authority", "evidence_refs": [str(parts_path)]},
        "subagents": {"status": "not_applicable", "reason": "deterministic local evaluation needs no delegation", "evidence_refs": [str(parts_path)]},
        "memory": {"status": "disabled", "reason": "workflow bodies and progress never write always-on memory", "evidence_refs": [str(parts_path)]},
    }


def run_loop_once(seed: str, root: Path, observed_repetition: int = 0, task_scope: str = "unknown") -> dict[str, Any]:
    paths = _paths(root)
    run_dir = _run_dir(root, seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = run_dir / "loop-receipt.json"
    if os.environ.get(KILL_SWITCH, "").lower() in {"1", "true", "yes", "on"}:
        blocked = {"schema": "hermes_workflow_kernel_loop_receipt_v2", "status": "blocked_by_kill_switch", "run_dir": str(run_dir), "kill_switch": KILL_SWITCH, "side_effects": dict(SIDE_EFFECTS)}
        _write(receipt_path, blocked)
        return blocked

    asset_decision = _load_script("workflow_asset_decision")
    module_pool = _load_script("workflow_module_pool")
    evaluator = _load_script("workflow_loop_evaluator")

    observation_path = run_dir / "observation.json"
    _write(observation_path, {"schema": "hermes_workflow_loop_observation_v1", "seed": seed, "observed_repetition": observed_repetition, "task_scope": task_scope, "observed_at": utc_now()})

    context: dict[str, Any] = {"observed_repetition": observed_repetition}
    if task_scope == "one_off":
        context["task_scope"] = "one_off"
    decision = asset_decision.decide_assetization(seed, context)
    plan = module_pool.plan_workflow_from_seed(seed, module_pool.load_registry(paths["registry"]))
    decision_path = run_dir / "decision.json"
    plan_path = run_dir / "module-plan.json"
    _write(decision_path, decision)
    _write(plan_path, plan)

    compile_path = run_dir / "compile.json"
    asset: dict[str, Any] | None = None
    asset_workdir: str | None = None
    if decision["decision"] in {"project_scoped_candidate", "reusable_candidate"}:
        asset = asset_decision.compile_workflow_asset(decision)
        assert asset is not None
        asset["source"]["module_plan_ref"] = str(plan_path)
        asset["source"]["module_ids"] = plan.get("selected_modules", [])
        asset["source"]["missing_capability_needs"] = plan.get("missing_capability_needs", [])
        compile_issues = asset_decision.validate_workflow_asset(asset)
        _write(compile_path, {"status": "PASS" if not compile_issues else "FAIL", "asset_id": asset["id"], "validation_issues": compile_issues})
        asset_receipt = asset_decision.scaffold_workspace(asset, paths["assets"])
        asset_workdir = asset_receipt["workdir"]
        _write(run_dir / "asset-receipt.json", asset_receipt)
    else:
        _write(compile_path, {"status": "PASS", "asset_id": None, "reason": "durable_asset_not_justified"})

    negative = asset_decision.decide_assetization("创建工作流：今天把这三个文件整理一下", {"task_scope": "one_off"})
    simulation_pass = negative["decision"] == "session_plan" and not any(plan.get("side_effects", {}).values())
    if asset is not None:
        simulation_pass = simulation_pass and not asset_decision.validate_workflow_asset(asset)
    simulation_path = run_dir / "simulation.json"
    _write(simulation_path, {"schema": "hermes_workflow_loop_simulation_v1", "status": "PASS" if simulation_pass else "FAIL", "positive_decision": decision["decision"], "negative_keyword_only_decision": negative["decision"], "side_effects_disabled": not any(plan.get("side_effects", {}).values())})

    execution_path = run_dir / "execution.json"
    _write(execution_path, {"schema": "hermes_workflow_loop_execution_v1", "status": "PASS", "action": "local_asset_scaffold" if asset_workdir else "no_durable_write", "asset_workdir": asset_workdir, "side_effects": dict(SIDE_EFFECTS)})

    required = [observation_path, decision_path, plan_path, compile_path, simulation_path, execution_path]
    if asset_workdir:
        required.extend(Path(asset_workdir) / name for name in ("workflow.json", "state.json", "eval-cases.json", "evidence.jsonl"))
    missing = [str(path) for path in required if not path.exists()]
    validation_issues = asset_decision.validate_workflow_asset(asset) if asset is not None else []
    verified = simulation_pass and not missing and not validation_issues and not any(SIDE_EFFECTS.values())
    verification_path = run_dir / "verification.json"
    _write(verification_path, {"schema": "hermes_workflow_loop_verification_v1", "status": "PASS" if verified else "FAIL", "readback_count": len(required) - len(missing), "missing_files": missing, "validation_issues": validation_issues, "side_effects_disabled": True})

    ratchet_path = run_dir / "ratchet.json"
    ratchet_action = "no_promotion"
    if verified and asset_workdir:
        workflow_path = Path(asset_workdir) / "workflow.json"
        state_path = Path(asset_workdir) / "state.json"
        persisted_asset = json.loads(workflow_path.read_text(encoding="utf-8"))
        persisted_state = json.loads(state_path.read_text(encoding="utf-8"))
        persisted_asset["classification"]["maturity"] = "candidate"
        persisted_state.update({"maturity": "candidate", "status": "candidate_after_local_verification"})
        _write(workflow_path, persisted_asset)
        _write(state_path, persisted_state)
        ratchet_action = "promote:draft->candidate"
    _write(ratchet_path, {"schema": "hermes_workflow_loop_ratchet_v1", "status": "PASS" if verified else "BLOCKED", "action": ratchet_action, "canonical_promotion": False, "external_mutation": False})

    module_ids = plan.get("selected_modules") or plan.get("capability_needs") or ["intent_seed_capture"]
    event = module_pool.usage_event(workflow_id=decision["id"], module_ids=module_ids, outcome="success" if verified else "failure", evidence_passed=verified, human_intervention=False, false_trigger=False)
    module_pool.append_jsonl(paths["ledger"], event)

    metrics_path = run_dir / "metrics.json"
    _write(metrics_path, {"schema": "hermes_workflow_loop_metrics_v1", "stage_total": len(STAGES), "stage_passed_before_evaluation": len(STAGES) if verified else 5, "false_trigger": False, "human_intervention": False, "evidence_passed": verified})
    cleanup_path = run_dir / "cleanup.json"
    _write(cleanup_path, {"schema": "hermes_workflow_loop_cleanup_v1", "status": "PASS", "mode": "advisory_only", "candidates": [], "deleted": []})
    scheduling_path = run_dir / "scheduling-boundary.json"
    _write(scheduling_path, {"schema": "hermes_workflow_loop_scheduling_boundary_v1", "status": "disabled", "reason": "local run-once has no cron or worker authority", "cron_enabled": False, "worker_enabled": False})
    parts_path = run_dir / "system-parts-boundary.json"
    _write(parts_path, {"schema": "hermes_workflow_loop_system_parts_v1", "parts": list(SYSTEM_PARTS), "local_only": True, "external_connectors_enabled": False, "memory_write_enabled": False})

    stage_paths = {"observe": observation_path, "orient": plan_path, "compile": compile_path, "simulate": simulation_path, "execute": execution_path, "verify": verification_path, "ratchet": ratchet_path, "monitor": metrics_path, "cleanup": cleanup_path}
    stages = [_stage(stage_id, stage_paths[stage_id], verified or stage_id in {"observe", "orient", "compile", "execute", "monitor", "cleanup"}) for stage_id in STAGES]
    controls = {
        "discovery": {"status": "covered", "evidence_refs": [str(observation_path), str(plan_path)]},
        "handoff": {"status": "covered", "evidence_refs": [str(compile_path), str(execution_path)]},
        "verification": {"status": "covered", "evidence_refs": [str(simulation_path), str(verification_path)]},
        "persistence": {"status": "covered", "evidence_refs": [str(paths["ledger"])]},
        "scheduling": {"status": "covered", "evidence_refs": [str(scheduling_path)]},
    }
    parts = _system_parts(parts_path, decision_path, plan_path, scheduling_path)
    coverage = {"kernel_stages": _coverage(len(stages), len(STAGES)), "control_moves": _coverage(len(controls), len(CONTROL_MOVES)), "system_parts": _coverage(len(parts), len(SYSTEM_PARTS)), "overall_percent": 100.0, "semantics": "contract coverage; operational health is separate"}
    receipt = {
        "schema": "hermes_workflow_kernel_loop_receipt_v2", "generator": "workflow_kernel_loop_v2", "status": "pending_evaluation",
        "seed": seed, "decision": decision["decision"], "run_dir": str(run_dir), "asset_workdir": asset_workdir,
        "module_plan_ref": str(plan_path), "usage_ledger": str(paths["ledger"]), "stages": stages,
        "control_moves": controls, "system_parts": parts, "engineering_coverage": coverage, "budgets": dict(BUDGETS),
        "kill_switch": KILL_SWITCH, "side_effects": dict(SIDE_EFFECTS), "created_at": utc_now(),
        "claims": {"global_certification": False, "canonical_ratchet_promotion": False},
    }
    procedure_registry_path = Path.home() / ".hermes" / "state" / "selfcheck" / "procedure_validation_registry.json"
    procedure_registry = None
    if procedure_registry_path.exists():
        try:
            procedure_registry = json.loads(procedure_registry_path.read_text(encoding="utf-8"))
            receipt["procedure_validation_ref"] = str(procedure_registry_path)
        except (OSError, json.JSONDecodeError):
            receipt["procedure_validation_ref"] = str(procedure_registry_path)
            receipt["procedure_validation_read_error"] = True
    _write(receipt_path, receipt)
    evaluation = evaluator.evaluate_receipt(receipt, procedure_registry=procedure_registry)
    _write(run_dir / "evaluation.json", evaluation)
    receipt["evaluation"] = evaluation
    receipt["status"] = "ok" if evaluation["status"] == "PASS" else "blocked_by_evaluator"
    _write(receipt_path, receipt)
    return receipt
