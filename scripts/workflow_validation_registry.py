#!/usr/bin/env python3
"""Evaluate procedure-level E2E declarations and receipts without executing them.

This module is intentionally local/read-only except for writing the requested
registry artifact. It never invokes a declared procedure and never grants
external authority.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REGISTRY_SCHEMA = "hermes_procedure_validation_registry_v1"
DEFINITIONS_SCHEMA = "hermes_procedure_definitions_v1"
RECEIPT_SCHEMA = "hermes_procedure_e2e_receipt_v1"
IMPLEMENTATION_STATES = {"missing", "scaffolded", "landed", "enabled"}
AUTHORITY_POLICIES = {"none", "exact_grant_required"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def validate_declaration(declaration: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not str(declaration.get("procedure_id") or "").strip():
        issues.append("missing_procedure_id")
    if not str(declaration.get("system_id") or "").strip():
        issues.append("missing_system_id")
    if declaration.get("implementation_state") not in IMPLEMENTATION_STATES:
        issues.append("invalid_implementation_state")
    if declaration.get("authority_policy") not in AUTHORITY_POLICIES:
        issues.append("invalid_authority_policy")
    if not str(declaration.get("side_effect_class") or "").strip():
        issues.append("missing_side_effect_class")
    freshness = declaration.get("freshness_seconds")
    if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness <= 0:
        issues.append("invalid_freshness_seconds")
    threshold = declaration.get("min_independent_successes", 1)
    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold <= 0:
        issues.append("invalid_min_independent_successes")
    if not _string_list(declaration.get("required_acceptance_atoms")):
        issues.append("missing_required_acceptance_atoms")
    if not isinstance(declaration.get("required_negative_assertions"), list):
        issues.append("invalid_required_negative_assertions")
    return sorted(set(issues))


def validate_receipt(receipt: dict[str, Any], declaration: dict[str, Any], now_dt: datetime | None = None) -> list[str]:
    issues: list[str] = []
    if receipt.get("schema") != RECEIPT_SCHEMA:
        issues.append("invalid_receipt_schema")
    if receipt.get("procedure_id") != declaration.get("procedure_id"):
        issues.append("procedure_id_mismatch")
    if not str(receipt.get("receipt_id") or "").strip():
        issues.append("missing_receipt_id")
    started = parse_time(receipt.get("started_at"))
    completed = parse_time(receipt.get("completed_at"))
    if started is None:
        issues.append("invalid_started_at")
    if completed is None:
        issues.append("invalid_completed_at")
    if started is not None and completed is not None and completed < started:
        issues.append("completed_before_started")
    if completed is not None and now_dt is not None and (completed - now_dt).total_seconds() > 300:
        issues.append("completed_at_in_future")
    if receipt.get("result") != "PASS":
        issues.append("result_not_pass")
    if receipt.get("execution_mode") != "live_e2e":
        issues.append("execution_mode_not_live_e2e")

    refs = _string_list(receipt.get("evidence_refs"))
    if not refs:
        issues.append("missing_evidence_ref")
    elif any(not Path(ref).exists() for ref in refs):
        issues.append("missing_evidence_ref")

    acceptance = receipt.get("acceptance_atoms") if isinstance(receipt.get("acceptance_atoms"), dict) else {}
    for atom in _string_list(declaration.get("required_acceptance_atoms")):
        if acceptance.get(atom) is not True:
            issues.append(f"acceptance_atom_not_passed:{atom}")

    negatives = receipt.get("negative_assertions") if isinstance(receipt.get("negative_assertions"), dict) else {}
    for assertion in _string_list(declaration.get("required_negative_assertions")):
        if negatives.get(assertion) is not True:
            issues.append(f"negative_assertion_not_passed:{assertion}")

    if receipt.get("cleanup_readback") != "PASS":
        issues.append("cleanup_readback_not_pass")

    authority = receipt.get("authority") if isinstance(receipt.get("authority"), dict) else {}
    if declaration.get("authority_policy") == "exact_grant_required":
        if authority.get("status") != "granted" or not str(authority.get("ref") or "").strip():
            issues.append("authority_not_granted")

    declared_effect = str(declaration.get("side_effect_class") or "")
    observed_effects = _string_list(receipt.get("side_effects_observed"))
    allowed_effects = set(_string_list(declaration.get("allowed_additional_side_effects")))
    if declared_effect not in {"", "none"}:
        allowed_effects.add(declared_effect)
    for effect in observed_effects:
        if effect not in allowed_effects:
            issues.append(f"undeclared_side_effect:{effect}")

    return sorted(set(issues))


def _receipt_sort_key(receipt: dict[str, Any]) -> datetime:
    return parse_time(receipt.get("completed_at")) or datetime.min.replace(tzinfo=timezone.utc)


def _evaluate_procedure(
    declaration: dict[str, Any],
    receipts: list[dict[str, Any]],
    now_dt: datetime,
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    procedure_id = str(declaration.get("procedure_id") or "")
    implementation_state = str(declaration.get("implementation_state") or "missing")
    required = bool(declaration.get("required", True))
    declaration_issues = validate_declaration(declaration)
    matching = sorted((r for r in receipts if r.get("procedure_id") == procedure_id), key=_receipt_sort_key)
    evaluated = [{"receipt": item, "issues": validate_receipt(item, declaration, now_dt)} for item in matching]
    valid_passes = [item for item in evaluated if not item["issues"]]
    distinct_success_ids = {str(item["receipt"].get("receipt_id")) for item in valid_passes}
    successful_receipt_count = len(distinct_success_ids)
    latest = evaluated[-1] if evaluated else None
    latest_receipt = latest["receipt"] if latest else None
    latest_issues = list(latest["issues"]) if latest else []
    latest_completed = parse_time(latest_receipt.get("completed_at")) if latest_receipt else None
    freshness_seconds = int(declaration.get("freshness_seconds") or 0)
    age_seconds = max(0.0, (now_dt - latest_completed).total_seconds()) if latest_completed else None
    latest_is_fresh = bool(latest_completed and freshness_seconds > 0 and age_seconds <= freshness_seconds)
    threshold = int(declaration.get("min_independent_successes") or 1)

    findings: list[str] = []
    validation_state = "untested"
    delivery_state = "pending"
    operational_state = "unknown"

    if declaration_issues:
        validation_state = "e2e_failed"
        delivery_state = "pending"
        operational_state = "unknown"
        findings.append("procedure_declaration_invalid")
    elif implementation_state in {"missing", "scaffolded"}:
        validation_state = "untested"
        delivery_state = "pending"
        operational_state = "not_running"
        findings.append("procedure_implementation_pending")
    elif latest is None:
        if declaration.get("authority_policy") == "exact_grant_required":
            validation_state = "blocked_by_authority"
            delivery_state = "blocked"
            findings.append("procedure_authority_blocked")
        else:
            validation_state = "untested"
            delivery_state = "landed_unverified"
            findings.append("procedure_validation_pending")
    elif latest_issues:
        validation_state = "e2e_failed"
        delivery_state = "partially_landed"
        operational_state = "degraded"
        findings.append("procedure_e2e_failed")
    elif not latest_is_fresh:
        validation_state = "stale"
        delivery_state = "landed_unverified"
        operational_state = "unknown"
        findings.append("procedure_validation_stale")
    else:
        validation_state = "e2e_passed"
        operational_state = "healthy"
        if successful_receipt_count >= threshold and implementation_state == "enabled":
            delivery_state = "fully_connected"
        else:
            delivery_state = "partially_landed"
            if successful_receipt_count < threshold:
                findings.append("ratchet_threshold_not_met")
            if implementation_state != "enabled":
                findings.append("procedure_not_enabled")

    previous_state = str((previous or {}).get("delivery_state") or "")
    if previous_state and previous_state != delivery_state:
        direction = "promoted" if delivery_state == "fully_connected" else "demoted" if previous_state == "fully_connected" else "transitioned"
        transition = f"{direction}:{previous_state}->{delivery_state}"
    else:
        transition = "stable" if previous_state else "initial"

    return {
        **declaration,
        "declaration_issues": declaration_issues,
        "validation_state": validation_state,
        "delivery_state": delivery_state,
        "operational_state": operational_state,
        "findings": sorted(set(findings)),
        "receipt_count": len(matching),
        "successful_receipt_count": successful_receipt_count,
        "required_successful_receipt_count": threshold,
        "latest_receipt_id": latest_receipt.get("receipt_id") if latest_receipt else None,
        "latest_receipt_completed_at": latest_receipt.get("completed_at") if latest_receipt else None,
        "latest_receipt_fresh": latest_is_fresh,
        "latest_receipt_age_seconds": round(age_seconds, 1) if age_seconds is not None else None,
        "receipt_issues": latest_issues,
        "evidence_refs": _string_list(latest_receipt.get("evidence_refs")) if latest_receipt else [],
        "ratchet_transition": transition,
        "promotion_allowed": delivery_state == "fully_connected" and not declaration_issues,
        "required": required,
    }


def evaluate_registry(
    declarations: Iterable[dict[str, Any]],
    receipts: Iterable[dict[str, Any]],
    enabled_system_ids: Iterable[str],
    system_exemptions: dict[str, str] | None,
    system_inventory_attestations: dict[str, dict[str, Any]] | None = None,
    now: str | None = None,
    previous_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now_raw = now or utc_now()
    now_dt = parse_time(now_raw)
    if now_dt is None:
        raise ValueError("now must be an ISO8601 timestamp")

    declaration_list = [item for item in declarations if isinstance(item, dict)]
    receipt_list = [item for item in receipts if isinstance(item, dict)]
    exemptions = {str(key): str(value).strip() for key, value in (system_exemptions or {}).items() if str(value).strip()}
    previous_by_id = {
        str(item.get("procedure_id")): item
        for item in (previous_registry or {}).get("procedures", [])
        if isinstance(item, dict) and item.get("procedure_id")
    }
    procedure_ids = {str(item.get("procedure_id")) for item in declaration_list if item.get("procedure_id")}
    mapped_system_ids = {str(item.get("system_id")) for item in declaration_list if item.get("system_id")}
    enabled = sorted({str(item) for item in enabled_system_ids if str(item)})
    unmapped = sorted(system_id for system_id in enabled if system_id not in mapped_system_ids and system_id not in exemptions)
    attestations = system_inventory_attestations or {}
    unattested: list[str] = []
    attestation_states: dict[str, dict[str, Any]] = {}
    for system_id in enabled:
        if system_id in exemptions or system_id not in mapped_system_ids:
            continue
        attestation = attestations.get(system_id) if isinstance(attestations.get(system_id), dict) else {}
        reviewed_at = parse_time(attestation.get("reviewed_at"))
        freshness = attestation.get("freshness_seconds")
        age_seconds = max(0.0, (now_dt - reviewed_at).total_seconds()) if reviewed_at else None
        valid = bool(
            attestation.get("scope_complete") is True
            and str(attestation.get("basis") or "").strip()
            and isinstance(freshness, int)
            and not isinstance(freshness, bool)
            and freshness > 0
            and age_seconds is not None
            and age_seconds <= freshness
        )
        attestation_states[system_id] = {
            **attestation,
            "valid": valid,
            "age_seconds": round(age_seconds, 1) if age_seconds is not None else None,
        }
        if not valid:
            unattested.append(system_id)
    unknown_receipts = sorted({str(item.get("procedure_id") or "__missing__") for item in receipt_list if item.get("procedure_id") not in procedure_ids})

    procedures = [
        _evaluate_procedure(item, receipt_list, now_dt, previous_by_id.get(str(item.get("procedure_id"))))
        for item in sorted(declaration_list, key=lambda value: str(value.get("procedure_id") or ""))
    ]
    required = [item for item in procedures if item.get("required")]
    fully_connected = [item for item in required if item.get("delivery_state") == "fully_connected"]
    inventory_complete = not unmapped and not unattested and not unknown_receipts
    all_required_connected = len(fully_connected) == len(required)
    can_claim = inventory_complete and all_required_connected

    return {
        "schema": REGISTRY_SCHEMA,
        "generated_at": now_raw,
        "side_effects": "local_read_evaluation_only",
        "ordinary_selfcheck_executes_procedures": False,
        "inventory": {
            "enabled_system_ids": enabled,
            "mapped_system_ids": sorted(mapped_system_ids),
            "system_exemptions": exemptions,
            "unmapped_system_ids": unmapped,
            "unattested_system_ids": sorted(unattested),
            "system_inventory_attestations": attestation_states,
            "unknown_receipt_procedure_ids": unknown_receipts,
        },
        "procedures": procedures,
        "summary": {
            "procedures": len(procedures),
            "required_procedures": len(required),
            "fully_connected": len(fully_connected),
            "pending": sum(1 for item in required if item.get("delivery_state") in {"pending", "landed_unverified", "partially_landed"}),
            "blocked_by_authority": sum(1 for item in required if item.get("validation_state") == "blocked_by_authority"),
            "stale": sum(1 for item in required if item.get("validation_state") == "stale"),
            "failed": sum(1 for item in required if item.get("validation_state") == "e2e_failed"),
            "inventory_complete": inventory_complete,
            "inventory_gap_systems": len(set(unmapped) | set(unattested)),
            "unattested_systems": len(unattested),
            "unknown_receipts": len(unknown_receipts),
            "can_claim_complete_procedure_validation": can_claim,
            "global_certification_status": "candidate_not_certified" if can_claim else "not_certified",
            "score_semantics": "procedure E2E validation is separate from engineering coverage and current operational health",
        },
    }


def load_receipts(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    values: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = read_json(path, {})
        if isinstance(payload, dict):
            values.append(payload)
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate procedure-level E2E receipts without executing procedures.")
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--definitions", type=Path, required=True)
    evaluate.add_argument("--receipts-dir", type=Path, required=True)
    evaluate.add_argument("--enabled-system", action="append", default=[])
    evaluate.add_argument("--now", default=None)
    evaluate.add_argument("--previous", type=Path, default=None)
    evaluate.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    definitions = read_json(args.definitions, {})
    if not isinstance(definitions, dict) or definitions.get("schema") != DEFINITIONS_SCHEMA:
        print(json.dumps({"status": "FAIL", "reason": "invalid_definitions_schema"}, sort_keys=True))
        return 2
    previous = read_json(args.previous, {}) if args.previous else None
    registry = evaluate_registry(
        declarations=definitions.get("procedures", []),
        receipts=load_receipts(args.receipts_dir),
        enabled_system_ids=args.enabled_system,
        system_exemptions=definitions.get("system_exemptions", {}),
        system_inventory_attestations=definitions.get("system_inventory_attestations", {}),
        now=args.now,
        previous_registry=previous if isinstance(previous, dict) else None,
    )
    write_json(args.out, registry)
    print(str(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
