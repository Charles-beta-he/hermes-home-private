from __future__ import annotations

import hashlib
import os

import pytest

from loop_a_protected.candidate_payload import canonical_candidate_payload
from loop_a_protected.canonical import with_self_digest
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.journal_store import (
    append_journal_record as _append_journal_record,
    read_journal_records,
)
from loop_a_protected.service_journal import finalize_service_record, finalize_state_evidence


TX = "12345678-1234-5678-9234-567812345678"
INSTANCE = "123e4567-e89b-42d3-a456-426614174001"
SOURCE = "b" * 64
MANIFEST = "c" * 64
INVENTORY = "d" * 64
SKILLS = "e" * 64
SKILL_NAME = "example-skill"
CANDIDATE_CONTENT = b"fixed-candidate-payload"
PAYLOAD = canonical_candidate_payload(
    run_id=TX, skill_name=SKILL_NAME, source_sha256=SOURCE,
    candidate_bytes=CANDIDATE_CONTENT,
)


class Gate:
    def __init__(self, fail_at=None):
        self.calls = 0
        self.fail_at = fail_at
        self.armed = False

    def assert_live(self):
        self.calls += 1
        if self.armed or self.fail_at == self.calls:
            raise RuntimeError("root mutation gate failed")


def append_journal_record(*args, **kwargs):
    kwargs["gate"] = kwargs.get("gate", Gate())
    return _append_journal_record(*args, **kwargs)


class Metadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd):
        return 0

    def has_extended_acl(self, fd):
        return False


def _owner(fd):
    status = os.fstat(fd)
    return status.st_uid, status.st_gid


def _record(state, sequence, prior, candidate_digest=None, inventory=None):
    evidence = finalize_state_evidence(TX, sequence, state, [
        {"name": "broker-fixed-transition", "passed": True, "detail_digest": SOURCE},
    ])
    return finalize_service_record({
        "schema": 1,
        "transaction_uuid": TX,
        "sequence": sequence,
        "purpose": "initial-cutover-smoke",
        "schedule_digest": None,
        "scheduled_occurrence": None,
        "scheduled_window_id": None,
        "service_epoch": 1,
        "service_instance": INSTANCE,
        "prior_record_digest": prior,
        "state": state,
        "recorded_at": f"2026-08-03T01:00:{sequence:02d}Z",
        "runtime_manifest_digest": MANIFEST,
        "skill_manifest_digest": SKILLS,
        "source_digest": None if state == "PREPARED" else SOURCE,
        "candidate_digest": candidate_digest,
        "receipt_digest": None,
        "inventory": [] if inventory is None else inventory,
        "evidence": evidence,
        "record_digest": None,
    })


