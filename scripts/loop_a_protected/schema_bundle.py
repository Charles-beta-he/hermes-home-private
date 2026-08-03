from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .canonical import canonical_bytes, with_self_digest


class SchemaBundleError(ValueError):
    pass


DRAFT = "https://json-schema.org/draft/2020-12/schema"
DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
UUID = {"type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"}
TOKEN = {"type": "string", "pattern": "^[A-Za-z0-9._:-]+$"}
TIMESTAMP = {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"}
UTC_MINUTE = {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:00Z$"}
POSITIVE = {"type": "integer", "minimum": 1, "maximum": 9007199254740991}
NONNEGATIVE = {"type": "integer", "minimum": 0, "maximum": 9007199254740991}
STRING = {"type": "string"}
BOOLEAN = {"type": "boolean"}
NULL = {"type": "null"}


def nullable(schema: Mapping[str, Any]) -> Dict[str, Any]:
    return {"oneOf": [deepcopy(dict(schema)), {"type": "null"}]}


def enum(*values: str) -> Dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def array(items: Mapping[str, Any]) -> Dict[str, Any]:
    return {"type": "array", "items": deepcopy(dict(items))}


def obj(properties: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    copied = {key: deepcopy(dict(value)) for key, value in properties.items()}
    return {"type": "object", "properties": copied, "required": list(copied), "additionalProperties": False}


OBSERVATION_INVENTORY_ENTRY = obj({
    "role": TOKEN, "path": STRING, "device": NONNEGATIVE, "inode": POSITIVE, "mode": NONNEGATIVE,
    "uid": NONNEGATIVE, "gid": NONNEGATIVE, "link_count": POSITIVE, "byte_count": nullable(NONNEGATIVE),
    "sha256": nullable(DIGEST),
})
SERVICE_INVENTORY_ENTRY = obj({
    "role": TOKEN, "relative_path": STRING, "device": NONNEGATIVE, "inode": POSITIVE,
    "mode": NONNEGATIVE, "uid": NONNEGATIVE, "gid": NONNEGATIVE, "link_count": NONNEGATIVE,
    "byte_count": NONNEGATIVE, "sha256": DIGEST,
})
VERSION_ENTRY = obj({
    "relative_path": STRING, "type": enum("directory", "file"), "mode": NONNEGATIVE,
    "uid": NONNEGATIVE, "gid": NONNEGATIVE, "size": nullable(NONNEGATIVE),
    "sha256": nullable(DIGEST), "executable": BOOLEAN,
})
TARGET_TUPLE = obj({
    "kind": enum("runtime", "active-skills"), "release_lineage": UUID, "release_sequence": POSITIVE,
    "manifest_digest": DIGEST, "inventory_digest": DIGEST,
})
FLOOR_ENTRY = obj({
    "kind": enum("runtime", "active-skills"), "release_sequence": POSITIVE,
    "manifest_digest": DIGEST, "inventory_digest": DIGEST, "disposition": enum("forward", "rollback"),
})
SCHEDULER_ACTION = obj({
    "old_job_id": nullable(TOKEN), "expected_enabled": BOOLEAN, "target_enabled": BOOLEAN,
    "launchd_label": {"const": "system/com.nous.hermes.loop-a"},
    "launchd_target_state": enum("enabled-loaded", "disabled-unloaded"),
    "on_demand_plist_digest": nullable(DIGEST), "final_plist_digest": nullable(DIGEST),
})
EXTERNAL_DEPENDENCY = obj({
    "path_or_image": STRING, "kind": TOKEN, "mode": NONNEGATIVE, "uid": NONNEGATIVE, "gid": NONNEGATIVE,
    "byte_count": nullable(NONNEGATIVE), "sha256": nullable(DIGEST), "platform_build": STRING,
    "snapshot_uuid": nullable(UUID), "seal_identity": nullable(STRING), "cryptex_generation": nullable(STRING),
    "dyld_cache_uuid": nullable(UUID), "designated_requirement": STRING,
})
EXECUTION_CLOSURE = obj({
    "protected_roles": array(STRING), "external_dependencies": array(EXTERNAL_DEPENDENCY),
    "platform_build": STRING, "snapshot_uuid": UUID, "seal_identity": STRING,
    "cryptex_generation": STRING, "dyld_cache_uuid": UUID, "sip_enabled": BOOLEAN,
})
EVIDENCE_ITEM = obj({"name": TOKEN, "passed": BOOLEAN, "detail_digest": nullable(DIGEST)})
KIND_INVENTORY = obj({"kind": enum("runtime", "active-skills"), "entries": array(OBSERVATION_INVENTORY_ENTRY)})
POINTER_ITEM = obj({
    "kind": enum("runtime", "active-skills"), "name": STRING, "target": STRING,
    "device": NONNEGATIVE, "inode": POSITIVE, "manifest_digest": DIGEST, "inventory_digest": DIGEST,
})
LEASE_EVIDENCE = obj({"device": NONNEGATIVE, "inode": POSITIVE, "holder_pid": nullable(POSITIVE), "exclusive": BOOLEAN})
PROCESS_ITEM = obj({"pid": POSITIVE, "uid": NONNEGATIVE, "executable_digest": nullable(DIGEST), "argv_digest": DIGEST})


FIELDS: Dict[str, Dict[str, Any]] = {
    "service-record": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "sequence": POSITIVE,
        "purpose": enum("nightly", "initial-cutover-smoke"), "schedule_digest": nullable(DIGEST),
        "scheduled_occurrence": nullable(UTC_MINUTE), "scheduled_window_id": nullable(DIGEST),
        "service_epoch": POSITIVE, "service_instance": UUID, "prior_record_digest": nullable(DIGEST),
        "state": enum("PREPARED", "SOURCE_CAPTURED", "SMOKE_STARTED", "CANDIDATE_STAGED", "CANDIDATE_WRITTEN",
                      "RECEIPT_WRITTEN", "VERIFIED", "COMMITTED", "ABORTED", "RECOVERY_REQUIRED", "ROLLED_BACK"),
        "recorded_at": TIMESTAMP, "runtime_manifest_digest": DIGEST, "skill_manifest_digest": DIGEST,
        "source_digest": nullable(DIGEST), "candidate_digest": nullable(DIGEST),
        "receipt_digest": nullable(DIGEST), "inventory": array(SERVICE_INVENTORY_ENTRY),
        "evidence": obj({"schema": {"const": 1}, "transaction_uuid": UUID, "sequence": POSITIVE,
                         "state": TOKEN, "assertions": array(EVIDENCE_ITEM), "evidence_digest": DIGEST}),
        "record_digest": DIGEST,
    },
    "state-evidence": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "sequence": POSITIVE, "state": TOKEN,
        "assertions": array(EVIDENCE_ITEM), "evidence_digest": DIGEST,
    },
    "candidate": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "purpose": enum("nightly", "initial-cutover-smoke"),
        "source_digest": DIGEST, "source_byte_count": POSITIVE, "generated_at": TIMESTAMP,
        "payload_digest": DIGEST, "candidate_digest": DIGEST,
    },
    "receipt": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "candidate_digest": DIGEST,
        "result": enum("PASS", "FAIL"), "checked_at": TIMESTAMP, "verifier_digest": DIGEST,
        "failure_code": nullable(TOKEN), "receipt_digest": DIGEST,
    },
    "manifest": {
        "schema": {"const": 1}, "kind": enum("runtime", "active-skills"), "version_digest": DIGEST,
        "created_at": TIMESTAMP, "policy_generation": POSITIVE, "release_lineage": UUID,
        "release_sequence": POSITIVE, "entries": array(VERSION_ENTRY), "inventory_digest": DIGEST,
        "execution_closure": nullable(EXECUTION_CLOSURE),
    },
    "inventory": {
        "schema": {"const": 1}, "kind": enum("runtime", "active-skills"), "release_lineage": UUID,
        "release_sequence": POSITIVE, "entries": array(VERSION_ENTRY), "inventory_digest": DIGEST,
    },
    "initial-target-bundle": {
        "schema": {"const": 1}, "runtime": TARGET_TUPLE, "active_skills": TARGET_TUPLE, "bundle_digest": DIGEST,
    },
    "authorization-payload": {
        "schema": {"const": 1}, "authorization_id": TOKEN,
        "operation": enum("install-initial", "promote-runtime", "promote-skill", "rollback-protected", "update-floor"),
        "approval_identity": TOKEN, "issued_at": TIMESTAMP, "expires_at": TIMESTAMP, "nonce": TOKEN,
        "transaction_uuid": UUID, "smoke_transaction_uuid": nullable(UUID), "service_epoch": POSITIVE,
        "policy_generation": POSITIVE, "release_lineage": UUID, "release_sequence": nullable(POSITIVE),
        "exact_destination": enum("protected-bundle", "runtime", "active-skills", "rollback-floor"),
        "prior_floor_digest": nullable(DIGEST), "proposed_floor": nullable(obj({"record_digest": DIGEST})),
        "proposed_floor_digest": nullable(DIGEST), "expected_current_manifest_digest": nullable(DIGEST),
        "expected_current_inventory_digest": nullable(DIGEST), "protected_source_digest": nullable(DIGEST),
        "candidate_digest": nullable(DIGEST), "target_manifest_digest": nullable(DIGEST),
        "target_inventory_digest": nullable(DIGEST), "initial_target_bundle": nullable(obj({"bundle_digest": DIGEST})),
        "initial_target_bundle_digest": nullable(DIGEST), "architecture_digest": DIGEST,
        "protocol_appendix_digest": DIGEST, "authority_packet_digest": DIGEST, "schema_bundle_digest": DIGEST,
        "installer_manifest_digest": DIGEST, "runtime_manifest_digest": DIGEST, "red_evidence_digest": DIGEST,
        "scheduler_before_digest": DIGEST, "scheduler_action": SCHEDULER_ACTION, "payload_digest": DIGEST,
    },
    "finalized-authorization": {
        "schema": {"const": 1}, "authorization_payload": obj({"payload_digest": DIGEST}),
        "payload_digest": DIGEST, "authority_grant": obj({"authority_grant_digest": DIGEST}),
        "authority_grant_digest": DIGEST, "authorization_digest": DIGEST,
    },
    "authority-grant": {
        "schema": {"const": 1}, "authorization_id": TOKEN, "payload_sha256": DIGEST,
        "operation": enum("install-initial", "promote-runtime", "promote-skill", "rollback-protected", "update-floor"),
        "destination": enum("protected-bundle", "runtime", "active-skills", "rollback-floor"),
        "issued_at": TIMESTAMP, "expires_at": TIMESTAMP, "nonce": TOKEN, "wire_sha256": DIGEST,
        "authority_grant_digest": DIGEST,
    },
    "consumed-record": {
        "schema": {"const": 1}, "authorization_id": TOKEN, "payload_digest": DIGEST,
        "authorization_digest": DIGEST, "authority_grant_digest": DIGEST, "installer_transaction_uuid": UUID,
        "smoke_transaction_uuid": nullable(UUID),
        "operation": enum("install-initial", "promote-runtime", "promote-skill", "rollback-protected", "update-floor"),
        "destination": enum("protected-bundle", "runtime", "active-skills", "rollback-floor"),
        "policy_generation": POSITIVE, "release_lineage": UUID, "release_sequence": nullable(POSITIVE),
        "prior_floor_digest": nullable(DIGEST), "proposed_floor_digest": nullable(DIGEST), "consumed_at": TIMESTAMP,
        "expected_current_manifest_digest": nullable(DIGEST), "expected_current_inventory_digest": nullable(DIGEST),
        "target_manifest_digest": nullable(DIGEST), "target_inventory_digest": nullable(DIGEST),
        "initial_target_bundle_digest": nullable(DIGEST), "scheduler_action_digest": DIGEST, "record_digest": DIGEST,
    },
    "installer-record": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "sequence": POSITIVE,
        "prior_record_digest": nullable(DIGEST), "state": TOKEN, "timestamp": TIMESTAMP,
        "authorization_id": TOKEN, "payload_digest": DIGEST, "authorization_digest": DIGEST,
        "authority_grant_digest": DIGEST, "policy_generation": POSITIVE, "release_lineage": UUID,
        "release_sequence": nullable(POSITIVE), "prior_floor_digest": nullable(DIGEST),
        "proposed_floor_digest": nullable(DIGEST), "expected_current_manifest_digest": nullable(DIGEST),
        "expected_current_inventory_digest": nullable(DIGEST), "target_manifest_digest": nullable(DIGEST),
        "target_inventory_digest": nullable(DIGEST), "initial_target_bundle_digest": nullable(DIGEST),
        "architecture_digest": DIGEST, "protocol_appendix_digest": DIGEST, "schema_bundle_digest": DIGEST,
        "authority_packet_digest": DIGEST, "installer_manifest_digest": DIGEST, "runtime_manifest_digest": DIGEST,
        "red_evidence_digest": DIGEST, "scheduler_before_digest": DIGEST, "scheduler_action": SCHEDULER_ACTION,
        "smoke_transaction_uuid": nullable(UUID), "smoke_gate_digest": nullable(DIGEST),
        "on_demand_plist_digest": nullable(DIGEST), "final_plist_digest": nullable(DIGEST),
        "tree_inventory": nullable(KIND_INVENTORY), "pointer_inventory": nullable(POINTER_ITEM),
        "operation_evidence": array(EVIDENCE_ITEM), "record_digest": DIGEST,
    },
    "broker-result": {
        "schema": {"const": 1}, "nonce": DIGEST, "child_pid": POSITIVE,
        "transaction_uuid": UUID, "source_digest": DIGEST,
        "runtime_manifest_digest": DIGEST, "runtime_inventory_digest": DIGEST,
        "candidate_sha256": DIGEST, "candidate_byte_count": POSITIVE,
        "result_digest": DIGEST,
    },
    "launchd-fd-bundle": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "broker_pid": POSITIVE,
        "nonce": DIGEST,
        "roles": {"const": ["entrypoint", "retained-executable", "version-root",
                            "runtime-manifest", "runtime-inventory", "source"]},
        "capability": {"const": "read-only-input-bundle"}, "record_digest": DIGEST,
    },
    "launch-receipt": {
        "schema": {"const": 1}, "kind": {"const": "launch-receipt"},
        "transaction_uuid": UUID, "nonce": DIGEST, "launcher_pid": POSITIVE,
        "child_pid": POSITIVE, "capability": {"const": "attestation-only"},
        "record_digest": DIGEST,
    },
    "swap-evidence": {
        "schema": {"const": 1}, "transaction_uuid": UUID, "sequence": POSITIVE,
        "state": TOKEN, "role": enum("rollback-floor", "epoch", "launchdaemon-plist", "runtime-pointer", "active-skills-pointer"),
        "parent_device": NONNEGATIVE, "parent_inode": POSITIVE,
        "current_name": STRING, "current_device": NONNEGATIVE, "current_inode": POSITIVE,
        "current_digest": nullable(DIGEST), "current_target": nullable(STRING),
        "staged_name": STRING, "staged_device": NONNEGATIVE, "staged_inode": POSITIVE,
        "staged_digest": nullable(DIGEST), "staged_target": nullable(STRING),
        "record_digest": DIGEST,
    },
    "rollback-floor": {
        "schema": {"const": 1}, "policy_generation": POSITIVE, "release_lineage": UUID,
        "minimum_release_sequence": NONNEGATIVE, "permitted_versions": array(FLOOR_ENTRY), "updated_at": TIMESTAMP,
        "prior_floor_digest": nullable(DIGEST), "authorization_id": TOKEN, "record_digest": DIGEST,
    },
    "epoch": {
        "epoch": POSITIVE, "schema": {"const": 1}, "service_instance": UUID, "updated_at": TIMESTAMP,
    },
    "scheduler-snapshot": {
        "schema": {"const": 1}, "timestamp": TIMESTAMP, "old_job_id": nullable(TOKEN),
        "old_persisted_enabled": BOOLEAN, "old_schedule": nullable(STRING), "old_script_path": nullable(STRING),
        "old_script_digest": nullable(DIGEST), "hermes_jobs_state_digest": DIGEST,
        "launchd_label": {"const": "system/com.nous.hermes.loop-a"}, "installed_plist_digest": nullable(DIGEST),
        "on_demand_plist_digest": nullable(DIGEST), "final_plist_digest": nullable(DIGEST),
        "launchctl_disabled": BOOLEAN, "launchctl_loaded": BOOLEAN, "launchctl_pid": nullable(POSITIVE),
        "service_lease": LEASE_EVIDENCE, "matching_processes": array(PROCESS_ITEM), "record_digest": DIGEST,
    },
    "scheduler-admission": {
        "schema": {"const": 1}, "daily_utc_hhmm": {"type": "string", "pattern": "^[0-2][0-9]:[0-5][0-9]$"},
        "admission_seconds": {"type": "integer", "minimum": 1, "maximum": 3600}, "schedule_digest": DIGEST,
    },
    "smoke-gate": {
        "schema": {"const": 1}, "authorization_id": TOKEN, "installer_transaction_uuid": UUID,
        "smoke_transaction_uuid": UUID, "service_epoch": POSITIVE, "service_instance": UUID,
        "runtime_manifest_digest": DIGEST, "runtime_inventory_digest": DIGEST,
        "skill_manifest_digest": DIGEST, "skill_inventory_digest": DIGEST,
        "purpose": {"const": "initial-cutover-smoke"}, "on_demand_plist_digest": DIGEST,
        "issued_at": TIMESTAMP, "expires_at": TIMESTAMP, "record_digest": DIGEST,
    },
}

