from __future__ import annotations

import fcntl
import hashlib
import os
import re
import signal
import socket
import stat
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Optional, Sequence, Tuple

from .broker_isolation import WorkerFd, validate_exact_launcher_fd_contract
from .darwin_handshake import HandshakeExpectation, PendingHandshake
from .fd_gateway import CleanMetadataAdapter, FdGatewayError, _validate_metadata


class DarwinLauncherError(OSError):
    pass


_FIXED_INTERPRETER = re.compile(
    r"^/private/var/db/hermes-loop-a/runtime/versions/[0-9a-f]{64}/bin/python3$"
)
_FIXED_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
}


def validate_worker_process_identity(worker_uid: int) -> None:
    if (isinstance(worker_uid, bool) or not isinstance(worker_uid, int) or worker_uid <= 0
            or os.geteuid() != worker_uid):
        raise DarwinLauncherError("launcher must already run as the distinct non-root worker UID")


def build_spawn_environment() -> Dict[str, str]:
    """Return a fresh, allowlist-only environment for the protected child."""
    return dict(_FIXED_ENVIRONMENT)


def build_spawn_argv(canonical_interpreter_path: str) -> Tuple[str, str, str, str, str]:
    if not isinstance(canonical_interpreter_path, str) or _FIXED_INTERPRETER.fullmatch(canonical_interpreter_path) is None:
        raise DarwinLauncherError("interpreter path is not the protocol-fixed canonical runtime path")
    return canonical_interpreter_path, "-I", "-S", "-B", "-"


@dataclass(frozen=True)
class ExecutableReadback:
    canonical_path: str
    identity: Tuple[int, int]
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class PhysicalAncestor:
    path: str
    device: int
    inode: int
    uid: int
    gid: int
    mode: int
    flags: int


def verify_physical_spawn_ancestors(entries: Sequence[PhysicalAncestor]) -> None:
    required = ("/", "/private", "/private/var", "/private/var/db")
    if tuple(item.path for item in entries) != required:
        raise DarwinLauncherError("physical spawn ancestor inventory is not exact")
    identities = set()
    for item in entries:
        value = os.stat(item.path, follow_symlinks=False)
        observed = (
            value.st_dev, value.st_ino, value.st_uid, value.st_gid,
            stat.S_IMODE(value.st_mode), getattr(value, "st_flags", 0),
        )
        expected = (item.device, item.inode, item.uid, item.gid, item.mode, item.flags)
        if not stat.S_ISDIR(value.st_mode) or observed != expected:
            raise DarwinLauncherError(f"physical spawn ancestor drifted: {item.path}")
        identity = (value.st_dev, value.st_ino)
        if identity in identities:
            raise DarwinLauncherError("physical spawn ancestor inventory contains an inode alias")
        identities.add(identity)


def _stable_status(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_gid,
        value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns,
        getattr(value, "st_flags", 0),
    )


def _read_exact_fd(fd: int, expected_size: int) -> bytes:
    before = os.fstat(fd)
    if before.st_size != expected_size:
        raise DarwinLauncherError("executable byte count differs from manifest")
    chunks = bytearray()
    offset = 0
    while offset <= expected_size:
        chunk = os.pread(fd, min(131072, expected_size + 1 - offset), offset)
        if not chunk:
            break
        chunks.extend(chunk)
        offset += len(chunk)
        if len(chunks) > expected_size:
            raise DarwinLauncherError("executable grew during held-FD read")
    after = os.fstat(fd)
    if _stable_status(before) != _stable_status(after) or len(chunks) != expected_size:
        raise DarwinLauncherError("executable changed during held-FD read")
    return bytes(chunks)


