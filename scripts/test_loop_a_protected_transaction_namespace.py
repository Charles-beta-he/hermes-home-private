from __future__ import annotations

import os

import pytest

from loop_a_protected.canonical import canonical_bytes, with_self_digest
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.transaction_namespace import TransactionNamespaceError, publish_transaction_namespace

TXN = "123e4567-e89b-42d3-a456-426614174000"


class TestMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd) -> int:
        return 0

    def has_extended_acl(self, fd) -> bool:
        return False


def prepared():
    return with_self_digest({
        "sequence": 1, "state": "PREPARED", "prior_record_digest": None,
        "transaction_uuid": TXN, "record_digest": None,
    }, "record_digest")


def open_parent(path):
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


@pytest.mark.parametrize("kind,children", [
    ("service", {"records", "sources", "candidates", "receipts"}),
    ("installer", {"records", "snapshots", "evidence"}),
])
def test_canonical_transaction_appears_only_with_prepared_and_exact_child_set(tmp_path, kind, children):
    parent_fd = open_parent(tmp_path)
    try:
        result = publish_transaction_namespace(
            parent_fd, TXN, prepared(), kind, os.getuid(), os.getgid(), TestMetadata(),
        )
    finally:
        os.close(parent_fd)
    root = tmp_path / TXN
    assert root.is_dir()
    assert {item.name for item in root.iterdir()} == children
    assert {item.name for item in (root / "records").iterdir()} == {"00000001-PREPARED.json"}
    assert (root / "records" / "00000001-PREPARED.json").read_bytes() == canonical_bytes(prepared())
    assert result.inode == root.stat().st_ino
    assert len(set(result.child_inodes.values())) == len(children)


def test_fault_before_final_rename_exposes_only_attributable_temp_namespace(tmp_path):
    def fault(event, _context):
        if event == "before_transaction_rename_excl":
            raise RuntimeError("crash")

    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(TransactionNamespaceError) as caught:
            publish_transaction_namespace(
                parent_fd, TXN, prepared(), "service", os.getuid(), os.getgid(), TestMetadata(), fault,
            )
    finally:
        os.close(parent_fd)
    assert caught.value.temp_name == f".{TXN}.tmp"
    assert not (tmp_path / TXN).exists()
    assert (tmp_path / f".{TXN}.tmp" / "records" / "00000001-PREPARED.json").is_file()


def test_extra_direct_child_fails_closed_and_retains_temp_for_reconciliation(tmp_path):
    def fault(event, context):
        if event == "before_transaction_verify":
            os.mkdir("extra", 0o700, dir_fd=context["fd"])

    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(TransactionNamespaceError, match="child set"):
            publish_transaction_namespace(
                parent_fd, TXN, prepared(), "installer", os.getuid(), os.getgid(), TestMetadata(), fault,
            )
    finally:
        os.close(parent_fd)
    assert not (tmp_path / TXN).exists()
    assert (tmp_path / f".{TXN}.tmp" / "extra").is_dir()


def test_prepared_removed_at_last_pre_rename_hook_never_publishes_namespace(tmp_path):
    def fault(event, context):
        if event == "before_transaction_rename_excl":
            os.unlink("00000001-PREPARED.json", dir_fd=context["records_fd"])

    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(TransactionNamespaceError, match="nested child set"):
            publish_transaction_namespace(
                parent_fd, TXN, prepared(), "service", os.getuid(), os.getgid(), TestMetadata(), fault,
            )
    finally:
        os.close(parent_fd)
    assert not (tmp_path / TXN).exists()
    assert (tmp_path / f".{TXN}.tmp").is_dir()


def test_existing_final_transaction_is_never_overwritten(tmp_path):
    (tmp_path / TXN).mkdir()
    marker = tmp_path / TXN / "marker"
    marker.write_bytes(b"prior")
    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(TransactionNamespaceError):
            publish_transaction_namespace(
                parent_fd, TXN, prepared(), "service", os.getuid(), os.getgid(), TestMetadata(),
            )
    finally:
        os.close(parent_fd)
    assert marker.read_bytes() == b"prior"
    assert (tmp_path / f".{TXN}.tmp").is_dir()
