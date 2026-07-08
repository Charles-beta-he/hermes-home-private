"""Local-only Ego-NeuroLoop loop-core contract helpers.

This module is deterministic scaffolding for the HEWOS looped-latent contract.
It is not an ML world model and does not execute external, hardware, credential,
payment, deploy, or destructive actions.
"""

from copy import deepcopy

from .contracts import ContractError, EXECUTABLE_RISK_CLASSES, validate_action_intent


RECEIPT_SCHEMA = "ego_neuroloop_core_receipt_v0"
EXIT_STABLE = "stable"
EXIT_BUDGET_EXHAUSTED = "budget_exhausted"
EXIT_RISK_GATE = "risk_gate"
EXIT_HUMAN_GATE = "human_gate"
EXIT_ERROR = "error"

SIDE_EFFECT_FLAGS = {
    "external_dispatch": False,
    "hardware_actuation": False,
    "credential_entry": False,
    "payment": False,
    "destructive_operation": False,
}

RISK_RANK = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "blocked": 3,
    "external_write": 3,
    "physical_action": 3,
    "publish": 3,
    "destructive": 3,
    "payment_or_credential": 3,
}


class LoopCoreError(ContractError):
    """Raised when loop-core inputs violate the local contract."""


def _risk_rank(value):
    return RISK_RANK.get(value, 2)


def _max_risk(a, b):
    return a if _risk_rank(a) >= _risk_rank(b) else b


def _require_neuro_state(neuro_state):
    if not isinstance(neuro_state, dict):
        raise LoopCoreError("neuro_state must be an object")
    if not neuro_state.get("evidence_refs"):
        raise LoopCoreError("neuro_state evidence_refs must be non-empty")
    confidence = neuro_state.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise LoopCoreError("neuro_state confidence must be a number between 0 and 1")
    uncertainty = neuro_state.get("uncertainty", 1 - confidence)
    if not isinstance(uncertainty, (int, float)) or not 0 <= uncertainty <= 1:
        raise LoopCoreError("neuro_state uncertainty must be a number between 0 and 1")
    return deepcopy(neuro_state)


def _safe_predicted_state(state, intent, loop_count):
    derived = deepcopy(state.get("derived", {}))
    return {
        "basis": "fixture_contract_projection",
        "source_state_id": state.get("state_id"),
        "intent_id": intent.get("intent_id"),
        "verb": intent.get("verb"),
        "target": deepcopy(intent.get("target")),
        "derived": derived,
        "loop_count": loop_count,
        "prediction_status": "prediction_not_evidence",
    }


def _deferred_decode(predicted_next_state, risk_level, exit_reason):
    if exit_reason in {EXIT_RISK_GATE, EXIT_HUMAN_GATE}:
        action = "blocked_pending_authority_or_risk_review"
    elif exit_reason == EXIT_BUDGET_EXHAUSTED:
        action = "return_cautious_prediction_with_known_limits"
    elif risk_level == "low":
        action = "recommend_low_risk_next_step"
    else:
        action = "recommend_review_before_action"
    return {
        "surface": "task_candidate" if exit_reason in {EXIT_RISK_GATE, EXIT_HUMAN_GATE} else "user_text",
        "recommended_action": action,
        "label": "prediction_not_verified_fact",
        "summary": f"{predicted_next_state.get('verb')} -> {predicted_next_state.get('prediction_status')}",
    }


