#!/usr/bin/env python3
"""Fail-closed structural validator for Scientific Inquiry packet schema 1.2.

This validates shape, enums, provenance fields, and cross-references only. It
does not certify truth, experimental validity, evidence authenticity, freshness
in the outside world, or authority.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ALLOWED_MODES = {"lite", "standard", "strong_inference", "meta_synthesis", "architecture_escalation"}
MIN_HYPOTHESES = {
    "lite": 1,
    "standard": 2,
    "strong_inference": 3,
    "meta_synthesis": 2,
    "architecture_escalation": 2,
}
ALLOWED_HYPOTHESIS_STATES = {
    "unsupported", "weakened", "still_live", "leading", "strongly_supported", "falsified"
}
ALLOWED_UPDATE_DIRECTIONS = {"strengthened", "weakened", "unchanged", "falsified", "reframed"}
ALLOWED_PROBE_RESULTS = {"not_run", "valid_result", "invalid_probe", "blocked"}
ALLOWED_EVIDENCE_SOURCE_TYPES = {
    "command", "file", "api", "log", "screenshot", "primary_source", "reported"
}
ALLOWED_EVIDENCE_STATUSES = {"verified", "reported", "inferred"}
ALLOWED_FRESHNESS = {"fresh", "historical"}
ALLOWED_CLOSURE_STATES = {
    "ratified", "provisional", "inconclusive", "falsified", "blocked", "reframed"
}


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: object) -> bool:
    return isinstance(value, list) and all(nonempty(item) for item in value)


def valid_iso8601(value: object) -> bool:
    if not nonempty(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate(packet: dict) -> list[str]:
    errors: list[str] = []
    required_top = [
        "schema_version", "inquiry_id", "mode", "problem", "baseline",
        "hypotheses", "probes", "evidence_ledger", "evidence_updates",
        "intervention", "reproduction", "closure",
    ]
    for key in required_top:
        if key not in packet:
            errors.append(f"missing top-level field: {key}")

    if packet.get("schema_version") != "1.2":
        errors.append(f"unsupported schema_version: {packet.get('schema_version')!r}")
    if not nonempty(packet.get("inquiry_id")):
        errors.append("inquiry_id must be non-empty")

    mode = packet.get("mode")
    if mode not in ALLOWED_MODES:
        errors.append(f"invalid mode: {mode!r}")
    mode_key = mode if isinstance(mode, str) else ""

    problem = packet.get("problem", {})
    if not isinstance(problem, dict):
        errors.append("problem must be an object")
        problem = {}
    else:
        for key in ("question", "decision_at_stake", "scope", "authority_boundary"):
            if not nonempty(problem.get(key)):
                errors.append(f"problem.{key} must be non-empty")
        for key in ("non_goals", "constraints"):
            if not isinstance(problem.get(key), list):
                errors.append(f"problem.{key} must be a list")

    baseline = packet.get("baseline", {})
    if not isinstance(baseline, dict):
        errors.append("baseline must be an object")
        baseline = {}
    else:
        for key in ("verified", "reported", "inferred", "missing"):
            if not isinstance(baseline.get(key), list):
                errors.append(f"baseline.{key} must be a list")

    hypotheses = packet.get("hypotheses", [])
    if not isinstance(hypotheses, list) or not hypotheses:
        errors.append("hypotheses must be a non-empty list")
        hypotheses = []
    minimum = MIN_HYPOTHESES.get(mode_key)
    if minimum is not None and len(hypotheses) < minimum:
        errors.append(f"mode {mode_key} requires at least {minimum} hypotheses")
    if mode_key == "lite" and len(hypotheses) == 1 and not nonempty(problem.get("hypothesis_space_constraint")):
        errors.append("problem.hypothesis_space_constraint must justify Lite single-hypothesis mode")

    hypothesis_ids: set[str] = set()
    hypothesis_prediction_refs: list[tuple[str, list[object]]] = []
    hypothesis_status: dict[str, object] = {}
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
            hypothesis_status[hypothesis_id] = item.get("status")
        for key in ("claim", "mechanism", "falsifier"):
            if not nonempty(item.get(key)):
                errors.append(f"{prefix}.{key} must be non-empty")
        for key in ("assumptions", "applies_when", "anti_conditions"):
            if not isinstance(item.get(key), list):
                errors.append(f"{prefix}.{key} must be a list")
        predictions = item.get("predictions")
        if not string_list(predictions) or not predictions:
            errors.append(f"{prefix}.predictions must be a non-empty string list")
        else:
            hypothesis_prediction_refs.append((prefix, predictions))
        if item.get("status") not in ALLOWED_HYPOTHESIS_STATES:
            errors.append(f"{prefix}.status is invalid")

    probes = packet.get("probes", [])
    if not isinstance(probes, list) or not probes:
        errors.append("probes must be a non-empty list")
        probes = []
    probe_ids: set[str] = set()
    probe_result_by_id: dict[str, object] = {}
    for index, probe in enumerate(probes):
        prefix = f"probes[{index}]"
        if not isinstance(probe, dict):
            errors.append(f"{prefix} must be an object")
            continue
        probe_id = probe.get("id")
        if not nonempty(probe_id):
            errors.append(f"{prefix}.id must be non-empty")
        elif probe_id in probe_ids:
            errors.append(f"duplicate probe id: {probe_id}")
        else:
            probe_ids.add(probe_id)
            probe_result_by_id[probe_id] = probe.get("result")
        for key in ("question", "target_variable", "stop_condition", "rollback", "evidence_artifact"):
            if not nonempty(probe.get(key)):
                errors.append(f"{prefix}.{key} must be non-empty")
        if not isinstance(probe.get("controlled_variables"), list):
            errors.append(f"{prefix}.controlled_variables must be a list")
        exact_context = probe.get("exact_context")
        if not isinstance(exact_context, dict):
            errors.append(f"{prefix}.exact_context must be an object")
        else:
            for key in ("artifact", "version", "environment", "input"):
                if not nonempty(exact_context.get(key)):
                    errors.append(f"{prefix}.exact_context.{key} must be non-empty")
        if not isinstance(probe.get("validity_threats"), list):
            errors.append(f"{prefix}.validity_threats must be a list")
        if probe.get("result") not in ALLOWED_PROBE_RESULTS:
            errors.append(f"{prefix}.result is invalid")

    for prefix, predictions in hypothesis_prediction_refs:
        unknown = set(predictions) - probe_ids
        if unknown:
            errors.append(f"{prefix}.predictions references unknown probes: {sorted(unknown)}")

    live_hypothesis_ids = {
        hypothesis_id for hypothesis_id, status in hypothesis_status.items() if status != "falsified"
    }
    discriminating_probe_found = False
    for index, probe in enumerate(probes):
        if not isinstance(probe, dict):
            continue
        prefix = f"probes[{index}]"
        predicted_results = probe.get("predicted_results")
        if not isinstance(predicted_results, dict):
            errors.append(f"{prefix}.predicted_results must be an object")
            continue
        keys = set(predicted_results)
        if keys != live_hypothesis_ids:
            errors.append(
                f"{prefix}.predicted_results must exactly cover live hypotheses: "
                f"expected {sorted(live_hypothesis_ids)}, got {sorted(keys)}"
            )
        for hypothesis_id, value in predicted_results.items():
            if not nonempty(value):
                errors.append(f"{prefix}.predicted_results[{hypothesis_id!r}] must be non-empty")
        values = [value.strip() for value in predicted_results.values() if nonempty(value)]
        if len(set(values)) >= 2:
            discriminating_probe_found = True
    if len(live_hypothesis_ids) >= 2 and probes and not discriminating_probe_found:
        errors.append("no probe has at least two distinct predicted results; probes do not discriminate")

    evidence_ledger = packet.get("evidence_ledger")
    evidence_ids: set[str] = set()
    evidence_by_id: dict[str, dict] = {}
    if not isinstance(evidence_ledger, list) or not evidence_ledger:
        errors.append("evidence_ledger must be a non-empty list")
        evidence_ledger = []
    for index, item in enumerate(evidence_ledger):
        prefix = f"evidence_ledger[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        evidence_id = item.get("id")
        if not nonempty(evidence_id):
            errors.append(f"{prefix}.id must be non-empty")
        elif evidence_id in evidence_ids:
            errors.append(f"duplicate evidence id: {evidence_id}")
        else:
            evidence_ids.add(evidence_id)
            evidence_by_id[evidence_id] = item
        claim_ids = item.get("claim_ids")
        if not string_list(claim_ids) or not claim_ids:
            errors.append(f"{prefix}.claim_ids must be a non-empty string list")
        else:
            unknown = set(claim_ids) - hypothesis_ids
            if unknown:
                errors.append(f"{prefix}.claim_ids has unknown hypotheses: {sorted(unknown)}")
        if item.get("probe_id") not in probe_ids:
            errors.append(f"{prefix}.probe_id references an unknown probe")
        if item.get("source_type") not in ALLOWED_EVIDENCE_SOURCE_TYPES:
            errors.append(f"{prefix}.source_type is invalid")
        for key in ("source_ref", "scope", "result"):
            if not nonempty(item.get(key)):
                errors.append(f"{prefix}.{key} must be non-empty")
        if not valid_iso8601(item.get("observed_at")):
            errors.append(f"{prefix}.observed_at must be ISO-8601")
        if item.get("freshness") not in ALLOWED_FRESHNESS:
            errors.append(f"{prefix}.freshness is invalid")
        if item.get("status") not in ALLOWED_EVIDENCE_STATUSES:
            errors.append(f"{prefix}.status is invalid")

    for key, expected_status in (("verified", "verified"), ("reported", "reported"), ("inferred", "inferred")):
        refs = baseline.get(key)
        if isinstance(refs, list):
            unknown = {ref for ref in refs if ref not in evidence_ids}
            if unknown:
                errors.append(f"baseline.{key} has unknown evidence ids: {sorted(unknown)}")
            wrong = {ref for ref in refs if ref in evidence_by_id and evidence_by_id[ref].get("status") != expected_status}
            if wrong:
                errors.append(f"baseline.{key} references evidence with the wrong status: {sorted(wrong)}")
    missing = baseline.get("missing")
    if isinstance(missing, list) and not all(nonempty(item) for item in missing):
        errors.append("baseline.missing entries must be non-empty")

    evidence_updates = packet.get("evidence_updates")
    if not isinstance(evidence_updates, list):
        errors.append("evidence_updates must be a list")
    else:
        for index, update in enumerate(evidence_updates):
            prefix = f"evidence_updates[{index}]"
            if not isinstance(update, dict):
                errors.append(f"{prefix} must be an object")
                continue
            update_probe_id = update.get("probe_id")
            if update_probe_id not in probe_ids:
                errors.append(f"{prefix}.probe_id references an unknown probe")
            elif probe_result_by_id.get(update_probe_id) != "valid_result":
                errors.append(f"{prefix} cannot update hypotheses from a non-valid probe")
            update_evidence_ids = update.get("evidence_ids")
            if not string_list(update_evidence_ids) or not update_evidence_ids:
                errors.append(f"{prefix}.evidence_ids must be a non-empty string list")
            else:
                unknown = set(update_evidence_ids) - evidence_ids
                if unknown:
                    errors.append(f"{prefix}.evidence_ids has unknown evidence ids: {sorted(unknown)}")
                mismatched = {
                    evidence_id for evidence_id in update_evidence_ids
                    if evidence_id in evidence_by_id
                    and evidence_by_id[evidence_id].get("probe_id") != update_probe_id
                }
                if mismatched:
                    errors.append(
                        f"{prefix} references evidence from a different probe: {sorted(mismatched)}"
                    )
            if not nonempty(update.get("observed")):
                errors.append(f"{prefix}.observed must be non-empty")
            updates = update.get("updates")
            if not isinstance(updates, dict) or not updates:
                errors.append(f"{prefix}.updates must be a non-empty object")
            else:
                unknown = set(updates) - hypothesis_ids
                if unknown:
                    errors.append(f"{prefix}.updates has unknown hypotheses: {sorted(unknown)}")
                for hypothesis_id, direction in updates.items():
                    if direction not in ALLOWED_UPDATE_DIRECTIONS:
                        errors.append(f"{prefix}.updates[{hypothesis_id!r}] is invalid")
                if string_list(update_evidence_ids):
                    covered_claims = {
                        claim_id
                        for evidence_id in update_evidence_ids
                        if evidence_id in evidence_by_id
                        for claim_id in evidence_by_id[evidence_id].get("claim_ids", [])
                        if isinstance(claim_id, str)
                    }
                    uncovered = set(updates) - covered_claims
                    if uncovered:
                        errors.append(
                            f"{prefix} has updated hypotheses not covered by evidence: {sorted(uncovered)}"
                        )
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
    reproduction_evidence_ids: list[str] = []
    if not isinstance(reproduction, dict):
        errors.append("reproduction must be an object")
    else:
        for key in ("baseline_failure", "focused_success", "independent_readback", "strongest_counterexample"):
            if not nonempty(reproduction.get(key)):
                errors.append(f"reproduction.{key} must be non-empty")
        if not isinstance(reproduction.get("negative_tests"), list):
            errors.append("reproduction.negative_tests must be a list")
        refs = reproduction.get("evidence_ids")
        if not string_list(refs) or not refs:
            errors.append("reproduction.evidence_ids must be a non-empty list")
        else:
            reproduction_evidence_ids = refs
            unknown = set(refs) - evidence_ids
            if unknown:
                errors.append(f"reproduction.evidence_ids has unknown evidence ids: {sorted(unknown)}")

    closure = packet.get("closure", {})
    closure_state = None
    supported_claim_ids: list[str] = []
    if not isinstance(closure, dict):
        errors.append("closure must be an object")
    else:
        closure_state = closure.get("state")
        if closure_state not in ALLOWED_CLOSURE_STATES:
            errors.append(f"invalid closure.state: {closure_state!r}")
        for key in ("supported_claims", "remaining_alternatives", "known_limits"):
            if not isinstance(closure.get(key), list):
                errors.append(f"closure.{key} must be a list")
        claim_refs = closure.get("supported_claim_ids")
        if not string_list(claim_refs):
            errors.append("closure.supported_claim_ids must be a string list")
        else:
            supported_claim_ids = claim_refs
            if len(set(claim_refs)) != len(claim_refs):
                errors.append("closure.supported_claim_ids must contain unique values")
            unknown = set(claim_refs) - hypothesis_ids
            if unknown:
                errors.append(f"closure.supported_claim_ids has unknown hypotheses: {sorted(unknown)}")
        if not nonempty(closure.get("next_discriminating_probe")):
            errors.append("closure.next_discriminating_probe must be non-empty")
        writeback = closure.get("writeback")
        if not isinstance(writeback, dict):
            errors.append("closure.writeback must be an object")
        else:
            for key in ("landing_zone", "falsifier", "demotion_path"):
                if not nonempty(writeback.get(key)):
                    errors.append(f"closure.writeback.{key} must be non-empty")
            for key in ("applicability", "anti_conditions"):
                if not isinstance(writeback.get(key), list):
                    errors.append(f"closure.writeback.{key} must be a list")

    if closure_state == "ratified":
        if not supported_claim_ids:
            errors.append("ratified closure requires non-empty supported_claim_ids")
        qualifying_reproduction = [
            evidence_by_id[evidence_id]
            for evidence_id in reproduction_evidence_ids
            if evidence_id in evidence_by_id
            and evidence_by_id[evidence_id].get("status") == "verified"
            and evidence_by_id[evidence_id].get("freshness") == "fresh"
            and probe_result_by_id.get(evidence_by_id[evidence_id].get("probe_id")) == "valid_result"
        ]
        if not qualifying_reproduction:
            errors.append("ratified closure requires fresh verified reproduction evidence from a valid probe")
        uncovered_supported_claims = {
            claim_id for claim_id in supported_claim_ids
            if not any(claim_id in item.get("claim_ids", []) for item in qualifying_reproduction)
        }
        if uncovered_supported_claims:
            errors.append(
                "ratified supported claims lack qualifying reproduction evidence: "
                f"{sorted(uncovered_supported_claims)}"
            )

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
