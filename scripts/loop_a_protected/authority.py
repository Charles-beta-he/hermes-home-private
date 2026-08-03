from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict

from .canonical import canonical_bytes, with_self_digest
from .policy import PolicyError, validate_initial_target_bundle, validate_rollback_floor
from .validation import ProtocolValidationError, require_exact_fields, validate_digest, validate_timestamp, validate_uuid

PAYLOAD_FIELDS = {
    "schema", "authorization_id", "operation", "approval_identity", "issued_at", "expires_at", "nonce",
    "transaction_uuid", "smoke_transaction_uuid", "service_epoch", "policy_generation", "release_lineage",
    "release_sequence", "exact_destination", "prior_floor_digest", "proposed_floor", "proposed_floor_digest",
    "expected_current_manifest_digest", "expected_current_inventory_digest", "protected_source_digest",
    "candidate_digest", "target_manifest_digest", "target_inventory_digest", "initial_target_bundle",
    "initial_target_bundle_digest", "architecture_digest", "protocol_appendix_digest", "authority_packet_digest",
    "schema_bundle_digest", "installer_manifest_digest", "runtime_manifest_digest", "red_evidence_digest",
    "scheduler_before_digest", "scheduler_action", "payload_digest",
}
GRANT_FIELDS = {"schema", "authorization_id", "payload_sha256", "operation", "destination", "issued_at",
                "expires_at", "nonce", "wire_sha256", "authority_grant_digest"}
AUTHORIZATION_FIELDS = {"schema", "authorization_payload", "payload_digest", "authority_grant",
                        "authority_grant_digest", "authorization_digest"}
SCHEDULER_ACTION_FIELDS = {"old_job_id", "expected_enabled", "target_enabled", "launchd_label",
                           "launchd_target_state", "on_demand_plist_digest", "final_plist_digest"}
DESTINATIONS = {
    "install-initial": {"protected-bundle"}, "promote-runtime": {"runtime"},
    "promote-skill": {"active-skills"}, "rollback-protected": {"runtime", "active-skills"},
    "update-floor": {"rollback-floor"},
}
_TOKEN = re.compile(r"[A-Za-z0-9._:-]+\Z")
_WIRE = re.compile(
    rb"HERMES-AUTH-V1 authorization_id=([A-Za-z0-9._:-]+) payload_sha256=([0-9a-f]{64}) "
    rb"operation=(install-initial|promote-runtime|promote-skill|rollback-protected|update-floor) "
    rb"destination=(protected-bundle|runtime|active-skills|rollback-floor) "
    rb"issued_at=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z) "
    rb"expires_at=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z) "
    rb"nonce=([A-Za-z0-9._:-]+)\n\Z"
)


class AuthorityError(ValueError):
    pass


