from __future__ import annotations

from copy import deepcopy

import pytest

from loop_a_protected.canonical import with_self_digest
from loop_a_protected.policy import finalize_initial_target_bundle
from loop_a_protected.schema_bundle import (
    SchemaBundleError,
    build_schema_bundle,
    export_schema_bundle,
    validate_instance,
    validate_schema_bundle,
)


BASES = {
    "service-record", "state-evidence", "candidate", "receipt", "manifest", "inventory",
    "initial-target-bundle", "authorization-payload", "finalized-authorization", "authority-grant",
    "consumed-record", "installer-record", "rollback-floor", "epoch", "scheduler-snapshot",
    "scheduler-admission", "smoke-gate", "swap-evidence", "broker-result",
    "launchd-fd-bundle", "launch-receipt",
}
SELF_DIGEST_FIELDS = {
    "service-record": "record_digest", "state-evidence": "evidence_digest",
    "candidate": "candidate_digest", "receipt": "receipt_digest", "manifest": "version_digest",
    "inventory": "inventory_digest", "initial-target-bundle": "bundle_digest",
    "authorization-payload": "payload_digest", "finalized-authorization": "authorization_digest",
    "authority-grant": "authority_grant_digest", "consumed-record": "record_digest",
    "installer-record": "record_digest", "rollback-floor": "record_digest",
    "scheduler-snapshot": "record_digest", "scheduler-admission": "schedule_digest",
    "smoke-gate": "record_digest", "swap-evidence": "record_digest",
    "broker-result": "result_digest", "launchd-fd-bundle": "record_digest",
    "launch-receipt": "record_digest",
}
EXPECTED = {f"{base}-{phase}-v1" for base in BASES for phase in ("preimage", "final")}


def object_nodes(value):
    if isinstance(value, dict):
        if value.get("type") == "object":
            yield value
        for child in value.values():
            yield from object_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from object_nodes(child)


def test_schema_bundle_export_is_deterministic_and_check_is_read_only(tmp_path):
    target = tmp_path / "schema-bundle.json"
    exported = export_schema_bundle(target)
    before = target.read_bytes()
    assert exported == before
    assert export_schema_bundle(target, check=True) == before
    target.write_bytes(b"tampered\n")
    with pytest.raises(SchemaBundleError, match="drift"):
        export_schema_bundle(target, check=True)
    assert target.read_bytes() == b"tampered\n"


def test_bundle_is_complete_deterministic_self_digested_and_closed():
    first = build_schema_bundle()
    second = build_schema_bundle()
    validate_schema_bundle(first)
    assert first == second
    assert set(first["schemas"]) == EXPECTED
    assert list(first["schemas"]) == sorted(first["schemas"], key=lambda item: item.encode("ascii"))
    assert len(first["bundle_digest"]) == 64
    for entry in first["schemas"].values():
        assert len(entry["schema_digest"]) == 64
        for node in object_nodes(entry["schema"]):
            assert node.get("additionalProperties") is False
            assert set(node["required"]) == set(node["properties"])


def test_every_preimage_and_final_schema_has_distinct_explicit_digest_rule():
    bundle = build_schema_bundle()
    for base, digest_field in SELF_DIGEST_FIELDS.items():
        pre = bundle["schemas"][f"{base}-preimage-v1"]["schema"]
        final = bundle["schemas"][f"{base}-final-v1"]["schema"]
        assert pre["properties"][digest_field] == {"type": "null"}
        assert final["properties"][digest_field]["pattern"] == "^[0-9a-f]{64}$"
        assert pre != final


def test_nested_final_objects_embed_the_complete_closed_schema():
    bundle = build_schema_bundle()
    def properties(base, field):
        schema = bundle["schemas"][f"{base}-final-v1"]["schema"]["properties"][field]
        if "oneOf" in schema:
            schema = schema["oneOf"][0]
        return set(schema["properties"])
    assert properties("authorization-payload", "proposed_floor") == set(
        bundle["schemas"]["rollback-floor-final-v1"]["schema"]["properties"]
    )
    assert properties("authorization-payload", "initial_target_bundle") == set(
        bundle["schemas"]["initial-target-bundle-final-v1"]["schema"]["properties"]
    )
    assert properties("finalized-authorization", "authorization_payload") == set(
        bundle["schemas"]["authorization-payload-final-v1"]["schema"]["properties"]
    )
    assert properties("finalized-authorization", "authority_grant") == set(
        bundle["schemas"]["authority-grant-final-v1"]["schema"]["properties"]
    )


