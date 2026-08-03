from __future__ import annotations

import os

import pytest

from loop_a_protected.canonical import canonical_bytes, with_self_digest
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.journal_store import (
    JournalStoreError,
    append_journal_record as _append_journal_record,
    read_journal_records,
)
from loop_a_protected.service_journal import finalize_service_record, finalize_state_evidence

TXN = "123e4567-e89b-42d3-a456-426614174000"
INSTANCE = "123e4567-e89b-42d3-a456-426614174001"
D0 = "0" * 64
D1 = "1" * 64


class LiveGate:
    def __init__(self, fail_after=None):
        self.calls = 0
        self.fail_after = fail_after

    def assert_live(self):
        self.calls += 1
        if self.fail_after is not None and self.calls > self.fail_after:
            raise RuntimeError("root mutation gate lost")


def append_journal_record(*args, **kwargs):
    kwargs["gate"] = kwargs.get("gate", LiveGate())
    return _append_journal_record(*args, **kwargs)


class TestMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd) -> int:
        return 0

    def has_extended_acl(self, fd) -> bool:
        return False


def record(sequence, state, prior=None):
    source = D0 if state != "PREPARED" else None
    evidence = finalize_state_evidence(TXN, sequence, state, [
        {"name": "held-fd-readback", "passed": True, "detail_digest": D0}
    ])
    return finalize_service_record({
        "schema": 1, "transaction_uuid": TXN, "sequence": sequence,
        "purpose": "initial-cutover-smoke", "schedule_digest": None,
        "scheduled_occurrence": None, "scheduled_window_id": None,
        "service_epoch": 1, "service_instance": INSTANCE,
        "prior_record_digest": prior, "state": state,
        "recorded_at": f"2026-08-03T01:00:{sequence:02d}Z",
        "runtime_manifest_digest": D0, "skill_manifest_digest": D1,
        "source_digest": source, "candidate_digest": None, "receipt_digest": None,
        "inventory": [], "evidence": evidence, "record_digest": None,
    })


def open_parent(path):
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def installer_prepared_and_authorization():
    from loop_a_protected.authority import (
        finalize_authorization,
        finalize_authorization_payload,
        parse_authority_grant_wire,
    )
    from loop_a_protected.installer_journal import finalize_installer_record
    from test_loop_a_protected_authority import payload_preimage, wire
    from test_loop_a_protected_installer_journal import fields

    payload = finalize_authorization_payload(payload_preimage())
    authorization = finalize_authorization(payload, parse_authority_grant_wire(wire(payload)))
    preimage = fields("promote-runtime", "runtime", "PREPARED", 1, None)
    preimage.update(
        payload_digest=authorization["payload_digest"],
        authorization_digest=authorization["authorization_digest"],
        authority_grant_digest=authorization["authority_grant_digest"],
    )
    return finalize_installer_record(preimage, "promote-runtime", "runtime"), authorization


def test_gate_loss_after_journal_validation_is_rechecked_inside_publication(tmp_path):
    parent_fd = open_parent(tmp_path)
    try:
        prepared = record(1, "PREPARED")
        with pytest.raises(JournalStoreError, match="publish immutable journal record"):
            _append_journal_record(
                parent_fd, prepared, os.getuid(), os.getgid(), TXN, TestMetadata(),
                journal_kind="service", gate=LiveGate(fail_after=1),
            )
        assert os.listdir(parent_fd) == []
    finally:
        os.close(parent_fd)


def test_append_and_readback_are_immutable_canonical_and_numerically_ordered(tmp_path):
    parent_fd = open_parent(tmp_path)
    try:
        first = record(1, "PREPARED")
        second = record(2, "SOURCE_CAPTURED", first["record_digest"])
        append_journal_record(parent_fd, first, os.getuid(), os.getgid(), TXN, TestMetadata(), journal_kind="service")
        append_journal_record(parent_fd, second, os.getuid(), os.getgid(), TXN, TestMetadata(), journal_kind="service")
        assert read_journal_records(parent_fd, os.getuid(), os.getgid(), TestMetadata(), journal_kind="service") == [first, second]
    finally:
        os.close(parent_fd)
    assert sorted(item.name for item in tmp_path.iterdir()) == [
        "00000001-PREPARED.json", "00000002-SOURCE_CAPTURED.json",
    ]


def test_append_performs_post_publication_full_chain_readback(tmp_path, monkeypatch):
    import loop_a_protected.journal_store as store

    parent_fd = open_parent(tmp_path)
    observed = []
    validations = []
    real_read = store._read_journal_records_unvalidated
    real_validate = store._validate_purpose

    def tracked_read(*args, **kwargs):
        result = real_read(*args, **kwargs)
        observed.append(tuple(item["record_digest"] for item in result))
        return result

    def tracked_validate(records, *args, **kwargs):
        validations.append(tuple(item["record_digest"] for item in records))
        return real_validate(records, *args, **kwargs)

    monkeypatch.setattr(store, "_read_journal_records_unvalidated", tracked_read)
    monkeypatch.setattr(store, "_validate_purpose", tracked_validate)
    try:
        first = record(1, "PREPARED")
        append_journal_record(parent_fd, first, os.getuid(), os.getgid(), TXN,
                              TestMetadata(), journal_kind="service")
        assert observed == [(), (first["record_digest"],)]
        assert validations == [(first["record_digest"],), (first["record_digest"],)]
    finally:
        os.close(parent_fd)


