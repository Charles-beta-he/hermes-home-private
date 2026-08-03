from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from .canonical import canonical_bytes, with_self_digest
from .schema_bundle import SchemaBundleError, validate_instance
from .validation import (
    ProtocolValidationError,
    require_exact_fields,
    validate_digest,
    validate_relative_path,
    validate_timestamp,
    validate_uuid,
)

_ENTRY_FIELDS = {"relative_path", "type", "mode", "uid", "gid", "size", "sha256", "executable"}
_INVENTORY_FIELDS = {"schema", "kind", "release_lineage", "release_sequence", "entries", "inventory_digest"}
_MANIFEST_FIELDS = {"schema", "kind", "version_digest", "created_at", "policy_generation", "release_lineage",
                    "release_sequence", "entries", "inventory_digest", "execution_closure"}
KINDS = {"runtime", "active-skills"}


class ManifestError(ValueError):
    pass


def _positive(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifestError(f"{label} must be a positive integer")


def _entry(value: Dict[str, Any]) -> None:
    try:
        require_exact_fields(value, _ENTRY_FIELDS)
        validate_relative_path(value["relative_path"])
        if value["type"] not in {"directory", "file"}:
            raise ManifestError("invalid entry type")
        if value["uid"] != 0 or value["gid"] != 0:
            raise ManifestError("version entries must be root:wheel")
        if not isinstance(value["executable"], bool):
            raise ManifestError("executable must be boolean")
        if value["type"] == "directory":
            if value["mode"] != 0o555 or value["size"] is not None or value["sha256"] is not None or value["executable"]:
                raise ManifestError("invalid directory metadata")
        else:
            if value["mode"] not in {0o444, 0o555} or value["executable"] != (value["mode"] == 0o555):
                raise ManifestError("invalid file mode/executable binding")
            if isinstance(value["size"], bool) or not isinstance(value["size"], int) or value["size"] < 0:
                raise ManifestError("invalid file size")
            validate_digest(value["sha256"])
    except (ProtocolValidationError, KeyError, TypeError) as exc:
        raise ManifestError(str(exc)) from exc


def _entries(values: List[Dict[str, Any]]) -> None:
    if not isinstance(values, list):
        raise ManifestError("entries must be an array")
    paths = []
    for value in values:
        if not isinstance(value, dict):
            raise ManifestError("entry must be an object")
        _entry(value)
        paths.append(value["relative_path"])
    if paths != sorted(paths, key=lambda path: path.encode("utf-8")) or len(paths) != len(set(paths)):
        raise ManifestError("entries must be uniquely sorted by UTF-8 path bytes")


def _validate_execution_closure(kind: str, closure: Any, entries: List[Dict[str, Any]]) -> None:
    if kind == "active-skills":
        if closure is not None:
            raise ManifestError("active-skills execution_closure must be null")
        return
    if not isinstance(closure, dict):
        raise ManifestError("runtime execution_closure must be an object")
    roles = closure.get("protected_roles")
    if not isinstance(roles, list):
        raise ManifestError("protected_roles must be an array")
    if any(not isinstance(role, str) or not role for role in roles):
        raise ManifestError("protected_roles must contain nonempty strings")
    if roles != sorted(roles, key=lambda item: item.encode("utf-8")) or len(roles) != len(set(roles)):
        raise ManifestError("protected_roles must be uniquely sorted by UTF-8 bytes")
    file_paths = {entry["relative_path"] for entry in entries if entry["type"] == "file"}
    if any(role not in file_paths for role in roles):
        raise ManifestError("protected_roles must name version file entries")
    dependencies = closure.get("external_dependencies")
    if not isinstance(dependencies, list):
        raise ManifestError("external_dependencies must be an array")
    raw_paths = [item.get("path_or_image") if isinstance(item, dict) else None for item in dependencies]
    if any(not isinstance(path, str) or not path for path in raw_paths):
        raise ManifestError("external dependency path_or_image must be nonempty")
    paths = [path for path in raw_paths if isinstance(path, str)]
    if paths != sorted(paths, key=lambda path: path.encode("utf-8")) or len(paths) != len(set(paths)):
        raise ManifestError("external_dependencies must be uniquely path-sorted")
    if closure.get("sip_enabled") is not True:
        raise ManifestError("runtime execution closure requires SIP enabled")
    for item in dependencies:
        if item.get("uid") != 0 or item.get("gid") != 0:
            raise ManifestError("external dependencies must be root:wheel")
        if not item.get("designated_requirement"):
            raise ManifestError("external dependency designated_requirement must be nonempty")
        if (item.get("byte_count") is None) != (item.get("sha256") is None):
            raise ManifestError("external dependency byte_count and sha256 nullability must match")
        for field in ("platform_build", "snapshot_uuid", "seal_identity", "cryptex_generation", "dyld_cache_uuid"):
            observed = item.get(field)
            if observed is not None and observed != closure.get(field):
                raise ManifestError(f"external dependency {field} differs from closure generation")


def _identity(kind: str, lineage: str, sequence: int) -> None:
    if kind not in KINDS:
        raise ManifestError("invalid manifest kind")
    try:
        validate_uuid(lineage)
    except ProtocolValidationError as exc:
        raise ManifestError(str(exc)) from exc
    _positive(sequence, "release_sequence")


def _validate_self_digest(value: Dict[str, Any], field: str) -> None:
    try:
        digest = validate_digest(value[field])
        preimage = dict(value)
        preimage[field] = None
        if hashlib.sha256(canonical_bytes(preimage)).hexdigest() != digest:
            raise ManifestError(f"invalid {field}")
    except (ProtocolValidationError, KeyError) as exc:
        raise ManifestError(str(exc)) from exc


def finalize_inventory(kind: str, lineage: str, sequence: int,
                       entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    _identity(kind, lineage, sequence)
    _entries(entries)
    preimage = {"schema": 1, "kind": kind, "release_lineage": lineage,
                "release_sequence": sequence, "entries": entries, "inventory_digest": None}
    try:
        validate_instance("inventory-preimage-v1", preimage)
    except SchemaBundleError as exc:
        raise ManifestError(str(exc)) from exc
    finalized = with_self_digest(preimage, "inventory_digest")
    try:
        validate_instance("inventory-final-v1", finalized)
    except SchemaBundleError as exc:
        raise ManifestError(str(exc)) from exc
    return finalized


def validate_inventory(value: Dict[str, Any]) -> None:
    try:
        validate_instance("inventory-final-v1", value)
        require_exact_fields(value, _INVENTORY_FIELDS)
    except (SchemaBundleError, ProtocolValidationError) as exc:
        raise ManifestError(str(exc)) from exc
    if value["schema"] != 1:
        raise ManifestError("unknown inventory schema")
    _identity(value["kind"], value["release_lineage"], value["release_sequence"])
    _entries(value["entries"])
    _validate_self_digest(value, "inventory_digest")


def finalize_manifest(kind: str, lineage: str, sequence: int, created_at: str, policy_generation: int,
                      entries: List[Dict[str, Any]], inventory_digest: str,
                      execution_closure: Any) -> Dict[str, Any]:
    _identity(kind, lineage, sequence)
    _positive(policy_generation, "policy_generation")
    try:
        validate_timestamp(created_at)
        validate_digest(inventory_digest)
    except ProtocolValidationError as exc:
        raise ManifestError(str(exc)) from exc
    _entries(entries)
    _validate_execution_closure(kind, execution_closure, entries)
    preimage = {"schema": 1, "kind": kind, "version_digest": None, "created_at": created_at,
                "policy_generation": policy_generation, "release_lineage": lineage,
                "release_sequence": sequence, "entries": entries, "inventory_digest": inventory_digest,
                "execution_closure": execution_closure}
    try:
        validate_instance("manifest-preimage-v1", preimage)
    except SchemaBundleError as exc:
        raise ManifestError(str(exc)) from exc
    finalized = with_self_digest(preimage, "version_digest")
    try:
        validate_instance("manifest-final-v1", finalized)
    except SchemaBundleError as exc:
        raise ManifestError(str(exc)) from exc
    return finalized


def validate_manifest(value: Dict[str, Any]) -> None:
    try:
        validate_instance("manifest-final-v1", value)
        require_exact_fields(value, _MANIFEST_FIELDS)
        validate_timestamp(value["created_at"])
        validate_digest(value["inventory_digest"])
    except (SchemaBundleError, ProtocolValidationError, KeyError) as exc:
        raise ManifestError(str(exc)) from exc
    if value["schema"] != 1:
        raise ManifestError("unknown manifest schema")
    _identity(value["kind"], value["release_lineage"], value["release_sequence"])
    _positive(value["policy_generation"], "policy_generation")
    _entries(value["entries"])
    _validate_execution_closure(value["kind"], value["execution_closure"], value["entries"])
    _validate_self_digest(value, "version_digest")


def validate_manifest_inventory_pair(manifest: Dict[str, Any], inventory: Dict[str, Any]) -> None:
    validate_manifest(manifest)
    validate_inventory(inventory)
    for field in ("kind", "release_lineage", "release_sequence", "entries", "inventory_digest"):
        if canonical_bytes(manifest[field]) != canonical_bytes(inventory[field]):
            raise ManifestError(f"manifest/inventory mismatch: {field}")