# Nested finalized objects are embedded in full rather than represented by digest-only placeholders.
# This keeps each standalone schema closed and independently auditable without a remote resolver.
FIELDS["service-record"]["evidence"] = obj(FIELDS["state-evidence"])
FIELDS["authorization-payload"]["proposed_floor"] = nullable(obj(FIELDS["rollback-floor"]))
FIELDS["authorization-payload"]["initial_target_bundle"] = nullable(obj(FIELDS["initial-target-bundle"]))
FIELDS["finalized-authorization"]["authorization_payload"] = obj(FIELDS["authorization-payload"])
FIELDS["finalized-authorization"]["authority_grant"] = obj(FIELDS["authority-grant"])

SELF_DIGEST_FIELDS = {
    "service-record": "record_digest", "state-evidence": "evidence_digest", "candidate": "candidate_digest",
    "receipt": "receipt_digest", "manifest": "version_digest", "inventory": "inventory_digest",
    "initial-target-bundle": "bundle_digest", "authorization-payload": "payload_digest",
    "finalized-authorization": "authorization_digest", "authority-grant": "authority_grant_digest",
    "consumed-record": "record_digest", "installer-record": "record_digest", "rollback-floor": "record_digest",
    "scheduler-snapshot": "record_digest", "scheduler-admission": "schedule_digest",
    "smoke-gate": "record_digest", "swap-evidence": "record_digest",
    "broker-result": "result_digest", "launchd-fd-bundle": "record_digest",
    "launch-receipt": "record_digest",
}


