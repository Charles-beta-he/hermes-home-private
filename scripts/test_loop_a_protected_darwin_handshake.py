from __future__ import annotations

import os
import socket
import struct
import threading

import pytest

from loop_a_protected.canonical import canonical_bytes, with_self_digest


D0 = "0" * 64
D1 = "1" * 64


def _recv_exact(sock, count):
    result = bytearray()
    while len(result) < count:
        chunk = sock.recv(count - len(result))
        if not chunk:
            raise EOFError
        result.extend(chunk)
    return bytes(result)


def _safe_close(fd):
    try:
        os.close(fd)
    except OSError:
        pass


def _send_frame(sock, value):
    payload = canonical_bytes(value)
    sock.sendall(struct.pack(">I", len(payload)) + payload)


def _inventory():
    return ({
        "role": "retained-executable", "fd": 5, "device": 1, "inode": 2,
        "mode": 0o555, "uid": 0, "gid": 0, "link_count": 1,
        "byte_count": 10, "sha256": D0,
    },)


def _expectation():
    from loop_a_protected.darwin_handshake import HandshakeExpectation

    return HandshakeExpectation(
        executable_device=1, executable_inode=2, executable_byte_count=10,
        executable_sha256=D0, manifest_digest=D0, inventory_digest=D1,
        protected_fd_inventory=_inventory(),
    )


def _response(nonce, pid):
    return with_self_digest({
        "schema": 1, "nonce": nonce, "child_pid": pid,
        "executable_device": 1, "executable_inode": 2, "executable_byte_count": 10,
        "executable_sha256": D0, "manifest_digest": D0, "inventory_digest": D1,
        "protected_fd_inventory": list(_inventory()), "record_digest": None,
    }, "record_digest")


def test_valid_handshake_returns_broker_session_ack_without_sending_any_fd():
    from loop_a_protected.darwin_handshake import PendingHandshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    received = {}

    def child_main():
        nonce = os.read(challenge_read, 32).hex()
        _send_frame(child, _response(nonce, os.getpid()))
        child.shutdown(socket.SHUT_WR)
        header, ancillary, _flags, _address = child.recvmsg(
            4, socket.CMSG_SPACE(struct.calcsize("i"))
        )
        received["ancillary"] = ancillary
        length = struct.unpack(">I", header)[0]
        received["ack"] = _recv_exact(child, length)

    worker = threading.Thread(target=child_main)
    worker.start()
    try:
        pending = PendingHandshake(os.getpid(), challenge_write, parent, _expectation(), timeout_seconds=2.0)
        ack = pending.complete()
        worker.join(timeout=2.0)
        assert not worker.is_alive()
        assert ack["capability"] == "attestation-only"
        assert b"attestation-only" in received["ack"]
        assert received["ancillary"] == []
        with pytest.raises(Exception, match="already"):
            pending.complete()
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()


def test_broker_supplied_nonce_is_used_exactly_and_wrong_length_is_rejected():
    from loop_a_protected.darwin_handshake import DarwinHandshakeError, PendingHandshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        pending = PendingHandshake(
            os.getpid(), challenge_write, parent, _expectation(),
            challenge_nonce=b"z" * 32,
        )
        assert pending.nonce == b"z" * 32
        pending.close()
        with pytest.raises(DarwinHandshakeError, match="32 bytes"):
            PendingHandshake(os.getpid(), challenge_write, child, _expectation(), challenge_nonce=b"short")
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()


