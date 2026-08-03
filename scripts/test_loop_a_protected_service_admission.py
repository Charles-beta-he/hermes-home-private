from __future__ import annotations

import fcntl
import os
from pathlib import Path

import pytest

from loop_a_protected.canonical import canonical_bytes, with_self_digest
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.service_admission import (
    ServiceAdmissionError,
    acquire_initial_smoke_epoch_lease,
    acquire_nightly_epoch_lease,
)


INSTANCE_1 = "123e4567-e89b-42d3-a456-426614174000"
INSTANCE_2 = "123e4567-e89b-42d3-a456-426614174001"


class Metadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd): return 0
    def has_extended_acl(self, fd): return False


def epoch(number=1, instance=INSTANCE_1):
    return {
        "epoch": number,
        "schema": 1,
        "service_instance": instance,
        "updated_at": f"2026-08-03T0{number}:00:00Z",
    }


def smoke_gate(**changes):
    value = {
        "schema": 1,
        "authorization_id": "auth-1",
        "installer_transaction_uuid": INSTANCE_1,
        "smoke_transaction_uuid": INSTANCE_2,
        "service_epoch": 1,
        "service_instance": INSTANCE_1,
        "runtime_manifest_digest": "a" * 64,
        "runtime_inventory_digest": "b" * 64,
        "skill_manifest_digest": "c" * 64,
        "skill_inventory_digest": "d" * 64,
        "purpose": "initial-cutover-smoke",
        "on_demand_plist_digest": "e" * 64,
        "issued_at": "2026-08-03T00:59:00Z",
        "expires_at": "2026-08-03T01:10:00Z",
        "record_digest": None,
    }
    value.update(changes)
    return with_self_digest(value, "record_digest")


def provision(path: Path, fenced=False):
    uid, gid = os.getuid(), os.getgid()
    os.chmod(path, 0o755)
    (path / "service").mkdir(mode=0o700)
    (path / "control").mkdir(mode=0o750)
    (path / "service" / "lease.lock").write_bytes(b"")
    os.chmod(path / "service" / "lease.lock", 0o600)
    (path / "control" / "epoch.json").write_bytes(canonical_bytes(epoch()))
    os.chmod(path / "control" / "epoch.json", 0o440)
    if fenced:
        (path / "FENCED").write_bytes(b"")
        os.chmod(path / "FENCED", 0o444)
    root_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    return uid, gid, root_fd, identity


def provision_initial_smoke_transaction(path: Path, gate, *, mutate_record=None):
    from loop_a_protected.service_journal import finalize_service_record, finalize_state_evidence

    txn = gate["smoke_transaction_uuid"]
    evidence = finalize_state_evidence(txn, 1, "PREPARED", [
        {"name": "initial-smoke-admission", "passed": True, "detail_digest": gate["record_digest"]},
    ])
    preimage = {
        "schema": 1, "transaction_uuid": txn, "sequence": 1,
        "purpose": "initial-cutover-smoke", "schedule_digest": None,
        "scheduled_occurrence": None, "scheduled_window_id": None,
        "service_epoch": gate["service_epoch"], "service_instance": gate["service_instance"],
        "prior_record_digest": None, "state": "PREPARED", "recorded_at": "2026-08-03T01:04:30Z",
        "runtime_manifest_digest": gate["runtime_manifest_digest"],
        "skill_manifest_digest": gate["skill_manifest_digest"],
        "source_digest": None, "candidate_digest": None, "receipt_digest": None,
        "inventory": [], "evidence": evidence, "record_digest": None,
    }
    if mutate_record is not None:
        mutate_record(preimage)
    record = finalize_service_record(preimage)
    transaction = path / "service-transactions" / txn
    records = transaction / "records"
    records.mkdir(parents=True)
    for name in ("sources", "candidates", "receipts"):
        (transaction / name).mkdir()
    os.chmod(path / "service-transactions", 0o700)
    os.chmod(transaction, 0o700)
    for child in transaction.iterdir():
        os.chmod(child, 0o700)
    record_path = records / "00000001-PREPARED.json"
    record_path.write_bytes(canonical_bytes(record))
    os.chmod(record_path, 0o400)
    return record_path, record


def append_initial_smoke_abort(path: Path, gate, prior):
    from loop_a_protected.service_journal import finalize_service_record, finalize_state_evidence

    txn = gate["smoke_transaction_uuid"]
    evidence = finalize_state_evidence(txn, 2, "ABORTED", [
        {"name": "abort", "passed": True, "detail_digest": prior["record_digest"]},
    ])
    record = finalize_service_record({
        "schema": 1, "transaction_uuid": txn, "sequence": 2,
        "purpose": "initial-cutover-smoke", "schedule_digest": None,
        "scheduled_occurrence": None, "scheduled_window_id": None,
        "service_epoch": gate["service_epoch"], "service_instance": gate["service_instance"],
        "prior_record_digest": prior["record_digest"], "state": "ABORTED",
        "recorded_at": "2026-08-03T01:05:00Z",
        "runtime_manifest_digest": gate["runtime_manifest_digest"],
        "skill_manifest_digest": gate["skill_manifest_digest"],
        "source_digest": None, "candidate_digest": None, "receipt_digest": None,
        "inventory": [], "evidence": evidence, "record_digest": None,
    })
    record_path = path / "service-transactions" / txn / "records" / "00000002-ABORTED.json"
    record_path.write_bytes(canonical_bytes(record))
    os.chmod(record_path, 0o400)
    return record


