from __future__ import annotations

import ctypes
import os
import socket
import tempfile

import pytest


@pytest.mark.parametrize("length,value", [(0, 1234), (ctypes.sizeof(ctypes.c_int), 0)])
def test_peer_pid_rejects_invalid_native_abi_results(length, value):
    import loop_a_protected.darwin_peer as peer

    class FakeLibrary:
        def getsockopt(self, _fd, _level, _option, value_pointer, length_pointer):
            ctypes.cast(value_pointer, ctypes.POINTER(ctypes.c_int)).contents.value = value
            ctypes.cast(length_pointer, ctypes.POINTER(ctypes.c_uint32)).contents.value = length
            return 0

    with pytest.raises(peer.DarwinPeerError, match="invalid ABI"):
        peer._peer_pid(FakeLibrary(), 7, 2)  # type: ignore[arg-type]


def test_real_darwin_socketpair_peer_credentials_bind_pid_uid_and_gid():
    from loop_a_protected.darwin_peer import read_peer_credentials

    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        observed = read_peer_credentials(left)
        assert observed.pid == os.getpid()
        assert observed.effective_pid == os.getpid()
        assert observed.uid == os.geteuid()
        assert observed.gid == os.getegid()
    finally:
        left.close()
        right.close()


def test_real_darwin_listener_observes_connecting_child_pid():
    from loop_a_protected.darwin_peer import read_peer_credentials

    socket_dir = tempfile.mkdtemp(prefix="lap-", dir="/tmp")
    path = os.path.join(socket_dir, "p.sock")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(path)
    listener.listen(1)
    pid = os.fork()
    if pid == 0:
        try:
            child = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            child.connect(path)
            child.sendall(b"ready")
            child.recv(1)
            child.close()
        finally:
            os._exit(0)
    accepted = None
    try:
        accepted, _ = listener.accept()
        assert accepted.recv(5) == b"ready"
        observed = read_peer_credentials(accepted)
        assert observed.pid == pid
        assert observed.effective_pid == pid
        assert observed.uid == os.geteuid()
        assert observed.gid == os.getegid()
        accepted.sendall(b"x")
    finally:
        if accepted is not None:
            accepted.close()
        listener.close()
        waited, status = os.waitpid(pid, 0)
        assert waited == pid
        assert os.waitstatus_to_exitcode(status) == 0
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
        os.rmdir(socket_dir)


def test_peer_admission_requires_root_broker_and_exact_launchd_identity(monkeypatch):
    import loop_a_protected.darwin_peer as peer

    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        expected = peer.PeerCredentials(pid=1234, effective_pid=1234, uid=501, gid=20)
        monkeypatch.setattr(peer, "read_peer_credentials", lambda sock: expected)
        assert peer.validate_launchd_worker_peer(
            left, broker_euid=0, expected_pid=1234, expected_uid=501, expected_gid=20,
        ) == expected
        with pytest.raises(peer.DarwinPeerError, match="broker"):
            peer.validate_launchd_worker_peer(
                left, broker_euid=501, expected_pid=1234, expected_uid=501, expected_gid=20,
            )
        for field, value, message in (
            ("expected_pid", 1235, "PID"),
            ("expected_uid", 502, "UID"),
            ("expected_gid", 21, "GID"),
        ):
            kwargs = dict(broker_euid=0, expected_pid=1234, expected_uid=501, expected_gid=20)
            kwargs[field] = value
            with pytest.raises(peer.DarwinPeerError, match=message):
                peer.validate_launchd_worker_peer(left, **kwargs)
    finally:
        left.close()
        right.close()


def test_worker_side_peer_admission_requires_exact_root_identity(monkeypatch):
    import loop_a_protected.darwin_peer as peer

    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        root = peer.PeerCredentials(pid=111, effective_pid=111, uid=0, gid=0)
        monkeypatch.setattr(peer, "read_peer_credentials", lambda sock: root)
        assert peer.validate_root_broker_peer(left, expected_pid=111) == root
        monkeypatch.setattr(peer, "read_peer_credentials", lambda sock: peer.PeerCredentials(
            pid=111, effective_pid=111, uid=501, gid=20,
        ))
        with pytest.raises(peer.DarwinPeerError, match="root broker"):
            peer.validate_root_broker_peer(left, expected_pid=111)
    finally:
        left.close()
        right.close()


def test_peer_admission_rejects_non_unix_or_unconnected_socket():
    from loop_a_protected.darwin_peer import DarwinPeerError, read_peer_credentials

    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        with pytest.raises(DarwinPeerError, match="AF_UNIX"):
            read_peer_credentials(tcp)
        with pytest.raises(DarwinPeerError, match="connected"):
            read_peer_credentials(unix)
    finally:
        tcp.close()
        unix.close()


def test_peer_admission_rejects_effective_pid_disagreement(monkeypatch):
    import loop_a_protected.darwin_peer as peer

    left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        monkeypatch.setattr(peer, "read_peer_credentials", lambda sock: peer.PeerCredentials(
            pid=1234, effective_pid=4321, uid=501, gid=20,
        ))
        with pytest.raises(peer.DarwinPeerError, match="effective PID"):
            peer.validate_launchd_worker_peer(
                left, broker_euid=0, expected_pid=1234, expected_uid=501, expected_gid=20,
            )
    finally:
        left.close()
        right.close()