def _schema(base: str, phase: str) -> Dict[str, Any]:
    properties = deepcopy(FIELDS[base])
    digest_field = SELF_DIGEST_FIELDS.get(base)
    if digest_field is not None:
        properties[digest_field] = deepcopy(NULL if phase == "preimage" else DIGEST)
    value = obj(properties)
    value["$schema"] = DRAFT
    value["$id"] = f"urn:nous:hermes:loop-a:{base}-{phase}-v1"
    return value


def build_schema_bundle() -> Dict[str, Any]:
    schemas: Dict[str, Any] = {}
    for base in sorted(FIELDS, key=lambda item: item.encode("ascii")):
        for phase in ("final", "preimage"):
            name = f"{base}-{phase}-v1"
            schema = _schema(base, phase)
            schemas[name] = {"schema": schema, "schema_digest": hashlib.sha256(canonical_bytes(schema)).hexdigest()}
    schemas = dict(sorted(schemas.items(), key=lambda item: item[0].encode("ascii")))
    preimage = {"schema": 1, "schemas": schemas, "bundle_digest": None}
    return with_self_digest(preimage, "bundle_digest")


def validate_schema_bundle(value: Dict[str, Any]) -> None:
    expected = build_schema_bundle()
    if value != expected:
        raise SchemaBundleError("schema bundle differs from the authoritative local candidate")