def test_service_run_holds_lease_and_adopts_durable_epoch(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path)
    try:
        with acquire_nightly_epoch_lease(root_fd, identity, uid, gid, uid + 1, gid, Metadata()) as run:
            assert run.startup_epoch == epoch()
            assert run.assert_epoch_current() == epoch()
            contender = os.open(tmp_path / "service" / "lease.lock", os.O_RDWR | os.O_NOFOLLOW)
            try:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(contender)
    finally:
        os.close(root_fd)


def test_per_mutation_check_rejects_new_fence_smoke_gate_or_lease_replacement(tmp_path):
    for mutation, message in (("fence", "FENCED"), ("smoke", "smoke gate"), ("lease", "lease.*identity")):
        root = tmp_path / mutation
        root.mkdir()
        uid, gid, root_fd, identity = provision(root)
        try:
            with acquire_nightly_epoch_lease(root_fd, identity, uid, gid, uid + 1, gid, Metadata()) as run:
                if mutation == "fence":
                    (root / "FENCED").write_bytes(b"")
                    os.chmod(root / "FENCED", 0o444)
                elif mutation == "smoke":
                    gate = root / "control" / "smoke-pending.json"
                    gate.write_bytes(b"{}")
                    os.chmod(gate, 0o440)
                else:
                    lease = root / "service" / "lease.lock"
                    lease.rename(root / "service" / "lease.retained")
                    lease.write_bytes(b"")
                    os.chmod(lease, 0o600)
                with pytest.raises(ServiceAdmissionError, match=message):
                    run.assert_epoch_current()
        finally:
            os.close(root_fd)


def test_service_run_rejects_durable_fence(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path, fenced=True)
    try:
        with pytest.raises(ServiceAdmissionError, match="FENCED"):
            with acquire_nightly_epoch_lease(root_fd, identity, uid, gid, uid + 1, gid, Metadata()):
                pytest.fail("fenced service must not run")
    finally:
        os.close(root_fd)


def test_nightly_service_rejects_present_smoke_gate_even_when_unfenced(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path)
    gate_path = tmp_path / "control" / "smoke-pending.json"
    gate_path.write_bytes(b"{}\n")
    os.chmod(gate_path, 0o440)
    try:
        with pytest.raises(ServiceAdmissionError, match="smoke gate"):
            with acquire_nightly_epoch_lease(root_fd, identity, uid, gid, uid + 1, gid, Metadata()):
                pytest.fail("normal nightly run must not consume smoke admission")
    finally:
        os.close(root_fd)


def test_retained_old_epoch_fd_cannot_bypass_name_reopen_check(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path)
    try:
        with acquire_nightly_epoch_lease(root_fd, identity, uid, gid, uid + 1, gid, Metadata()) as run:
            staged = tmp_path / "control" / ".epoch.next"
            staged.write_bytes(canonical_bytes(epoch(2, INSTANCE_2)))
            os.chmod(staged, 0o440)
            os.replace(staged, tmp_path / "control" / "epoch.json")
            with pytest.raises(ServiceAdmissionError, match="stale epoch"):
                run.assert_epoch_current()
    finally:
        os.close(root_fd)


def test_initial_smoke_requires_exact_live_gate_and_matching_epoch(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path)
    gate = smoke_gate()
    provision_initial_smoke_transaction(tmp_path, gate)
    gate_path = tmp_path / "control" / "smoke-pending.json"
    gate_path.write_bytes(canonical_bytes(gate))
    os.chmod(gate_path, 0o440)
    try:
        with acquire_initial_smoke_epoch_lease(
                root_fd, identity, uid, gid, uid + 1, gid, Metadata(),
                expected_smoke_gate=gate, admitted_at="2026-08-03T01:00:00Z") as run:
            assert run.assert_epoch_current() == epoch()
    finally:
        os.close(root_fd)


def test_initial_smoke_rejects_missing_malformed_or_misbound_prepared(tmp_path):
    cases = ("missing", "malformed", "misbound")
    for case in cases:
        root = tmp_path / case
        root.mkdir()
        uid, gid, root_fd, identity = provision(root)
        gate = smoke_gate()
        gate_path = root / "control" / "smoke-pending.json"
        gate_path.write_bytes(canonical_bytes(gate))
        os.chmod(gate_path, 0o440)
        if case == "malformed":
            record_path, _record = provision_initial_smoke_transaction(root, gate)
            os.chmod(record_path, 0o600)
            record_path.write_bytes(b"{}\n")
            os.chmod(record_path, 0o400)
        elif case == "misbound":
            provision_initial_smoke_transaction(
                root, gate, mutate_record=lambda record: record.update(runtime_manifest_digest="f" * 64),
            )
        try:
            with pytest.raises(ServiceAdmissionError, match="transaction|journal|binding|evidence"):
                with acquire_initial_smoke_epoch_lease(
                        root_fd, identity, uid, gid, uid + 1, gid, Metadata(),
                        expected_smoke_gate=gate, admitted_at="2026-08-03T01:00:00Z"):
                    pytest.fail("invalid initial-smoke PREPARED must not admit service")
        finally:
            os.close(root_fd)


