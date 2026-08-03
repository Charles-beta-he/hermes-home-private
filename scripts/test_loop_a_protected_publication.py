from __future__ import annotations

import ctypes
import os
import stat
from pathlib import Path

import pytest

import loop_a_protected.publication as publication
from loop_a_protected.publication import (
    PublicationError,
    publish_directory_tree,
    publish_regular_file,
)

TXN = "123e4567-e89b-42d3-a456-426614174000"


class StickyGate:
    def __init__(self):
        self.armed = False
        self.calls = 0

    def assert_live(self):
        self.calls += 1
        if self.armed:
            raise RuntimeError("sticky root gate loss")


def open_parent(path: Path) -> int:
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def assume_xattr_free(monkeypatch):
    monkeypatch.setattr(publication, "_flistxattr", lambda _fd, _buffer, _size, _options: 0)


def test_same_parent_publication_is_durable_identity_bound_and_exact(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    parent_fd = open_parent(tmp_path)
    try:
        result = publish_regular_file(parent_fd, "final.json", b"payload\n", 0o400, os.getuid(), os.getgid(), TXN)
        st = os.stat("final.json", dir_fd=parent_fd, follow_symlinks=False)
        assert (st.st_dev, st.st_ino) == (result.device, result.inode)
        assert stat.S_IMODE(st.st_mode) == 0o400
        assert (tmp_path / "final.json").read_bytes() == b"payload\n"
        assert not list(tmp_path.glob(".*.tmp"))
    finally:
        os.close(parent_fd)


def test_regular_file_publication_fsyncs_parent_after_namespace_mutation(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    parent_fd = open_parent(tmp_path)
    real_fsync = publication.os.fsync
    calls = []

    def tracked_fsync(fd):
        calls.append(fd)
        return real_fsync(fd)

    monkeypatch.setattr(publication.os, "fsync", tracked_fsync)
    try:
        publish_regular_file(parent_fd, "durable.json", b"payload", 0o400,
                             os.getuid(), os.getgid(), TXN)
        assert calls[-1] == parent_fd
        assert calls.count(parent_fd) == 1
    finally:
        os.close(parent_fd)


def test_launchd_plist_publication_supports_protocol_required_0644_mode(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    parent_fd = open_parent(tmp_path)
    try:
        result = publish_regular_file(
            parent_fd, "com.nous.hermes.loop-a.plist", b"<plist/>\n", 0o644,
            os.getuid(), os.getgid(), TXN,
        )
        status = os.stat(result.name, dir_fd=parent_fd, follow_symlinks=False)
        assert stat.S_IMODE(status.st_mode) == 0o644
        assert (tmp_path / result.name).read_bytes() == b"<plist/>\n"
    finally:
        os.close(parent_fd)


def test_final_name_collision_preserves_both_inodes_and_never_overwrites(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    (tmp_path / "final.json").write_bytes(b"sentinel")
    sentinel = (tmp_path / "final.json").stat()
    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(PublicationError) as caught:
            publish_regular_file(parent_fd, "final.json", b"candidate", 0o400, os.getuid(), os.getgid(), TXN)
        after = (tmp_path / "final.json").stat()
        assert (after.st_dev, after.st_ino, (tmp_path / "final.json").read_bytes()) == (sentinel.st_dev, sentinel.st_ino, b"sentinel")
        assert os.stat(caught.value.temp_name, dir_fd=parent_fd, follow_symlinks=False).st_ino != sentinel.st_ino
    finally:
        os.close(parent_fd)


def test_zero_write_fails_before_publish_and_retains_attributable_temp(tmp_path, monkeypatch):
    parent_fd = open_parent(tmp_path)
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication.os, "write", lambda _fd, _data: 0)
    try:
        with pytest.raises(PublicationError, match="zero write") as caught:
            publish_regular_file(parent_fd, "final.json", b"payload", 0o400, os.getuid(), os.getgid(), TXN)
        with pytest.raises(FileNotFoundError):
            os.stat("final.json", dir_fd=parent_fd, follow_symlinks=False)
        os.stat(caught.value.temp_name, dir_fd=parent_fd, follow_symlinks=False)
    finally:
        os.close(parent_fd)


def test_fault_after_full_sync_never_publishes_final_name(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    parent_fd = open_parent(tmp_path)
    def fault(event, _context):
        if event == "after_full_fsync":
            raise RuntimeError("injected crash")
    try:
        with pytest.raises(PublicationError, match="injected crash"):
            publish_regular_file(parent_fd, "final.json", b"payload", 0o400, os.getuid(), os.getgid(), TXN, fault)
        with pytest.raises(FileNotFoundError):
            os.stat("final.json", dir_fd=parent_fd, follow_symlinks=False)
    finally:
        os.close(parent_fd)


def test_fresh_directory_tree_publication_has_exact_unique_child_set(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: False)
    parent_fd = open_parent(tmp_path)
    try:
        result = publish_directory_tree(
            parent_fd, "version", {"a": (b"A", 0o400), "b": (b"B", 0o400)},
            0o500, os.getuid(), os.getgid(), TXN,
        )
        assert result.name == "version"
        assert set(result.children) == {"a", "b"}
        assert {entry.name for entry in (tmp_path / "version").iterdir()} == {"a", "b"}
        assert len({(tmp_path / "version" / name).stat().st_ino for name in ("a", "b")}) == 2
    finally:
        os.close(parent_fd)


def test_sticky_gate_loss_before_child_write_preserves_zero_byte_temp_and_no_final_tree(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: False)
    parent_fd = open_parent(tmp_path)
    gate = StickyGate()

    def arm_after_metadata(event, _context):
        if event == "after_metadata":
            gate.armed = True

    try:
        with pytest.raises(PublicationError, match="sticky root gate loss") as caught:
            publish_directory_tree(
                parent_fd, "version", {"a": (b"NONEMPTY", 0o400)}, 0o500,
                os.getuid(), os.getgid(), TXN, arm_after_metadata, gate=gate,
            )
        assert not (tmp_path / "version").exists()
        temp_tree = tmp_path / caught.value.temp_name
        child_temps = list(temp_tree.glob(".a.txn-*.tmp"))
        assert len(child_temps) == 1
        assert child_temps[0].stat().st_size == 0
    finally:
        os.close(parent_fd)


def test_sticky_gate_loss_immediately_before_directory_rename_never_publishes_final(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: False)
    parent_fd = open_parent(tmp_path)
    gate = StickyGate()

    def arm_after_tree_fsync(event, _context):
        if event == "after_tree_fsync":
            gate.armed = True

    try:
        with pytest.raises(PublicationError, match="sticky root gate loss") as caught:
            publish_directory_tree(
                parent_fd, "version", {"a": (b"A", 0o400)}, 0o500,
                os.getuid(), os.getgid(), TXN, arm_after_tree_fsync, gate=gate,
            )
        assert not (tmp_path / "version").exists()
        temp_tree = tmp_path / caught.value.temp_name
        assert (temp_tree / "a").read_bytes() == b"A"
    finally:
        os.close(parent_fd)


def test_directory_tree_publication_fsyncs_parent_after_namespace_mutation(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: False)
    parent_fd = open_parent(tmp_path)
    real_fsync = publication.os.fsync
    calls = []

    def tracked_fsync(fd):
        calls.append(fd)
        return real_fsync(fd)

    monkeypatch.setattr(publication.os, "fsync", tracked_fsync)
    try:
        publish_directory_tree(
            parent_fd, "version", {"a": (b"A", 0o400)}, 0o500,
            os.getuid(), os.getgid(), TXN,
        )
        assert calls[-1] == parent_fd
        assert calls.count(parent_fd) == 1
    finally:
        os.close(parent_fd)


def test_tree_publication_rejects_injected_inode_alias_and_retains_transaction_tree(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: False)
    parent_fd = open_parent(tmp_path)
    def fault(event, context):
        if event == "before_tree_verify":
            os.link("a", "alias", src_dir_fd=context["fd"], dst_dir_fd=context["fd"])
    try:
        with pytest.raises(PublicationError, match="child set|link count|alias") as caught:
            publish_directory_tree(parent_fd, "version", {"a": (b"A", 0o400)}, 0o500,
                                   os.getuid(), os.getgid(), TXN, fault)
        assert not (tmp_path / "version").exists()
        os.stat(caught.value.temp_name, dir_fd=parent_fd, follow_symlinks=False)
    finally:
        os.close(parent_fd)


def test_nonempty_acl_inventory_fails_closed_before_publish(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: True)
    parent_fd = open_parent(tmp_path)
    try:
        with pytest.raises(PublicationError, match="extended ACL"):
            publish_regular_file(parent_fd, "final.json", b"payload", 0o400, os.getuid(), os.getgid(), TXN)
        assert not (tmp_path / "final.json").exists()
    finally:
        os.close(parent_fd)


def test_mutation_through_held_fd_after_readback_never_publishes_stale_digest(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    parent_fd = open_parent(tmp_path)
    try:
        def mutate(event, context):
            if event == "before_rename_excl":
                os.pwrite(context["fd"], b"EVIL", 0)
                os.ftruncate(context["fd"], 4)

        with pytest.raises(PublicationError, match="byte readback mismatch"):
            publish_regular_file(
                parent_fd, "final.json", b"GOOD", 0o400, os.getuid(), os.getgid(), TXN, mutate,
            )
        assert not (tmp_path / "final.json").exists()
    finally:
        os.close(parent_fd)


def test_fault_after_rename_is_reconcilable_by_final_inode_identity(tmp_path, monkeypatch):
    assume_xattr_free(monkeypatch)
    monkeypatch.setattr(publication, "_has_extended_acl", lambda _fd: False)
    parent_fd = open_parent(tmp_path)
    seen = {}
    def fault(event, context):
        if event == "after_rename_excl":
            seen["inode"] = os.fstat(context["fd"]).st_ino
            raise RuntimeError("crash after namespace mutation")
    try:
        with pytest.raises(PublicationError, match="crash after namespace mutation"):
            publish_regular_file(parent_fd, "final.json", b"payload", 0o400, os.getuid(), os.getgid(), TXN, fault)
        named = os.stat("final.json", dir_fd=parent_fd, follow_symlinks=False)
        assert named.st_ino == seen["inode"]
        assert not (tmp_path / f".final.json.txn-{TXN}.tmp").exists()
    finally:
        os.close(parent_fd)


def test_unchecked_public_rename_swap_surface_is_not_exposed():
    assert not hasattr(publication, "rename_swap_names")


def test_nonempty_xattr_inventory_fails_closed_without_attempting_cleanup(tmp_path, monkeypatch):
    parent_fd = open_parent(tmp_path)
    name = b"com.example.hostile\0"
    def listxattr(_fd, buffer, _size, _options):
        if buffer is None:
            return len(name)
        ctypes.memmove(buffer, name, len(name))
        return len(name)
    monkeypatch.setattr(publication, "_flistxattr", listxattr)
    monkeypatch.setattr(publication, "_fremovexattr", lambda *_args: pytest.fail("publisher must not mutate xattrs"), raising=False)
    try:
        with pytest.raises(PublicationError, match="staged inode has xattrs"):
            publish_regular_file(parent_fd, "final.json", b"payload", 0o400, os.getuid(), os.getgid(), TXN)
        with pytest.raises(FileNotFoundError):
            os.stat("final.json", dir_fd=parent_fd, follow_symlinks=False)
    finally:
        os.close(parent_fd)
