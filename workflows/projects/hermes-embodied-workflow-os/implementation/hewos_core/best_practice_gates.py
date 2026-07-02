class GateError(ValueError):
    """Raised when a HEWOS best-practice gate fails closed."""


HIGH_RISK_ACTIONS = {
    "external_dispatch",
    "taskpool_write",
    "hardware_execution",
    "robot_execution",
    "deploy",
    "publish",
    "credential_entry",
    "payment",
    "destructive",
    "broad_fanout",
}

BEST_PRACTICE_PHASE_ORDER = [
    "contract_core",
    "evidence_replay",
    "projection_fixtures",
    "static_workbench",
    "local_runtime_smoke",
    "ui_quality_audit",
    "simulation_write_local_ledger",
    "approval_decision_local_ledger",
    "external_adapter_intent",
    "harness_write_through",
    "real_adapter_write_through",
]

BEST_PRACTICE_PHASES = {
    "contract_core": {
        "required_evidence": ["tests", "contract_readback", "rollback"],
        "allowed_side_effects": ["local_file_write"],
    },
    "evidence_replay": {
        "required_evidence": ["tests", "replay_readback", "append_only_check", "rollback"],
        "allowed_side_effects": ["local_file_write"],
    },
    "projection_fixtures": {
        "required_evidence": ["tests", "projection_readback", "side_effect_scan", "rollback"],
        "allowed_side_effects": ["local_file_write"],
    },
    "static_workbench": {
        "required_evidence": ["tests", "html_readback", "side_effect_scan", "rollback"],
        "allowed_side_effects": ["local_file_write"],
    },
    "local_runtime_smoke": {
        "required_evidence": ["tests", "py_compile", "readback", "rollback"],
        "allowed_side_effects": ["local_process"],
    },
    "ui_quality_audit": {
        "required_evidence": ["tests", "browser_smoke", "console_readback", "screenshot_readback", "rollback"],
        "allowed_side_effects": ["local_file_write", "local_browser_smoke"],
    },
    "simulation_write_local_ledger": {
        "required_evidence": ["tests", "ledger_receipt", "idempotency_readback", "rollback"],
        "allowed_side_effects": ["local_ledger_write"],
    },
    "approval_decision_local_ledger": {
        "required_evidence": ["tests", "decision_receipt", "single_use_check", "rollback"],
        "allowed_side_effects": ["local_ledger_write"],
    },
    "external_adapter_intent": {
        "required_evidence": ["tests", "intent_digest", "allowlist_readback", "rollback"],
        "allowed_side_effects": ["intent_only"],
    },
    "harness_write_through": {
        "required_evidence": ["tests", "harness_receipt", "post_action_readback", "rollback"],
        "allowed_side_effects": ["local_harness_write"],
    },
    "real_adapter_write_through": {
        "required_evidence": ["tests", "exact_authority", "adapter_receipt", "post_action_readback", "rollback"],
        "allowed_side_effects": ["adapter_write"],
    },
}


def _require(condition, message):
    if not condition:
        raise GateError(message)


def next_allowed_phase(current_phase):
    if current_phase not in BEST_PRACTICE_PHASE_ORDER:
        raise GateError(f"unknown phase: {current_phase}")
    index = BEST_PRACTICE_PHASE_ORDER.index(current_phase)
    if index + 1 >= len(BEST_PRACTICE_PHASE_ORDER):
        return None
    return BEST_PRACTICE_PHASE_ORDER[index + 1]


def validate_process_phase(phase):
    _require(isinstance(phase, dict), "process phase must be an object")
    name = phase.get("phase")
    _require(name in BEST_PRACTICE_PHASES, f"unknown phase: {name}")
    previous = phase.get("previous_phase")
    if previous:
        _require(next_allowed_phase(previous) == name, "phase order violation")
        _require(bool(phase.get("previous_receipt")), "previous_receipt is required")
    allowed = set(phase.get("allowed_side_effects", []))
    expected = set(BEST_PRACTICE_PHASES[name]["allowed_side_effects"])
    _require(allowed.issubset(expected), "allowed_side_effects exceed phase policy")
    _require(bool(phase.get("exit_criteria")), "exit_criteria must be non-empty")
    return dict(phase)