def export_schema_bundle(path: Any, check: bool = False) -> bytes:
    target = Path(path)
    expected = canonical_bytes(build_schema_bundle())
    if check:
        try:
            actual = target.read_bytes()
        except FileNotFoundError as exc:
            raise SchemaBundleError("schema bundle drift: artifact is missing") from exc
        if actual != expected:
            raise SchemaBundleError("schema bundle drift: artifact bytes differ")
        return actual
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(expected)
    if target.read_bytes() != expected:
        raise SchemaBundleError("schema bundle write readback mismatch")
    return expected


def _same_json_scalar(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right


def _validate_json_schema(schema: Dict[str, Any], value: Any, path: str) -> None:
    if "oneOf" in schema:
        successes = 0
        for option in schema["oneOf"]:
            try:
                _validate_json_schema(option, value, path)
                successes += 1
            except SchemaBundleError:
                pass
        if successes != 1:
            raise SchemaBundleError(f"{path}: expected exactly one schema branch")
        return
    if "const" in schema and not _same_json_scalar(value, schema["const"]):
        raise SchemaBundleError(f"{path}: const mismatch")
    if "enum" in schema and not any(_same_json_scalar(value, item) for item in schema["enum"]):
        raise SchemaBundleError(f"{path}: enum mismatch")
    kind = schema.get("type")
    if kind == "null":
        if value is not None:
            raise SchemaBundleError(f"{path}: expected null")
    elif kind == "boolean":
        if not isinstance(value, bool):
            raise SchemaBundleError(f"{path}: expected boolean")
    elif kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchemaBundleError(f"{path}: expected integer")
        if "minimum" in schema and value < schema["minimum"]:
            raise SchemaBundleError(f"{path}: integer below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise SchemaBundleError(f"{path}: integer above maximum")
    elif kind == "string":
        if not isinstance(value, str):
            raise SchemaBundleError(f"{path}: expected string")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            raise SchemaBundleError(f"{path}: string pattern mismatch")
    elif kind == "array":
        if not isinstance(value, list):
            raise SchemaBundleError(f"{path}: expected array")
        for index, item in enumerate(value):
            _validate_json_schema(schema["items"], item, f"{path}[{index}]")
    elif kind == "object":
        if not isinstance(value, dict):
            raise SchemaBundleError(f"{path}: expected object")
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        if set(value) != required or set(properties) != required:
            raise SchemaBundleError(f"{path}: object fields differ from exact schema")
        for field, child_schema in properties.items():
            _validate_json_schema(child_schema, value[field], f"{path}.{field}")


def validate_instance(schema_name: str, value: Any, bundle: Optional[Dict[str, Any]] = None) -> None:
    selected = build_schema_bundle() if bundle is None else bundle
    validate_schema_bundle(selected)
    try:
        schema = selected["schemas"][schema_name]["schema"]
    except (KeyError, TypeError) as exc:
        raise SchemaBundleError("unknown schema name") from exc
    _validate_json_schema(schema, value, schema_name)
    if schema_name.endswith("-final-v1"):
        base = schema_name[:-len("-final-v1")]
        digest_field = SELF_DIGEST_FIELDS.get(base)
        if digest_field is None:
            return
        preimage = dict(value)
        digest = preimage[digest_field]
        preimage[digest_field] = None
        expected = hashlib.sha256(canonical_bytes(preimage)).hexdigest()
        if digest != expected:
            raise SchemaBundleError(f"{schema_name}: self digest mismatch")
