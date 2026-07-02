class ContractError(ValueError):
    """Raised when a HEWOS contract payload fails validation."""


CAPABILITY_REQUIRED_FIELDS = (
    "capability_id",
    "actor_id",
    "adapter_id",
    "capability_type",
    "input_schema",
    "output_schema",
    "risk_class",
    "required_gates",
    "dry_run_supported",
    "readback_required",
    "audit_required",
    "idempotency_policy",
)

OBSERVATION_REQUIRED_FIELDS = (
    "observation_id",
    "session_id",
    "source_adapter_id",
    "type",
    "timestamp",
    "raw_ref_or_hash",
    "confidence",
    "evidence_refs",
    "derived_facts",
)

ACTION_INTENT_REQUIRED_FIELDS = (
    "intent_id",
    "session_id",
    "taskgraph_node_id",
    "actor_id",
    "capability_id",
    "verb",
    "target",
    "parameters",
    "risk_level",
    "preconditions",
    "expected_observation_delta",
    "verification_plan",
    "evidence_refs",
    "requested_authority",
    "dry_run",
    "idempotency_key",
    "rollback_or_abort",
)

VERIFICATION_RESULT_REQUIRED_FIELDS = (
    "verification_id",
    "intent_id",
    "status",
    "observations_checked",
    "evidence_refs",
    "world_state_delta",
    "next_action",
)

EVIDENCE_LEDGER_ENTRY_REQUIRED_FIELDS = (
    "entry_id",
    "timestamp",
    "kind",
    "subject_id",
    "source",
    "claims",
    "evidence_refs",
    "checksum_or_hash",
    "append_only",
)

EXECUTABLE_RISK_CLASSES = {
    "external_write",
    "physical_action",
    "publish",
    "destructive",
    "payment_or_credential",
}


def require_fields(payload, required_fields):
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ContractError(f"missing required field(s): {', '.join(missing)}")


def validate_capability_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ContractError("manifest must be an object")
    require_fields(manifest, CAPABILITY_REQUIRED_FIELDS)
    if manifest["risk_class"] in EXECUTABLE_RISK_CLASSES:
        if manifest.get("readback_required") is not True:
            raise ContractError("readback_required must be true for executable capabilities")
        if manifest.get("audit_required") is not True:
            raise ContractError("audit_required must be true for executable capabilities")
        if not manifest.get("required_gates"):
            raise ContractError("required_gates must be non-empty for executable capabilities")
        if manifest.get("idempotency_policy") in (None, "", "not_required"):
            raise ContractError("idempotency_policy is required for executable capabilities")
    return dict(manifest)


def validate_observation(observation):
    if not isinstance(observation, dict):
        raise ContractError("observation must be an object")
    require_fields(observation, OBSERVATION_REQUIRED_FIELDS)
    confidence = observation["confidence"]
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise ContractError("confidence must be a number between 0 and 1")
    if not observation.get("evidence_refs"):
        raise ContractError("evidence_refs must be non-empty")
    return dict(observation)


def validate_action_intent(intent):
    if not isinstance(intent, dict):
        raise ContractError("action intent must be an object")
    require_fields(intent, ACTION_INTENT_REQUIRED_FIELDS)
    if not intent.get("evidence_refs"):
        raise ContractError("evidence_refs must be non-empty")
    if intent["risk_level"] in EXECUTABLE_RISK_CLASSES:
        gates = intent.get("gate_status") or {}
        if gates.get("SafetyGate") != "pass":
            raise ContractError("SafetyGate must pass for executable action intents")
        if gates.get("ExternalControlGate") != "pass":
            raise ContractError("ExternalControlGate must pass for executable action intents")
        if not intent.get("idempotency_key"):
            raise ContractError("idempotency_key is required for executable action intents")
    return dict(intent)


def validate_evidence_ledger_entry(entry):
    if not isinstance(entry, dict):
        raise ContractError("ledger entry must be an object")
    require_fields(entry, EVIDENCE_LEDGER_ENTRY_REQUIRED_FIELDS)
    if entry.get("append_only") is not True:
        raise ContractError("append_only must be true")
    if not entry.get("checksum_or_hash"):
        raise ContractError("checksum_or_hash must be non-empty")
    return dict(entry)


def validate_verification_result(result):
    if not isinstance(result, dict):
        raise ContractError("verification result must be an object")
    require_fields(result, VERIFICATION_RESULT_REQUIRED_FIELDS)
    if result.get("status") in {"passed", "completed"} and not result.get("evidence_refs"):
        raise ContractError("evidence_refs must be non-empty for passed verification")
    return dict(result)