def run_loop_core(
    neuro_state,
    action_intent,
    *,
    loop_budget=3,
    stable_delta_threshold=0.05,
    confidence_threshold=0.8,
    risk_policy=None,
):
    """Run a deterministic local loop-core contract and return a receipt.

    The loop monotonically reduces synthetic uncertainty to prove the contract
    shape: adaptive early exit, budget exhaustion, risk handoff, and deferred
    decode labels. It never enables side-effect flags.
    """

    risk_policy = dict(risk_policy or {})
    try:
        state = _require_neuro_state(neuro_state)
        intent = validate_action_intent(action_intent)
        if not isinstance(loop_budget, int) or loop_budget < 1:
            raise LoopCoreError("loop_budget must be a positive integer")
        if not 0 <= stable_delta_threshold <= 1:
            raise LoopCoreError("stable_delta_threshold must be between 0 and 1")
        if not 0 <= confidence_threshold <= 1:
            raise LoopCoreError("confidence_threshold must be between 0 and 1")
    except ContractError as exc:
        return build_loop_receipt(
            input_refs=[],
            action_intent_id=action_intent.get("intent_id") if isinstance(action_intent, dict) else None,
            loop_budget=loop_budget if isinstance(loop_budget, int) else 0,
            loop_count=0,
            exit_reason=EXIT_ERROR,
            state_delta=None,
            confidence=None,
            risk_level="blocked",
            predicted_next_state={},
            decoded={"surface": "none", "recommended_action": None, "label": "invalid_contract"},
            evidence_refs=[],
            known_limits=[str(exc)],
        )

    evidence_refs = list(dict.fromkeys(state.get("evidence_refs", []) + intent.get("evidence_refs", [])))
    risk_level = _max_risk(state.get("risk_level", "medium"), intent.get("risk_level", "medium"))
    requested_authority = set(intent.get("requested_authority") or [])
    force_human = bool(requested_authority - {"local_read", "local_test", "local_projection"})
    force_risk = intent.get("risk_level") in EXECUTABLE_RISK_CLASSES or risk_policy.get("force_high_risk_handoff")

    loop_count = 0
    state_delta = state.get("uncertainty", 1 - state.get("confidence", 0))
    confidence = state.get("confidence", 0)
    contradiction = bool(state.get("contradictions"))
    exit_reason = EXIT_BUDGET_EXHAUSTED

    if force_human:
        exit_reason = EXIT_HUMAN_GATE
        risk_level = "blocked"
    elif force_risk:
        exit_reason = EXIT_RISK_GATE
        risk_level = "blocked"
    else:
        for i in range(1, loop_budget + 1):
            loop_count = i
            state_delta = max(0.0, state_delta * 0.5)
            confidence = min(1.0, confidence + 0.18)
            if contradiction:
                risk_level = _max_risk(risk_level, "high")
                continue
            if state_delta <= stable_delta_threshold and confidence >= confidence_threshold:
                exit_reason = EXIT_STABLE
                break

    predicted = _safe_predicted_state(state, intent, loop_count)
    decoded = _deferred_decode(predicted, risk_level, exit_reason)
    known_limits = []
    if contradiction:
        known_limits.append("input_state_contains_contradictions")
    if exit_reason == EXIT_BUDGET_EXHAUSTED:
        known_limits.append("loop_budget_exhausted_before_stability")
    if exit_reason in {EXIT_RISK_GATE, EXIT_HUMAN_GATE}:
        known_limits.append("side_effect_or_authority_boundary_not_opened")

    return build_loop_receipt(
        input_refs=evidence_refs,
        action_intent_id=intent.get("intent_id"),
        loop_budget=loop_budget,
        loop_count=loop_count,
        exit_reason=exit_reason,
        state_delta=round(state_delta, 6) if isinstance(state_delta, (int, float)) else None,
        confidence=round(confidence, 6) if isinstance(confidence, (int, float)) else None,
        risk_level=risk_level,
        predicted_next_state=predicted,
        decoded=decoded,
        evidence_refs=evidence_refs,
        known_limits=known_limits,
    )


def build_loop_receipt(
    *,
    input_refs,
    action_intent_id,
    loop_budget,
    loop_count,
    exit_reason,
    state_delta,
    confidence,
    risk_level,
    predicted_next_state,
    decoded,
    evidence_refs,
    known_limits,
):
    return {
        "schema": RECEIPT_SCHEMA,
        "project": "hermes-embodied-workflow-os",
        "mode": "runtime_mock",
        "input_refs": list(input_refs),
        "action_intent_id": action_intent_id,
        "loop_budget": loop_budget,
        "loop_count": loop_count,
        "exit_reason": exit_reason,
        "state_delta": state_delta,
        "confidence": confidence,
        "risk_level": risk_level,
        "predicted_next_state": deepcopy(predicted_next_state),
        "recommended_action": decoded.get("recommended_action"),
        "deferred_decode_surface": decoded.get("surface", "none"),
        "deferred_decode_label": decoded.get("label"),
        "boundary_flags": dict(SIDE_EFFECT_FLAGS),
        "evidence_refs": list(evidence_refs),
        "known_limits": list(known_limits),
    }


def assert_no_side_effect_flags(receipt):
    flags = receipt.get("boundary_flags") or {}
    if any(flags.values()):
        raise LoopCoreError("loop-core receipt must keep all side-effect flags false")
    return True