def _open_staged(tmp_path):
    records_path = tmp_path / "records"
    candidates_path = tmp_path / "candidates"
    records_path.mkdir(mode=0o700)
    candidates_path.mkdir(mode=0o700)
    records_fd = os.open(records_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    candidates_fd = os.open(candidates_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    prior = None
    for sequence, state in enumerate(("PREPARED", "SOURCE_CAPTURED", "SMOKE_STARTED", "CANDIDATE_STAGED"), 1):
        record = _record(state, sequence, prior)
        append_journal_record(
            records_fd, record, *_owner(records_fd), TX, Metadata(), journal_kind="service",
        )
        prior = record["record_digest"]
    return records_fd, candidates_fd


def _adapter(records_fd, candidates_fd, fault_hook=None):
    from loop_a_protected.broker_transaction import JournalCandidateTransaction

    return JournalCandidateTransaction(
        records_fd=records_fd,
        candidates_fd=candidates_fd,
        uid=_owner(records_fd)[0],
        gid=_owner(records_fd)[1],
        worker_uid=max(1, os.geteuid() + 1),
        metadata=Metadata(),
        transaction_uuid=TX,
        skill_name=SKILL_NAME,
        runtime_inventory_digest=INVENTORY,
        source_byte_count=123,
        timestamp=lambda: "2026-08-03T01:01:00Z",
        fault_hook=fault_hook,
    )


def test_transaction_adapter_rejects_nonbroker_or_worker_owned_publication_identity(tmp_path, monkeypatch):
    import loop_a_protected.broker_transaction as transaction_module

    records_fd, candidates_fd = _open_staged(tmp_path)
    try:
        broker_uid, broker_gid = _owner(records_fd)
        monkeypatch.setattr(transaction_module.os, "geteuid", lambda: broker_uid + 1)
        with pytest.raises(transaction_module.BrokerTransactionError, match="effective broker UID"):
            transaction_module.JournalCandidateTransaction(
                records_fd=records_fd, candidates_fd=candidates_fd,
                uid=broker_uid, gid=broker_gid, worker_uid=broker_uid + 2,
                metadata=Metadata(), transaction_uuid=TX, skill_name=SKILL_NAME,
                runtime_inventory_digest=INVENTORY, source_byte_count=123,
                timestamp=lambda: "2026-08-03T01:01:00Z",
            )
        assert os.listdir(candidates_fd) == []
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_fixed_transaction_publishes_exact_tree_and_appends_candidate_written(tmp_path):
    records_fd, candidates_fd = _open_staged(tmp_path)
    try:
        adapter = _adapter(records_fd, candidates_fd)
        binding = adapter.snapshot()
        assert binding.transaction_uuid == TX
        assert binding.state == "CANDIDATE_STAGED"
        assert binding.runtime_manifest_digest == MANIFEST
        assert binding.runtime_inventory_digest == INVENTORY

        payload_digest = hashlib.sha256(PAYLOAD).hexdigest()
        committed = adapter.commit_candidate(PAYLOAD, payload_digest, Gate())
        assert committed.byte_count == len(PAYLOAD)
        assert committed.candidate_sha256 == payload_digest
        assert set(os.listdir(candidates_fd)) == {"candidate"}

        candidate_fd = os.open("candidate", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=candidates_fd)
        try:
            assert set(os.listdir(candidate_fd)) == {"candidate.json", "payload.bin"}
            payload_fd = os.open("payload.bin", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=candidate_fd)
            candidate_record_fd = os.open("candidate.json", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=candidate_fd)
            try:
                assert os.read(payload_fd, 1024) == PAYLOAD
                candidate_record = os.read(candidate_record_fd, 65536)
                assert b'"payload_digest":"' + payload_digest.encode() + b'"' in candidate_record
            finally:
                os.close(payload_fd)
                os.close(candidate_record_fd)
        finally:
            os.close(candidate_fd)

        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert [record["state"] for record in records] == [
            "PREPARED", "SOURCE_CAPTURED", "SMOKE_STARTED", "CANDIDATE_STAGED", "CANDIDATE_WRITTEN",
        ]
        assert records[-1]["candidate_digest"]
        assert {item["role"] for item in records[-1]["inventory"]} == {
            "candidate-payload", "candidate-record",
        }
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_root_gate_failure_inside_commit_precedes_candidate_or_journal_mutation(tmp_path):
    records_fd, candidates_fd = _open_staged(tmp_path)
    try:
        adapter = _adapter(records_fd, candidates_fd)
        with pytest.raises(RuntimeError, match="root mutation gate failed"):
            adapter.commit_candidate(PAYLOAD, hashlib.sha256(PAYLOAD).hexdigest(), Gate(fail_at=1))
        assert os.listdir(candidates_fd) == []
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "CANDIDATE_STAGED"
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_publication_failure_is_durably_marked_recovery_required(tmp_path):
    from loop_a_protected.broker_transaction import BrokerTransactionRecoveryRequired

    records_fd, candidates_fd = _open_staged(tmp_path)

    def fail(event, **_kwargs):
        if event == "after_tree_create":
            raise OSError("injected publication failure")

    try:
        adapter = _adapter(records_fd, candidates_fd, fault_hook=fail)
        with pytest.raises(BrokerTransactionRecoveryRequired):
            adapter.commit_candidate(PAYLOAD, hashlib.sha256(PAYLOAD).hexdigest(), Gate())
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "RECOVERY_REQUIRED"
        assert records[-1]["candidate_digest"] is None
        assert os.listdir(candidates_fd) == [f".candidate.txn-{TX}.tmp"]
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_sticky_gate_loss_before_candidate_written_append_leaves_staged_journal(tmp_path, monkeypatch):
    import loop_a_protected.broker_transaction as transaction_module
    from loop_a_protected.broker_transaction import BrokerTransactionRecoveryRequired

    records_fd, candidates_fd = _open_staged(tmp_path)
    gate = Gate()
    real_append = transaction_module.append_journal_record
    flipped = {"once": False}

    def lose_gate_after_outer_check(parent_fd, record, *args, **kwargs):
        if record["state"] == "CANDIDATE_WRITTEN" and not flipped["once"]:
            flipped["once"] = True
            gate.armed = True
        return real_append(parent_fd, record, *args, **kwargs)

    monkeypatch.setattr(transaction_module, "append_journal_record", lose_gate_after_outer_check)
    try:
        adapter = _adapter(records_fd, candidates_fd)
        with pytest.raises(BrokerTransactionRecoveryRequired, match="recovery append failed"):
            adapter.commit_candidate(PAYLOAD, hashlib.sha256(PAYLOAD).hexdigest(), gate)
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "CANDIDATE_STAGED"
        assert sorted(os.listdir(candidates_fd)) == ["candidate"]
        assert (tmp_path / "candidates" / "candidate" / "payload.bin").read_bytes() == PAYLOAD
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_candidate_written_append_failure_is_durably_reconciled(tmp_path, monkeypatch):
    import loop_a_protected.broker_transaction as transaction_module
    from loop_a_protected.broker_transaction import BrokerTransactionRecoveryRequired

    records_fd, candidates_fd = _open_staged(tmp_path)
    real_append = transaction_module.append_journal_record
    failed = {"once": False}

    def fail_candidate_written_once(parent_fd, record, *args, **kwargs):
        if record["state"] == "CANDIDATE_WRITTEN" and not failed["once"]:
            failed["once"] = True
            raise OSError("injected journal append failure")
        return real_append(parent_fd, record, *args, **kwargs)

    monkeypatch.setattr(transaction_module, "append_journal_record", fail_candidate_written_once)
    try:
        adapter = _adapter(records_fd, candidates_fd)
        with pytest.raises(BrokerTransactionRecoveryRequired, match="durably marked"):
            adapter.commit_candidate(PAYLOAD, hashlib.sha256(PAYLOAD).hexdigest(), Gate())
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "RECOVERY_REQUIRED"
        assert records[-1]["candidate_digest"] is not None
        assert sorted(os.listdir(candidates_fd)) == ["candidate"]
        assert (tmp_path / "candidates" / "candidate" / "payload.bin").read_bytes() == PAYLOAD
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_candidate_written_append_committed_then_threw_is_read_back_as_success(tmp_path, monkeypatch):
    import loop_a_protected.broker_transaction as transaction_module

    records_fd, candidates_fd = _open_staged(tmp_path)
    real_append = transaction_module.append_journal_record
    injected = {"once": False}

    def append_then_throw(parent_fd, record, *args, **kwargs):
        result = real_append(parent_fd, record, *args, **kwargs)
        if record["state"] == "CANDIDATE_WRITTEN" and not injected["once"]:
            injected["once"] = True
            raise OSError("injected post-commit acknowledgement loss")
        return result

    monkeypatch.setattr(transaction_module, "append_journal_record", append_then_throw)
    try:
        committed = _adapter(records_fd, candidates_fd).commit_candidate(
            PAYLOAD, hashlib.sha256(PAYLOAD).hexdigest(), Gate()
        )
        assert committed.candidate_sha256 == hashlib.sha256(PAYLOAD).hexdigest()
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "CANDIDATE_WRITTEN"
        assert all(record["state"] != "RECOVERY_REQUIRED" for record in records)
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_semantically_invalid_candidate_payload_is_rejected_before_any_publication(tmp_path):
    from loop_a_protected.broker_transaction import BrokerTransactionError

    records_fd, candidates_fd = _open_staged(tmp_path)
    try:
        adapter = _adapter(records_fd, candidates_fd)
        malformed = b'{"attacker":"chosen"}\n'
        with pytest.raises(BrokerTransactionError, match="semantic validation"):
            adapter.commit_candidate(malformed, hashlib.sha256(malformed).hexdigest(), Gate())
        assert os.listdir(candidates_fd) == []
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "CANDIDATE_STAGED"
        assert len(records) == 4
    finally:
        os.close(records_fd)
        os.close(candidates_fd)


def test_invalid_worker_result_through_real_adapter_leaves_no_candidate_or_journal_mutation(tmp_path):
    from loop_a_protected.broker_coordinator import BrokerCoordinatorError, accept_worker_candidate

    records_fd, candidates_fd = _open_staged(tmp_path)
    try:
        adapter = _adapter(records_fd, candidates_fd)
        binding = adapter.snapshot()

        class Gate:
            def assert_live(self):
                return None

        result = with_self_digest({
            "schema": 1,
            "nonce": "a" * 64,
            "child_pid": 1234,
            "transaction_uuid": TX,
            "source_digest": SOURCE,
            "runtime_manifest_digest": MANIFEST,
            "runtime_inventory_digest": INVENTORY,
            "candidate_sha256": hashlib.sha256(PAYLOAD).hexdigest(),
            "candidate_byte_count": len(PAYLOAD),
            "path": "attacker-controlled",
            "result_digest": None,
        }, "result_digest")
        with pytest.raises(BrokerCoordinatorError, match="worker result"):
            accept_worker_candidate(
                gate=Gate(), transaction=adapter, record=result, candidate_bytes=PAYLOAD,
                expected_nonce="a" * 64, expected_child_pid=1234, expected_binding=binding,
            )
        assert os.listdir(candidates_fd) == []
        records = read_journal_records(
            records_fd, *_owner(records_fd), Metadata(), journal_kind="service",
        )
        assert records[-1]["state"] == "CANDIDATE_STAGED"
        assert len(records) == 4
    finally:
        os.close(records_fd)
        os.close(candidates_fd)
