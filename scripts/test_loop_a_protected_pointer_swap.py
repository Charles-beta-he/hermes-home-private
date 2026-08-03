from __future__ import annotations

import os
from pathlib import Path

import pytest

from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.pointer_swap import PointerSwapError, swap_version_pointer
from loop_a_protected.root_gate import acquire_root_mutation_gate
from test_loop_a_protected_swap_support import (
    make_authorization,
    make_swap_evidence,
    provision_swap_journal,
)


class CleanMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd: int) -> int: return 0
    def has_extended_acl(self, fd: int) -> bool: return False


class Probe:
    def old_job_is_inhibited(self): return True
    def launchd_is_disabled_and_booted_out(self): return True
    def matching_service_processes(self): return ()


OLD = "1" * 64
NEW = "2" * 64
STAGED = ".current.txn-123e4567-e89b-42d3-a456-426614174000.tmp"


def provision(path: Path, *, with_journal=True):
    uid, gid = os.getuid(), os.getgid()
    os.chmod(path, 0o755)
    for name, mode in (("locks", 0o755), ("service", 0o700), ("runtime", 0o755)):
        (path / name).mkdir(mode=mode)
    (path / "locks" / "installer.lock").write_bytes(b"")
    (path / "service" / "lease.lock").write_bytes(b"")
    (path / "FENCED").write_bytes(b"")
    os.chmod(path / "locks" / "installer.lock", 0o640)
    os.chmod(path / "service" / "lease.lock", 0o600)
    os.chmod(path / "FENCED", 0o444)
    os.symlink(f"versions/{OLD}", path / "runtime" / "current")
    os.symlink(f"versions/{NEW}", path / "runtime" / STAGED)
    root_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    parent_fd = os.open(path / "runtime", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    root_identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    parent_identity = (os.fstat(parent_fd).st_dev, os.fstat(parent_fd).st_ino)
    authorization = make_authorization("promote-runtime", "runtime")
    if with_journal:
        evidence = make_swap_evidence(
            authorization=authorization, sequence=5, state="RUNTIME_POINTER_STAGED",
            role="runtime-pointer", parent_status=os.fstat(parent_fd),
            current_name="current", current_status=os.stat("current", dir_fd=parent_fd, follow_symlinks=False),
            staged_name=STAGED, staged_status=os.stat(STAGED, dir_fd=parent_fd, follow_symlinks=False),
            current_target=f"versions/{OLD}", staged_target=f"versions/{NEW}",
        )
        provision_swap_journal(path, authorization, "RUNTIME_POINTER_STAGED", "runtime-pointer", evidence)
    context = acquire_root_mutation_gate(
        root_fd, root_identity, uid, gid, uid, gid, Probe(), CleanMetadata(), nonblocking=True,
    )
    return uid, gid, root_fd, parent_fd, parent_identity, authorization, context


def test_runtime_pointer_swap_is_gate_state_inode_and_target_bound(tmp_path):
    uid, gid, root_fd, parent_fd, identity, authorization, context = provision(tmp_path)
    try:
        before_current = os.stat("current", dir_fd=parent_fd, follow_symlinks=False).st_ino
        before_staged = os.stat(STAGED, dir_fd=parent_fd, follow_symlinks=False).st_ino
        with context as gate:
            result = swap_version_pointer(
                parent_fd=parent_fd, expected_parent_identity=identity, gate=gate,
                authorization=authorization, kind="runtime",
                staged_name=STAGED, expected_current_target=f"versions/{OLD}",
                expected_staged_target=f"versions/{NEW}",
                uid=uid, gid=gid, metadata=CleanMetadata(),
            )
        assert os.readlink("current", dir_fd=parent_fd) == f"versions/{NEW}"
        assert os.readlink(STAGED, dir_fd=parent_fd) == f"versions/{OLD}"
        assert (result.current_inode, result.retained_inode) == (before_staged, before_current)
    finally:
        os.close(parent_fd); os.close(root_fd)


def test_pointer_swap_rejects_unbound_target_without_mutation(tmp_path):
    uid, gid, root_fd, parent_fd, identity, authorization, context = provision(tmp_path)
    try:
        with context as gate:
            with pytest.raises(PointerSwapError, match="target"):
                swap_version_pointer(
                    parent_fd=parent_fd, expected_parent_identity=identity, gate=gate,
                    authorization=authorization, kind="runtime", staged_name=STAGED,
                    expected_current_target=f"versions/{OLD}",
                    expected_staged_target=f"versions/{'3' * 64}",
                    uid=uid, gid=gid, metadata=CleanMetadata(),
                )
        assert os.readlink("current", dir_fd=parent_fd) == f"versions/{OLD}"
        assert os.readlink(STAGED, dir_fd=parent_fd) == f"versions/{NEW}"
    finally:
        os.close(parent_fd); os.close(root_fd)


def test_pointer_swap_rejects_inode_replacement_after_durable_evidence(tmp_path):
    uid, gid, root_fd, parent_fd, identity, authorization, context = provision(tmp_path)
    try:
        os.unlink(STAGED, dir_fd=parent_fd)
        os.symlink(f"versions/{NEW}", STAGED, dir_fd=parent_fd)
        with context as gate:
            with pytest.raises(PointerSwapError, match="inode"):
                swap_version_pointer(
                    parent_fd=parent_fd, expected_parent_identity=identity, gate=gate,
                    authorization=authorization, kind="runtime", staged_name=STAGED,
                    expected_current_target=f"versions/{OLD}", expected_staged_target=f"versions/{NEW}",
                    uid=uid, gid=gid, metadata=CleanMetadata(),
                )
        assert os.readlink("current", dir_fd=parent_fd) == f"versions/{OLD}"
    finally:
        os.close(parent_fd); os.close(root_fd)


def test_pointer_swap_rejects_missing_durable_evidence_and_decoy_name(tmp_path):
    root = tmp_path / "missing"
    root.mkdir()
    uid, gid, root_fd, parent_fd, identity, authorization, context = provision(root, with_journal=False)
    try:
        with context as gate:
            with pytest.raises(PointerSwapError, match="staged name"):
                swap_version_pointer(
                    parent_fd=parent_fd, expected_parent_identity=identity, gate=gate,
                    authorization=authorization, kind="runtime", staged_name=".runtime.next",
                    expected_current_target=f"versions/{OLD}", expected_staged_target=f"versions/{NEW}",
                    uid=uid, gid=gid, metadata=CleanMetadata(),
                )
            with pytest.raises(PointerSwapError, match="durable swap evidence"):
                swap_version_pointer(
                    parent_fd=parent_fd, expected_parent_identity=identity, gate=gate,
                    authorization=authorization, kind="runtime", staged_name=STAGED,
                    expected_current_target=f"versions/{OLD}", expected_staged_target=f"versions/{NEW}",
                    uid=uid, gid=gid, metadata=CleanMetadata(),
                )
    finally:
        os.close(parent_fd); os.close(root_fd)