def test_extra_frame_before_half_close_sends_no_ack_and_terminates_child(monkeypatch):
    import loop_a_protected.darwin_handshake as handshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    killed = []
    waited = []
    received = {}
    monkeypatch.setattr(handshake.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr(handshake.os, "waitpid", lambda pid, options: waited.append((pid, options)) or (pid, 9))

    def child_main():
        nonce = os.read(challenge_read, 32).hex()
        _send_frame(child, _response(nonce, 4244))
        _send_frame(child, _response(nonce, 4244))
        child.shutdown(socket.SHUT_WR)
        received["data"] = child.recv(65536)

    worker = threading.Thread(target=child_main)
    worker.start()
    try:
        pending = handshake.PendingHandshake(4244, challenge_write, parent, _expectation(), timeout_seconds=1.0)
        with pytest.raises(handshake.DarwinHandshakeError, match="extra"):
            pending.complete()
        worker.join(timeout=1.0)
        assert not worker.is_alive()
        assert received["data"] == b""
        assert killed == [(4244, handshake.signal.SIGKILL)]
        assert waited == [(4244, 0)]
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()


def test_missing_request_half_close_times_out_without_ack(monkeypatch):
    import loop_a_protected.darwin_handshake as handshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    killed = []
    received = {}
    monkeypatch.setattr(handshake.os, "kill", lambda pid, sig: killed.append((pid, sig)))

    def child_main():
        nonce = os.read(challenge_read, 32).hex()
        _send_frame(child, _response(nonce, 4245))
        received["data"] = child.recv(65536)

    worker = threading.Thread(target=child_main)
    worker.start()
    try:
        pending = handshake.PendingHandshake(4245, challenge_write, parent, _expectation(), timeout_seconds=0.05)
        with pytest.raises(handshake.DarwinHandshakeError, match="failed closed"):
            pending.complete()
        worker.join(timeout=1.0)
        assert not worker.is_alive()
        assert received["data"] == b""
        assert killed == [(4245, handshake.signal.SIGKILL)]
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()


def test_mismatched_handshake_sends_no_ack_and_terminates_child(monkeypatch):
    import loop_a_protected.darwin_handshake as handshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    killed = []
    received = {}
    monkeypatch.setattr(handshake.os, "kill", lambda pid, sig: killed.append((pid, sig)))

    def child_main():
        os.read(challenge_read, 32)
        _send_frame(child, _response("f" * 64, 4242))
        child.shutdown(socket.SHUT_WR)
        received["data"] = child.recv(65536)

    worker = threading.Thread(target=child_main)
    worker.start()
    try:
        pending = handshake.PendingHandshake(4242, challenge_write, parent, _expectation(), timeout_seconds=1.0)
        with pytest.raises(handshake.DarwinHandshakeError, match="differs"):
            pending.complete()
        worker.join(timeout=1.0)
        assert not worker.is_alive()
        assert received["data"] == b""
        assert killed == [(4242, handshake.signal.SIGKILL)]
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()


_FIELD_MUTATIONS = (
    ("child_pid", 4247),
    ("executable_device", 7),
    ("executable_inode", 8),
    ("executable_byte_count", 11),
    ("executable_sha256", D1),
    ("manifest_digest", D1),
    ("inventory_digest", D0),
    ("protected_fd_inventory.role", "manifest"),
    ("protected_fd_inventory.fd", 6),
    ("protected_fd_inventory.device", 7),
    ("protected_fd_inventory.inode", 8),
    ("protected_fd_inventory.mode", 0o444),
    ("protected_fd_inventory.uid", 1),
    ("protected_fd_inventory.gid", 1),
    ("protected_fd_inventory.link_count", 2),
    ("protected_fd_inventory.byte_count", 11),
    ("protected_fd_inventory.sha256", D1),
)


@pytest.mark.parametrize(("field", "replacement"), _FIELD_MUTATIONS)
def test_each_handshake_binding_field_is_independently_required(monkeypatch, field, replacement):
    import loop_a_protected.darwin_handshake as handshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    monkeypatch.setattr(handshake.os, "kill", lambda _pid, _sig: None)
    monkeypatch.setattr(handshake.os, "waitpid", lambda pid, _options: (pid, 9))
    try:
        pending = handshake.PendingHandshake(4246, challenge_write, parent, _expectation(), timeout_seconds=1.0)
        response = _response(pending.nonce.hex(), 4246)
        response["record_digest"] = None
        if field.startswith("protected_fd_inventory."):
            nested = dict(response["protected_fd_inventory"][0])
            nested[field.split(".", 1)[1]] = replacement
            response["protected_fd_inventory"] = [nested]
        else:
            response[field] = replacement
        response = with_self_digest(response, "record_digest")
        _send_frame(child, response)
        child.shutdown(socket.SHUT_WR)
        with pytest.raises(handshake.DarwinHandshakeError, match="differs"):
            pending.complete()
        assert child.recv(1) == b""
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()


def test_missing_handshake_times_out_without_sending_ack(monkeypatch):
    import loop_a_protected.darwin_handshake as handshake

    challenge_read, challenge_write = os.pipe()
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    killed = []
    monkeypatch.setattr(handshake.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    try:
        pending = handshake.PendingHandshake(4243, challenge_write, parent, _expectation(), timeout_seconds=0.05)
        with pytest.raises(handshake.DarwinHandshakeError, match="failed closed"):
            pending.complete()
        child.settimeout(0.05)
        assert child.recv(1) == b""
        assert killed == [(4243, handshake.signal.SIGKILL)]
    finally:
        os.close(challenge_read)
        _safe_close(challenge_write)
        parent.close()
        child.close()