def test_initial_smoke_rejects_extra_record_at_admission_and_terminal_after_admission(tmp_path):
    for phase in ("admission", "mutation"):
        root = tmp_path / phase
        root.mkdir()
        uid, gid, root_fd, identity = provision(root)
        gate = smoke_gate()
        _record_path, prepared = provision_initial_smoke_transaction(root, gate)
        gate_path = root / "control" / "smoke-pending.json"
        gate_path.write_bytes(canonical_bytes(gate))
        os.chmod(gate_path, 0o440)
        try:
            if phase == "admission":
                append_initial_smoke_abort(root, gate, prepared)
                with pytest.raises(ServiceAdmissionError, match="exactly PREPARED"):
                    with acquire_initial_smoke_epoch_lease(
                            root_fd, identity, uid, gid, uid + 1, gid, Metadata(),
                            expected_smoke_gate=gate, admitted_at="2026-08-03T01:00:00Z"):
                        pytest.fail("extra initial-smoke record must block admission")
            else:
                with acquire_initial_smoke_epoch_lease(
                        root_fd, identity, uid, gid, uid + 1, gid, Metadata(),
                        expected_smoke_gate=gate, admitted_at="2026-08-03T01:00:00Z") as run:
                    append_initial_smoke_abort(root, gate, prepared)
                    with pytest.raises(ServiceAdmissionError, match="terminal"):
                        run.assert_epoch_current()
        finally:
            os.close(root_fd)


def test_initial_smoke_rechecks_exact_gate_before_mutation(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path)
    gate = smoke_gate()
    provision_initial_smoke_transaction(tmp_path, gate)
    gate_path = tmp_path / "control" / "smoke-pending.json"
    gate_path.write_bytes(canonical_bytes(gate))
    os.chmod(gate_path, 0o440)
    try:
        with acquire_initial_smoke_epoch_lease(
                root_fd, identity, uid, gid, uid + 1, gid, Metadata(),
                expected_smoke_gate=gate, admitted_at="2026-08-03T01:00:00Z") as run:
            os.chmod(gate_path, 0o600)
            gate_path.write_bytes(canonical_bytes(smoke_gate(runtime_inventory_digest="f" * 64)))
            os.chmod(gate_path, 0o440)
            with pytest.raises(ServiceAdmissionError, match="differs"):
                run.assert_epoch_current()
    finally:
        os.close(root_fd)


@pytest.mark.parametrize(
    "gate,expected,now,message",
    [
        (smoke_gate(runtime_manifest_digest="f" * 64), smoke_gate(), "2026-08-03T01:00:00Z", "differs"),
        (smoke_gate(), smoke_gate(), "2026-08-03T00:58:00Z", "window"),
        (smoke_gate(), smoke_gate(), "2026-08-03T01:10:00Z", "window"),
        (smoke_gate(service_epoch=2), smoke_gate(service_epoch=2), "2026-08-03T01:00:00Z", "epoch"),
    ],
)
def test_initial_smoke_rejects_substitution_time_window_and_epoch_mismatch(tmp_path, gate, expected, now, message):
    uid, gid, root_fd, identity = provision(tmp_path)
    provision_initial_smoke_transaction(tmp_path, expected)
    gate_path = tmp_path / "control" / "smoke-pending.json"
    gate_path.write_bytes(canonical_bytes(gate))
    os.chmod(gate_path, 0o440)
    try:
        with pytest.raises(ServiceAdmissionError, match=message):
            with acquire_initial_smoke_epoch_lease(
                    root_fd, identity, uid, gid, uid + 1, gid, Metadata(),
                    expected_smoke_gate=expected, admitted_at=now):
                pytest.fail("invalid smoke gate must not admit service")
    finally:
        os.close(root_fd)


def test_malformed_or_noncanonical_epoch_fails_closed(tmp_path):
    uid, gid, root_fd, identity = provision(tmp_path)
    epoch_path = tmp_path / "control" / "epoch.json"
    os.chmod(epoch_path, 0o600)
    epoch_path.write_bytes(b'{"schema":1, "epoch":1}\n')
    os.chmod(epoch_path, 0o440)
    try:
        with pytest.raises(ServiceAdmissionError, match="epoch"):
            with acquire_nightly_epoch_lease(root_fd, identity, uid, gid, uid + 1, gid, Metadata()):
                pytest.fail("malformed epoch must not admit service")
    finally:
        os.close(root_fd)
