from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Tuple

from .canonical import canonical_bytes, with_self_digest
from .validation import (
    ProtocolValidationError,
    require_exact_fields,
    validate_digest,
    validate_timestamp,
    validate_uuid,
)


class PolicyError(ValueError):
    pass


_TARGET_FIELDS = {"kind", "release_lineage", "release_sequence", "manifest_digest", "inventory_digest"}
_BUNDLE_FIELDS = {"schema", "runtime", "active_skills", "bundle_digest"}
_ENTRY_FIELDS = {"kind", "release_sequence", "manifest_digest", "inventory_digest", "disposition"}
_FLOOR_FIELDS = {
    "schema", "policy_generation", "release_lineage", "minimum_release_sequence",
    "permitted_versions", "updated_at", "prior_floor_digest", "authorization_id", "record_digest",
}


def _positive(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PolicyError(f"{label} must be a positive integer")
    return value


def _nonnegative(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PolicyError(f"{label} must be a nonnegative integer")
    return value


def _exact(value: Dict[str, Any], fields: set) -> None:
    try:
        require_exact_fields(value, fields)
    except ProtocolValidationError as exc:
        raise PolicyError(str(exc)) from exc


def _digest(value: Any, nullable: bool = False) -> Any:
    if value is None and nullable:
        return None
    try:
        return validate_digest(value)
    except ProtocolValidationError as exc:
        raise PolicyError(str(exc)) from exc


def _uuid(value: Any) -> str:
    try:
        return validate_uuid(value)
    except ProtocolValidationError as exc:
        raise PolicyError(str(exc)) from exc


def _target(value: Dict[str, Any], expected_kind: str, expected_lineage: str = None) -> Dict[str, Any]:
    _exact(value, _TARGET_FIELDS)
    if value["kind"] != expected_kind:
        raise PolicyError("initial target kind mismatch")
    lineage = _uuid(value["release_lineage"])
    if expected_lineage is not None and lineage != expected_lineage:
        raise PolicyError("initial target lineage mismatch")
    _positive(value["release_sequence"], "release_sequence")
    _digest(value["manifest_digest"])
    _digest(value["inventory_digest"])
    return value


def _validate_bundle(value: Dict[str, Any], finalized: bool) -> None:
    _exact(value, _BUNDLE_FIELDS)
    if value["schema"] != 1:
        raise PolicyError("unknown initial-target-bundle schema")
    runtime = _target(value["runtime"], "runtime")
    _target(value["active_skills"], "active-skills", runtime["release_lineage"])
    if finalized:
        digest = _digest(value["bundle_digest"])
        preimage = dict(value)
        preimage["bundle_digest"] = None
        if hashlib.sha256(canonical_bytes(preimage)).hexdigest() != digest:
            raise PolicyError("bundle_digest mismatch")
    elif value["bundle_digest"] is not None:
        raise PolicyError("bundle_digest must be null in preimage")


def finalize_initial_target_bundle(runtime: Dict[str, Any], active_skills: Dict[str, Any]) -> Dict[str, Any]:
    preimage = {"schema": 1, "runtime": runtime, "active_skills": active_skills, "bundle_digest": None}
    _validate_bundle(preimage, finalized=False)
    return with_self_digest(preimage, "bundle_digest")


def validate_initial_target_bundle(value: Dict[str, Any]) -> None:
    _validate_bundle(value, finalized=True)


def _entry(value: Dict[str, Any]) -> Tuple[bytes, int, bytes, bytes, bytes]:
    _exact(value, _ENTRY_FIELDS)
    if value["kind"] not in {"runtime", "active-skills"}:
        raise PolicyError("unknown permitted kind")
    _positive(value["release_sequence"], "permitted release_sequence")
    _digest(value["manifest_digest"])
    _digest(value["inventory_digest"])
    if value["disposition"] not in {"forward", "rollback"}:
        raise PolicyError("unknown disposition")
    return (value["kind"].encode("ascii"), value["release_sequence"],
            value["manifest_digest"].encode("ascii"), value["inventory_digest"].encode("ascii"),
            value["disposition"].encode("ascii"))


def _validate_floor(value: Dict[str, Any], finalized: bool = True) -> None:
    _exact(value, _FLOOR_FIELDS)
    if value["schema"] != 1:
        raise PolicyError("unknown rollback-floor schema")
    _positive(value["policy_generation"], "policy_generation")
    _uuid(value["release_lineage"])
    _nonnegative(value["minimum_release_sequence"], "minimum_release_sequence")
    if not isinstance(value["permitted_versions"], list):
        raise PolicyError("permitted_versions must be an array")
    keys = [_entry(item) for item in value["permitted_versions"]]
    if keys != sorted(keys):
        raise PolicyError("permitted_versions are not in canonical tuple order")
    if len(keys) != len(set(keys)):
        raise PolicyError("duplicate permitted tuple")
    kind_sequences = [(item[0], item[1]) for item in keys]
    if len(kind_sequences) != len(set(kind_sequences)):
        raise PolicyError("duplicate permitted kind/release_sequence")
    try:
        validate_timestamp(value["updated_at"])
    except ProtocolValidationError as exc:
        raise PolicyError(str(exc)) from exc
    _digest(value["prior_floor_digest"], nullable=True)
    if not isinstance(value["authorization_id"], str) or not value["authorization_id"] or any(c.isspace() for c in value["authorization_id"]):
        raise PolicyError("invalid authorization_id")
    if finalized:
        digest = _digest(value["record_digest"])
        preimage = dict(value)
        preimage["record_digest"] = None
        if hashlib.sha256(canonical_bytes(preimage)).hexdigest() != digest:
            raise PolicyError("record_digest mismatch")
    elif value["record_digest"] is not None:
        raise PolicyError("record_digest must be null in preimage")


def finalize_rollback_floor(policy_generation: int, release_lineage: str, minimum_release_sequence: int,
                            permitted_versions: List[Dict[str, Any]], updated_at: str,
                            prior_floor_digest: Any, authorization_id: str) -> Dict[str, Any]:
    preimage = {
        "schema": 1, "policy_generation": policy_generation, "release_lineage": release_lineage,
        "minimum_release_sequence": minimum_release_sequence, "permitted_versions": permitted_versions,
        "updated_at": updated_at, "prior_floor_digest": prior_floor_digest,
        "authorization_id": authorization_id, "record_digest": None,
    }
    _validate_floor(preimage, finalized=False)
    return with_self_digest(preimage, "record_digest")


def validate_rollback_floor(value: Dict[str, Any]) -> None:
    _validate_floor(value, finalized=True)


def target_is_permitted(floor: Dict[str, Any], release_lineage: str, kind: str, release_sequence: int,
                        manifest_digest: str, inventory_digest: str) -> bool:
    _validate_floor(floor)
    if release_lineage != floor["release_lineage"] or release_sequence < floor["minimum_release_sequence"]:
        return False
    target = (kind, release_sequence, manifest_digest, inventory_digest)
    return any((entry["kind"], entry["release_sequence"], entry["manifest_digest"], entry["inventory_digest"]) == target
               for entry in floor["permitted_versions"])


def validate_floor_update(prior: Dict[str, Any], proposed: Dict[str, Any]) -> None:
    _validate_floor(prior)
    _validate_floor(proposed)
    if proposed["policy_generation"] != prior["policy_generation"] + 1:
        raise PolicyError("policy generation must increment exactly once")
    if proposed["release_lineage"] != prior["release_lineage"]:
        raise PolicyError("release lineage cannot change")
    if proposed["minimum_release_sequence"] < prior["minimum_release_sequence"]:
        raise PolicyError("minimum release sequence cannot decrease")
    if proposed["prior_floor_digest"] != prior["record_digest"]:
        raise PolicyError("prior floor digest mismatch")
    old = {(entry["kind"], entry["release_sequence"]): (entry["manifest_digest"], entry["inventory_digest"])
           for entry in prior["permitted_versions"]}
    new = {(entry["kind"], entry["release_sequence"]): (entry["manifest_digest"], entry["inventory_digest"])
           for entry in proposed["permitted_versions"]}
    for key, identity in old.items():
        if key in new and new[key] != identity:
            raise PolicyError("existing release sequence rebound to another digest")


def validate_floor_history(floors: List[Dict[str, Any]]) -> None:
    if not isinstance(floors, list) or not floors:
        raise PolicyError("floor history must be nonempty")
    first = floors[0]
    _validate_floor(first)
    if first["policy_generation"] != 1 or first["prior_floor_digest"] is not None:
        raise PolicyError("floor history must begin at generation 1")
    identities: Dict[Tuple[str, int], Tuple[str, str]] = {}
    for index, current in enumerate(floors):
        if index:
            validate_floor_update(floors[index - 1], current)
        for entry in current["permitted_versions"]:
            key = (entry["kind"], entry["release_sequence"])
            identity = (entry["manifest_digest"], entry["inventory_digest"])
            prior_identity = identities.get(key)
            if prior_identity is not None and prior_identity != identity:
                raise PolicyError("historical sequence rebinding")
            identities[key] = identity
