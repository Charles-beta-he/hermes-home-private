from __future__ import annotations

import os
import socket
import stat
from types import SimpleNamespace

import pytest

from loop_a_protected.fd_gateway import CleanMetadataAdapter


class Clean(CleanMetadataAdapter):
    def xattr_bytes(self, fd):
        return 0

    def has_extended_acl(self, fd):
        return False


def _status(*, inode, uid=0, gid=0, mode=0o750, device=1, links=2):
    return SimpleNamespace(
        st_dev=device, st_ino=inode, st_mode=stat.S_IFDIR | mode,
        st_uid=uid, st_gid=gid, st_nlink=links, st_flags=0,
    )


def test_broker_must_be_root_and_worker_must_be_distinct_nonroot():
    from loop_a_protected.broker_isolation import BrokerIsolationError, validate_broker_worker_identity

    assert validate_broker_worker_identity(broker_euid=0, worker_uid=501, worker_gids=[20]) == frozenset({20})
    with pytest.raises(BrokerIsolationError, match="broker"):
        validate_broker_worker_identity(broker_euid=501, worker_uid=502, worker_gids=[20])
    with pytest.raises(BrokerIsolationError, match="non-root"):
        validate_broker_worker_identity(broker_euid=0, worker_uid=0, worker_gids=[0])


MUTATION_ROOT_ROLES = (
    "active-skills", "authorizations", "control", "installer-transactions",
    "locks", "policy", "runtime", "service", "service-transactions",
)


def _root_map(start=10):
    return {role: start + index for index, role in enumerate(MUTATION_ROOT_ROLES)}


def test_mutation_roots_require_exact_inventory_and_reject_worker_owner_group_or_other_write(monkeypatch):
    import loop_a_protected.broker_isolation as isolation

    root_map = _root_map()
    statuses = {fd: _status(inode=fd, mode=0o700) for fd in root_map.values()}
    monkeypatch.setattr(isolation.os, "fstat", lambda fd: statuses[fd])
    assert isolation.validate_mutation_roots(
        mutation_root_fds=root_map, worker_uid=501, worker_gids=[20], metadata=Clean(),
    ) == frozenset((1, fd) for fd in root_map.values())

    for malformed in (
        {key: value for key, value in root_map.items() if key != "service"},
        dict(root_map, unexpected=99),
    ):
        with pytest.raises(isolation.BrokerIsolationError, match="not exact"):
            isolation.validate_mutation_roots(
                mutation_root_fds=malformed, worker_uid=501, worker_gids=[20], metadata=Clean(),
            )

    for role, bad in (
        ("service", _status(inode=root_map["service"], mode=0o770, gid=20)),
        ("service", _status(inode=root_map["service"], mode=0o707)),
        ("service", _status(inode=root_map["service"], mode=0o700, uid=501)),
    ):
        original = statuses[root_map[role]]
        statuses[root_map[role]] = bad
        message = "root-owned" if bad.st_uid == 501 else "write authority"
        with pytest.raises(isolation.BrokerIsolationError, match=message):
            isolation.validate_mutation_roots(
                mutation_root_fds=root_map, worker_uid=501, worker_gids=[20], metadata=Clean(),
            )
        statuses[root_map[role]] = original


def test_worker_fd_map_rejects_mutation_root_alias_and_writable_protected_input(tmp_path):
    from loop_a_protected.broker_isolation import BrokerIsolationError, WorkerFd, validate_worker_fd_map

    protected = tmp_path / "protected"
    protected.write_bytes(b"protected")
    read_fd = os.open(protected, os.O_RDONLY | os.O_NOFOLLOW)
    write_fd = os.open(protected, os.O_RDWR | os.O_NOFOLLOW)
    mutation_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    mutation_identity = (os.fstat(mutation_fd).st_dev, os.fstat(mutation_fd).st_ino)
    try:
        assert validate_worker_fd_map(
            worker_fds=[WorkerFd("entrypoint", read_fd, "read")],
            mutation_root_identities=frozenset({mutation_identity}),
        )[0].fd == read_fd
        with pytest.raises(BrokerIsolationError, match="writable"):
            validate_worker_fd_map(
                worker_fds=[WorkerFd("entrypoint", write_fd, "read")],
                mutation_root_identities=frozenset({mutation_identity}),
            )
        with pytest.raises(BrokerIsolationError, match="mutation-root"):
            validate_worker_fd_map(
                worker_fds=[WorkerFd("service-root", mutation_fd, "read")],
                mutation_root_identities=frozenset({mutation_identity}),
            )
    finally:
        os.close(read_fd)
        os.close(write_fd)
        os.close(mutation_fd)


