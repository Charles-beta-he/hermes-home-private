#!/usr/bin/env python3
"""Fail-closed validator for b2b_delivery_workflow_v1 manifests."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

STAGE_ORDER = [f"S{i}" for i in range(8)]
STAGE_NAMES = {
    "S0": "qualification",
    "S1": "discovery_baseline",
    "S2": "commercial_spec_authority",
    "S3": "solution_workspace",
    "S4": "pilot_slice",
    "S5": "production_delivery",
    "S6": "acceptance_handover",
    "S7": "operations_ratchet",
}
BOUNDARY_STAGE = {
    "diagnosis": "S1",
    "solution": "S3",
    "pilot": "S4",
    "production": "S5",
    "acceptance": "S6",
    "operations": "S7",
}
VALID_STAGE_STATES = {
    "not_started", "in_progress", "blocked", "ready_for_review",
    "accepted", "rejected", "superseded",
}
VALID_CLAIM_STATES = {"verified", "disputed", "unverified", "superseded"}
VALID_CLOSURE_STATES = {
    "in_progress", "ready_for_review", "accepted", "waiting_acceptance",
    "blocked", "rolled_back", "superseded",
}
VALID_EXTERNAL_ACTIONS = {
    "push", "deploy", "external_send", "credential_entry", "payment_or_funds",
    "destructive_operation", "broad_fanout",
}
HUMAN_ONLY_EXTERNAL_ACTIONS = {"credential_entry", "payment_or_funds"}
REQUIRED_ARTIFACT_TYPES = {
    "S0": {"qualification"},
    "S1": {"baseline"},
    "S2": {"spec", "authority_matrix"},
    "S3": {"solution_workspace", "risk_register"},
    "S4": {"pilot_evidence", "test_evidence"},
    "S5": {"release_provenance", "runtime_evidence", "rollback_plan"},
    "S6": {"client_acceptance", "handover"},
    "S7": {"kpi_readback", "operations_log"},
}
PLACEHOLDER_RE = re.compile(r"replace[-_ ]with|YYYY-MM-DD|\[[A-Z][^]]*\]", re.I)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_duplicate_error(errors: list[str], seen: set[str], value: object, label: str) -> None:
    if not nonempty(value):
        errors.append(f"{label} must be non-empty")
    elif value in seen:
        errors.append(f"duplicate {label}: {value}")
    else:
        seen.add(value)


def validate_date(value: object, label: str, errors: list[str]) -> None:
    if not nonempty(value):
        errors.append(f"{label} must be non-empty")
        return
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be ISO date YYYY-MM-DD")
        return
    if parsed > date.today():
        errors.append(f"{label} cannot be in the future")


def validate_local_ref(item: dict, label: str, errors: list[str]) -> None:
    ref = item.get("ref")
    if not nonempty(ref):
        errors.append(f"{label}.ref must be non-empty")
        return
    if PLACEHOLDER_RE.search(ref):
        errors.append(f"{label}.ref contains placeholder")
    path = Path(ref).expanduser()
    if not path.is_absolute():
        return
    if not path.is_file():
        errors.append(f"{label}.ref local file does not exist: {ref}")
        return
    digest = item.get("sha256")
    if not nonempty(digest):
        errors.append(f"{label}.sha256 is required for absolute local evidence")
        return
    if not SHA256_RE.fullmatch(digest):
        errors.append(f"{label}.sha256 must be 64 lowercase hex characters")
        return
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != digest:
        errors.append(f"{label}.sha256 mismatch for {ref}")


def validate_refs(values: object, known: set[str], label: str, errors: list[str], *, required: bool = False) -> None:
    if not isinstance(values, list):
        errors.append(f"{label} must be a list")
        return
    if required and not values:
        errors.append(f"{label} must not be empty")
    for ref in values:
        if not nonempty(ref):
            errors.append(f"{label} contains empty reference")
        elif ref not in known:
            errors.append(f"{label} references unknown id: {ref}")


def validate(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    required = {
        "schema", "engagement_id", "client_alias", "service_type",
        "completion_boundary", "closure_state", "confidentiality",
        "truth_sources", "artifacts", "claims", "contradictions", "authority",
        "stages", "metrics", "risks", "public_case", "client_acceptance",
    }
    for key in sorted(required - data.keys()):
        errors.append(f"missing top-level field: {key}")

    if data.get("schema") != "b2b_delivery_workflow_v1":
        errors.append("schema must be b2b_delivery_workflow_v1")
    for key in ("engagement_id", "client_alias", "service_type"):
        value = data.get(key)
        if not nonempty(value):
            errors.append(f"{key} must be non-empty")
        elif PLACEHOLDER_RE.search(value):
            errors.append(f"{key} contains placeholder")

    boundary = data.get("completion_boundary")
    if not isinstance(boundary, str) or boundary not in BOUNDARY_STAGE:
        errors.append(f"completion_boundary must be one of {sorted(BOUNDARY_STAGE)}")
    closure = data.get("closure_state")
    if not isinstance(closure, str) or closure not in VALID_CLOSURE_STATES:
        errors.append(f"invalid closure_state: {closure}")
    confidentiality = data.get("confidentiality")
    if not isinstance(confidentiality, str) or confidentiality not in {"internal", "client_confidential", "public"}:
        errors.append("confidentiality must be internal, client_confidential, or public")

    source_ids: set[str] = set()
    truth_sources = data.get("truth_sources")
    if not isinstance(truth_sources, list) or not truth_sources:
        errors.append("truth_sources must be a non-empty list")
    else:
        for idx, source in enumerate(truth_sources):
            label = f"truth_sources[{idx}]"
            if not isinstance(source, dict):
                errors.append(f"{label} must be an object")
                continue
            add_duplicate_error(errors, source_ids, source.get("id"), "truth source id")
            for key in ("type", "scope"):
                value = source.get(key)
                if not nonempty(value):
                    errors.append(f"{label}.{key} must be non-empty")
                elif PLACEHOLDER_RE.search(value):
                    errors.append(f"{label}.{key} contains placeholder")
            validate_date(source.get("observed_at"), f"{label}.observed_at", errors)
            validate_local_ref(source, label, errors)

    artifact_ids: set[str] = set()
    artifact_type_by_id: dict[str, str] = {}
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be a list")
    else:
        for idx, artifact in enumerate(artifacts):
            label = f"artifacts[{idx}]"
            if not isinstance(artifact, dict):
                errors.append(f"{label} must be an object")
                continue
            artifact_id = artifact.get("id")
            is_new_id = nonempty(artifact_id) and artifact_id not in artifact_ids
            add_duplicate_error(errors, artifact_ids, artifact_id, "artifact id")
            for key in ("type", "owner", "scope"):
                value = artifact.get(key)
                if not nonempty(value):
                    errors.append(f"{label}.{key} must be non-empty")
                elif PLACEHOLDER_RE.search(value):
                    errors.append(f"{label}.{key} contains placeholder")
            if is_new_id and nonempty(artifact.get("type")):
                artifact_type_by_id[artifact_id] = artifact["type"]
            validate_local_ref(artifact, label, errors)

    claim_ids: set[str] = set()
    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
    else:
        for idx, claim in enumerate(claims):
            label = f"claims[{idx}]"
            if not isinstance(claim, dict):
                errors.append(f"{label} must be an object")
                continue
            cid = claim.get("id")
            add_duplicate_error(errors, claim_ids, cid, "claim id")
            for key in ("text", "scope"):
                if not nonempty(claim.get(key)):
                    errors.append(f"{label}.{key} must be non-empty")
            status = claim.get("status")
            if not isinstance(status, str) or status not in VALID_CLAIM_STATES:
                errors.append(f"{label} has invalid status: {status}")
            validate_refs(
                claim.get("evidence_refs"), source_ids,
                f"{label}.evidence_refs", errors, required=status == "verified",
            )
            validate_refs(
                claim.get("negative_evidence_refs"), source_ids,
                f"{label}.negative_evidence_refs", errors,
            )
            limitations = claim.get("limitations")
            if status == "verified" and not isinstance(limitations, list):
                errors.append(f"verified claim {cid or idx} must have limitations list")

    contradiction_ids: set[str] = set()
    unresolved_claims: set[str] = set()
    contradictions = data.get("contradictions")
    if not isinstance(contradictions, list):
        errors.append("contradictions must be a list")
    else:
        for idx, item in enumerate(contradictions):
            label = f"contradictions[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            add_duplicate_error(errors, contradiction_ids, item.get("id"), "contradiction id")
            status = item.get("status")
            if not isinstance(status, str) or status not in {"unresolved", "resolved", "accepted_risk"}:
                errors.append(f"{label} has invalid status: {status}")
            refs = item.get("claim_refs")
            validate_refs(refs, claim_ids, f"{label}.claim_refs", errors)
            if isinstance(refs, list) and len(refs) < 2:
                errors.append(f"{label}.claim_refs must contain at least 2 claims")
            if status == "unresolved":
                errors.append(f"unresolved contradiction: {item.get('id', idx)}")
                unresolved_claims.update(ref for ref in (refs or []) if isinstance(ref, str))
            elif isinstance(status, str) and status in {"resolved", "accepted_risk"} and not nonempty(item.get("resolution")):
                errors.append(f"{status} contradiction {item.get('id', idx)} needs resolution")

    if unresolved_claims and isinstance(claims, list):
        for claim in claims:
            if isinstance(claim, dict) and claim.get("id") in unresolved_claims and claim.get("status") == "verified":
                errors.append(f"claim {claim.get('id')} cannot remain verified in unresolved contradiction")

    authority = data.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
    else:
        for key in ("local_read_only", "local_reversible_write"):
            if not isinstance(authority.get(key), bool):
                errors.append(f"authority.{key} must be boolean")
        action_ids: set[str] = set()
        actions = authority.get("external_actions")
        if not isinstance(actions, list):
            errors.append("authority.external_actions must be a list")
        else:
            for idx, action in enumerate(actions):
                label = f"external_actions[{idx}]"
                if not isinstance(action, dict):
                    errors.append(f"{label} must be an object")
                    continue
                action_name = action.get("action")
                add_duplicate_error(errors, action_ids, action_name, "external action")
                if nonempty(action_name) and action_name not in VALID_EXTERNAL_ACTIONS:
                    errors.append(f"unknown external action: {action_name}")
                if action.get("allowed") is True:
                    if nonempty(action_name) and action_name in HUMAN_ONLY_EXTERNAL_ACTIONS:
                        errors.append(f"{action_name} cannot be enabled; it requires a human-only gate")
                    for key in ("target", "scope", "grant_ref", "rollback", "readback"):
                        if not nonempty(action.get(key)):
                            errors.append(f"allowed external action {action_name or idx} needs {key}")
                elif action.get("allowed") is not False:
                    errors.append(f"{label}.allowed must be boolean")

    stage_map: dict[str, dict] = {}
    stages = data.get("stages")
    if not isinstance(stages, list):
        errors.append("stages must be a list")
    else:
        for idx, stage in enumerate(stages):
            if not isinstance(stage, dict):
                errors.append(f"stages[{idx}] must be an object")
                continue
            sid = stage.get("id")
            if not nonempty(sid):
                errors.append(f"stages[{idx}].id must be non-empty")
                continue
            if sid in stage_map:
                errors.append(f"duplicate stage id: {sid}")
                continue
            stage_map[sid] = stage
            if sid not in STAGE_NAMES:
                errors.append(f"unknown stage id: {sid}")
                continue
            if stage.get("name") != STAGE_NAMES[sid]:
                errors.append(f"stage {sid} name must be {STAGE_NAMES[sid]}")
            status = stage.get("status")
            if not isinstance(status, str) or status not in VALID_STAGE_STATES:
                errors.append(f"stage {sid} has invalid status: {status}")
            stage_artifacts = stage.get("artifacts")
            stage_evidence = stage.get("evidence_refs")
            blockers = stage.get("blockers")
            validate_refs(stage_artifacts, artifact_ids, f"stage {sid}.artifacts", errors)
            validate_refs(stage_evidence, source_ids, f"stage {sid}.evidence_refs", errors)
            if not isinstance(blockers, list):
                errors.append(f"stage {sid}.blockers must be a list")
                blockers = []
            if isinstance(status, str) and status in {"accepted", "in_progress", "blocked", "ready_for_review", "rejected"} and not nonempty(stage.get("owner")):
                errors.append(f"active stage {sid} needs owner")
            if status == "accepted":
                if not stage_artifacts:
                    errors.append(f"accepted stage {sid} needs artifacts")
                elif isinstance(stage_artifacts, list):
                    actual_types = {
                        artifact_type_by_id.get(ref)
                        for ref in stage_artifacts
                        if isinstance(ref, str) and ref in artifact_type_by_id
                    }
                    missing_types = REQUIRED_ARTIFACT_TYPES[sid] - actual_types
                    if missing_types:
                        errors.append(
                            f"accepted stage {sid} missing required artifact types: "
                            f"{', '.join(sorted(missing_types))}"
                        )
                if not stage_evidence:
                    errors.append(f"accepted stage {sid} needs evidence_refs")
                if blockers:
                    errors.append(f"accepted stage {sid} cannot have blockers")
            if status == "blocked" and not blockers:
                errors.append(f"blocked stage {sid} needs blockers")
        for sid in STAGE_ORDER:
            if sid not in stage_map:
                errors.append(f"missing required stage: {sid}")

    if all(sid in stage_map for sid in STAGE_ORDER):
        for idx, sid in enumerate(STAGE_ORDER):
            status = stage_map[sid].get("status")
            if not isinstance(status, str) or status not in {"not_started", "superseded"}:
                for prior_sid in STAGE_ORDER[:idx]:
                    if stage_map[prior_sid].get("status") != "accepted":
                        errors.append(f"stage {sid} cannot be {status} before {prior_sid} is accepted")
                        break

        if isinstance(boundary, str) and boundary in BOUNDARY_STAGE:
            boundary_sid = BOUNDARY_STAGE[boundary]
            boundary_idx = STAGE_ORDER.index(boundary_sid)
            prior = STAGE_ORDER[:boundary_idx]
            for sid in STAGE_ORDER[boundary_idx + 1:]:
                status = stage_map[sid].get("status")
                if not isinstance(status, str) or status not in {"not_started", "superseded"}:
                    errors.append(
                        f"stage {sid} is beyond completion boundary {boundary} and cannot be {status}"
                    )
            if closure == "accepted":
                for sid in STAGE_ORDER[: boundary_idx + 1]:
                    if stage_map[sid].get("status") != "accepted":
                        errors.append(f"accepted {boundary} closure requires accepted stage {sid}")
            elif closure == "ready_for_review":
                for sid in prior:
                    if stage_map[sid].get("status") != "accepted":
                        errors.append(f"ready_for_review {boundary} closure requires accepted stage {sid}")
                if stage_map[boundary_sid].get("status") != "ready_for_review":
                    errors.append(f"ready_for_review closure requires stage {boundary_sid}=ready_for_review")
            elif closure == "waiting_acceptance":
                if boundary != "acceptance":
                    errors.append("waiting_acceptance closure requires completion_boundary=acceptance")
                for sid in STAGE_ORDER[:6]:
                    if stage_map[sid].get("status") != "accepted":
                        errors.append(f"waiting_acceptance requires accepted stage {sid}")
                if stage_map["S6"].get("status") != "ready_for_review":
                    errors.append("waiting_acceptance requires stage S6=ready_for_review")
            elif closure == "blocked" and not any(
                stage_map[sid].get("status") == "blocked"
                for sid in STAGE_ORDER[: boundary_idx + 1]
            ):
                errors.append("blocked closure requires a blocked stage within completion boundary")
            elif closure == "rolled_back" and not any(
                stage_map[sid].get("status") in {"rejected", "superseded"}
                for sid in STAGE_ORDER[: boundary_idx + 1]
            ):
                errors.append("rolled_back closure requires rejected or superseded stage")

    metric_ids: set[str] = set()
    metrics = data.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append("metrics must be a non-empty list")
    else:
        for idx, metric in enumerate(metrics):
            label = f"metrics[{idx}]"
            if not isinstance(metric, dict):
                errors.append(f"{label} must be an object")
                continue
            add_duplicate_error(errors, metric_ids, metric.get("id"), "metric id")
            for key in ("name", "measurement_ref"):
                value = metric.get(key)
                if not nonempty(value):
                    errors.append(f"{label}.{key} must be non-empty")
                elif PLACEHOLDER_RE.search(value):
                    errors.append(f"{label}.{key} contains placeholder")
            if "baseline" not in metric:
                errors.append(f"{label} needs baseline")
            if "target" not in metric:
                errors.append(f"{label} needs target")
            validate_refs(metric.get("evidence_refs"), source_ids, f"{label}.evidence_refs", errors)

    risk_ids: set[str] = set()
    risks = data.get("risks")
    if not isinstance(risks, list):
        errors.append("risks must be a list")
    else:
        for idx, risk in enumerate(risks):
            label = f"risks[{idx}]"
            if not isinstance(risk, dict):
                errors.append(f"{label} must be an object")
                continue
            add_duplicate_error(errors, risk_ids, risk.get("id"), "risk id")
            severity = risk.get("severity")
            if not isinstance(severity, str) or severity not in {"low", "medium", "high", "critical"}:
                errors.append(f"{label} has invalid severity")
            for key in ("description", "detection", "mitigation"):
                value = risk.get(key)
                if not nonempty(value):
                    errors.append(f"{label}.{key} must be non-empty")
                elif PLACEHOLDER_RE.search(value):
                    errors.append(f"{label}.{key} contains placeholder")
            if isinstance(severity, str) and severity in {"high", "critical"} and not nonempty(risk.get("rollback")):
                errors.append(f"high/critical risk {risk.get('id', idx)} needs rollback")

    public_case = data.get("public_case")
    if not isinstance(public_case, dict):
        errors.append("public_case must be an object")
    else:
        status = public_case.get("status")
        if not isinstance(status, str) or status not in {"not_ready", "ready"}:
            errors.append("public_case.status must be not_ready or ready")
        markers = public_case.get("sensitive_markers")
        if not isinstance(markers, list):
            errors.append("public_case.sensitive_markers must be a list")
            markers = []
        if status == "ready":
            if confidentiality != "public":
                errors.append("public case ready requires confidentiality=public")
            if public_case.get("publication_rights_verified") is not True:
                errors.append("public case ready requires verified publication rights")
            if public_case.get("anonymization_check") is not True:
                errors.append("public case ready requires anonymization_check=true")
            if markers:
                errors.append("public case ready cannot contain sensitive markers")

    acceptance = data.get("client_acceptance")
    acceptance_status = None
    if not isinstance(acceptance, dict):
        errors.append("client_acceptance must be an object")
    else:
        acceptance_status = acceptance.get("status")
        if not isinstance(acceptance_status, str) or acceptance_status not in {"not_requested", "pending", "accepted", "rejected"}:
            errors.append("client_acceptance.status is invalid")
        if acceptance_status == "accepted":
            for key in ("accepted_by", "accepted_at", "scope"):
                if not nonempty(acceptance.get(key)):
                    errors.append(f"accepted client acceptance needs {key}")
        if closure == "waiting_acceptance" and acceptance_status != "pending":
            errors.append("waiting_acceptance closure requires client_acceptance=pending")

    if all(sid in stage_map for sid in ("S6", "S7")):
        if stage_map["S6"].get("status") == "accepted" and acceptance_status != "accepted":
            errors.append("accepted stage S6 requires client_acceptance=accepted")
        s7_status = stage_map["S7"].get("status")
        if isinstance(s7_status, str) and s7_status in {"in_progress", "ready_for_review", "accepted"} and acceptance_status != "accepted":
            errors.append("active/accepted stage S7 requires client_acceptance=accepted")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: verify_delivery_workflow.py <manifest.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        print(f"FAIL {path}: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        f"PASS {path}: manifest gates passed "
        f"(boundary={data.get('completion_boundary')}, closure={data.get('closure_state')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