def test_out_of_order_append_is_rejected_without_mutation(tmp_path):
    parent_fd = open_parent(tmp_path)
    try:
        first = record(1, "PREPARED")
        second = record(2, "SOURCE_CAPTURED", first["record_digest"])
        with pytest.raises(JournalStoreError, match="PREPARED|sequence"):
            append_journal_record(parent_fd, second, os.getuid(), os.getgid(), TXN, TestMetadata(), journal_kind="service")
        assert os.listdir(parent_fd) == []
    finally:
        os.close(parent_fd)


def test_service_store_rejects_generic_digest_chained_record_before_mutation(tmp_path):
    parent_fd = open_parent(tmp_path)
    try:
        generic = with_self_digest({
            "sequence": 1, "state": "PREPARED", "prior_record_digest": None,
            "transaction_uuid": TXN, "record_digest": None,
        }, "record_digest")
        with pytest.raises(JournalStoreError, match="service|schema"):
            append_journal_record(
                parent_fd, generic, os.getuid(), os.getgid(), TXN, TestMetadata(),
                journal_kind="service",
            )
        assert os.listdir(parent_fd) == []
    finally:
        os.close(parent_fd)


def test_existing_sequence_state_name_is_never_overwritten(tmp_path):
    parent_fd = open_parent(tmp_path)
    try:
        original = record(1, "PREPARED")
        append_journal_record(parent_fd, original, os.getuid(), os.getgid(), TXN, TestMetadata(), journal_kind="service")
        mutated = dict(original, transaction_uuid="123e4567-e89b-42d3-a456-426614174001")
        mutated = with_self_digest(dict(mutated, record_digest=None), "record_digest")
        with pytest.raises(JournalStoreError, match="sequence|transaction"):
            append_journal_record(parent_fd, mutated, os.getuid(), os.getgid(), TXN, TestMetadata(), journal_kind="service")
    finally:
        os.close(parent_fd)
    assert (tmp_path / "00000001-PREPARED.json").read_bytes() == canonical_bytes(original)


def test_unknown_name_malformed_bytes_and_filename_field_mismatch_fail_closed(tmp_path):
    parent_fd = open_parent(tmp_path)
    try:
        (tmp_path / "unexpected").write_bytes(b"x")
        os.chmod(tmp_path / "unexpected", 0o400)
        with pytest.raises(JournalStoreError, match="unknown"):
            read_journal_records(parent_fd, os.getuid(), os.getgid(), TestMetadata(), journal_kind="service")
        (tmp_path / "unexpected").unlink()
        (tmp_path / "00000001-PREPARED.json").write_bytes(b"{}\n")
        os.chmod(tmp_path / "00000001-PREPARED.json", 0o400)
        with pytest.raises(JournalStoreError, match="invalid"):
            read_journal_records(parent_fd, os.getuid(), os.getgid(), TestMetadata(), journal_kind="service")
        os.chmod(tmp_path / "00000001-PREPARED.json", 0o600)
        (tmp_path / "00000001-PREPARED.json").write_bytes(canonical_bytes(record(2, "PREPARED")))
        os.chmod(tmp_path / "00000001-PREPARED.json", 0o400)
        with pytest.raises(JournalStoreError, match="filename"):
            read_journal_records(parent_fd, os.getuid(), os.getgid(), TestMetadata(), journal_kind="service")
    finally:
        os.close(parent_fd)


def test_duplicate_sequence_and_inode_alias_are_rejected(tmp_path):
    left = tmp_path / "00000001-PREPARED.json"
    left.write_bytes(canonical_bytes(record(1, "PREPARED")))
    os.chmod(left, 0o400)
    os.link(left, tmp_path / "00000001-SOURCE_CAPTURED.json")
    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(JournalStoreError, match="duplicate sequence|inode alias"):
            read_journal_records(parent_fd, os.getuid(), os.getgid(), TestMetadata(), journal_kind="service")
    finally:
        os.close(parent_fd)


def test_installer_store_dispatches_exact_operation_and_destination(tmp_path):
    prepared, authorization = installer_prepared_and_authorization()
    parent_fd = open_parent(tmp_path)
    try:
        append_journal_record(
            parent_fd, prepared, os.getuid(), os.getgid(), TXN, TestMetadata(),
            journal_kind="installer", operation="promote-runtime", destination="runtime",
            authorization=authorization,
        )
        assert read_journal_records(
            parent_fd, os.getuid(), os.getgid(), TestMetadata(),
            journal_kind="installer", operation="promote-runtime", destination="runtime",
            authorization=authorization,
        ) == [prepared]
        with pytest.raises(JournalStoreError, match="installer.*schema|state chain"):
            read_journal_records(
                parent_fd, os.getuid(), os.getgid(), TestMetadata(),
                journal_kind="installer", operation="promote-skill", destination="active-skills",
                authorization=authorization,
            )
    finally:
        os.close(parent_fd)


def test_installer_store_rejects_wrong_dispatch_before_publication(tmp_path):
    prepared, authorization = installer_prepared_and_authorization()
    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(JournalStoreError, match="installer.*schema|state chain"):
            append_journal_record(
                parent_fd, prepared, os.getuid(), os.getgid(), TXN, TestMetadata(),
                journal_kind="installer", operation="promote-skill", destination="active-skills",
                authorization=authorization,
            )
        assert os.listdir(parent_fd) == []
    finally:
        os.close(parent_fd)