def test_worker_fd_map_rejects_duplicate_roles_numbers_and_bad_direction(tmp_path):
    from loop_a_protected.broker_isolation import BrokerIsolationError, WorkerFd, validate_worker_fd_map

    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        rows = (
            [WorkerFd("x", fd, "read"), WorkerFd("x", fd + 1, "read")],
            [WorkerFd("x", fd, "read"), WorkerFd("y", fd, "read")],
            [WorkerFd("x", fd, "duplex")],
        )
        for row in rows:
            with pytest.raises(BrokerIsolationError):
                validate_worker_fd_map(worker_fds=row, mutation_root_identities=frozenset())
    finally:
        os.close(fd)


def test_exact_launcher_fd_contract_binds_roles_directions_cloexec_and_excludes_mutation_roots(tmp_path):
    from loop_a_protected.broker_isolation import (
        BrokerIsolationError, WorkerFd, validate_exact_launcher_fd_contract,
    )

    entry_read, entry_write = os.pipe()
    result_read, result_write = os.pipe()
    diagnostic_read, diagnostic_write = os.pipe()
    challenge_read, challenge_write = os.pipe()
    parent_socket, child_socket = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    interpreter = version = manifest = inventory = source = mutation = writable_manifest = -1
    try:
        interpreter_path = tmp_path / "python3"
        manifest_path = tmp_path / "manifest.json"
        inventory_path = tmp_path / "inventory.json"
        source_path = tmp_path / "source.bin"
        writable_path = tmp_path / "writable.json"
        for path in (interpreter_path, manifest_path, inventory_path, source_path, writable_path):
            path.write_bytes(b"x")
        interpreter = os.open(interpreter_path, os.O_RDONLY | os.O_NOFOLLOW)
        version = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        manifest = os.open(manifest_path, os.O_RDONLY | os.O_NOFOLLOW)
        inventory = os.open(inventory_path, os.O_RDONLY | os.O_NOFOLLOW)
        source = os.open(source_path, os.O_RDONLY | os.O_NOFOLLOW)
        writable_manifest = os.open(writable_path, os.O_RDWR | os.O_NOFOLLOW)
        mutation_path = tmp_path / "mutation-root"
        mutation_path.mkdir()
        mutation = os.open(mutation_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        mutation_identity = (os.fstat(mutation).st_dev, os.fstat(mutation).st_ino)
        rows = [
            WorkerFd("entrypoint", entry_read, "read"),
            WorkerFd("result", result_write, "write"),
            WorkerFd("diagnostics", diagnostic_write, "write"),
            WorkerFd("challenge", challenge_read, "read"),
            WorkerFd("attestation-control", child_socket.fileno(), "write"),
            WorkerFd("retained-executable", interpreter, "read"),
            WorkerFd("version-root", version, "read"),
            WorkerFd("manifest", manifest, "read"),
            WorkerFd("inventory", inventory, "read"),
            WorkerFd("source", source, "read"),
        ]
        assert validate_exact_launcher_fd_contract(rows, frozenset({mutation_identity})) == tuple(rows)

        changed = list(rows)
        changed[7] = WorkerFd("manifest", writable_manifest, "read")
        with pytest.raises(BrokerIsolationError, match="writable"):
            validate_exact_launcher_fd_contract(changed, frozenset({mutation_identity}))

        changed[7] = WorkerFd("manifest", mutation, "read")
        with pytest.raises(BrokerIsolationError, match="mutation-root"):
            validate_exact_launcher_fd_contract(changed, frozenset({mutation_identity}))

        changed = list(rows)
        changed[7] = WorkerFd("wrong-role", manifest, "read")
        with pytest.raises(BrokerIsolationError, match="exact"):
            validate_exact_launcher_fd_contract(changed, frozenset({mutation_identity}))

        os.set_inheritable(entry_read, True)
        with pytest.raises(BrokerIsolationError, match="inheritable"):
            validate_exact_launcher_fd_contract(rows, frozenset({mutation_identity}))
    finally:
        for fd in (entry_read, entry_write, result_read, result_write, diagnostic_read,
                   diagnostic_write, challenge_read, challenge_write, interpreter,
                   version, manifest, inventory, source, mutation, writable_manifest):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        parent_socket.close()
        child_socket.close()
