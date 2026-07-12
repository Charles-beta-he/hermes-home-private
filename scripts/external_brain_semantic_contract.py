"""Structured semantic-intent contract for the local external brain.

This module deliberately ignores surface text. Text understanding belongs to an
upstream model/calibration step; authority is derived only from a validated,
versioned intent envelope and the capability registry.
"""
import re
from typing import Any, Dict, List, Mapping

SCHEMA_VERSION = "external_brain_semantic_intent_v1"
INTENTS = {"deliver", "investigate", "decide", "evolve", "govern", "observe"}
LEARNING_SCOPES = {"none", "task", "project", "reusable_procedure", "stable_user_preference", "ratchet_candidate"}
SIDE_EFFECTS = {"none", "local_read", "local_write", "external_read", "external_write", "destructive", "payment", "credential_entry", "physical_action", "publish"}
LANES = {"work", "evolution", "advisory"}
MULTIMODEL_MODES = {"auto", "required", "forbidden"}
MULTIMODEL_PURPOSES = {"advisory", "certification"}
CONTENT_PROCESSING = {
    "observe": "evidence_observation",
    "investigate": "source_grounded_investigation",
    "decide": "decision_synthesis",
    "evolve": "capability_evolution",
    "govern": "governance_evaluation",
    "deliver": "delivery_planning",
}


def _is_string_list(value: Any, *, allow_empty: bool) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def validate_capability_registry(registry: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    if not isinstance(registry, Mapping) or registry.get("schema_version") != "external_brain_capability_registry_v1":
        reasons.append("known_capability_registry_schema_required")
    capabilities = registry.get("capabilities") if isinstance(registry, Mapping) else None
    if not isinstance(capabilities, Mapping) or not capabilities:
        reasons.append("nonempty_capability_registry_required")
        return reasons
    for name, raw in capabilities.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(raw, Mapping):
            reasons.append("valid_capability_row_required")
            continue
        if not isinstance(raw.get("brain"), str) or not str(raw.get("brain")).strip():
            reasons.append(f"capability_brain_required:{name}")
        if not _is_string_list(raw.get("allowed_intents"), allow_empty=False) or any(item not in INTENTS for item in raw.get("allowed_intents", [])):
            reasons.append(f"capability_allowed_intents_required:{name}")
        if raw.get("lane") not in LANES:
            reasons.append(f"capability_lane_required:{name}")
        if not _is_string_list(raw.get("task_classes"), allow_empty=False):
            reasons.append(f"capability_task_classes_required:{name}")
        if not _is_string_list(raw.get("brain_profiles"), allow_empty=False):
            reasons.append(f"capability_brain_profiles_required:{name}")
    return sorted(set(reasons))


def _closed(reasons: List[str], *, decision: str = "clarify_or_collect_evidence") -> Dict[str, Any]:
    return {
        "decision": decision,
        "brain": "main",
        "policy": {"may_execute": False, "may_write_learning": False, "content_processing": "evidence_collection"},
        "required_gates": sorted(set(reasons)),
        "semantic_authority": "structured_envelope_only",
    }


def semantic_contract_selfcheck() -> Dict[str, Any]:
    registry = {"schema_version": "external_brain_capability_registry_v1", "capabilities": {"probe": {"brain": "main", "allowed_intents": ["observe"], "lane": "advisory", "task_classes": ["evidence-only"], "brain_profiles": ["main"]}}}
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "intent_class": "observe",
        "domain_capabilities": ["probe"],
        "requested_outcome": "probe",
        "risk_dimensions": [],
        "evidence_requirements": ["probe_evidence"],
        "learning_scope": "none",
        "side_effect_class": "none",
        "confidence": 1.0,
        "source_refs": ["selfcheck"],
        "routing": {"lane": "advisory", "task_class": "evidence-only", "brain_profile": "main"},
        "multimodel": {"mode": "forbidden", "purpose": "advisory", "triggers": []},
    }
    neutral = evaluate_semantic_intent(envelope, registry, surface_text="knowledge solution workflow")
    changed_text = evaluate_semantic_intent(envelope, registry, surface_text="unrelated surface form")
    unsafe = dict(envelope)
    unsafe["side_effect_class"] = "external_write"
    blocked = evaluate_semantic_intent(unsafe, registry, surface_text="harmless wording")
    malformed = []
    for field, value in (
        ("risk_dimensions", "authority"),
        ("requested_outcome", ""),
        ("confidence", True),
        ("source_refs", [""]),
    ):
        candidate = dict(envelope)
        candidate[field] = value
        malformed.append(evaluate_semantic_intent(candidate, registry))
    malformed_blocked = all(item.get("decision") != "route" for item in malformed)
    passed = (
        neutral == changed_text
        and neutral.get("decision") == "route"
        and blocked.get("decision") == "authority_blocked"
        and malformed_blocked
        and not validate_capability_registry(registry)
    )
    return {"status": "PASS" if passed else "FAIL", "surface_text_invariant": neutral == changed_text, "unsafe_blocked": blocked.get("decision") == "authority_blocked", "malformed_blocked": malformed_blocked, "registry_valid": not validate_capability_registry(registry)}


