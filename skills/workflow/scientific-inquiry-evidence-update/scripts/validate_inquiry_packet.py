#!/usr/bin/env python3
"""Structural validator for Scientific Inquiry packets.

This validates completeness and cross-references only. It does not certify truth,
experimental validity, evidence authenticity, or authority.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_MODES = {"lite", "standard", "strong_inference", "meta_synthesis", "architecture_escalation"}
ALLOWED_HYPOTHESIS_STATES = {
    "unsupported", "weakened", "still_live", "leading", "strongly_supported", "falsified"
}
ALLOWED_CLOSURE_STATES = {
    "ratified", "provisional", "inconclusive", "falsified", "blocked", "reframed"
}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(packet: dict) -> list[str]:
    errors: list[str] = []
    required_top = [
        "schema_version", "inquiry_id", "mode", "problem", "baseline",
        "hypotheses", "probes", "evidence_updates", "intervention",
        "reproduction", "closure",
    ]
    for key in required_top:
        if key not in packet:
            errors.append(f"missing top-level field: {key}")

    if packet.get("schema_version") != "1.0":
        errors.append(f"unsupported schema_version: {packet.get('schema_version')!r}")
    if not nonempty(packet.get("inquiry_id")):
        errors.append("inquiry_id must be non-empty")

    mode = packet.get("mode")
    if mode not in ALLOWED_MODES:
        errors.append(f"invalid mode: {mode!r}")

    problem = packet.get("problem", {})
    if not isinstance(problem, dict):
        errors.append("problem must be an object")
    else:
        for key in ("question", "decision_at_stake", "scope", "authority_boundary"):
            if not nonempty(problem.get(key)):
                errors.append(f"problem.{key} must be non-empty")

    baseline = packet.get("baseline", {})
    if not isinstance(baseline, dict):
        errors.append("baseline must be an object")
    else:
        for key in ("verified", "reported", "inferred", "missing"):
            if not isinstance(baseline.get(key), list):
                errors.append(f"baseline.{key} must be a list")

    hypotheses = packet.get("hypotheses", [])
    if not isinstance(hypotheses, list) or not hypotheses:
        errors.append("hypotheses must be a non-empty list")
        hypotheses = []
    if mode != "lite" and len(hypotheses) < 2:
        errors.append("standard or stronger modes require at least two hypotheses")

    hypothesis_ids: set[str] = set()
    for index, item in enumerate(hypotheses):
        prefix = f"hypotheses[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        hypothesis_id = item.get("id")
        if not nonempty(hypothesis_id):
            errors.append(f"{prefix}.id must be non-empty")
        elif hypothesis_id in hypothesis_ids:
            errors.append(f"duplicate hypothesis id: {hypothesis_id}")
        else:
            hypothesis_ids.add(hypothesis_id)
        for key in ("claim", "mechanism", "falsifier"):
            if not nonempty(item.get(key)):
                errors.append(f"{prefix}.{key} must be non-empty")
        for key in ("assumptions", "applies_when", "anti_conditions"):
            if not isinstance(item.get(key), list):
                errors.append(f"{prefix}.{key} must be a list")
        predictions = item.get("predictions")
        if not isinstance(predictions, list) or not predictions:
            errors.append(f"{prefix}.predictions must be a non-empty list")
        if item.get("status") not in ALLOWED_HYPOTHESIS_STATES:
            errors.append(f"{prefix}.status is invalid")

    probes = packet.get("probes", [])
    if not isinstance(probes, list) or not probes:
        errors.append("probes must be a non-empty list")
        probes = []
    discriminating_probe_found = False
    for index, probe in enumerate(probes):
        prefix = f"probes[{index}]"
        if not isinstance(probe, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("id", "question", "target_variable", "stop_condition", "rollback", "evidence_artifact"):
            if not nonempty(probe.get(key)):
                errors.append(f"{prefix}.{key} must be non-empty")
        exact_context = probe.get("exact_context")
        if not isinstance(exact_context, dict):
            errors.append(f"{prefix}.exact_context must be an object")
        else:
            for key in ("artifact", "version", "environment", "input"):
                if not nonempty(exact_context.get(key)):
                    errors.append(f"{prefix}.exact_context.{key} must be non-empty")
        predictions = probe.get("predicted_results")
        if not isinstance(predictions, dict):
            errors.append(f"{prefix}.predicted_results must be an object")
        else:
            unknown = set(predictions) - hypothesis_ids
            if unknown:
                errors.append(f"{prefix}.predicted_results has unknown hypotheses: {sorted(unknown)}")
            values = [str(value).strip() for value in predictions.values() if str(value).strip()]
            if len(set(values)) >= 2:
                discriminating_probe_found = True
        if not isinstance(probe.get("validity_threats"), list):
            errors.append(f"{prefix}.validity_threats must be a list")
    if hypotheses and probes and not discriminating_probe_found:
        errors.append("no probe has at least two distinct predicted results; probes do not discriminate")

    evidence_updates = packet.get("evidence_updates")
    if not isinstance(evidence_updates, list):
        errors.append("evidence_updates must be a list")
    else:
        probe_ids = {probe.get("id") for probe in probes if isinstance(probe, dict)}
        for index, update in enumerate(evidence_updates):
            prefix = f"evidence_updates[{index}]"
            if not isinstance(update, dict):
                errors.append(f"{prefix} must be an object")
                continue
            if update.get("probe_id") not in probe_ids:
                errors.append(f"{prefix}.probe_id references an unknown probe")
            if not nonempty(update.get("observed")):
                errors.append(f"{prefix}.observed must be non-empty")
            if not isinstance(update.get("updates"), dict):
                errors.append(f"{prefix}.updates must be an object")
            if not isinstance(update.get("limits"), list):
                errors.append(f"{prefix}.limits must be a list")

    intervention = packet.get("intervention", {})
    if not isinstance(intervention, dict):
        errors.append("intervention must be an object")
    else:
        for key in ("decision", "targeted_mechanism", "reversibility", "separate_authority_gate"):
            if not nonempty(intervention.get(key)):
                errors.append(f"intervention.{key} must be non-empty")
        if not isinstance(intervention.get("verification"), list):
            errors.append("intervention.verification must be a list")

    reproduction = packet.get("reproduction", {})
    if not isinstance(reproduction, dict):
        errors.append("reproduction must be an object")
    else:
        for key in ("baseline_failure", "focused_success", "independent_readback", "strongest_counterexample"):
            if not nonempty(reproduction.get(key)):
                errors.append(f"reproduction.{key} must be non-empty")
        if not isinstance(reproduction.get("negative_tests"), list):
            errors.append("reproduction.negative_tests must be a list")

    closure = packet.get("closure", {})
    if not isinstance(closure, dict):
        errors.append("closure must be an object")
    elif closure.get("state") not in ALLOWED_CLOSURE_STATES:
        errors.append(f"invalid closure.state: {closure.get('state')!r}")
    else:
        for key in ("supported_claims", "remaining_alternatives", "known_limits"):
            if not isinstance(closure.get(key), list):
                errors.append(f"closure.{key} must be a list")
        if not nonempty(closure.get("next_discriminating_probe")):
            errors.append("closure.next_discriminating_probe must be non-empty")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_inquiry_packet.py <packet.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    if not isinstance(packet, dict):
        print(json.dumps({"ok": False, "errors": ["packet root must be an object"]}, ensure_ascii=False, indent=2))
        return 1
    errors = validate(packet)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