def _positive(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AuthorityError(f"{label} must be a positive integer")


def _token(value: Any, label: str) -> None:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise AuthorityError(f"{label} must be a canonical ASCII token")


def _nullable_digest(value: Any, label: str) -> None:
    if value is None:
        return
    try:
        validate_digest(value)
    except ProtocolValidationError as exc:
        raise AuthorityError(f"invalid {label}") from exc


def _nullable_uuid(value: Any, label: str) -> None:
    if value is None:
        return
    try:
        validate_uuid(value)
    except ProtocolValidationError as exc:
        raise AuthorityError(f"invalid {label}") from exc


def _digest_matches(value: Dict[str, Any], field: str) -> None:
    try:
        digest = validate_digest(value[field])
    except (KeyError, ProtocolValidationError) as exc:
        raise AuthorityError(f"invalid {field}") from exc
    preimage = dict(value)
    preimage[field] = None
    if hashlib.sha256(canonical_bytes(preimage)).hexdigest() != digest:
        raise AuthorityError(f"{field} does not match preimage")


def _validate_scheduler_action(value: Any) -> None:
    if not isinstance(value, dict):
        raise AuthorityError("scheduler_action must be an object")
    try:
        require_exact_fields(value, SCHEDULER_ACTION_FIELDS)
    except ProtocolValidationError as exc:
        raise AuthorityError(str(exc)) from exc
    if value["old_job_id"] is not None:
        _token(value["old_job_id"], "old_job_id")
    for label in ("expected_enabled", "target_enabled"):
        if not isinstance(value[label], bool):
            raise AuthorityError(f"{label} must be boolean")
    if value["launchd_label"] != "system/com.nous.hermes.loop-a":
        raise AuthorityError("unexpected launchd_label")
    if value["launchd_target_state"] not in {"enabled-loaded", "disabled-unloaded"}:
        raise AuthorityError("invalid launchd_target_state")
    for label in ("on_demand_plist_digest", "final_plist_digest"):
        _nullable_digest(value[label], label)


def _validate_payload_shape(value: Dict[str, Any], preimage: bool) -> None:
    try:
        require_exact_fields(value, PAYLOAD_FIELDS)
    except ProtocolValidationError as exc:
        raise AuthorityError(str(exc)) from exc
    if value["schema"] != 1:
        raise AuthorityError("unknown payload schema")
    operation = value["operation"]
    destination = value["exact_destination"]
    if operation not in DESTINATIONS or destination not in DESTINATIONS[operation]:
        raise AuthorityError("invalid operation/destination pair")
    for label in ("authorization_id", "approval_identity", "nonce"):
        _token(value[label], label)
    _validate_scheduler_action(value["scheduler_action"])
    try:
        validate_uuid(value["transaction_uuid"])
        validate_uuid(value["release_lineage"])
        validate_timestamp(value["issued_at"])
        validate_timestamp(value["expires_at"])
    except ProtocolValidationError as exc:
        raise AuthorityError(str(exc)) from exc
    if datetime.strptime(value["issued_at"], "%Y-%m-%dT%H:%M:%SZ") >= datetime.strptime(value["expires_at"], "%Y-%m-%dT%H:%M:%SZ"):
        raise AuthorityError("authorization interval must be positive")
    _positive(value["service_epoch"], "service_epoch")
    _positive(value["policy_generation"], "policy_generation")
    _nullable_uuid(value["smoke_transaction_uuid"], "smoke_transaction_uuid")
    for label in PAYLOAD_FIELDS:
        if label.endswith("_digest") and label != "payload_digest":
            _nullable_digest(value[label], label)
    for label in ("architecture_digest", "protocol_appendix_digest", "authority_packet_digest",
                  "schema_bundle_digest", "installer_manifest_digest", "runtime_manifest_digest",
                  "red_evidence_digest", "scheduler_before_digest"):
        if value[label] is None:
            raise AuthorityError(f"{label} must not be null")
    if preimage:
        if value["payload_digest"] is not None:
            raise AuthorityError("payload_digest must be null in preimage")
    else:
        _digest_matches(value, "payload_digest")
    _validate_operation_nullability(value)


def _validate_nested_policy(value: Dict[str, Any]) -> None:
    bundle = value["initial_target_bundle"]
    floor = value["proposed_floor"]
    try:
        if bundle is not None:
            validate_initial_target_bundle(bundle)
        if floor is not None:
            validate_rollback_floor(floor)
    except PolicyError as exc:
        raise AuthorityError(f"invalid nested bundle or floor: {exc}") from exc
    if bundle is not None and value["initial_target_bundle_digest"] != bundle["bundle_digest"]:
        raise AuthorityError("initial-target bundle digest mismatch")
    if floor is not None:
        if value["proposed_floor_digest"] != floor["record_digest"]:
            raise AuthorityError("proposed floor digest mismatch")
        if floor["policy_generation"] != value["policy_generation"] or floor["release_lineage"] != value["release_lineage"]:
            raise AuthorityError("proposed floor policy binding mismatch")
        if floor["authorization_id"] != value["authorization_id"] or floor["prior_floor_digest"] != value["prior_floor_digest"]:
            raise AuthorityError("proposed floor authorization or prior binding mismatch")
    if value["operation"] == "install-initial":
        expected = []
        for field in ("active_skills", "runtime"):
            target = bundle[field]
            expected.append({"kind": target["kind"], "release_sequence": target["release_sequence"],
                             "manifest_digest": target["manifest_digest"], "inventory_digest": target["inventory_digest"],
                             "disposition": "forward"})
        expected.sort(key=lambda item: (item["kind"].encode("ascii"), item["release_sequence"],
                                        item["manifest_digest"].encode("ascii"), item["inventory_digest"].encode("ascii"),
                                        item["disposition"].encode("ascii")))
        if floor["minimum_release_sequence"] != 1 or floor["permitted_versions"] != expected:
            raise AuthorityError("initial bundle/floor tuple mismatch")


def _validate_operation_nullability(value: Dict[str, Any]) -> None:
    operation = value["operation"]
    promote = operation in {"promote-runtime", "promote-skill"}
    single = promote or operation == "rollback-protected"
    if single:
        _positive(value["release_sequence"], "release_sequence")
    elif value["release_sequence"] is not None:
        raise AuthorityError("release_sequence must be null for this operation")
    if (operation == "install-initial") != (value["smoke_transaction_uuid"] is not None):
        raise AuthorityError("invalid smoke_transaction_uuid nullability")
    required_single = ("expected_current_manifest_digest", "expected_current_inventory_digest",
                       "target_manifest_digest", "target_inventory_digest")
    for label in required_single:
        if (value[label] is not None) != single:
            raise AuthorityError(f"invalid {label} nullability")
    for label in ("protected_source_digest", "candidate_digest"):
        if (value[label] is not None) != promote:
            raise AuthorityError(f"invalid {label} nullability")
    has_bundle = operation == "install-initial"
    for label in ("initial_target_bundle", "initial_target_bundle_digest"):
        if (value[label] is not None) != has_bundle:
            raise AuthorityError(f"invalid {label} nullability")
    has_floor = operation in {"install-initial", "update-floor"}
    for label in ("proposed_floor", "proposed_floor_digest"):
        if (value[label] is not None) != has_floor:
            raise AuthorityError(f"invalid {label} nullability")
    if value["initial_target_bundle"] is not None and not isinstance(value["initial_target_bundle"], dict):
        raise AuthorityError("initial_target_bundle must be an object")
    if value["proposed_floor"] is not None and not isinstance(value["proposed_floor"], dict):
        raise AuthorityError("proposed_floor must be an object")
    _validate_nested_policy(value)


def finalize_authorization_payload(preimage: Dict[str, Any]) -> Dict[str, Any]:
    _validate_payload_shape(preimage, preimage=True)
    finalized = with_self_digest(preimage, "payload_digest")
    _validate_payload_shape(finalized, preimage=False)
    return finalized


def validate_authorization_payload(value: Dict[str, Any]) -> None:
    _validate_payload_shape(value, preimage=False)


def parse_authority_grant_wire(raw: bytes) -> Dict[str, Any]:
    if not isinstance(raw, bytes):
        raise AuthorityError("grant wire must be bytes")
    match = _WIRE.fullmatch(raw)
    if match is None:
        raise AuthorityError("noncanonical AuthorityGrant wire")
    try:
        authorization_id, payload_sha256, operation, destination, issued_at, expires_at, nonce = (
            part.decode("ascii") for part in match.groups()
        )
        validate_digest(payload_sha256)
        validate_timestamp(issued_at)
        validate_timestamp(expires_at)
    except (UnicodeError, ProtocolValidationError) as exc:
        raise AuthorityError(str(exc)) from exc
    if destination not in DESTINATIONS[operation]:
        raise AuthorityError("invalid grant operation/destination pair")
    preimage = {"schema": 1, "authorization_id": authorization_id, "payload_sha256": payload_sha256,
                "operation": operation, "destination": destination, "issued_at": issued_at,
                "expires_at": expires_at, "nonce": nonce, "wire_sha256": hashlib.sha256(raw).hexdigest(),
                "authority_grant_digest": None}
    return with_self_digest(preimage, "authority_grant_digest")


def validate_authority_grant(value: Dict[str, Any]) -> None:
    try:
        require_exact_fields(value, GRANT_FIELDS)
    except ProtocolValidationError as exc:
        raise AuthorityError(str(exc)) from exc
    if value["schema"] != 1 or value["operation"] not in DESTINATIONS or value["destination"] not in DESTINATIONS[value["operation"]]:
        raise AuthorityError("invalid grant schema or operation/destination")
    for label in ("authorization_id", "nonce"):
        _token(value[label], label)
    try:
        validate_digest(value["payload_sha256"])
        validate_digest(value["wire_sha256"])
        validate_timestamp(value["issued_at"])
        validate_timestamp(value["expires_at"])
    except ProtocolValidationError as exc:
        raise AuthorityError(str(exc)) from exc
    _digest_matches(value, "authority_grant_digest")


def validate_grant_for_payload(grant: Dict[str, Any], payload: Dict[str, Any]) -> None:
    validate_authority_grant(grant)
    validate_authorization_payload(payload)
    mapping = {"authorization_id": "authorization_id", "payload_sha256": "payload_digest",
               "operation": "operation", "destination": "exact_destination", "issued_at": "issued_at",
               "expires_at": "expires_at", "nonce": "nonce"}
    for grant_field, payload_field in mapping.items():
        if grant[grant_field] != payload[payload_field]:
            raise AuthorityError(f"grant/payload mismatch: {grant_field}")


def finalize_authorization(payload: Dict[str, Any], grant: Dict[str, Any]) -> Dict[str, Any]:
    validate_grant_for_payload(grant, payload)
    preimage = {"schema": 1, "authorization_payload": payload, "payload_digest": payload["payload_digest"],
                "authority_grant": grant, "authority_grant_digest": grant["authority_grant_digest"],
                "authorization_digest": None}
    finalized = with_self_digest(preimage, "authorization_digest")
    validate_authorization(finalized)
    return finalized


def validate_authorization(value: Dict[str, Any]) -> None:
    try:
        require_exact_fields(value, AUTHORIZATION_FIELDS)
    except ProtocolValidationError as exc:
        raise AuthorityError(str(exc)) from exc
    if value["schema"] != 1 or not isinstance(value["authorization_payload"], dict) or not isinstance(value["authority_grant"], dict):
        raise AuthorityError("invalid finalized authorization shape")
    validate_grant_for_payload(value["authority_grant"], value["authorization_payload"])
    if value["payload_digest"] != value["authorization_payload"]["payload_digest"]:
        raise AuthorityError("outer payload digest mismatch")
    if value["authority_grant_digest"] != value["authority_grant"]["authority_grant_digest"]:
        raise AuthorityError("outer AuthorityGrant digest mismatch")
    _digest_matches(value, "authorization_digest")