def evaluate_semantic_intent(
    envelope: Mapping[str, Any], registry: Mapping[str, Any], *, surface_text: str = ""
) -> Dict[str, Any]:
    """Validate and project a semantic envelope; ``surface_text`` has no authority."""
    required = {
        "schema_version", "intent_class", "domain_capabilities", "requested_outcome",
        "risk_dimensions", "evidence_requirements", "learning_scope", "side_effect_class",
        "confidence", "source_refs", "routing", "multimodel",
    }
    if not isinstance(envelope, Mapping) or required - set(envelope):
        return _closed(["valid_semantic_intent_required"])
    registry_reasons = validate_capability_registry(registry)
    if registry_reasons:
        return _closed(registry_reasons)
    intent = str(envelope.get("intent_class") or "")
    learning = str(envelope.get("learning_scope") or "")
    side_effect = str(envelope.get("side_effect_class") or "")
    outcome = envelope.get("requested_outcome")
    capabilities = envelope.get("domain_capabilities")
    risks = envelope.get("risk_dimensions")
    evidence = envelope.get("evidence_requirements")
    sources = envelope.get("source_refs")
    concept_refs = envelope.get("concept_refs", [])
    confidence = envelope.get("confidence")
    if not isinstance(outcome, str) or not outcome.strip():
        return _closed(["requested_outcome_required"])
    if not _is_string_list(capabilities, allow_empty=False) or not _is_string_list(risks, allow_empty=True):
        return _closed(["semantic_string_list_contract"])
    risk_list: List[str] = [str(item) for item in risks] if isinstance(risks, list) else []
    if not _is_string_list(evidence, allow_empty=False) or not _is_string_list(sources, allow_empty=False):
        return _closed(["evidence_contract_required"])
    if (
        not _is_string_list(concept_refs, allow_empty=True)
        or len(concept_refs) > 12
        or len(set(concept_refs)) != len(concept_refs)
        or any(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}", item) is None for item in concept_refs)
    ):
        return _closed(["concept_refs_contract"])
    if envelope.get("schema_version") != SCHEMA_VERSION or intent not in INTENTS:
        return _closed(["known_schema_and_intent_required"])
    if learning not in LEARNING_SCOPES or side_effect not in SIDE_EFFECTS:
        return _closed(["known_learning_and_side_effect_class_required"])
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or confidence < 0.65 or confidence > 1:
        return _closed(["semantic_confidence_gate"])
    capability_map = registry.get("capabilities") if isinstance(registry, Mapping) else None
    if not isinstance(capabilities, list) or not capabilities or not isinstance(capability_map, Mapping):
        return _closed(["known_capability_required"])
    raw_rows = [capability_map.get(str(item)) for item in capabilities]
    if any(not isinstance(row, Mapping) for row in raw_rows):
        return _closed(["known_capability_required"])
    rows: List[Mapping[str, Any]] = [row for row in raw_rows if isinstance(row, Mapping)]
    if any(intent not in row.get("allowed_intents", []) for row in rows):
        return _closed(["capability_intent_contract"])
    brains = {str(row.get("brain") or "main") for row in rows}
    if len(brains) != 1:
        return _closed(["multi_brain_arbitration_required"])
    routing = envelope.get("routing")
    multimodel = envelope.get("multimodel")
    if not isinstance(routing, Mapping) or not isinstance(multimodel, Mapping):
        return _closed(["routing_and_multimodel_contract_required"])
    if not all(isinstance(routing.get(key), str) and bool(str(routing.get(key)).strip()) for key in ("lane", "task_class", "brain_profile")):
        return _closed(["routing_string_contract"])
    lane = str(routing.get("lane"))
    task_class = str(routing.get("task_class"))
    brain_profile = str(routing.get("brain_profile"))
    if lane not in LANES or any(str(row.get("lane") or "") != lane for row in rows):
        return _closed(["capability_lane_contract"])
    if not task_class or any(task_class not in row.get("task_classes", []) for row in rows):
        return _closed(["capability_task_class_contract"])
    if not brain_profile or any(brain_profile not in row.get("brain_profiles", []) for row in rows):
        return _closed(["capability_brain_profile_contract"])
    mm_mode = str(multimodel.get("mode") or "")
    mm_purpose = str(multimodel.get("purpose") or "")
    mm_triggers = multimodel.get("triggers")
    if (
        not isinstance(multimodel.get("mode"), str)
        or not isinstance(multimodel.get("purpose"), str)
        or mm_mode not in MULTIMODEL_MODES
        or mm_purpose not in MULTIMODEL_PURPOSES
        or not _is_string_list(mm_triggers, allow_empty=True)
    ):
        return _closed(["multimodel_contract"])
    mm_triggers_list: List[str] = [str(item) for item in mm_triggers] if isinstance(mm_triggers, list) else []
    if side_effect in {"external_write", "destructive", "payment", "credential_entry", "physical_action", "publish"}:
        return _closed(["exact_authority_grant"], decision="authority_blocked")

    gates = list(evidence) if isinstance(evidence, list) else []
    may_execute = intent == "deliver" and side_effect in {"none", "local_read", "local_write"}
    may_write_learning = learning in {"task", "project"}
    if learning in {"reusable_procedure", "stable_user_preference", "ratchet_candidate"}:
        gates.extend(["repeated_evidence", "writeback_classifier"])
        may_write_learning = False
    return {
        "decision": "route",
        "brain": next(iter(brains)),
        "policy": {
            "may_execute": may_execute,
            "may_write_learning": may_write_learning,
            "content_processing": CONTENT_PROCESSING[intent],
            "learning_scope": learning,
            "side_effect_class": side_effect,
        },
        "routing": {"lane": lane, "task_class": task_class, "brain_profile": brain_profile},
        "risk_dimensions": risk_list,
        "multimodel": {
            "mode": mm_mode,
            "purpose": mm_purpose,
            "triggers": mm_triggers_list,
            "required": mm_mode == "required",
        },
        "required_gates": sorted(set(str(item) for item in gates)),
        "semantic_authority": "structured_envelope_only",
    }
