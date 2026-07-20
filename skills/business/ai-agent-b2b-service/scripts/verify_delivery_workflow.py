#!/usr/bin/env python3
"""Fail-closed validator for b2b_delivery_workflow_v1 manifests."""
from __future__ import annotations

import json
import sys
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


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be a JSON object"]

    required = {
        "schema", "engagement_id", "client_alias", "service_type",
        "completion_boundary", "closure_state", "confidentiality",
        "truth_sources", "claims", "contradictions", "authority", "stages",
        "metrics", "risks", "public_case", "client_acceptance",
    }
    for key in sorted(required - data.keys()):
        errors.append(f"missing top-level field: {key}")

    if data.get("schema") != "b2b_delivery_workflow_v1":
        errors.append("schema must be b2b_delivery_workflow_v1")
    for key in ("engagement_id", "client_alias", "service_type"):
        if not nonempty(data.get(key)):
            errors.append(f"{key} must be non-empty")

    boundary = data.get("completion_boundary")
    if boundary not in BOUNDARY_STAGE:
        errors.append(f"completion_boundary must be one of {sorted(BOUNDARY_STAGE)}")
    closure = data.get("closure_state")
    if closure not in VALID_CLOSURE_STATES:
        errors.append(f"invalid closure_state: {closure}")
    if data.get("confidentiality") not in {"internal", "client_confidential", "public"}:
        errors.append("confidentiality must be internal, client_confidential, or public")

    truth_sources = data.get("truth_sources")
    source_ids: set[str] = set()
    if not isinstance(truth_sources, list) or not truth_sources:
        errors.append("truth_sources must be a non-empty list")
    else:
        for idx, source in enumerate(truth_sources):
            if not isinstance(source, dict):
                errors.append(f"truth_sources[{idx}] must be an object")
                continue
            sid = source.get("id")
            if not nonempty(sid):
                errors.append(f"truth_sources[{idx}].id must be non-empty")
            elif sid in source_ids:
                errors.append(f"duplicate truth source id: {sid}")
            else:
                source_ids.add(sid)
            for key in ("type", "ref", "observed_at", "scope"):
                if not nonempty(source.get(key)):
                    errors.append(f"truth_sources[{idx}].{key} must be non-empty")

    claims = data.get("claims")
    claim_ids: set[str] = set()
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
    else:
        for idx, claim in enumerate(claims):
            if not isinstance(claim, dict):
                errors.append(f"claims[{idx}] must be an object")
                continue
            cid = claim.get("id")
            if not nonempty(cid):
                errors.append(f"claims[{idx}].id must be non-empty")
            elif cid in claim_ids:
                errors.append(f"duplicate claim id: {cid}")
            else:
                claim_ids.add(cid)
            if not nonempty(claim.get("text")):
                errors.append(f"claims[{idx}].text must be non-empty")
            if not nonempty(claim.get("scope")):
                errors.append(f"claims[{idx}].scope must be non-empty")
            status = claim.get("status")
            if status not in VALID_CLAIM_STATES:
                errors.append(f"claims[{idx}] has invalid status: {status}")
            evidence_refs = claim.get("evidence_refs")
            if not isinstance(evidence_refs, list):
                errors.append(f"claims[{idx}].evidence_refs must be a list")
            elif status == "verified" and not evidence_refs:
                errors.append(f"verified claim {cid or idx} must have evidence_refs")
            if status == "verified" and not isinstance(claim.get("limitations"), list):
                errors.append(f"verified claim {cid or idx} must have limitations list")

    contradictions = data.get("contradictions")
    unresolved_claims: set[str] = set()
    if not isinstance(contradictions, list):
        errors.append("contradictions must be a list")
    else:
        for idx, item in enumerate(contradictions):
            if not isinstance(item, dict):
                errors.append(f"contradictions[{idx}] must be an object")
                continue
            status = item.get("status")
            if status not in {"unresolved", "resolved", "accepted_risk"}:
                errors.append(f"contradictions[{idx}] has invalid status: {status}")
            refs = item.get("claim_refs")
            if not isinstance(refs, list) or len(refs) < 2:
                errors.append(f"contradictions[{idx}].claim_refs must contain at least 2 claims")
            if status == "unresolved":
                errors.append(f"unresolved contradiction: {item.get('id', idx)}")
                unresolved_claims.update(refs or [])
            elif status == "resolved" and not nonempty(item.get("resolution")):
                errors.append(f"resolved contradiction {item.get('id', idx)} needs resolution")

    if unresolved_claims and isinstance(claims, list):
        for claim in claims:
            if isinstance(claim, dict) and claim.get("id") in unresolved_claims and claim.get("status") == "verified":
                errors.append(f"claim {claim.get('id')} cannot remain verified in unresolved contradiction")

    authority = data.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
    else:
        actions = authority.get("external_actions")
        if not isinstance(actions, list):
            errors.append("authority.external_actions must be a list")
        else:
            for idx, action in enumerate(actions):
                if not isinstance(action, dict):
                    errors.append(f"external_actions[{idx}] must be an object")
                    continue
                if not nonempty(action.get("action")):
                    errors.append(f"external_actions[{idx}].action must be non-empty")
                if action.get("allowed") is True:
                    for key in ("target", "rollback", "readback"):
                        if not nonempty(action.get(key)):
                            errors.append(f"allowed external action {action.get('action', idx)} needs {key}")
                elif action.get("allowed") is not False:
                    errors.append(f"external_actions[{idx}].allowed must be boolean")

    stages = data.get("stages")
    stage_map: dict[str, dict] = {}
    if not isinstance(stages, list):
        errors.append("stages must be a list")
    else:
        for idx, stage in enumerate(stages):
            if not isinstance(stage, dict):
                errors.append(f"stages[{idx}] must be an object")
                continue
            sid = stage.get("id")
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
            if status not in VALID_STAGE_STATES:
                errors.append(f"stage {sid} has invalid status: {status}")
            for key in ("artifacts", "evidence_refs", "blockers"):
                if not isinstance(stage.get(key), list):
                    errors.append(f"stage {sid}.{key} must be a list")
            if status == "accepted":
                if not nonempty(stage.get("owner")):
                    errors.append(f"accepted stage {sid} needs owner")
                if not stage.get("artifacts"):
                    errors.append(f"accepted stage {sid} needs artifacts")
                if not stage.get("evidence_refs"):
                    errors.append(f"accepted stage {sid} needs evidence_refs")
                if stage.get("blockers"):
                    errors.append(f"accepted stage {sid} cannot have blockers")
        for sid in STAGE_ORDER:
            if sid not in stage_map:
                errors.append(f"missing required stage: {sid}")

    if boundary in BOUNDARY_STAGE and all(sid in stage_map for sid in STAGE_ORDER):
        boundary_sid = BOUNDARY_STAGE[boundary]
        boundary_idx = STAGE_ORDER.index(boundary_sid)
        for sid in STAGE_ORDER[: boundary_idx + 1]:
            if stage_map[sid].get("status") != "accepted":
                errors.append(f"completion boundary {boundary} requires accepted stage {sid}")
        if closure == "accepted" and stage_map[boundary_sid].get("status") != "accepted":
            errors.append("accepted closure requires accepted completion-boundary stage")

    metrics = data.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        errors.append("metrics must be a non-empty list")
    else:
        for idx, metric in enumerate(metrics):
            if not isinstance(metric, dict):
                errors.append(f"metrics[{idx}] must be an object")
                continue
            for key in ("id", "name", "measurement_ref"):
                if not nonempty(metric.get(key)):
                    errors.append(f"metrics[{idx}].{key} must be non-empty")
            if "target" not in metric:
                errors.append(f"metrics[{idx}] needs target")

    risks = data.get("risks")
    if not isinstance(risks, list):
        errors.append("risks must be a list")
    else:
        for idx, risk in enumerate(risks):
            if not isinstance(risk, dict):
                errors.append(f"risks[{idx}] must be an object")
                continue
            if risk.get("severity") not in {"low", "medium", "high", "critical"}:
                errors.append(f"risks[{idx}] has invalid severity")
            for key in ("id", "description", "detection", "mitigation"):
                if not nonempty(risk.get(key)):
                    errors.append(f"risks[{idx}].{key} must be non-empty")
            if risk.get("severity") in {"high", "critical"} and not nonempty(risk.get("rollback")):
                errors.append(f"high/critical risk {risk.get('id', idx)} needs rollback")

    public_case = data.get("public_case")
    if not isinstance(public_case, dict):
        errors.append("public_case must be an object")
    else:
        status = public_case.get("status")
        if status not in {"not_ready", "ready"}:
            errors.append("public_case.status must be not_ready or ready")
        markers = public_case.get("sensitive_markers")
        if not isinstance(markers, list):
            errors.append("public_case.sensitive_markers must be a list")
            markers = []
        if status == "ready":
            if public_case.get("publication_rights_verified") is not True:
                errors.append("public case ready requires verified publication rights")
            if public_case.get("anonymization_check") is not True:
                errors.append("public case ready requires anonymization_check=true")
            if markers:
                errors.append("public case ready cannot contain sensitive markers")

    acceptance = data.get("client_acceptance")
    if not isinstance(acceptance, dict):
        errors.append("client_acceptance must be an object")
    else:
        status = acceptance.get("status")
        if status not in {"not_requested", "pending", "accepted", "rejected"}:
            errors.append("client_acceptance.status is invalid")
        if status == "accepted":
            for key in ("accepted_by", "accepted_at", "scope"):
                if not nonempty(acceptance.get(key)):
                    errors.append(f"accepted client acceptance needs {key}")
        if closure == "accepted" and boundary in {"acceptance", "operations"} and status != "accepted":
            errors.append("accepted acceptance/operations closure requires client_acceptance=accepted")

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
    print(f"PASS {path}: b2b_delivery_workflow_v1 is structurally converged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
