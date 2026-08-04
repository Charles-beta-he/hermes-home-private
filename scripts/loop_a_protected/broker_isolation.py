from __future__ import annotations

import fcntl
import os
import stat
from dataclasses import dataclass
from typing import FrozenSet, Iterable, Mapping, Sequence, Tuple

from .fd_gateway import CleanMetadataAdapter


class BrokerIsolationError(PermissionError):
    pass


@dataclass(frozen=True)
class WorkerFd:
    role: str
    fd: int
    direction: str


_ALLOWED_DIRECTIONS = {"read", "write", "control"}


def _identity(fd: int) -> Tuple[int, int]:
    value = os.fstat(fd)
    return value.st_dev, value.st_ino


def _mode_grants_write(value: os.stat_result, worker_uid: int, worker_gids: frozenset[int]) -> bool:
    if value.st_uid == worker_uid:
        return bool(value.st_mode & stat.S_IWUSR)
    if value.st_gid in worker_gids:
        return bool(value.st_mode & stat.S_IWGRP)
    return bool(value.st_mode & stat.S_IWOTH)


def validate_broker_worker_identity(*, broker_euid: int, worker_uid: int,
                                    worker_gids: Iterable[int]) -> frozenset[int]:
    if broker_euid != 0:
        raise BrokerIsolationError("mutation broker must run as root")
    if isinstance(worker_uid, bool) or not isinstance(worker_uid, int) or worker_uid <= 0:
        raise BrokerIsolationError("worker UID must be a distinct non-root identity")
    gids = frozenset(worker_gids)
    if not gids or any(isinstance(gid, bool) or not isinstance(gid, int) or gid < 0 for gid in gids):
        raise BrokerIsolationError("worker groups are invalid")
    return gids


_REQUIRED_MUTATION_ROOT_ROLES = frozenset({
    "locks",
    "control",
    "runtime",
    "active-skills",
    "authorizations",
    "policy",
    "installer-transactions",
    "service",
    "service-transactions",
})


def validate_mutation_roots(*, mutation_root_fds: Mapping[str, int], worker_uid: int,
                            worker_gids: Iterable[int], metadata: CleanMetadataAdapter) -> frozenset[Tuple[int, int]]:
    gids = frozenset(worker_gids)
    roles = frozenset(mutation_root_fds)
    if roles != _REQUIRED_MUTATION_ROOT_ROLES:
        missing = sorted(_REQUIRED_MUTATION_ROOT_ROLES - roles)
        extra = sorted(roles - _REQUIRED_MUTATION_ROOT_ROLES)
        raise BrokerIsolationError(f"mutation-root inventory is not exact: missing={missing!r} extra={extra!r}")
    identities = set()
    for role, fd in sorted(mutation_root_fds.items()):
        if not role or isinstance(fd, bool) or not isinstance(fd, int) or fd < 0:
            raise BrokerIsolationError("mutation-root inventory is malformed")
        value = os.fstat(fd)
        if not stat.S_ISDIR(value.st_mode) or value.st_uid != 0:
            raise BrokerIsolationError(f"mutation root {role} is not a root-owned directory")
        if value.st_nlink < 2 or _mode_grants_write(value, worker_uid, gids):
            raise BrokerIsolationError(f"worker has ambient pathname write authority to {role}")
        if metadata.has_extended_acl(fd) or metadata.xattr_bytes(fd) != 0 or getattr(value, "st_flags", 0) != 0:
            raise BrokerIsolationError(f"mutation root {role} has unbound metadata authority")
        identity = (value.st_dev, value.st_ino)
        if identity in identities:
            raise BrokerIsolationError("mutation-root inventory contains an inode alias")
        identities.add(identity)
    return frozenset(identities)


def validate_worker_fd_map(*, worker_fds: Sequence[WorkerFd],
                           mutation_root_identities: frozenset[Tuple[int, int]]) -> Tuple[WorkerFd, ...]:
    if not worker_fds:
        raise BrokerIsolationError("worker FD map is empty")
    roles = set()
    numbers = set()
    result = []
    for item in worker_fds:
        if not isinstance(item, WorkerFd) or not item.role or item.role in roles:
            raise BrokerIsolationError("worker FD roles are malformed or duplicated")
        if isinstance(item.fd, bool) or not isinstance(item.fd, int) or item.fd < 0 or item.fd in numbers:
            raise BrokerIsolationError("worker FD numbers are malformed or duplicated")
        if item.direction not in _ALLOWED_DIRECTIONS:
            raise BrokerIsolationError("worker FD direction is invalid")
        value = os.fstat(item.fd)
        if (value.st_dev, value.st_ino) in mutation_root_identities:
            raise BrokerIsolationError("worker inherited a mutation-root descriptor")
        access = fcntl.fcntl(item.fd, fcntl.F_GETFL) & os.O_ACCMODE
        if item.direction == "read" and access != os.O_RDONLY:
            raise BrokerIsolationError(f"read-only worker FD {item.role} is writable")
        if item.direction == "write" and access == os.O_RDONLY:
            raise BrokerIsolationError(f"write worker FD {item.role} is not writable")
        if item.direction == "control" and access != os.O_RDWR:
            raise BrokerIsolationError(f"control worker FD {item.role} is not duplex")
        roles.add(item.role)
        numbers.add(item.fd)
        result.append(item)
    return tuple(result)


_EXACT_LAUNCHER_FD_CONTRACT = (
    ("entrypoint", "read", stat.S_ISFIFO),
    ("result", "write", stat.S_ISFIFO),
    ("diagnostics", "write", stat.S_ISFIFO),
    ("challenge", "read", stat.S_ISFIFO),
    ("attestation-control", "control", stat.S_ISSOCK),
    ("retained-executable", "read", stat.S_ISREG),
    ("version-root", "read", stat.S_ISDIR),
    ("manifest", "read", stat.S_ISREG),
    ("inventory", "read", stat.S_ISREG),
    ("source", "read", stat.S_ISREG),
)


def validate_exact_launcher_fd_contract(
        worker_fds: Sequence[WorkerFd],
        mutation_root_identities: FrozenSet[Tuple[int, int]]) -> Tuple[WorkerFd, ...]:
    rows = tuple(worker_fds)
    observed = tuple((row.role, row.direction) for row in rows)
    expected = tuple((role, direction) for role, direction, _ in _EXACT_LAUNCHER_FD_CONTRACT)
    if observed != expected:
        raise BrokerIsolationError("worker launcher FD contract is not exact")
    validated = validate_worker_fd_map(
        worker_fds=rows,
        mutation_root_identities=mutation_root_identities,
    )
    for row, (_, _, type_check) in zip(validated, _EXACT_LAUNCHER_FD_CONTRACT):
        try:
            status = os.fstat(row.fd)
            inheritable = os.get_inheritable(row.fd)
        except OSError as exc:
            raise BrokerIsolationError("worker launcher FD cannot be inspected") from exc
        if not type_check(status.st_mode):
            raise BrokerIsolationError(f"worker launcher FD type differs for {row.role}")
        if inheritable:
            raise BrokerIsolationError(f"worker launcher FD is inheritable before spawn: {row.role}")
    return validated