def verify_adjacent_executable(*, version_root_fd: int, retained_executable_fd: int,
                               version_root_path: str, expected_size: int,
                               expected_sha256: str, uid: int, gid: int,
                               metadata: CleanMetadataAdapter) -> ExecutableReadback:
    if not isinstance(version_root_path, str) or not os.path.isabs(version_root_path) or os.path.normpath(version_root_path) != version_root_path:
        raise DarwinLauncherError("version root path is not canonical absolute form")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or not 1 <= expected_size <= 536_870_912:
        raise DarwinLauncherError("executable byte count is outside the launcher bound")
    if not isinstance(expected_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        raise DarwinLauncherError("executable digest is invalid")
    bin_fd = fresh_fd = -1
    try:
        root = _validate_metadata(version_root_fd, "directory", os.fstat(version_root_fd).st_dev,
                                  uid, gid, 0o555, metadata)
        named_root = os.stat(version_root_path, follow_symlinks=False)
        if not stat.S_ISDIR(named_root.st_mode) or (named_root.st_dev, named_root.st_ino) != (root.st_dev, root.st_ino):
            raise DarwinLauncherError("version pathname identity differs from held root FD")
        bin_fd = os.open("bin", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=version_root_fd)
        bin_status = _validate_metadata(bin_fd, "directory", root.st_dev, uid, gid, 0o555, metadata)
        fresh_fd = os.open("python3", os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=bin_fd)
        retained = _validate_metadata(retained_executable_fd, "regular file", root.st_dev,
                                      uid, gid, 0o555, metadata)
        fresh = _validate_metadata(fresh_fd, "regular file", root.st_dev, uid, gid, 0o555, metadata)
        if retained.st_nlink != 1 or fresh.st_nlink != 1:
            raise DarwinLauncherError("executable link count is not one")
        if (fresh.st_dev, fresh.st_ino) != (retained.st_dev, retained.st_ino):
            raise DarwinLauncherError("canonical executable pathname differs from retained FD")
        if (fresh.st_dev, fresh.st_ino) in {(root.st_dev, root.st_ino), (bin_status.st_dev, bin_status.st_ino)}:
            raise DarwinLauncherError("execution namespace contains an inode alias")
        canonical_path = os.path.join(version_root_path, "bin", "python3")
        named_leaf = os.stat(canonical_path, follow_symlinks=False)
        if not stat.S_ISREG(named_leaf.st_mode) or (named_leaf.st_dev, named_leaf.st_ino) != (fresh.st_dev, fresh.st_ino):
            raise DarwinLauncherError("absolute executable pathname differs from adjacent FD")
        retained_bytes = _read_exact_fd(retained_executable_fd, expected_size)
        fresh_bytes = _read_exact_fd(fresh_fd, expected_size)
        digest = hashlib.sha256(fresh_bytes).hexdigest()
        if retained_bytes != fresh_bytes or digest != expected_sha256:
            raise DarwinLauncherError("executable bytes differ from retained FD or manifest")
        return ExecutableReadback(canonical_path, (fresh.st_dev, fresh.st_ino), expected_size, digest)
    except (FdGatewayError, OSError) as exc:
        if isinstance(exc, DarwinLauncherError):
            raise
        raise DarwinLauncherError(getattr(exc, "errno", None), "adjacent executable verification failed") from exc
    finally:
        if fresh_fd >= 0:
            os.close(fresh_fd)
        if bin_fd >= 0:
            os.close(bin_fd)


def _open_fd_numbers() -> set[int]:
    result = set()
    for name in os.listdir("/dev/fd"):
        if name.isdecimal():
            fd = int(name)
            try:
                os.fstat(fd)
            except OSError:
                continue
            result.add(fd)
    return result


def _posix_spawn_pending(canonical_interpreter_path: str, source_fds: Tuple[int, ...]) -> int:
    """Low-level, no-callback spawn primitive; callers must complete adjacent verification first."""
    if len(source_fds) != 10 or any(isinstance(fd, bool) or not isinstance(fd, int) or fd < 0 for fd in source_fds):
        raise DarwinLauncherError("spawn requires exactly ten ordered source FDs")
    if len(set(source_fds)) != 10:
        raise DarwinLauncherError("spawn source FDs must be distinct")
    argv = build_spawn_argv(canonical_interpreter_path)
    normalized = []
    try:
        for fd in source_fds:
            os.fstat(fd)
            normalized.append(fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 10))
        open_fds = _open_fd_numbers()
        file_actions: list = [
            (os.POSIX_SPAWN_DUP2, source_fd, target_fd)
            for target_fd, source_fd in enumerate(normalized)
        ]
        file_actions.extend(
            (os.POSIX_SPAWN_CLOSE, fd)
            for fd in sorted(open_fds)
            if fd >= 10
        )
        return os.posix_spawn(
            canonical_interpreter_path,
            argv,
            build_spawn_environment(),
            file_actions=file_actions,
        )
    except OSError as exc:
        raise DarwinLauncherError(getattr(exc, "errno", None), "posix_spawn failed closed") from exc
    finally:
        for fd in normalized:
            try:
                os.close(fd)
            except OSError:
                pass


