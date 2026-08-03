from __future__ import annotations

import os
import socket
import struct

import pytest

from loop_a_protected.darwin_launchd_transport import (
    DarwinLaunchdTransportError,
    PROTECTED_ROLES,
    receive_fd_bundle,
    send_fd_bundle,
)


TX = "123e4567-e89b-42d3-a456-426614174000"


def _descriptors(tmp_path):
    result = {}
    for index, role in enumerate(PROTECTED_ROLES):
        path = tmp_path / f"{index}-{role}"
        if role == "version-root":
            path.mkdir()
            result[role] = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        else:
            path.write_bytes(role.encode("ascii"))
            result[role] = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    return result


def _send(sock, descriptors):
    identities = {role: (os.fstat(fd).st_dev, os.fstat(fd).st_ino) for role, fd in descriptors.items()}
    return send_fd_bundle(
        sock, transaction_uuid=TX, broker_pid=os.getpid(), nonce="a" * 64,
        descriptors=descriptors, expected_identities=identities,
        mutation_root_identities=frozenset(),
    )


def _close_all(values):
    for fd in values.values():
        try:
            os.close(fd)
        except OSError:
            pass


def test_stream_transport_transfers_exact_read_only_inventory_cloexec(tmp_path):
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    source = _descriptors(tmp_path)
    bundle = None
    try:
        record = _send(left, source)
        assert record["roles"] == list(PROTECTED_ROLES)
        assert record["capability"] == "read-only-input-bundle"
        bundle = receive_fd_bundle(right)
        assert bundle.transaction_uuid == TX
        assert bundle.broker_pid == os.getpid()
        assert bundle.nonce == "a" * 64
        assert set(bundle.descriptors) == set(PROTECTED_ROLES)
        for role, fd in bundle.descriptors.items():
            assert os.get_inheritable(fd) is False
            if role == "version-root":
                assert os.path.samestat(os.fstat(fd), os.fstat(source[role]))
                continue
            assert os.pread(fd, 1024, 0) == role.encode("ascii")
            with pytest.raises(OSError):
                os.write(fd, b"x")
    finally:
        if bundle is not None:
            bundle.close()
        _close_all(source)
        left.close()
        right.close()


def test_transport_rejects_missing_extra_and_inode_alias_without_sending(tmp_path):
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    source = _descriptors(tmp_path)
    try:
        missing = dict(source)
        missing.pop(PROTECTED_ROLES[0])
        with pytest.raises(DarwinLaunchdTransportError, match="roles"):
            _send(left, missing)
        extra = dict(source, mutation=source[PROTECTED_ROLES[0]])
        with pytest.raises(DarwinLaunchdTransportError, match="roles"):
            _send(left, extra)
        aliased = dict(source)
        aliased[PROTECTED_ROLES[-1]] = source[PROTECTED_ROLES[0]]
        with pytest.raises(DarwinLaunchdTransportError, match="alias"):
            _send(left, aliased)
        writable_path = tmp_path / "writable-input"
        writable_path.write_bytes(b"x")
        writable_fd = os.open(writable_path, os.O_RDWR | os.O_CLOEXEC)
        writable = dict(source)
        writable[PROTECTED_ROLES[0]] = writable_fd
        try:
            with pytest.raises(DarwinLaunchdTransportError, match="read-only"):
                _send(left, writable)
        finally:
            os.close(writable_fd)
    finally:
        _close_all(source)
        left.close()
        right.close()


def test_transport_rejects_wrong_type_identity_and_mutation_namespace_before_send(tmp_path):
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    source = _descriptors(tmp_path)
    wrong_version_path = tmp_path / "wrong-version-file"
    wrong_version_path.write_bytes(b"not-a-directory")
    wrong_version_fd = os.open(wrong_version_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        wrong_type = dict(source)
        wrong_type["version-root"] = wrong_version_fd
        with pytest.raises(DarwinLaunchdTransportError, match="type"):
            _send(left, wrong_type)

        identities = {role: (os.fstat(fd).st_dev, os.fstat(fd).st_ino) for role, fd in source.items()}
        mismatched = dict(identities)
        mismatched["source"] = identities["entrypoint"]
        with pytest.raises(DarwinLaunchdTransportError, match="approved handle"):
            send_fd_bundle(
                left, transaction_uuid=TX, broker_pid=os.getpid(), nonce="a" * 64,
                descriptors=source, expected_identities=mismatched,
                mutation_root_identities=frozenset(),
            )

        version_identity = identities["version-root"]
        with pytest.raises(DarwinLaunchdTransportError, match="mutation root"):
            send_fd_bundle(
                left, transaction_uuid=TX, broker_pid=os.getpid(), nonce="a" * 64,
                descriptors=source, expected_identities=identities,
                mutation_root_identities=frozenset({version_identity}),
            )

        mutation_root = tmp_path / "mutable"
        nested_version = mutation_root / "immutable-looking"
        nested_version.mkdir(parents=True)
        nested_fd = os.open(nested_version, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        mutation_fd = os.open(mutation_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            beneath = dict(source)
            beneath["version-root"] = nested_fd
            beneath_identities = {
                role: (os.fstat(fd).st_dev, os.fstat(fd).st_ino) for role, fd in beneath.items()
            }
            mutation_identity = (os.fstat(mutation_fd).st_dev, os.fstat(mutation_fd).st_ino)
            with pytest.raises(DarwinLaunchdTransportError, match="beneath"):
                send_fd_bundle(
                    left, transaction_uuid=TX, broker_pid=os.getpid(), nonce="a" * 64,
                    descriptors=beneath, expected_identities=beneath_identities,
                    mutation_root_identities=frozenset({mutation_identity}),
                )
        finally:
            os.close(nested_fd)
            os.close(mutation_fd)
    finally:
        os.close(wrong_version_fd)
        _close_all(source)
        left.close()
        right.close()


@pytest.mark.parametrize("role", [role for role in PROTECTED_ROLES if role != "version-root"])
def test_sender_rejects_directory_for_each_regular_protected_role_before_sendmsg(tmp_path, role):
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    right.settimeout(0.01)
    source = _descriptors(tmp_path)
    wrong_path = tmp_path / f"wrong-directory-{role}"
    wrong_path.mkdir()
    wrong_fd = os.open(wrong_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)

    try:
        wrong_type = dict(source)
        wrong_type[role] = wrong_fd
        with pytest.raises(DarwinLaunchdTransportError, match="type"):
            _send(left, wrong_type)
        with pytest.raises(socket.timeout):
            right.recv(1)
    finally:
        os.close(wrong_fd)
        _close_all(source)
        left.close()
        right.close()


def test_transport_rejects_payload_without_exact_rights(tmp_path):
    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        left.sendall(struct.pack(">I", 2) + b"{}")
        with pytest.raises(DarwinLaunchdTransportError, match="ancillary"):
            receive_fd_bundle(right)
    finally:
        left.close()
        right.close()
