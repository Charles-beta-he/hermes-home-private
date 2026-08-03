from __future__ import annotations

import fcntl
import os
from pathlib import Path

import pytest

from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.root_gate import RootGateError, acquire_root_mutation_gate


class CleanMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd: int) -> int:
        return 0

    def has_extended_acl(self, fd: int) -> bool:
        return False


class SchedulerProbe:
    def __init__(self, inhibited: bool = True, processes=()):
        self.inhibited = inhibited
        self.processes = tuple(processes)
        self.calls = []

    def old_job_is_inhibited(self) -> bool:
        self.calls.append("old-job")
        return self.inhibited

    def launchd_is_disabled_and_booted_out(self) -> bool:
        self.calls.append("launchd")
        return self.inhibited

    def matching_service_processes(self):
        self.calls.append("processes")
        return self.processes


def provision_root(path: Path):
    root_uid, root_gid = os.getuid(), os.getgid()
    service_uid, service_gid = root_uid + 1, root_gid + 1
    os.chmod(path, 0o755)
    (path / "locks").mkdir(mode=0o755)
    (path / "service").mkdir(mode=0o700)
    (path / "locks" / "installer.lock").write_bytes(b"")
    (path / "service" / "lease.lock").write_bytes(b"")
    (path / "FENCED").write_bytes(b"")
    os.chmod(path / "locks" / "installer.lock", 0o640)
    os.chmod(path / "service" / "lease.lock", 0o600)
    os.chmod(path / "FENCED", 0o444)
    return root_uid, root_gid, service_uid, service_gid


def acquire(path: Path, probe=None):
    ids = provision_root(path)
    root_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    gate = acquire_root_mutation_gate(
        root_fd, identity, *ids, probe or SchedulerProbe(), CleanMetadata(), nonblocking=True,
    )
    return root_fd, gate


def test_root_gate_holds_installer_then_service_locks_and_rechecks_scheduler(tmp_path):
    probe = SchedulerProbe()
    root_fd, gate_context = acquire(tmp_path, probe)
    try:
        with gate_context as gate:
            assert gate.root_identity == (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
            assert gate.fence_identity[0] == gate.root_identity[0]
            assert probe.calls == ["old-job", "launchd", "processes", "old-job", "launchd", "processes"]
            with pytest.raises(BlockingIOError):
                contender = os.open(tmp_path / "service" / "lease.lock", os.O_RDWR | os.O_NOFOLLOW)
                try:
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
                finally:
                    os.close(contender)
    finally:
        os.close(root_fd)


def test_missing_fence_fails_closed_after_lock_acquisition(tmp_path):
    ids = provision_root(tmp_path)
    (tmp_path / "FENCED").unlink()
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    try:
        with pytest.raises(RootGateError, match="FENCED"):
            with acquire_root_mutation_gate(
                root_fd, identity, *ids, SchedulerProbe(), CleanMetadata(), nonblocking=True,
            ):
                pytest.fail("gate must not open")
    finally:
        os.close(root_fd)


def test_scheduler_or_process_uncertainty_fails_before_locking(tmp_path):
    ids = provision_root(tmp_path)
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    try:
        for probe in (SchedulerProbe(inhibited=False), SchedulerProbe(processes=(123,))):
            with pytest.raises(RootGateError, match="scheduler|process"):
                with acquire_root_mutation_gate(
                    root_fd, identity, *ids, probe, CleanMetadata(), nonblocking=True,
                ):
                    pytest.fail("gate must not open")
    finally:
        os.close(root_fd)


def test_live_gate_rejects_renamed_one_link_canonical_lock_replacement(tmp_path):
    for directory, name, mode in (("locks", "installer.lock", 0o640), ("service", "lease.lock", 0o600)):
        root = tmp_path / directory
        root.mkdir()
        root_fd, gate_context = acquire(root)
        replacement_fd = -1
        try:
            with gate_context as gate:
                original = root / directory / name
                retained = root / directory / f"{name}.retained"
                original.rename(retained)
                original.write_bytes(b"")
                os.chmod(original, mode)
                replacement_fd = os.open(original, os.O_RDWR | os.O_NOFOLLOW)
                fcntl.flock(replacement_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with pytest.raises(RootGateError, match="canonical.*identity|lock identity"):
                    gate.assert_live()
        finally:
            if replacement_fd >= 0:
                os.close(replacement_fd)
            os.close(root_fd)


def test_live_gate_rejects_fence_or_lock_path_replacement(tmp_path):
    root_fd, gate_context = acquire(tmp_path)
    try:
        with gate_context as gate:
            (tmp_path / "FENCED").unlink()
            (tmp_path / "FENCED").write_bytes(b"")
            os.chmod(tmp_path / "FENCED", 0o444)
            with pytest.raises(RootGateError, match="FENCED"):
                gate.assert_live()
    finally:
        os.close(root_fd)

    other = tmp_path / "other"
    other.mkdir()
    root_fd, gate_context = acquire(other)
    try:
        with gate_context as gate:
            (other / "locks" / "installer.lock").unlink()
            (other / "locks" / "installer.lock").write_bytes(b"")
            os.chmod(other / "locks" / "installer.lock", 0o640)
            with pytest.raises(RootGateError, match="lock identity"):
                gate.assert_live()
    finally:
        os.close(root_fd)