@dataclass(frozen=True)
class PendingProtectedChild:
    pid: int
    executable_readback: ExecutableReadback
    handshake: PendingHandshake


def _fd_inventory_item(role: str, target_fd: int, source_fd: int,
                       sha256: Optional[str]) -> Dict[str, Any]:
    value = os.fstat(source_fd)
    return {
        "role": role,
        "fd": target_fd,
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "uid": value.st_uid,
        "gid": value.st_gid,
        "link_count": value.st_nlink,
        "byte_count": value.st_size,
        "sha256": sha256,
    }


def spawn_pending_handshake_after_adjacent_executable(
        *, canonical_interpreter_path: str, version_root_fd: int,
        retained_executable_fd: int, version_root_path: str,
        expected_executable_size: int, expected_executable_sha256: str,
        uid: int, gid: int, metadata: CleanMetadataAdapter,
        worker_uid: int,
        entrypoint_fd: int, result_fd: int, diagnostics_fd: int,
        manifest_fd: int, inventory_fd: int, source_fd: int, entrypoint_sha256: str,
        manifest_digest: str, inventory_digest: str, source_digest: str,
        physical_ancestors: Sequence[PhysicalAncestor],
        mutation_root_identities: FrozenSet[Tuple[int, int]],
        timeout_seconds: float = 5.0,
        challenge_nonce: Optional[bytes] = None) -> PendingProtectedChild:
    """Perform physical-chain and adjacent readback, then spawn an isolated worker."""
    validate_worker_process_identity(worker_uid)
    challenge_read = challenge_write = -1
    parent_socket: Optional[socket.socket] = None
    child_socket: Optional[socket.socket] = None
    pid: Optional[int] = None
    try:
        challenge_read, challenge_write = os.pipe()
        parent_socket, child_socket = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        source_fds = (
            entrypoint_fd, result_fd, diagnostics_fd, challenge_read, child_socket.fileno(),
            retained_executable_fd, version_root_fd, manifest_fd, inventory_fd, source_fd,
        )
        roles = (
            ("entrypoint", entrypoint_sha256), ("result", None), ("diagnostics", None),
            ("challenge", None), ("attestation-control", None),
            ("retained-executable", expected_executable_sha256), ("version-root", None),
            ("manifest", manifest_digest), ("inventory", inventory_digest), ("source", source_digest),
        )
        directions = ("read", "write", "write", "read", "write", "read", "read", "read", "read", "read")
        validate_exact_launcher_fd_contract(
            tuple(WorkerFd(role, source_fd, direction) for source_fd, (role, _), direction
                  in zip(source_fds, roles, directions)),
            mutation_root_identities,
        )
        protected_inventory = tuple(
            _fd_inventory_item(role, target_fd, source_fd, digest)
            for target_fd, (source_fd, (role, digest)) in enumerate(zip(source_fds, roles))
        )
        expectation = HandshakeExpectation(
            executable_device=os.fstat(retained_executable_fd).st_dev,
            executable_inode=os.fstat(retained_executable_fd).st_ino,
            executable_byte_count=expected_executable_size,
            executable_sha256=expected_executable_sha256,
            manifest_digest=manifest_digest,
            inventory_digest=inventory_digest,
            protected_fd_inventory=protected_inventory,
        )
        verify_physical_spawn_ancestors(physical_ancestors)
        readback = verify_adjacent_executable(
            version_root_fd=version_root_fd,
            retained_executable_fd=retained_executable_fd,
            version_root_path=version_root_path,
            expected_size=expected_executable_size,
            expected_sha256=expected_executable_sha256,
            uid=uid,
            gid=gid,
            metadata=metadata,
        )
        # Spawn only the pathname proven adjacent to the retained executable FD.
        # The caller-supplied path is retained for API compatibility but is not an
        # independent authority source.
        pid = _posix_spawn_pending(readback.canonical_path, source_fds)
        os.close(challenge_read)
        challenge_read = -1
        child_socket.close()
        child_socket = None
        pending = PendingHandshake(
            pid, challenge_write, parent_socket, expectation, timeout_seconds,
            challenge_nonce=challenge_nonce,
        )
        challenge_write = -1
        parent_socket = None
        return PendingProtectedChild(pid, readback, pending)
    except Exception:
        if pid is not None:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
        raise
    finally:
        for fd in (challenge_read, challenge_write):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if parent_socket is not None:
            parent_socket.close()
        if child_socket is not None:
            child_socket.close()