def validate_gate_packet(packet):
    _require(isinstance(packet, dict), "gate packet must be an object")
    for field in (
        "gate_id",
        "phase",
        "risk_class",
        "side_effect_class",
        "required_evidence",
        "provided_evidence",
        "authority",
        "idempotency_key",
        "rollback_plan",
        "readback_plan",
        "next_phase",
    ):
        _require(field in packet, f"missing field: {field}")
    phase = packet["phase"]
    _require(phase in BEST_PRACTICE_PHASES, f"unknown phase: {phase}")
    required = list(packet["required_evidence"])
    expected_required = BEST_PRACTICE_PHASES[phase]["required_evidence"]
    _require(required == expected_required, "required_evidence does not match phase policy")
    provided = packet.get("provided_evidence") or {}
    missing = [item for item in required if not provided.get(item)]
    _require(not missing, f"missing evidence: {', '.join(missing)}")
    authority = packet.get("authority") or {}
    _require(authority.get("scope") == "local-only", "authority.scope must be local-only for this gate")
    forbidden = set(authority.get("forbidden_actions") or [])
    missing_forbidden = HIGH_RISK_ACTIONS.intersection({
        "external_dispatch", "taskpool_write", "hardware_execution", "deploy", "credential_entry"
    }) - forbidden
    _require(not missing_forbidden, f"forbidden_actions missing: {', '.join(sorted(missing_forbidden))}")
    _require(bool(packet.get("idempotency_key")), "idempotency_key is required")
    _require(bool(packet.get("rollback_plan")), "rollback_plan is required")
    _require(bool(packet.get("readback_plan")), "readback_plan is required")
    next_phase = packet.get("next_phase")
    _require(next_phase is None or next_phase in BEST_PRACTICE_PHASES, f"unknown next_phase: {next_phase}")
    result = dict(packet)
    result["decision"] = "pass"
    result["execution_enabled"] = False
    return result


def evaluate_authority_ladder(current_phase, requested_phase, requested_actions):
    reasons = []
    try:
        expected = next_allowed_phase(current_phase)
        if requested_phase != expected:
            reasons.append("phase_skip")
    except GateError:
        reasons.append("unknown_current_phase")
    if requested_phase not in BEST_PRACTICE_PHASES:
        reasons.append("unknown_requested_phase")
    actions = set(requested_actions or [])
    if actions.intersection(HIGH_RISK_ACTIONS):
        reasons.append("forbidden_action")
    return {
        "decision": "blocked" if reasons else "pass",
        "reasons": sorted(set(reasons)),
        "execution_enabled": False,
        "next_allowed_phase": None if reasons else requested_phase,
    }


def build_gate_packet(gate_id, phase, risk_class, side_effect_class, provided_evidence, next_phase):
    _require(phase in BEST_PRACTICE_PHASES, f"unknown phase: {phase}")
    return {
        "gate_id": gate_id,
        "phase": phase,
        "risk_class": risk_class,
        "side_effect_class": side_effect_class,
        "required_evidence": list(BEST_PRACTICE_PHASES[phase]["required_evidence"]),
        "provided_evidence": dict(provided_evidence),
        "authority": {
            "scope": "local-only",
            "expires_at": "bounded-by-current-session",
            "allowed_actions": list(BEST_PRACTICE_PHASES[phase]["allowed_side_effects"]),
            "forbidden_actions": sorted({
                "external_dispatch",
                "taskpool_write",
                "hardware_execution",
                "deploy",
                "credential_entry",
            }),
        },
        "idempotency_key": f"{gate_id}:{phase}",
        "rollback_plan": "git revert scoped commit or remove generated local artifacts",
        "readback_plan": "read back generated artifact, test output, and gate result",
        "next_phase": next_phase,
    }
