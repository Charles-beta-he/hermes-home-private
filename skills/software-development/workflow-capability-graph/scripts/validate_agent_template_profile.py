#!/usr/bin/env python3
"""Validate a Hermes Agent Template Profile JSON file.

No third-party dependencies. Accepts JSON only so it can run in minimal Hermes environments.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP = [
    "id", "name", "purpose", "source_refs", "capability_graph_refs", "intent_routes",
    "inputs", "outputs", "authority", "side_effect_matrix", "gates", "runtime",
    "observability", "cannot_do",
]
REQUIRED_INPUTS = {"allowed_sources": list, "freshness_rules": list, "privacy_class": str}
REQUIRED_OUTPUTS = {"artifact_types": list, "delivery_targets": str}
REQUIRED_AUTHORITY = {
    "read": str,
    "local_write": str,
    "external_write": str,
    "code_execution": str,
    "credentials": str,
    "publish_deploy_push": str,
    "destructive": str,
}
REQUIRED_SIDE_EFFECTS = [
    "S0_read_only", "S1_local_write", "S2_external_read", "S3_external_write",
    "S4_publish_deploy_push", "S5_destructive", "S6_payment_credentials", "S7_broad_fanout",
]
REQUIRED_GATES = ["preflight", "evidence", "approval", "rollback", "receipt_readback"]
REQUIRED_RUNTIME = {"model_policy": str, "tool_policy": list, "budget_policy": str, "kill_switch": str}
REQUIRED_OBSERVABILITY = {"receipts": list, "ledgers": list, "health_checks": list}
PRIVACY_CLASSES = {"public", "private", "sensitive", "secret"}
DELIVERY_TARGETS = {"local_only", "exact_allowlist_required"}


def fail(errors: list[str]) -> None:
    print("INVALID_AGENT_TEMPLATE_PROFILE")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)


def require_dict(obj: dict[str, Any], key: str, expected: type, errors: list[str]) -> Any:
    if key not in obj:
        errors.append(f"missing {key}")
        return None
    if not isinstance(obj[key], expected):
        errors.append(f"{key} must be {expected.__name__}")
        return None
    return obj[key]


def validate(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP:
        if key not in profile:
            errors.append(f"missing top-level field {key}")

    for key in ["id", "name", "purpose"]:
        value = profile.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be non-empty string")

    for key in ["source_refs", "capability_graph_refs", "intent_routes", "cannot_do"]:
        value = profile.get(key)
        if not isinstance(value, list) or not all(isinstance(x, str) and x.strip() for x in value):
            errors.append(f"{key} must be list of non-empty strings")

    inputs = require_dict(profile, "inputs", dict, errors) or {}
    for key, typ in REQUIRED_INPUTS.items():
        value = inputs.get(key)
        if not isinstance(value, typ):
            errors.append(f"inputs.{key} must be {typ.__name__}")
    if inputs.get("privacy_class") not in PRIVACY_CLASSES:
        errors.append(f"inputs.privacy_class must be one of {sorted(PRIVACY_CLASSES)}")

    outputs = require_dict(profile, "outputs", dict, errors) or {}
    for key, typ in REQUIRED_OUTPUTS.items():
        value = outputs.get(key)
        if not isinstance(value, typ):
            errors.append(f"outputs.{key} must be {typ.__name__}")
    if outputs.get("delivery_targets") not in DELIVERY_TARGETS:
        errors.append(f"outputs.delivery_targets must be one of {sorted(DELIVERY_TARGETS)}")

    authority = require_dict(profile, "authority", dict, errors) or {}
    for key, typ in REQUIRED_AUTHORITY.items():
        value = authority.get(key)
        if not isinstance(value, typ) or not value.strip():
            errors.append(f"authority.{key} must be non-empty {typ.__name__}")
    if authority.get("credentials") != "never_agent_typed":
        errors.append("authority.credentials must be never_agent_typed")

    side_effects = require_dict(profile, "side_effect_matrix", dict, errors) or {}
    for key in REQUIRED_SIDE_EFFECTS:
        if key not in side_effects:
            errors.append(f"side_effect_matrix missing {key}")
        elif not isinstance(side_effects[key], list):
            errors.append(f"side_effect_matrix.{key} must be list")

    gates = require_dict(profile, "gates", dict, errors) or {}
    for key in REQUIRED_GATES:
        if key not in gates:
            errors.append(f"gates missing {key}")
        elif not isinstance(gates[key], list):
            errors.append(f"gates.{key} must be list")

    runtime = require_dict(profile, "runtime", dict, errors) or {}
    for key, typ in REQUIRED_RUNTIME.items():
        if not isinstance(runtime.get(key), typ):
            errors.append(f"runtime.{key} must be {typ.__name__}")

    observability = require_dict(profile, "observability", dict, errors) or {}
    for key, typ in REQUIRED_OBSERVABILITY.items():
        if not isinstance(observability.get(key), typ):
            errors.append(f"observability.{key} must be {typ.__name__}")

    external_delivery = outputs.get("delivery_targets") == "exact_allowlist_required"
    if external_delivery and not gates.get("receipt_readback"):
        errors.append("gates.receipt_readback is required for exact_allowlist_required delivery")
    if external_delivery and not gates.get("rollback"):
        errors.append("gates.rollback is required for exact_allowlist_required delivery")

    risky_classes = ["S3_external_write", "S4_publish_deploy_push", "S5_destructive", "S6_payment_credentials", "S7_broad_fanout"]
    for klass in risky_classes:
        if side_effects.get(klass) and authority.get("external_write") == "none":
            errors.append(f"{klass} declares side effects but authority.external_write is none")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_agent_template_profile.py <profile.json>")
        return 2
    path = Path(argv[1])
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"INVALID_AGENT_TEMPLATE_PROFILE\n- cannot read JSON: {exc}")
        return 1
    if not isinstance(profile, dict):
        print("INVALID_AGENT_TEMPLATE_PROFILE\n- root must be object")
        return 1
    errors = validate(profile)
    if errors:
        fail(errors)
    print("VALID_AGENT_TEMPLATE_PROFILE")
    print(json.dumps({"path": str(path), "id": profile["id"], "delivery_targets": profile["outputs"]["delivery_targets"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
