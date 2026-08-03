from __future__ import annotations

import hashlib

import pytest

from loop_a_protected.policy import finalize_initial_target_bundle, finalize_rollback_floor
from loop_a_protected.authority import (
    AuthorityError,
    finalize_authorization,
    finalize_authorization_payload,
    parse_authority_grant_wire,
    validate_authorization,
    validate_grant_for_payload,
)

D = "ab" * 32
D2 = "cd" * 32
D3 = "ef" * 32
U1 = "123e4567-e89b-42d3-a456-426614174000"
U2 = "123e4567-e89b-42d3-a456-426614174001"


def payload_preimage():
    return {
        "schema": 1, "authorization_id": "auth-1", "operation": "promote-runtime",
        "approval_identity": "origin-user", "issued_at": "2026-08-03T01:00:00Z",
        "expires_at": "2026-08-03T01:10:00Z", "nonce": "nonce-1", "transaction_uuid": U1,
        "smoke_transaction_uuid": None, "service_epoch": 1, "policy_generation": 1,
        "release_lineage": U2, "release_sequence": 1, "exact_destination": "runtime",
        "prior_floor_digest": D, "proposed_floor": None, "proposed_floor_digest": None,
        "expected_current_manifest_digest": D, "expected_current_inventory_digest": D,
        "protected_source_digest": D, "candidate_digest": D, "target_manifest_digest": D,
        "target_inventory_digest": D, "initial_target_bundle": None,
        "initial_target_bundle_digest": None, "architecture_digest": D,
        "protocol_appendix_digest": D, "authority_packet_digest": D, "schema_bundle_digest": D,
        "installer_manifest_digest": D, "runtime_manifest_digest": D, "red_evidence_digest": D,
        "scheduler_before_digest": D, "scheduler_action": {
            "old_job_id": "600370f80d83", "expected_enabled": True, "target_enabled": False,
            "launchd_label": "system/com.nous.hermes.loop-a", "launchd_target_state": "disabled-unloaded",
            "on_demand_plist_digest": None, "final_plist_digest": D,
        },
        "payload_digest": None,
    }


def initial_payload_preimage():
    value = payload_preimage()
    runtime = {"kind": "runtime", "release_lineage": U2, "release_sequence": 1,
               "manifest_digest": D, "inventory_digest": D2}
    skills = {"kind": "active-skills", "release_lineage": U2, "release_sequence": 1,
              "manifest_digest": D2, "inventory_digest": D3}
    bundle = finalize_initial_target_bundle(runtime, skills)
    floor = finalize_rollback_floor(
        1, U2, 1,
        [
            {"kind": "active-skills", "release_sequence": 1, "manifest_digest": D2,
             "inventory_digest": D3, "disposition": "forward"},
            {"kind": "runtime", "release_sequence": 1, "manifest_digest": D,
             "inventory_digest": D2, "disposition": "forward"},
        ],
        "2026-08-03T01:00:00Z", None, "auth-1",
    )
    value.update({
        "operation": "install-initial", "exact_destination": "protected-bundle",
        "smoke_transaction_uuid": U2, "release_sequence": None, "prior_floor_digest": None,
        "proposed_floor": floor, "proposed_floor_digest": floor["record_digest"],
        "expected_current_manifest_digest": None, "expected_current_inventory_digest": None,
        "protected_source_digest": None, "candidate_digest": None,
        "target_manifest_digest": None, "target_inventory_digest": None,
        "initial_target_bundle": bundle, "initial_target_bundle_digest": bundle["bundle_digest"],
    })
    value["scheduler_action"] = dict(value["scheduler_action"], on_demand_plist_digest=D2)
    return value


def wire(payload):
    return (
        "HERMES-AUTH-V1 authorization_id=auth-1 payload_sha256=" + payload["payload_digest"] +
        " operation=promote-runtime destination=runtime issued_at=2026-08-03T01:00:00Z" +
        " expires_at=2026-08-03T01:10:00Z nonce=nonce-1\n"
    ).encode("ascii")


def test_payload_grant_and_final_authorization_are_acyclic_and_bound():
    payload = finalize_authorization_payload(payload_preimage())
    raw = wire(payload)
    grant = parse_authority_grant_wire(raw)
    validate_grant_for_payload(grant, payload)
    authorization = finalize_authorization(payload, grant)
    assert grant["wire_sha256"] == hashlib.sha256(raw).hexdigest()
    assert authorization["payload_digest"] == payload["payload_digest"]
    assert authorization["authority_grant_digest"] == grant["authority_grant_digest"]
    assert authorization["authorization_digest"]


