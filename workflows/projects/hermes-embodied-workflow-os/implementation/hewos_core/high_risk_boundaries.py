import hashlib
import json


REQUESTED_HIGH_RISK_BOUNDARIES = [
    "taskpool_lifecycle",
    "external_dispatch",
    "hardware_execution",
    "deploy_publish",
    "auth_credential",
]


BOUNDARY_CATALOG = {
    "taskpool_lifecycle": {
        "label": "Taskpool lifecycle write-through",
        "mode": "exact_local_target_required",
        "minimum_authority": "specific task id, intended status/action, idempotency key, evidence refs, rollback, readback",
        "rollback_required": True,
    },
    "external_dispatch": {
        "label": "External dispatch / outbox / sender",
        "mode": "exact_allowlist_required",
        "minimum_authority": "specific platform/channel/target, payload hash, allowlist proof, evidence refs, readback",
        "rollback_required": False,
    },
    "hardware_execution": {
        "label": "Hardware / robot physical execution",
        "mode": "device_identity_telemetry_and_onsite_gate_required",
        "minimum_authority": "device id, telemetry freshness, command preview, safety gates, idempotency, audit path, readback",
        "rollback_required": True,
    },
    "deploy_publish": {
        "label": "Deploy / publish / push",
        "mode": "exact_target_required",
        "minimum_authority": "repository/env/branch or deployment target, rollback path, receipt, post-action readback",
        "rollback_required": True,
    },
    "auth_credential": {
        "label": "Auth / credential / payment boundary",
        "mode": "human_secret_entry_required",
        "minimum_authority": "human enters secrets outside agent; agent records only non-secret gate receipt and denied/ready state",
        "rollback_required": False,
    },
}


class BoundaryError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise BoundaryError(message)


def _digest(data):
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_boundary_catalog(catalog=BOUNDARY_CATALOG):
    missing = [item for item in REQUESTED_HIGH_RISK_BOUNDARIES if item not in catalog]
    malformed = []
    for boundary_id, cfg in catalog.items():
        for field in ("label", "mode", "minimum_authority", "rollback_required"):
            if field not in cfg:
                malformed.append(f"{boundary_id}:{field}")
    return {
        "ok": not missing and not malformed,
        "missing": missing,
        "malformed": malformed,
        "boundary_count": len(catalog),
    }


def boundary_record(boundary_id, cfg):
    return {
        "id": boundary_id,
        "label": cfg["label"],
        "mode": cfg["mode"],
        "governance_covered": True,
        "exact_target_required": True,
        "receipt_required": True,
        "rollback_required": bool(cfg["rollback_required"]),
        "readback_required": True,
        "executed": False,
        "execution_status": "not_executed_exact_target_required",
        "token_read_allowed": False,
        "stores_secrets": False,
        "agent_may_type_secret": False if boundary_id == "auth_credential" else None,
        "minimum_authority": cfg["minimum_authority"],
    }


def boundary_coverage_matrix(catalog=BOUNDARY_CATALOG):
    validation = validate_boundary_catalog(catalog)
    boundaries = [boundary_record(item, catalog[item]) for item in REQUESTED_HIGH_RISK_BOUNDARIES if item in catalog]
    coverage = 0 if not REQUESTED_HIGH_RISK_BOUNDARIES else int(100 * len(boundaries) / len(REQUESTED_HIGH_RISK_BOUNDARIES))
    return {
        "schema": "hewos_high_risk_boundary_coverage_v1",
        "requested_boundaries": list(REQUESTED_HIGH_RISK_BOUNDARIES),
        "governance_coverage_percent": coverage if validation["ok"] else min(coverage, 99),
        "live_execution_enabled": False,
        "production_resource_touched": False,
        "boundaries": boundaries,
        "validation": validation,
    }


def authorize_boundary_intent(request):
    _require(isinstance(request, dict), "request must be object")
    boundary_id = request.get("boundary_id")
    _require(boundary_id in BOUNDARY_CATALOG, f"unknown boundary: {boundary_id}")
    reasons = []
    for field, reason in (
        ("exact_target", "missing_exact_target"),
        ("payload_hash", "missing_payload_hash"),
        ("evidence_refs", "missing_evidence_refs"),
        ("readback_plan", "missing_readback_plan"),
        ("rollback_plan", "missing_rollback_plan"),
        ("idempotency_key", "missing_idempotency_key"),
    ):
        value = request.get(field)
        if not value:
            reasons.append(reason)
    requested_action = request.get("requested_action")
    if requested_action not in {"authorize_intent", "execute"}:
        reasons.append("unsupported_requested_action")
    if boundary_id == "auth_credential":
        secret_like = [key for key in request if any(token in key.lower() for token in ("secret", "token", "password", "key")) and key != "idempotency_key"]
        if secret_like:
            reasons.append("secret_material_not_allowed")
    if requested_action == "execute":
        reasons.append("live_execution_not_opened_by_intent_gate")
    base = {
        "schema": "hewos_boundary_intent_authorization_v1",
        "boundary_id": boundary_id,
        "requested_action": requested_action,
        "execution_enabled": False,
        "token_read_allowed": False,
        "stores_secrets": False,
        "agent_may_type_secret": False,
    }
    if reasons:
        base.update({
            "decision": "blocked",
            "reasons": sorted(set(reasons)),
            "intent_digest": None,
        })
        return base
    intent_basis = {
        "boundary_id": boundary_id,
        "exact_target": request["exact_target"],
        "payload_hash": request["payload_hash"],
        "idempotency_key": request["idempotency_key"],
        "readback_plan": request["readback_plan"],
        "rollback_plan": request["rollback_plan"],
    }
    base.update({
        "decision": "authorized_intent_only",
        "reasons": [],
        "exact_target": request["exact_target"],
        "payload_hash": request["payload_hash"],
        "evidence_refs": list(request["evidence_refs"]),
        "readback_plan": request["readback_plan"],
        "rollback_plan": request["rollback_plan"],
        "idempotency_key": request["idempotency_key"],
        "intent_digest": _digest(intent_basis),
    })
    return base
