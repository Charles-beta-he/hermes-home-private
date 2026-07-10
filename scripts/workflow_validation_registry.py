#!/usr/bin/env python3
"""Evaluate procedure-level E2E declarations and receipts without executing them.

This module is intentionally local/read-only except for writing the requested
registry artifact. It never invokes a declared procedure and never grants
external authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REGISTRY_SCHEMA = "hermes_procedure_validation_registry_v1"
DEFINITIONS_SCHEMA = "hermes_procedure_definitions_v1"
RECEIPT_SCHEMA = "hermes_procedure_e2e_receipt_v1"
IMPLEMENTATION_STATES = {"missing", "scaffolded", "landed", "enabled"}
AUTHORITY_POLICIES = {"none", "exact_grant_required"}
VALIDATION_POLICIES = {"fresh_live_e2e_receipt"}
EVIDENCE_KINDS = {"evidence_refs", "acceptance_atoms", "negative_assertions", "cleanup_readback"}
FAILURE_EXPECTATIONS = {"fail_closed_and_surface_finding"}
RECOVERY_EXPECTATIONS = {"revalidate_after_local_remediation", "wait_for_exact_grant_then_revalidate"}
PROPAGATION_TARGETS = {
    "procedure_registry", "coverage_registry", "agent_os_projection", "lifecycle",
    "repair_packet", "workflow_loop_evaluator",
}


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
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strict_string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def _has_symlink_component(path: Path) -> bool:
    candidate = path.expanduser().absolute()
    return any(part.is_symlink() for part in (candidate, *candidate.parents))


def _read_regular_file_no_symlinks(path: Path, *, max_bytes: int = 1_048_576) -> bytes:
    absolute = path.expanduser().absolute()
    parts = absolute.parts
    if len(parts) < 2:
        raise ValueError("invalid authority artifact path")
    fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in parts[1:-1]:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
                raise ValueError("authority artifact is not a bounded regular file")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(file_fd, min(65_536, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("authority artifact exceeds size limit")
            after = os.fstat(file_fd)
            if (
                before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns
            ) != (
                after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                raise ValueError("authority artifact changed while reading")
            return b"".join(chunks)
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def validate_declaration(declaration: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not isinstance(declaration.get("required"), bool):
        issues.append("invalid_required")
    if not _nonempty_string(declaration.get("procedure_id")):
        issues.append("missing_procedure_id")
    if not _nonempty_string(declaration.get("system_id")):
        issues.append("missing_system_id")
    if declaration.get("implementation_state") not in IMPLEMENTATION_STATES:
        issues.append("invalid_implementation_state")
    if declaration.get("authority_policy") not in AUTHORITY_POLICIES:
        issues.append("invalid_authority_policy")
    elif declaration.get("authority_policy") == "exact_grant_required":
        if not _nonempty_string(declaration.get("authority_grant_root")):
            issues.append("missing_authority_grant_root")
        if not _nonempty_string(declaration.get("authority_issuer")):
            issues.append("missing_authority_issuer")
    if not _nonempty_string(declaration.get("side_effect_class")):
        issues.append("missing_side_effect_class")
    freshness = declaration.get("freshness_seconds")
    if not isinstance(freshness, int) or isinstance(freshness, bool) or freshness <= 0:
        issues.append("invalid_freshness_seconds")
    threshold = declaration.get("min_independent_successes", 1)
    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold <= 0:
        issues.append("invalid_min_independent_successes")
    if not _strict_string_list(declaration.get("required_acceptance_atoms")):
        issues.append("missing_required_acceptance_atoms")
    if not _strict_string_list(declaration.get("required_negative_assertions"), allow_empty=True):
        issues.append("invalid_required_negative_assertions")
    validation_policy = declaration.get("validation_policy")
    if not _nonempty_string(validation_policy):
        issues.append("missing_validation_policy")
    elif validation_policy not in VALIDATION_POLICIES:
        issues.append("invalid_validation_policy")
    raw_evidence_kinds = declaration.get("required_evidence_kinds")
    evidence_kinds = _string_list(raw_evidence_kinds)
    if not evidence_kinds:
        issues.append("missing_required_evidence_kinds")
    elif (
        not _strict_string_list(raw_evidence_kinds)
        or len(evidence_kinds) != len(set(evidence_kinds))
        or set(evidence_kinds) != EVIDENCE_KINDS
    ):
        issues.append("invalid_required_evidence_kinds")
    failure_expectation = declaration.get("failure_expectation")
    if not _nonempty_string(failure_expectation):
        issues.append("missing_failure_expectation")
    elif failure_expectation not in FAILURE_EXPECTATIONS:
        issues.append("invalid_failure_expectation")
    recovery_expectation = declaration.get("recovery_expectation")
    if not _nonempty_string(recovery_expectation):
        issues.append("missing_recovery_expectation")
    elif recovery_expectation not in RECOVERY_EXPECTATIONS:
        issues.append("invalid_recovery_expectation")
    raw_propagation_targets = declaration.get("propagation_targets")
    propagation_targets = _string_list(raw_propagation_targets)
    if not propagation_targets:
        issues.append("missing_propagation_targets")
    elif (
        not _strict_string_list(raw_propagation_targets)
        or len(propagation_targets) != len(set(propagation_targets))
        or not set(propagation_targets).issubset(PROPAGATION_TARGETS)
    ):
        issues.append("invalid_propagation_targets")
    return sorted(set(issues))


def _exact_authority_grant_valid(
    authority: dict[str, Any],
    declaration: dict[str, Any],
    started: datetime | None,
    completed: datetime | None,
    receipt_id: Any,
) -> bool:
    ref = authority.get("ref")
    root_ref = declaration.get("authority_grant_root")
    if not _nonempty_string(ref) or not _nonempty_string(root_ref) or started is None or completed is None:
        return False
    path = Path(str(ref)).expanduser()
    root = Path(str(root_ref)).expanduser()
    absolute_path = path.absolute()
    absolute_root = root.absolute()
    if _has_symlink_component(absolute_root) or _has_symlink_component(absolute_path) or not absolute_root.is_dir():
        return False
    try:
        absolute_path.relative_to(absolute_root)
        raw_grant = _read_regular_file_no_symlinks(absolute_path)
        digest = hashlib.sha256(raw_grant).hexdigest()
        grant = json.loads(raw_grant.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if authority.get("sha256") != digest or not isinstance(grant, dict):
        return False
    valid_from = parse_time(grant.get("valid_from"))
    expires_at = parse_time(grant.get("expires_at"))
    return bool(
        grant.get("schema") == "hermes_procedure_authority_grant_v1"
        and grant.get("grant_id") == path.stem
        and grant.get("status") == "active"
        and grant.get("procedure_id") == declaration.get("procedure_id")
        and grant.get("system_id") == declaration.get("system_id")
        and grant.get("action") == "execute_live_e2e_validation"
        and grant.get("scope") == declaration.get("procedure_id")
        and _nonempty_string(receipt_id)
        and grant.get("receipt_id") == receipt_id
        and grant.get("issued_by") == declaration.get("authority_issuer")
        and valid_from is not None
        and expires_at is not None
        and valid_from <= started <= completed <= expires_at
    )


def validate_receipt(receipt: dict[str, Any], declaration: dict[str, Any], now_dt: datetime | None = None) -> list[str]:
    issues: list[str] = []
    if receipt.get("schema") != RECEIPT_SCHEMA:
        issues.append("invalid_receipt_schema")
    if receipt.get("procedure_id") != declaration.get("procedure_id"):
        issues.append("procedure_id_mismatch")
    if not _nonempty_string(receipt.get("receipt_id")):
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

    raw_refs = receipt.get("evidence_refs")
    refs = _string_list(raw_refs)
    if (
        not _strict_string_list(raw_refs)
        or any(_has_symlink_component(Path(ref)) or not Path(ref).is_file() for ref in refs)
    ):
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

    raw_authority = receipt.get("authority")
    authority: dict[str, Any] = raw_authority if isinstance(raw_authority, dict) else {}
    if declaration.get("authority_policy") == "exact_grant_required":
        if authority.get("status") != "granted" or not _exact_authority_grant_valid(
            authority, declaration, started, completed, receipt.get("receipt_id")
        ):
            issues.append("authority_not_granted")

    declared_effect = str(declaration.get("side_effect_class") or "")
    raw_observed_effects = receipt.get("side_effects_observed")
    observed_effects = _string_list(raw_observed_effects)
    if not _strict_string_list(raw_observed_effects, allow_empty=True):
        issues.append("invalid_side_effects_observed")
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
    required_value = declaration.get("required", True)
    # Invalid values fail closed as required rather than escaping inventory
    # accounting through Python truthiness.
    required = required_value if isinstance(required_value, bool) else True
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
    freshness_value = declaration.get("freshness_seconds")
    freshness_seconds = freshness_value if isinstance(freshness_value, int) and not isinstance(freshness_value, bool) and freshness_value > 0 else 0
    age_seconds = max(0.0, (now_dt - latest_completed).total_seconds()) if latest_completed else None
    latest_is_fresh = bool(latest_completed and freshness_seconds > 0 and age_seconds <= freshness_seconds)
    threshold_value = declaration.get("min_independent_successes", 1)
    threshold = threshold_value if isinstance(threshold_value, int) and not isinstance(threshold_value, bool) and threshold_value > 0 else 1

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
        future_dated = bool(reviewed_at and reviewed_at > now_dt)
        valid = bool(
            attestation.get("scope_complete") is True
            and str(attestation.get("basis") or "").strip()
            and isinstance(freshness, int)
            and not isinstance(freshness, bool)
            and freshness > 0
            and age_seconds is not None
            and age_seconds <= freshness
            and not future_dated
        )
        attestation_states[system_id] = {
            **attestation,
            "valid": valid,
            "future_dated": future_dated,
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
    all_required_connected = bool(required) and len(fully_connected) == len(required)
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
