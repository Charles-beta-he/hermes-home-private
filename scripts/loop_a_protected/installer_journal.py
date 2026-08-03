from __future__ import annotations

from typing import Any, Dict, List

from .authority import AuthorityError, validate_authorization
from .canonical import with_self_digest
from .schema_bundle import SchemaBundleError, validate_instance
from .states import INSTALLER_PATHS, StateTransitionError, require_installer_transition


class InstallerJournalError(ValueError):
    pass


MUTABLE_FIELDS = {
    "sequence", "prior_record_digest", "state", "timestamp", "tree_inventory", "pointer_inventory",
    "operation_evidence", "record_digest",
}


def _validate_operation_shape(value: Dict[str, Any], operation: str, destination: str) -> None:
    if (operation, destination) not in INSTALLER_PATHS:
        raise InstallerJournalError("invalid installer operation/destination pair")
    initial = operation == "install-initial"
    single = operation in {"promote-runtime", "promote-skill", "rollback-protected"}
    has_floor = operation in {"install-initial", "update-floor"}
    if (value["release_sequence"] is not None) != single:
        raise InstallerJournalError("invalid installer release sequence nullability")
    for field in ("expected_current_manifest_digest", "expected_current_inventory_digest",
                  "target_manifest_digest", "target_inventory_digest"):
        if (value[field] is not None) != single:
            raise InstallerJournalError(f"invalid {field} nullability")
    if (value["initial_target_bundle_digest"] is not None) != initial:
        raise InstallerJournalError("invalid initial-target-bundle nullability")
    if (value["proposed_floor_digest"] is not None) != has_floor:
        raise InstallerJournalError("invalid proposed-floor nullability")
    for field in ("smoke_transaction_uuid", "smoke_gate_digest", "on_demand_plist_digest"):
        if (value[field] is not None) != initial:
            raise InstallerJournalError(f"invalid {field} nullability")

    state = value["state"]
    tree_kind = "runtime" if state.startswith("RUNTIME_TREE_") else "active-skills" if state.startswith("SKILL_TREE_") else None
    pointer_kind = "runtime" if state.startswith("RUNTIME_POINTER_") else "active-skills" if state.startswith("SKILL_POINTER_") else None
    if (value["tree_inventory"] is not None) != (tree_kind is not None):
        raise InstallerJournalError("tree inventory state mismatch")
    if tree_kind is not None and value["tree_inventory"]["kind"] != tree_kind:
        raise InstallerJournalError("tree inventory kind mismatch")
    if (value["pointer_inventory"] is not None) != (pointer_kind is not None):
        raise InstallerJournalError("pointer inventory state mismatch")
    if pointer_kind is not None and value["pointer_inventory"]["kind"] != pointer_kind:
        raise InstallerJournalError("pointer inventory kind mismatch")


def validate_installer_record(value: Dict[str, Any], operation: str, destination: str) -> None:
    try:
        validate_instance("installer-record-final-v1", value)
    except SchemaBundleError as exc:
        raise InstallerJournalError(str(exc)) from exc
    _validate_operation_shape(value, operation, destination)


def finalize_installer_record(preimage: Dict[str, Any], operation: str, destination: str) -> Dict[str, Any]:
    try:
        validate_instance("installer-record-preimage-v1", preimage)
    except SchemaBundleError as exc:
        raise InstallerJournalError(str(exc)) from exc
    _validate_operation_shape(preimage, operation, destination)
    finalized = with_self_digest(preimage, "record_digest")
    validate_installer_record(finalized, operation, destination)
    return finalized


def validate_installer_chain(records: List[Dict[str, Any]], operation: str, destination: str) -> None:
    if not isinstance(records, list) or not records:
        raise InstallerJournalError("installer chain must be nonempty")
    for record in records:
        validate_installer_record(record, operation, destination)
    first = records[0]
    if first["sequence"] != 1 or first["prior_record_digest"] is not None or first["state"] != "PREPARED":
        raise InstallerJournalError("installer chain must start with PREPARED sequence 1")
    immutable = {field: value for field, value in first.items() if field not in MUTABLE_FIELDS}
    for index, record in enumerate(records):
        if record["sequence"] != index + 1:
            raise InstallerJournalError("installer sequence gap or duplicate")
        if any(record[field] != expected for field, expected in immutable.items()):
            raise InstallerJournalError("immutable installer field changed")
        if index:
            prior = records[index - 1]
            if record["prior_record_digest"] != prior["record_digest"]:
                raise InstallerJournalError("installer prior-record digest mismatch")
            try:
                require_installer_transition(operation, destination, prior["state"], record["state"])
            except StateTransitionError as exc:
                raise InstallerJournalError(str(exc)) from exc
    states = [record["state"] for record in records]
    if records[-1]["state"] == "COMMITTED":
        expected = INSTALLER_PATHS[(operation, destination)][1:]
        if states != expected:
            raise InstallerJournalError("COMMITTED requires the exact operation path")
    if "RECOVERY_REQUIRED" in states and records[-1]["state"] not in {"RECOVERY_REQUIRED", "ROLLED_BACK"}:
        raise InstallerJournalError("recovery chain can only remain fenced or roll back")


def validate_installer_authorization(records: List[Dict[str, Any]], authorization: Dict[str, Any],
                                     operation: str, destination: str) -> None:
    """Bind the externally named installer path to the digest-authorized record fields."""
    try:
        validate_authorization(authorization)
    except AuthorityError as exc:
        raise InstallerJournalError("invalid finalized authorization") from exc
    payload = authorization["authorization_payload"]
    if payload["operation"] != operation or payload["exact_destination"] != destination:
        raise InstallerJournalError("installer operation/destination differs from authorization")
    direct_mapping = {
        "authorization_id": "authorization_id",
        "transaction_uuid": "transaction_uuid",
        "policy_generation": "policy_generation",
        "release_lineage": "release_lineage",
        "release_sequence": "release_sequence",
        "prior_floor_digest": "prior_floor_digest",
        "proposed_floor_digest": "proposed_floor_digest",
        "expected_current_manifest_digest": "expected_current_manifest_digest",
        "expected_current_inventory_digest": "expected_current_inventory_digest",
        "target_manifest_digest": "target_manifest_digest",
        "target_inventory_digest": "target_inventory_digest",
        "initial_target_bundle_digest": "initial_target_bundle_digest",
        "architecture_digest": "architecture_digest",
        "protocol_appendix_digest": "protocol_appendix_digest",
        "schema_bundle_digest": "schema_bundle_digest",
        "authority_packet_digest": "authority_packet_digest",
        "installer_manifest_digest": "installer_manifest_digest",
        "runtime_manifest_digest": "runtime_manifest_digest",
        "red_evidence_digest": "red_evidence_digest",
        "scheduler_before_digest": "scheduler_before_digest",
        "scheduler_action": "scheduler_action",
        "smoke_transaction_uuid": "smoke_transaction_uuid",
    }
    outer_mapping = {
        "payload_digest": "payload_digest",
        "authorization_digest": "authorization_digest",
        "authority_grant_digest": "authority_grant_digest",
    }
    expected = {record_field: payload[payload_field] for record_field, payload_field in direct_mapping.items()}
    expected.update({record_field: authorization[outer_field] for record_field, outer_field in outer_mapping.items()})
    expected["on_demand_plist_digest"] = payload["scheduler_action"]["on_demand_plist_digest"]
    expected["final_plist_digest"] = payload["scheduler_action"]["final_plist_digest"]
    for record in records:
        for field, value in expected.items():
            if record[field] != value:
                raise InstallerJournalError(f"installer record authorization binding mismatch: {field}")
