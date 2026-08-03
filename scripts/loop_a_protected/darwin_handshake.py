from __future__ import annotations

import os
import secrets
import signal
import socket
import struct
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest


class DarwinHandshakeError(RuntimeError):
    def __init__(self, message: str, *, child_reaped: bool = False) -> None:
        super().__init__(message)
        self.child_reaped = child_reaped


@dataclass(frozen=True)
class HandshakeExpectation:
    executable_device: int
    executable_inode: int
    executable_byte_count: int
    executable_sha256: str
    manifest_digest: str
    inventory_digest: str
    protected_fd_inventory: Tuple[Dict[str, Any], ...]


class PendingHandshake:
    def __init__(self, child_pid: int, challenge_write_fd: int, response_socket: socket.socket,
                 expectation: HandshakeExpectation, timeout_seconds: float = 5.0,
                 challenge_nonce: Optional[bytes] = None) -> None:
        if isinstance(child_pid, bool) or not isinstance(child_pid, int) or child_pid <= 0:
            raise DarwinHandshakeError("child PID must be positive")
        if not isinstance(response_socket, socket.socket) or response_socket.family != socket.AF_UNIX:
            raise DarwinHandshakeError("response channel must be an AF_UNIX socket")
        if not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 30:
            raise DarwinHandshakeError("handshake timeout is outside the fixed bound")
        if challenge_nonce is not None and (not isinstance(challenge_nonce, bytes) or len(challenge_nonce) != 32):
            raise DarwinHandshakeError("handshake challenge nonce must be exactly 32 bytes")
        os.fstat(challenge_write_fd)
        self.child_pid = child_pid
        self.challenge_write_fd = challenge_write_fd
        self.response_socket = response_socket
        self.expectation = expectation
        self.timeout_seconds = float(timeout_seconds)
        self.nonce = secrets.token_bytes(32) if challenge_nonce is None else challenge_nonce
        self._used = False

    @staticmethod
    def _recv_exact(sock: socket.socket, count: int) -> bytes:
        result = bytearray()
        while len(result) < count:
            chunk = sock.recv(count - len(result))
            if not chunk:
                raise DarwinHandshakeError("child closed handshake channel")
            result.extend(chunk)
        return bytes(result)

    def _recv_record(self) -> Dict[str, Any]:
        header = self._recv_exact(self.response_socket, 4)
        length = struct.unpack(">I", header)[0]
        if not 1 <= length <= 65_536:
            raise DarwinHandshakeError("handshake frame length is outside the fixed bound")
        payload = self._recv_exact(self.response_socket, length)
        try:
            value = parse_canonical_bytes(payload)
        except CanonicalJSONError as exc:
            raise DarwinHandshakeError("handshake record is not canonical JSON") from exc
        if not isinstance(value, dict):
            raise DarwinHandshakeError("handshake record must be an object")
        return value

    def _expected_record(self) -> Dict[str, Any]:
        value = {
            "schema": 1,
            "nonce": self.nonce.hex(),
            "child_pid": self.child_pid,
            "executable_device": self.expectation.executable_device,
            "executable_inode": self.expectation.executable_inode,
            "executable_byte_count": self.expectation.executable_byte_count,
            "executable_sha256": self.expectation.executable_sha256,
            "manifest_digest": self.expectation.manifest_digest,
            "inventory_digest": self.expectation.inventory_digest,
            "protected_fd_inventory": [dict(item) for item in self.expectation.protected_fd_inventory],
            "record_digest": None,
        }
        return with_self_digest(value, "record_digest")

    def _terminate_child(self) -> None:
        if self.child_pid == os.getpid():
            return
        try:
            os.kill(self.child_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(self.child_pid, 0)
        except ChildProcessError:
            pass
        self.child_pid = -1

    def close(self) -> None:
        if self.challenge_write_fd >= 0:
            try:
                os.close(self.challenge_write_fd)
            except OSError:
                pass
            self.challenge_write_fd = -1
        self.response_socket.close()

    def complete(self) -> Dict[str, Any]:
        if self._used:
            raise DarwinHandshakeError("handshake capability was already consumed")
        self._used = True
        try:
            self.response_socket.settimeout(self.timeout_seconds)
            written = os.write(self.challenge_write_fd, self.nonce)
            if written != len(self.nonce):
                raise DarwinHandshakeError("short challenge write")
            record = self._recv_record()
            extra = self.response_socket.recv(1)
            if extra:
                raise DarwinHandshakeError("child sent extra handshake frame data")
            if canonical_bytes(record) != canonical_bytes(self._expected_record()):
                raise DarwinHandshakeError("child handshake differs from exact expectation")
            ack = with_self_digest({
                "schema": 1,
                "nonce": self.nonce.hex(),
                "child_pid": self.child_pid,
                "capability": "attestation-only",
                "ack_digest": None,
            }, "ack_digest")
            payload = canonical_bytes(ack)
            frame = struct.pack(">I", len(payload)) + payload
            self.response_socket.sendall(frame)
            return ack
        except (OSError, CanonicalJSONError, DarwinHandshakeError) as exc:
            self._terminate_child()
            if isinstance(exc, DarwinHandshakeError):
                exc.child_reaped = True
                raise
            wrapped = DarwinHandshakeError("handshake failed closed")
            wrapped.child_reaped = True
            raise wrapped from exc
        finally:
            self.close()