@pytest.mark.parametrize(
    "mutator",
    [
        lambda b: b.replace(b"\n", b"\r\n"),
        lambda b: b.replace(b" operation=", b"  operation="),
        lambda b: b.replace(b"operation=promote-runtime destination=runtime", b"destination=runtime operation=promote-runtime"),
        lambda b: b + b"suffix",
        lambda b: b.replace(b"nonce=nonce-1", b"nonce=bad=value"),
    ],
)
def test_wire_rejects_any_normalization_or_grammar_change(mutator):
    payload = finalize_authorization_payload(payload_preimage())
    with pytest.raises(AuthorityError):
        parse_authority_grant_wire(mutator(wire(payload)))


def test_payload_rejects_unknown_fields_and_operation_nullability_substitution():
    extra = payload_preimage()
    extra["extra"] = None
    with pytest.raises(AuthorityError):
        finalize_authorization_payload(extra)
    wrong = payload_preimage()
    wrong["smoke_transaction_uuid"] = U2
    with pytest.raises(AuthorityError):
        finalize_authorization_payload(wrong)


def test_grant_rejects_payload_digest_destination_or_identity_substitution():
    payload = finalize_authorization_payload(payload_preimage())
    grant = parse_authority_grant_wire(wire(payload))
    for field, value in [("payload_digest", "cd" * 32), ("exact_destination", "active-skills"), ("nonce", "nonce-2")]:
        forged = dict(payload)
        forged[field] = value
        with pytest.raises(AuthorityError):
            validate_grant_for_payload(grant, forged)


def test_scheduler_action_is_an_exact_typed_object_not_a_token():
    for mutation in (
        "replace-protected-schedule",
        {"old_job_id": "600370f80d83"},
        {**payload_preimage()["scheduler_action"], "extra": None},
        {**payload_preimage()["scheduler_action"], "expected_enabled": 1},
        {**payload_preimage()["scheduler_action"], "final_plist_digest": "not-a-digest"},
    ):
        candidate = payload_preimage()
        candidate["scheduler_action"] = mutation
        with pytest.raises(AuthorityError):
            finalize_authorization_payload(candidate)


def test_finalized_authorization_validator_rejects_nested_or_outer_substitution():
    payload = finalize_authorization_payload(payload_preimage())
    grant = parse_authority_grant_wire(wire(payload))
    authorization = finalize_authorization(payload, grant)
    validate_authorization(authorization)
    for field, replacement in (
        ("payload_digest", D2),
        ("authority_grant_digest", D2),
        ("authorization_digest", D2),
    ):
        forged = dict(authorization)
        forged[field] = replacement
        with pytest.raises(AuthorityError):
            validate_authorization(forged)


def test_initial_payload_binds_finalized_bundle_and_floor_exactly():
    finalized = finalize_authorization_payload(initial_payload_preimage())
    assert finalized["initial_target_bundle_digest"] == finalized["initial_target_bundle"]["bundle_digest"]
    assert finalized["proposed_floor_digest"] == finalized["proposed_floor"]["record_digest"]

    bad_bundle = initial_payload_preimage()
    bad_bundle["initial_target_bundle"] = dict(bad_bundle["initial_target_bundle"])
    bad_bundle["initial_target_bundle"]["runtime"] = dict(bad_bundle["initial_target_bundle"]["runtime"], manifest_digest=D3)
    with pytest.raises(AuthorityError):
        finalize_authorization_payload(bad_bundle)

    bad_floor = initial_payload_preimage()
    bad_floor["proposed_floor"] = finalize_rollback_floor(
        1, U2, 1,
        [
            {"kind": "active-skills", "release_sequence": 1, "manifest_digest": D2,
             "inventory_digest": D3, "disposition": "forward"},
            {"kind": "runtime", "release_sequence": 2, "manifest_digest": D,
             "inventory_digest": D2, "disposition": "forward"},
        ],
        "2026-08-03T01:00:00Z", None, "auth-1",
    )
    bad_floor["proposed_floor_digest"] = bad_floor["proposed_floor"]["record_digest"]
    with pytest.raises(AuthorityError, match="bundle|floor"):
        finalize_authorization_payload(bad_floor)
