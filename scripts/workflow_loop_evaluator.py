#!/usr/bin/env python3
"""Independent fail-closed evaluator for local Workflow Kernel Loop receipts.

The generator may call this module, but evaluation rules live here and may veto
promotion. No external action or lifecycle mutation is performed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EVALUATOR = "workflow_loop_evaluator_v1"
RECEIPT_SCHEMA = "hermes_workflow_kernel_loop_receipt_v2"
RECEIPT_GENERATOR = "workflow_kernel_loop_v2"
RECEIPT_PENDING_STATUS = "pending_evaluation"
RECEIPT_FINAL_STATUSES = {"ok": ("PASS", False), "blocked_by_evaluator": ("FAIL", True)}
REQUIRED_STAGES = ("observe", "orient", "compile", "simulate", "execute", "verify", "ratchet", "monitor", "cleanup")
REQUIRED_CONTROL_MOVES = ("discovery", "handoff", "verification", "persistence", "scheduling")
REQUIRED_SYSTEM_PARTS = ("automations", "worktrees", "skills", "connectors", "subagents", "memory")
REQUIRED_SIDE_EFFECTS = ("external", "cron", "taskpool", "agentos")
REQUIRED_BUDGETS = ("max_iterations", "max_runtime_seconds", "max_retries", "max_evidence_files")
ALLOWED_PART_STATUS = {"enabled", "disabled", "not_applicable"}


def _regular_file_without_symlinks(path_value: str) -> bool:
    path = Path(path_value).expanduser().absolute()
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current = current / component
        if current.is_symlink():
            return False
    return path.is_file()


def _refs_valid(refs: Any) -> bool:
    if not isinstance(refs, list) or not refs:
        return False
    return all(
        isinstance(ref, str)
        and ref.strip()
        and _regular_file_without_symlinks(ref)
        for ref in refs
    )


def _procedure_projection(procedure_registry: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(procedure_registry, dict):
        return {
            "state": "not_provided",
            "registry_present": False,
            "inventory_complete": False,
            "can_claim_complete": False,
            "counts": {},
        }
    summary = procedure_registry.get("summary", {})
    if procedure_registry.get("schema") != "hermes_procedure_validation_registry_v1" or not isinstance(summary, dict):
        return {
            "state": "invalid_registry",
            "registry_present": True,
            "inventory_complete": False,
            "can_claim_complete": False,
            "counts": {},
        }
    can_claim_raw = summary.get("can_claim_complete_procedure_validation")
    inventory_complete_raw = summary.get("inventory_complete")
    if not isinstance(can_claim_raw, bool) or not isinstance(inventory_complete_raw, bool):
        return {
            "state": "invalid_registry",
            "registry_present": True,
            "inventory_complete": False,
            "can_claim_complete": False,
            "counts": {},
        }
    can_claim = can_claim_raw
    inventory_complete = inventory_complete_raw
    count_names = ("required_procedures", "fully_connected", "pending", "stale", "failed", "blocked_by_authority", "operationally_degraded")
    raw_counts = {name: summary.get(name, 0) for name in count_names}
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in raw_counts.values()):
        return {
            "state": "invalid_registry",
            "registry_present": True,
            "inventory_complete": False,
            "can_claim_complete": False,
            "counts": {},
        }
    counts = raw_counts
    complete_count_names = {"required_procedures", "fully_connected", "pending", "stale", "failed", "blocked_by_authority"}
    contradictory_complete = can_claim and (
        not complete_count_names.issubset(summary)
        or not inventory_complete
        or counts["required_procedures"] == 0
        or counts["fully_connected"] != counts["required_procedures"]
        or any(counts[name] > 0 for name in ("pending", "stale", "failed", "blocked_by_authority", "operationally_degraded"))
    )
    if contradictory_complete:
        return {
            "state": "invalid_registry",
            "registry_present": True,
            "inventory_complete": False,
            "can_claim_complete": False,
            "counts": counts,
        }
    return {
        "state": "complete_candidate" if can_claim else "attention_required",
        "registry_present": True,
        "inventory_complete": inventory_complete,
        "can_claim_complete": can_claim,
        "counts": counts,
        "certification_semantics": "necessary_not_sufficient",
    }


def evaluate_receipt(receipt: dict[str, Any], procedure_registry: dict[str, Any] | None = None) -> dict[str, Any]:
    issues: list[str] = []

    if receipt.get("schema") != RECEIPT_SCHEMA:
        issues.append("invalid_receipt_schema")
    if receipt.get("generator") != RECEIPT_GENERATOR:
        issues.append("invalid_receipt_generator")
    receipt_status = receipt.get("status")
    if receipt_status != RECEIPT_PENDING_STATUS and receipt_status not in RECEIPT_FINAL_STATUSES:
        issues.append("invalid_receipt_status")
    elif receipt_status in RECEIPT_FINAL_STATUSES:
        expected_status, expected_veto = RECEIPT_FINAL_STATUSES[receipt_status]
        embedded = receipt.get("evaluation")
        if not (
            isinstance(embedded, dict)
            and embedded.get("evaluator") == EVALUATOR
            and embedded.get("status") == expected_status
            and embedded.get("veto") is expected_veto
        ):
            issues.append("final_status_evaluation_mismatch")

    raw_stages = receipt.get("stages")
    if not isinstance(raw_stages, list):
        issues.append("invalid_stages")
        raw_stages = []
    stage_map = {str(stage.get("id")): stage for stage in raw_stages if isinstance(stage, dict)}
    for stage_id in REQUIRED_STAGES:
        stage = stage_map.get(stage_id)
        if stage is None:
            issues.append(f"missing_stage:{stage_id}")
            continue
        if stage.get("status") != "PASS":
            issues.append(f"stage_not_pass:{stage_id}")
        if not _refs_valid(stage.get("evidence_refs")):
            issues.append(f"missing_stage_evidence:{stage_id}")

    control_moves = receipt.get("control_moves", {})
    if not isinstance(control_moves, dict):
        issues.append("invalid_control_moves")
        control_moves = {}
    for move in REQUIRED_CONTROL_MOVES:
        control = control_moves.get(move)
        if not isinstance(control, dict):
            issues.append(f"missing_control_move:{move}")
            continue
        if control.get("status") != "covered":
            issues.append(f"control_move_not_covered:{move}")
        if not _refs_valid(control.get("evidence_refs")):
            issues.append(f"missing_control_evidence:{move}")

    system_parts = receipt.get("system_parts", {})
    if not isinstance(system_parts, dict):
        issues.append("invalid_system_parts")
        system_parts = {}
    for part in REQUIRED_SYSTEM_PARTS:
        declaration = system_parts.get(part)
        if not isinstance(declaration, dict):
            issues.append(f"missing_system_part:{part}")
            continue
        if declaration.get("status") not in ALLOWED_PART_STATUS:
            issues.append(f"invalid_system_part_status:{part}")
        if not str(declaration.get("reason", "")).strip():
            issues.append(f"missing_system_part_reason:{part}")
        if not _refs_valid(declaration.get("evidence_refs")):
            issues.append(f"missing_system_part_evidence:{part}")

    budgets = receipt.get("budgets", {})
    if not isinstance(budgets, dict):
        issues.append("invalid_budgets")
        budgets = {}
    for name in REQUIRED_BUDGETS:
        value = budgets.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            issues.append(f"invalid_budget:{name}")

    if not str(receipt.get("kill_switch", "")).strip():
        issues.append("missing_kill_switch")

    side_effects = receipt.get("side_effects", {})
    if not isinstance(side_effects, dict):
        issues.append("invalid_side_effects")
        side_effects = {}
    for name in REQUIRED_SIDE_EFFECTS:
        if name not in side_effects:
            issues.append(f"missing_side_effect_declaration:{name}")
        elif side_effects.get(name) is not False:
            issues.append(f"side_effect_enabled:{name}")

    procedure_validation = _procedure_projection(procedure_registry)
    claims = receipt.get("claims", {})
    if not isinstance(claims, dict):
        issues.append("invalid_claims")
        claims = {}
    global_certification_claimed = claims.get("global_certification") is True
    canonical_promotion_claimed = claims.get("canonical_ratchet_promotion") is True
    if (global_certification_claimed or canonical_promotion_claimed) and not procedure_validation["registry_present"]:
        issues.append("procedure_registry_missing_for_claim")
    elif global_certification_claimed and not procedure_validation["can_claim_complete"]:
        issues.append("procedure_global_certification_not_allowed")
    elif canonical_promotion_claimed and not procedure_validation["can_claim_complete"]:
        issues.append("procedure_canonical_promotion_not_allowed")

    if receipt_status in RECEIPT_FINAL_STATUSES:
        _, expected_veto = RECEIPT_FINAL_STATUSES[receipt_status]
        if bool(issues) is not expected_veto:
            issues.append("final_evaluation_replay_mismatch")

    total_requirements = len(REQUIRED_STAGES) + len(REQUIRED_CONTROL_MOVES) + len(REQUIRED_SYSTEM_PARTS) + len(REQUIRED_BUDGETS) + 1 + len(REQUIRED_SIDE_EFFECTS)
    passed_requirements = max(0, total_requirements - len(set(issues)))
    score = round(100.0 * passed_requirements / total_requirements, 1)
    veto = bool(issues)
    return {
        "schema": "hermes_workflow_loop_evaluation_v1",
        "evaluator": EVALUATOR,
        "generator": "workflow_kernel_loop_v2",
        "independent_module": True,
        "status": "FAIL" if veto else "PASS",
        "veto": veto,
        "score_percent": 0.0 if veto else 100.0,
        "diagnostic_score_percent": score,
        "issues": sorted(set(issues)),
        "procedure_validation": procedure_validation,
        "claims_evaluated": {
            "global_certification": global_certification_claimed,
            "canonical_ratchet_promotion": canonical_promotion_claimed,
        },
        "would_execute_anything": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a local Workflow Kernel Loop receipt")
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--procedure-registry")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    procedure_registry = None
    if args.procedure_registry:
        procedure_registry = json.loads(Path(args.procedure_registry).read_text(encoding="utf-8"))
    result = evaluate_receipt(receipt, procedure_registry=procedure_registry)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
