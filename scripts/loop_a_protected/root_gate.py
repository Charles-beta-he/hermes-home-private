from __future__ import annotations

import fcntl
import os
from typing import Protocol, Sequence, Tuple

from .fd_gateway import CleanMetadataAdapter, _validate_metadata


class RootGateError(OSError):
    pass


class SchedulerProcessProbe(Protocol):
    def old_job_is_inhibited(self) -> bool: ...
    def launchd_is_disabled_and_booted_out(self) -> bool: ...
    def matching_service_processes(self) -> Sequence[int]: ...


class RootMutationGate:
    def __init__(self, context: "_RootMutationGateContext", root_identity: Tuple[int, int],
                 fence_identity: Tuple[int, int], installer_lock_fd: int, service_lease_fd: int):
        self._context = context
        self.root_identity = root_identity
        self.fence_identity = fence_identity
        self.installer_lock_fd = installer_lock_fd
        self.service_lease_fd = service_lease_fd

    @property
    def root_fd(self) -> int:
        return self._context.root_fd

    def assert_live(self) -> None:
        self._context._assert_gate_live(self)


class _RootMutationGateContext:
    def __init__(self, root_fd: int, expected_root_identity: Tuple[int, int], root_uid: int, root_gid: int,
                 service_uid: int, service_gid: int, probe: SchedulerProcessProbe,
                 metadata: CleanMetadataAdapter, nonblocking: bool):
        self.root_fd = root_fd
        self.expected_root_identity = expected_root_identity
        self.root_uid = root_uid
        self.root_gid = root_gid
        self.service_uid = service_uid
        self.service_gid = service_gid
        self.probe = probe
        self.metadata = metadata
        self.nonblocking = nonblocking
        self._fds = []
        self._locked = []
        self._locks_fd = -1
        self._service_fd = -1
        self._active = False

    def _open_directory(self, parent_fd: int, name: str, uid: int, gid: int, mode: int, device: int) -> int:
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            _validate_metadata(fd, "directory", device, uid, gid, mode, self.metadata)
        except BaseException:
            os.close(fd)
            raise
        self._fds.append(fd)
        return fd

    def _open_lock(self, parent_fd: int, name: str, uid: int, gid: int, mode: int, device: int) -> int:
        fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            status = _validate_metadata(fd, "regular", device, uid, gid, mode, self.metadata)
            if status.st_nlink != 1:
                raise RootGateError(f"{name} is not a one-link lock file")
        except BaseException:
            os.close(fd)
            raise
        self._fds.append(fd)
        return fd

    def _verify_scheduler_and_process_exclusion(self) -> None:
        try:
            old_inhibited = self.probe.old_job_is_inhibited()
            launchd_inhibited = self.probe.launchd_is_disabled_and_booted_out()
            processes = tuple(self.probe.matching_service_processes())
        except BaseException as exc:
            raise RootGateError("scheduler or process exclusion is uncertain") from exc
        if old_inhibited is not True or launchd_inhibited is not True:
            raise RootGateError("scheduler inhibition is not exact")
        if processes:
            raise RootGateError("matching service process still exists")

    def _lock(self, fd: int) -> None:
        operation = fcntl.LOCK_EX | (fcntl.LOCK_NB if self.nonblocking else 0)
        fcntl.flock(fd, operation)
        self._locked.append(fd)

    def _assert_canonical_lock_identity(self, directory_name: str, held_directory_fd: int,
                                        directory_uid: int, directory_gid: int, directory_mode: int,
                                        lock_name: str, held_lock_fd: int,
                                        lock_uid: int, lock_gid: int, lock_mode: int,
                                        device: int) -> None:
        directory_fd = lock_fd = -1
        try:
            directory_fd = os.open(
                directory_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=self.root_fd,
            )
            directory = _validate_metadata(
                directory_fd, "directory", device, directory_uid, directory_gid,
                directory_mode, self.metadata,
            )
            held_directory = os.fstat(held_directory_fd)
            if (directory.st_dev, directory.st_ino) != (held_directory.st_dev, held_directory.st_ino):
                raise RootGateError(f"canonical {directory_name} directory identity changed")
            lock_fd = os.open(
                lock_name, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd,
            )
            lock = _validate_metadata(
                lock_fd, "regular", device, lock_uid, lock_gid, lock_mode, self.metadata,
            )
            held_lock = os.fstat(held_lock_fd)
            if lock.st_nlink != 1 or (lock.st_dev, lock.st_ino) != (held_lock.st_dev, held_lock.st_ino):
                raise RootGateError(f"canonical {lock_name} lock identity changed")
        finally:
            if lock_fd >= 0:
                os.close(lock_fd)
            if directory_fd >= 0:
                os.close(directory_fd)

    def _assert_gate_live(self, gate: RootMutationGate) -> None:
        if not self._active:
            raise RootGateError("root mutation gate is not active")
        root = os.fstat(self.root_fd)
        if (root.st_dev, root.st_ino) != gate.root_identity:
            raise RootGateError("root mutation gate identity changed")
        installer = _validate_metadata(
            gate.installer_lock_fd, "regular", root.st_dev,
            self.root_uid, self.root_gid, 0o640, self.metadata,
        )
        lease = _validate_metadata(
            gate.service_lease_fd, "regular", root.st_dev,
            self.root_uid, self.root_gid, 0o600, self.metadata,
        )
        if installer.st_nlink != 1 or lease.st_nlink != 1:
            raise RootGateError("root mutation lock identity changed")
        self._assert_canonical_lock_identity(
            "locks", self._locks_fd, self.root_uid, self.root_gid, 0o755,
            "installer.lock", gate.installer_lock_fd,
            self.root_uid, self.root_gid, 0o640, root.st_dev,
        )
        self._assert_canonical_lock_identity(
            "service", self._service_fd, self.root_uid, self.root_gid, 0o700,
            "lease.lock", gate.service_lease_fd,
            self.root_uid, self.root_gid, 0o600, root.st_dev,
        )
        self._verify_scheduler_and_process_exclusion()
        fence_fd = os.open("FENCED", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.root_fd)
        try:
            fence = _validate_metadata(
                fence_fd, "regular", root.st_dev, self.root_uid, self.root_gid, 0o444, self.metadata,
            )
            if fence.st_nlink != 1 or (fence.st_dev, fence.st_ino) != gate.fence_identity:
                raise RootGateError("FENCED identity changed")
        finally:
            os.close(fence_fd)

    def __enter__(self) -> RootMutationGate:
        try:
            root = os.fstat(self.root_fd)
            if (root.st_dev, root.st_ino) != self.expected_root_identity:
                raise RootGateError("canonical root identity mismatch")
            _validate_metadata(
                self.root_fd, "directory", root.st_dev, self.root_uid, self.root_gid, 0o755, self.metadata,
            )
            self._verify_scheduler_and_process_exclusion()
            locks_fd = self._open_directory(
                self.root_fd, "locks", self.root_uid, self.root_gid, 0o755, root.st_dev,
            )
            self._locks_fd = locks_fd
            service_fd = self._open_directory(
                self.root_fd, "service", self.root_uid, self.root_gid, 0o700, root.st_dev,
            )
            self._service_fd = service_fd
            installer_fd = self._open_lock(
                locks_fd, "installer.lock", self.root_uid, self.root_gid, 0o640, root.st_dev,
            )
            lease_fd = self._open_lock(
                service_fd, "lease.lock", self.root_uid, self.root_gid, 0o600, root.st_dev,
            )
            self._lock(installer_fd)
            self._lock(lease_fd)
            self._verify_scheduler_and_process_exclusion()
            fence_fd = os.open("FENCED", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.root_fd)
            try:
                fence = _validate_metadata(
                    fence_fd, "regular", root.st_dev, self.root_uid, self.root_gid, 0o444, self.metadata,
                )
                if fence.st_nlink != 1:
                    raise RootGateError("FENCED is not a one-link regular file")
                fence_identity = (fence.st_dev, fence.st_ino)
            finally:
                os.close(fence_fd)
            self._active = True
            return RootMutationGate(
                context=self,
                root_identity=self.expected_root_identity,
                fence_identity=fence_identity,
                installer_lock_fd=installer_fd,
                service_lease_fd=lease_fd,
            )
        except BaseException as exc:
            self.__exit__(type(exc), exc, exc.__traceback__)
            if isinstance(exc, RootGateError):
                raise
            if isinstance(exc, BlockingIOError):
                raise
            raise RootGateError(str(exc)) from exc

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self._active = False
        for fd in reversed(self._locked):
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        self._locked.clear()
        for fd in reversed(self._fds):
            try:
                os.close(fd)
            except OSError:
                pass
        self._fds.clear()
        self._locks_fd = -1
        self._service_fd = -1


def acquire_root_mutation_gate(root_fd: int, expected_root_identity: Tuple[int, int],
                               root_uid: int, root_gid: int, service_uid: int, service_gid: int,
                               probe: SchedulerProcessProbe, metadata: CleanMetadataAdapter,
                               nonblocking: bool = False) -> _RootMutationGateContext:
    return _RootMutationGateContext(
        root_fd, expected_root_identity, root_uid, root_gid, service_uid, service_gid,
        probe, metadata, nonblocking,
    )