def test_frozen_v7_epoch_smoke_gate_and_consumed_record_field_sets_are_literal():
    bundle = build_schema_bundle()
    def fields(name):
        return set(bundle["schemas"][f"{name}-final-v1"]["schema"]["properties"])

    assert fields("epoch") == {"epoch", "schema", "service_instance", "updated_at"}
    assert fields("smoke-gate") == {
        "schema", "authorization_id", "installer_transaction_uuid", "smoke_transaction_uuid",
        "service_epoch", "service_instance", "runtime_manifest_digest", "runtime_inventory_digest",
        "skill_manifest_digest", "skill_inventory_digest", "purpose", "on_demand_plist_digest",
        "issued_at", "expires_at", "record_digest",
    }
    assert fields("consumed-record") == {
        "schema", "authorization_id", "payload_digest", "authorization_digest", "authority_grant_digest",
        "installer_transaction_uuid", "smoke_transaction_uuid", "operation", "destination",
        "policy_generation", "release_lineage", "release_sequence", "prior_floor_digest",
        "proposed_floor_digest", "consumed_at", "expected_current_manifest_digest",
        "expected_current_inventory_digest", "target_manifest_digest", "target_inventory_digest",
        "initial_target_bundle_digest", "scheduler_action_digest", "record_digest",
    }
    assert bundle["schemas"]["epoch-preimage-v1"]["schema"]["properties"] == \
           bundle["schemas"]["epoch-final-v1"]["schema"]["properties"]


def test_manifest_and_inventory_embed_version_tree_entries_not_runtime_observation_entries():
    bundle = build_schema_bundle()
    expected = {"relative_path", "type", "mode", "uid", "gid", "size", "sha256", "executable"}
    for base in ("manifest", "inventory"):
        entry = bundle["schemas"][f"{base}-final-v1"]["schema"]["properties"]["entries"]["items"]
        assert set(entry["properties"]) == expected
        assert set(entry["required"]) == expected


def test_schema_dispatcher_enforces_shape_phase_and_self_digest():
    lineage = "123e4567-e89b-42d3-a456-426614174000"
    runtime = {"kind": "runtime", "release_lineage": lineage, "release_sequence": 1,
               "manifest_digest": "0" * 64, "inventory_digest": "1" * 64}
    skills = {"kind": "active-skills", "release_lineage": lineage, "release_sequence": 2,
              "manifest_digest": "2" * 64, "inventory_digest": "3" * 64}
    finalized = finalize_initial_target_bundle(runtime, skills)
    preimage = dict(finalized, bundle_digest=None)
    validate_instance("initial-target-bundle-preimage-v1", preimage)
    validate_instance("initial-target-bundle-final-v1", finalized)
    for forged in (
        dict(finalized, bundle_digest=None),
        dict(finalized, bundle_digest="f" * 64),
        {**finalized, "extra": None},
        {key: value for key, value in finalized.items() if key != "runtime"},
    ):
        with pytest.raises(SchemaBundleError):
            validate_instance("initial-target-bundle-final-v1", forged)
    with pytest.raises(SchemaBundleError):
        validate_instance("unknown-v1", finalized)


def test_new_darwin_wire_schemas_are_exact_and_mutation_closed():
    bundle_record = with_self_digest({
        "schema": 1,
        "transaction_uuid": "123e4567-e89b-42d3-a456-426614174000",
        "broker_pid": 10,
        "nonce": "a" * 64,
        "roles": ["entrypoint", "retained-executable", "version-root", "runtime-manifest",
                  "runtime-inventory", "source"],
        "capability": "read-only-input-bundle",
        "record_digest": None,
    }, "record_digest")
    launch_receipt = with_self_digest({
        "schema": 1,
        "kind": "launch-receipt",
        "transaction_uuid": "123e4567-e89b-42d3-a456-426614174000",
        "nonce": "b" * 64,
        "launcher_pid": 11,
        "child_pid": 12,
        "capability": "attestation-only",
        "record_digest": None,
    }, "record_digest")
    for schema_name, record in (
        ("launchd-fd-bundle-final-v1", bundle_record),
        ("launch-receipt-final-v1", launch_receipt),
    ):
        validate_instance(schema_name, record)
        for forged in (
            {**record, "record_digest": "f" * 64},
            {**record, "extra": None},
            {key: value for key, value in record.items() if key != "capability"},
        ):
            with pytest.raises(SchemaBundleError):
                validate_instance(schema_name, forged)
    wrong_roles = dict(bundle_record)
    wrong_roles["roles"] = list(reversed(wrong_roles["roles"]))
    wrong_roles["record_digest"] = None
    wrong_roles = with_self_digest(wrong_roles, "record_digest")
    with pytest.raises(SchemaBundleError):
        validate_instance("launchd-fd-bundle-final-v1", wrong_roles)


def test_bundle_rejects_schema_or_digest_substitution():
    for mutator in (
        lambda value: value["schemas"].pop("receipt-final-v1"),
        lambda value: value["schemas"]["receipt-final-v1"].update(schema_digest="0" * 64),
        lambda value: value.update(bundle_digest="0" * 64),
        lambda value: value["schemas"]["receipt-final-v1"]["schema"]["properties"].update(extra={"type": "null"}),
    ):
        forged = deepcopy(build_schema_bundle())
        mutator(forged)
        with pytest.raises(SchemaBundleError):
            validate_schema_bundle(forged)
