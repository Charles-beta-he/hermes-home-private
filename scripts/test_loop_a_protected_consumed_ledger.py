from __future__ import annotations

import hashlib
import multiprocessing
import os
from pathlib import Path

import pytest

from loop_a_protected.authority import (
    finalize_authorization,
    finalize_authorization_payload,
    parse_authority_grant_wire,
)
from loop_a_protected.canonical import canonical_bytes
from loop_a_protected.consumed_ledger import (
    AuthorizationConsumedError,
    consume_authorization,
    consumed_filename,
    derive_consumed_record_preimage,
    finalize_consumed_record,
)
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.root_gate import RootGateError, acquire_root_mutation_gate

D = "ab" * 32
D2 = "cd" * 32
TXN1 = "123e4567-e89b-42d3-a456-426614174000"
TXN2 = "123e4567-e89b-42d3-a456-426614174001"
NOW = "2026-08-03T01:05:00Z"


class TestMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd) -> int:
        return 0

    def has_extended_acl(self, fd):
        return False


class DirtyMetadata(TestMetadata):
    def xattr_bytes(self, fd) -> int:
        return 1 if (os.fstat(fd).st_mode & 0o777) == 0o640 else 0


def payload_preimage(transaction_uuid=TXN1, target_digest=D, expires_at="2026-08-03T01:10:00Z"):
    return {
        "schema": 1, "authorization_id": "auth-1", "operation": "promote-runtime",
        "approval_identity": "origin-user", "issued_at": "2026-08-03T01:00:00Z",
        "expires_at": expires_at, "nonce": "nonce-1", "transaction_uuid": transaction_uuid,
        "smoke_transaction_uuid": None, "service_epoch": 1, "policy_generation": 1,
        "release_lineage": TXN2, "release_sequence": 1, "exact_destination": "runtime",
        "prior_floor_digest": D, "proposed_floor": None, "proposed_floor_digest": None,
        "expected_current_manifest_digest": D, "expected_current_inventory_digest": D,
        "protected_source_digest": D, "candidate_digest": D, "target_manifest_digest": target_digest,
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


def authorization(transaction_uuid=TXN1, target_digest=D, expires_at="2026-08-03T01:10:00Z"):
    payload = finalize_authorization_payload(payload_preimage(transaction_uuid, target_digest, expires_at))
    raw = (
        f"HERMES-AUTH-V1 authorization_id=auth-1 payload_sha256={payload['payload_digest']} "
        "operation=promote-runtime destination=runtime issued_at=2026-08-03T01:00:00Z "
        f"expires_at={expires_at} nonce=nonce-1\n"
    ).encode("ascii")
    return finalize_authorization(payload, parse_authority_grant_wire(raw))


def observations(auth):
    payload = auth["authorization_payload"]
    return {
        "service_epoch": 1, "policy_generation": 1, "release_lineage": TXN2,
        "prior_floor_digest": D, "current_manifest_digest": D, "current_inventory_digest": D,
        "scheduler_before_digest": D,
        "scheduler_action_digest": hashlib.sha256(canonical_bytes(payload["scheduler_action"])).hexdigest(),
    }


class GateProbe:
    def old_job_is_inhibited(self): return True
    def launchd_is_disabled_and_booted_out(self): return True
    def matching_service_processes(self): return ()


def setup_root(path: Path):
    os.chmod(path, 0o755)
    (path / "locks").mkdir()
    (path / "service").mkdir()
    (path / "authorizations").mkdir()
    (path / "authorizations" / "consumed").mkdir()
    os.chmod(path / "locks", 0o755)
    os.chmod(path / "service", 0o700)
    os.chmod(path / "authorizations", 0o700)
    os.chmod(path / "authorizations" / "consumed", 0o700)
    (path / "locks" / "installer.lock").write_bytes(b"")
    (path / "service" / "lease.lock").write_bytes(b"")
    (path / "FENCED").write_bytes(b"")
    os.chmod(path / "locks" / "installer.lock", 0o640)
    os.chmod(path / "service" / "lease.lock", 0o600)
    os.chmod(path / "FENCED", 0o444)


def provision_prepared(path: Path, auth):
    from loop_a_protected.installer_journal import finalize_installer_record
    from test_loop_a_protected_installer_journal import fields

    payload = auth["authorization_payload"]
    preimage = fields(payload["operation"], payload["exact_destination"], "PREPARED", 1, None)
    direct = (
        "authorization_id", "transaction_uuid", "policy_generation", "release_lineage",
        "release_sequence", "prior_floor_digest", "proposed_floor_digest",
        "expected_current_manifest_digest", "expected_current_inventory_digest",
        "target_manifest_digest", "target_inventory_digest", "initial_target_bundle_digest",
        "architecture_digest", "protocol_appendix_digest", "schema_bundle_digest",
        "authority_packet_digest", "installer_manifest_digest", "runtime_manifest_digest",
        "red_evidence_digest", "scheduler_before_digest", "scheduler_action",
        "smoke_transaction_uuid",
    )
    for name in direct:
        preimage[name] = payload[name]
    preimage.update(
        payload_digest=auth["payload_digest"],
        authorization_digest=auth["authorization_digest"],
        authority_grant_digest=auth["authority_grant_digest"],
        on_demand_plist_digest=payload["scheduler_action"]["on_demand_plist_digest"],
        final_plist_digest=payload["scheduler_action"]["final_plist_digest"],
    )
    prepared = finalize_installer_record(preimage, payload["operation"], payload["exact_destination"])
    transaction = path / "installer-transactions" / payload["transaction_uuid"]
    records = transaction / "records"
    records.mkdir(parents=True)
    (transaction / "snapshots").mkdir()
    (transaction / "evidence").mkdir()
    os.chmod(path / "installer-transactions", 0o700)
    os.chmod(transaction, 0o700)
    for child in (records, transaction / "snapshots", transaction / "evidence"):
        os.chmod(child, 0o700)
    record_path = records / "00000001-PREPARED.json"
    record_path.write_bytes(canonical_bytes(prepared))
    os.chmod(record_path, 0o400)


def consume_at_root_fd(root_fd, auth, observed, metadata):
    status = os.fstat(root_fd)
    gate_context = acquire_root_mutation_gate(
        root_fd, (status.st_dev, status.st_ino), os.getuid(), os.getgid(),
        os.getuid(), os.getgid(), GateProbe(), metadata, nonblocking=False,
    )
    with gate_context as gate:
        return consume_authorization(
            root_fd, (status.st_dev, status.st_ino), auth, observed, NOW,
            os.getuid(), os.getgid(), os.getgid(), metadata, gate=gate,
        )


def consume(path: str, auth):
    root = Path(path)
    if not (root / "installer-transactions").exists():
        provision_prepared(root, auth)
    root_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        return consume_at_root_fd(root_fd, auth, observations(auth), TestMetadata())
    finally:
        os.close(root_fd)


def _worker(root, auth, start, queue):
    start.wait(5)
    try:
        _record, created = consume(root, auth)
        queue.put("created" if created else "idempotent")
    except AuthorizationConsumedError:
        queue.put("conflict")


def run_pair(tmp_path: Path, left, right):
    setup_root(tmp_path)
    provision_prepared(tmp_path, left)
    context = multiprocessing.get_context("spawn")
    start = context.Event(); queue = context.Queue()
    processes = [context.Process(target=_worker, args=(str(tmp_path), item, start, queue)) for item in (left, right)]
    for process in processes: process.start()
    start.set()
    results = [queue.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(timeout=10); assert process.exitcode == 0
    return sorted(results)


def test_consumed_record_is_derived_closed_and_self_digest_bound():
    auth = authorization()
    preimage = derive_consumed_record_preimage(auth, observations(auth), NOW)
    record = finalize_consumed_record(preimage)
    assert record["authorization_digest"] == auth["authorization_digest"]
    with pytest.raises(ValueError):
        finalize_consumed_record(dict(preimage, extra=True))


def test_filename_is_exact_authorization_id_not_an_incompatible_hash():
    assert consumed_filename("auth-1") == "auth-1.json"
    with pytest.raises(ValueError): consumed_filename("../escape")


def test_same_authorization_has_one_winner_and_replay_fails_closed_under_real_process_race(tmp_path):
    assert run_pair(tmp_path, authorization(), authorization()) == ["conflict", "created"]
    consumed = tmp_path / "authorizations" / "consumed"
    assert [item.name for item in consumed.glob("auth-1.json")] == ["auth-1.json"]
    with pytest.raises(AuthorizationConsumedError, match="already consumed"):
        consume(str(tmp_path), authorization())


def test_same_id_cannot_bind_other_transaction_or_target(tmp_path):
    assert run_pair(tmp_path, authorization(TXN1, D), authorization(TXN2, D)) == ["conflict", "created"]
    other = tmp_path / "other"; other.mkdir()
    setup_root(other)
    consume(str(other), authorization(TXN1, D))
    with pytest.raises(AuthorizationConsumedError, match="another authorization target"):
        consume(str(other), authorization(TXN1, D2))


def test_expired_or_live_precondition_mismatch_has_zero_effect(tmp_path):
    setup_root(tmp_path)
    expired = authorization(expires_at="2026-08-03T01:04:00Z")
    with pytest.raises(AuthorizationConsumedError, match="expired"):
        consume(str(tmp_path), expired)
    auth = authorization(); bad = observations(auth); bad["policy_generation"] = 2
    precondition_root = tmp_path / "precondition"
    precondition_root.mkdir()
    setup_root(precondition_root)
    provision_prepared(precondition_root, auth)
    root_fd = os.open(precondition_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with pytest.raises(AuthorizationConsumedError, match="precondition"):
            consume_at_root_fd(root_fd, auth, bad, TestMetadata())
    finally:
        os.close(root_fd)
    assert not (tmp_path / "authorizations" / "consumed" / "auth-1.json").exists()


def test_consumption_rejects_missing_durable_prepared(tmp_path):
    setup_root(tmp_path)
    auth = authorization()
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with pytest.raises(AuthorizationConsumedError, match="durable PREPARED"):
            consume_at_root_fd(root_fd, auth, observations(auth), TestMetadata())
    finally:
        os.close(root_fd)
    assert list((tmp_path / "authorizations" / "consumed").iterdir()) == []


def test_malformed_existing_record_fences_instead_of_overwriting(tmp_path):
    setup_root(tmp_path)
    name = consumed_filename("auth-1")
    target = tmp_path / "authorizations" / "consumed" / name
    target.write_bytes(b"{}\n"); os.chmod(target, 0o400)
    with pytest.raises(AuthorizationConsumedError, match="invalid"):
        consume(str(tmp_path), authorization())
    assert target.read_bytes() == b"{}\n"


def test_expired_root_gate_cannot_write_consumed_record(tmp_path):
    setup_root(tmp_path)
    auth = authorization()
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        status = os.fstat(root_fd)
        context = acquire_root_mutation_gate(
            root_fd, (status.st_dev, status.st_ino), os.getuid(), os.getgid(),
            os.getuid(), os.getgid(), GateProbe(), TestMetadata(), nonblocking=True,
        )
        with context as gate:
            pass
        with pytest.raises(AuthorizationConsumedError, match="validation"):
            consume_authorization(
                root_fd, (status.st_dev, status.st_ino), auth, observations(auth), NOW,
                os.getuid(), os.getgid(), os.getgid(), TestMetadata(), gate=gate,
            )
    finally:
        os.close(root_fd)
    assert not (tmp_path / "authorizations" / "consumed" / "auth-1.json").exists()


def test_lock_with_forbidden_metadata_is_rejected_by_root_gate_before_mutation(tmp_path):
    setup_root(tmp_path)
    auth = authorization()
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with pytest.raises(RootGateError, match="xattrs"):
            consume_at_root_fd(root_fd, auth, observations(auth), DirtyMetadata())
    finally:
        os.close(root_fd)
    assert not (tmp_path / "authorizations" / "consumed" / "auth-1.json").exists()
