#!/usr/bin/env python3
"""Deterministic resident-consumer harness for the N1 durable outbox.

This N2 module is deliberately local and effect-free: it can run only an injected
bounded worker command after a successful durable claim.  It does not import or
invoke taskpool dispatch, agents, models, schedulers, networks, or services.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
import selectors
import signal
import socket
import sqlite3
import stat
import struct
import subprocess
import threading
import time
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple, Union
import uuid

from taskpool_event_outbox import DurableTaskpoolEventOutbox

MAX_WORK_EPOCH = (1 << 63) - 1
_RUNTIME_SCHEMA = 1
_INTENT_KEYS = frozenset(
    {"schema", "channel_nonce", "sequence", "event_id", "generation", "kind", "result"}
)


class RuntimeStateError(RuntimeError):
    """Durable broker runtime identity is absent, corrupt, stale, or exhausted."""


class BrokerProtocolError(RuntimeError):
    """A local wake or worker frame violated the closed protocol."""


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BrokerProtocolError("payload is not strict finite JSON") from exc


def _safe_private_path(path: Union[str, os.PathLike], root: Union[str, os.PathLike]) -> Path:
    candidate = Path(path).expanduser().absolute()
    allowed = Path(root).expanduser().absolute()
    try:
        candidate.relative_to(allowed)
    except ValueError as exc:
        raise RuntimeStateError("path escapes allowed root") from exc
    current = allowed
    if current.exists() and stat.S_ISLNK(os.lstat(current).st_mode):
        raise RuntimeStateError("allowed root may not be a symlink")
    for part in candidate.relative_to(allowed).parts:
        current = current / part
        if current.exists() and stat.S_ISLNK(os.lstat(current).st_mode):
            raise RuntimeStateError("runtime path may not traverse a symlink")
    return candidate


class BrokerRuntimeState:
    """Durable generation/epoch state held through one inode-bound SQLite handle."""

    def __init__(self, path: Union[str, os.PathLike], *, allowed_root: Union[str, os.PathLike]):
        self._root = Path(allowed_root).expanduser().absolute()
        self.path = _safe_private_path(path, self._root)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        self._parent_real = self.path.parent.resolve(strict=True)
        if not self.path.exists():
            flags = os.O_CREAT | os.O_EXCL | os.O_RDWR
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(self.path, flags, 0o600)
            os.close(descriptor)
        info = os.lstat(self.path)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1:
            raise RuntimeStateError("runtime database must be a private single-link regular file")
        self._db_identity = (info.st_dev, info.st_ino)
        self._lock = threading.RLock()
        self._connection, self._db_fd = self._open_persistent_connection()
        try:
            self._connection.execute("PRAGMA journal_mode=DELETE")
            self._connection.execute("PRAGMA synchronous=FULL")
            self._connection.execute(
                """CREATE TABLE IF NOT EXISTS broker_runtime (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    schema_version INTEGER NOT NULL CHECK(schema_version=1),
                    db_generation TEXT NOT NULL,
                    work_epoch INTEGER NOT NULL CHECK(work_epoch>=0),
                    updated_at REAL NOT NULL)"""
            )
            count = self._connection.execute("SELECT COUNT(*) FROM broker_runtime").fetchone()[0]
            if count == 0:
                self._connection.execute(
                    "INSERT INTO broker_runtime VALUES(1,?,?,0,?)",
                    (_RUNTIME_SCHEMA, str(uuid.uuid4()), time.time()),
                )
            elif count != 1:
                raise RuntimeStateError("runtime singleton cardinality failure")
            row = self._connection.execute("SELECT db_generation FROM broker_runtime WHERE singleton=1").fetchone()
            if row is None or type(row[0]) is not str:
                raise RuntimeStateError("runtime store generation missing")
            self._store_generation = row[0]
            self.snapshot()
        except Exception:
            self.close()
            raise

    @staticmethod
    def _open_fd_identities() -> Dict[int, Tuple[int, int, int]]:
        directory = "/dev/fd" if os.path.isdir("/dev/fd") else "/proc/self/fd"
        identities: Dict[int, Tuple[int, int, int]] = {}
        for name in os.listdir(directory):
            if not name.isdigit():
                continue
            descriptor = int(name)
            try:
                info = os.fstat(descriptor)
            except OSError:
                continue
            identities[descriptor] = (stat.S_IFMT(info.st_mode), info.st_dev, info.st_ino)
        return identities

    def _open_persistent_connection(self) -> Tuple[sqlite3.Connection, int]:
        before = self._open_fd_identities()
        connection = sqlite3.connect(str(self.path), timeout=5.0, isolation_level=None, check_same_thread=False)
        try:
            connection.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
            matching = []
            after = self._open_fd_identities()
            for descriptor, identity in after.items():
                file_type, device, inode = identity
                if (
                    file_type == stat.S_IFREG
                    and (device, inode) == self._db_identity
                    and before.get(descriptor) != identity
                ):
                    matching.append(descriptor)
            if len(matching) != 1:
                raise RuntimeStateError("cannot bind SQLite connection to frozen runtime inode")
            return connection, matching[0]
        except Exception:
            connection.close()
            raise

    def _verify_path(self) -> None:
        _safe_private_path(self.path, self._root)
        info = os.lstat(self.path)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_nlink != 1
            or (info.st_dev, info.st_ino) != self._db_identity
            or self.path.parent.resolve(strict=True) != self._parent_real
        ):
            raise RuntimeStateError("runtime database path identity changed")

    def _verify_connection(self) -> None:
        self._verify_path()
        try:
            info = os.fstat(self._db_fd)
        except OSError as exc:
            raise RuntimeStateError("runtime connection descriptor disappeared") from exc
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != self._db_identity:
            raise RuntimeStateError("runtime connection inode changed")

    @staticmethod
    def _validated(row: Optional[Sequence[Any]]) -> Dict[str, Any]:
        if (
            row is None or len(row) != 3
            or type(row[0]) is not int or row[0] != _RUNTIME_SCHEMA
            or type(row[1]) is not str or not row[1]
            or type(row[2]) is not int or not (0 <= row[2] <= MAX_WORK_EPOCH)
        ):
            raise RuntimeStateError("runtime identity integrity failure")
        try:
            uuid.UUID(row[1])
        except (ValueError, AttributeError) as exc:
            raise RuntimeStateError("invalid db_generation") from exc
        return {"db_generation": row[1], "work_epoch": row[2]}

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            self._verify_connection()
            row = self._connection.execute(
                "SELECT schema_version,db_generation,work_epoch FROM broker_runtime WHERE singleton=1"
            ).fetchone()
            validated = self._validated(row)
            if validated["db_generation"] != self._store_generation:
                raise RuntimeStateError("connected runtime store identity changed")
            self._verify_connection()
            return validated

    def advance(self, *, expected: Mapping[str, Any]) -> Dict[str, Any]:
        frozen = {"db_generation": expected.get("db_generation"), "work_epoch": expected.get("work_epoch")}
        if type(frozen["db_generation"]) is not str or type(frozen["work_epoch"]) is not int:
            raise RuntimeStateError("expected identity is not exact")
        with self._lock:
            self._verify_connection()
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                row = self._connection.execute(
                    "SELECT schema_version,db_generation,work_epoch FROM broker_runtime WHERE singleton=1"
                ).fetchone()
                current = self._validated(row)
                if current != frozen or current["db_generation"] != self._store_generation:
                    raise RuntimeStateError("stale runtime identity")
                if current["work_epoch"] == MAX_WORK_EPOCH:
                    raise RuntimeStateError("work_epoch exhausted")
                next_epoch = current["work_epoch"] + 1
                updated = self._connection.execute(
                    """UPDATE broker_runtime SET work_epoch=?,updated_at=?
                    WHERE singleton=1 AND db_generation=? AND work_epoch=?""",
                    (next_epoch, time.time(), current["db_generation"], current["work_epoch"]),
                )
                if updated.rowcount != 1:
                    raise RuntimeStateError("runtime identity CAS failed")
                self._verify_connection()
                self._connection.commit()
                self._verify_connection()
                return {"db_generation": current["db_generation"], "work_epoch": next_epoch}
            except Exception:
                self._connection.rollback()
                raise

    def close(self) -> None:
        with self._lock:
            connection = getattr(self, "_connection", None)
            if connection is not None:
                connection.close()
                self._connection = None
                self._db_fd = -1


class StrictFrameCodec:
    """Length-delimited, nonce/sequence-bound, HMAC-authenticated local frames."""

    MAX_BODY = 1024 * 1024

    def __init__(self, *, key: bytes, channel_nonce: str):
        if type(key) is not bytes or len(key) < 32:
            raise BrokerProtocolError("frame key must contain at least 32 bytes")
        if type(channel_nonce) is not str or not channel_nonce:
            raise BrokerProtocolError("channel nonce must be non-empty")
        self._key = key
        self.channel_nonce = channel_nonce

    def encode(self, *, sequence: int, payload: Any) -> bytes:
        if type(sequence) is not int or sequence <= 0:
            raise BrokerProtocolError("sequence must be a positive exact integer")
        body = _canonical_json(
            {"channel_nonce": self.channel_nonce, "sequence": sequence, "payload": payload}
        )
        if len(body) > self.MAX_BODY:
            raise BrokerProtocolError("frame body too large")
        tag = hmac.new(self._key, body, hashlib.sha256).digest()
        return struct.pack(">I", len(body)) + body + tag

    def decode(self, frame: bytes, *, expected_sequence: Optional[int] = None) -> Any:
        if type(frame) is not bytes or len(frame) < 4 + 32:
            raise BrokerProtocolError("truncated frame")
        size = struct.unpack(">I", frame[:4])[0]
        if size > self.MAX_BODY or len(frame) != 4 + size + 32:
            raise BrokerProtocolError("frame length mismatch")
        body, supplied = frame[4 : 4 + size], frame[4 + size :]
        expected = hmac.new(self._key, body, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied, expected):
            raise BrokerProtocolError("frame authentication failed")
        try:
            envelope = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BrokerProtocolError("frame JSON invalid") from exc
        if type(envelope) is not dict or set(envelope) != {"channel_nonce", "sequence", "payload"}:
            raise BrokerProtocolError("frame envelope schema mismatch")
        if envelope["channel_nonce"] != self.channel_nonce:
            raise BrokerProtocolError("frame nonce mismatch")
        if (
            type(envelope["sequence"]) is not int
            or envelope["sequence"] <= 0
            or (expected_sequence is not None and envelope["sequence"] != expected_sequence)
        ):
            raise BrokerProtocolError("frame sequence mismatch")
        if _canonical_json(envelope) != body:
            raise BrokerProtocolError("frame JSON is not canonical")
        return envelope["payload"]


class UnixWakeEndpoint:
    """Authenticated Unix-stream wake endpoint with replay and pathname fencing."""

    def __init__(
        self,
        path: Union[str, os.PathLike],
        *,
        key: bytes,
        channel_nonce: Optional[str] = None,
        expected_socket_identity: Optional[Tuple[int, int]] = None,
        peer_timeout: float = 0.25,
    ):
        if type(peer_timeout) not in (int, float) or not math.isfinite(peer_timeout) or peer_timeout <= 0:
            raise BrokerProtocolError("peer_timeout must be finite and positive")
        self.path = Path(path)
        self._key = key
        self._channel_nonce = channel_nonce or secrets.token_hex(16)
        self._codec = StrictFrameCodec(key=key, channel_nonce=self._channel_nonce)
        self._listener: Optional[socket.socket] = None
        self._socket_identity: Optional[Tuple[int, int]] = None
        self._expected_socket_identity = expected_socket_identity
        self._peer_timeout = float(peer_timeout)
        self.registered = False

    def register(self) -> None:
        if self.registered or self.path.exists():
            raise BrokerProtocolError("wake endpoint already exists or is registered")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(str(self.path))
            os.chmod(self.path, 0o600)
            info = os.lstat(self.path)
            if not stat.S_ISSOCK(info.st_mode):
                raise BrokerProtocolError("wake endpoint did not bind a socket")
            listener.listen(8)
            self._socket_identity = (info.st_dev, info.st_ino)
            self._expected_socket_identity = self._socket_identity
            self._listener = listener
            self.registered = True
        except Exception:
            listener.close()
            raise

    def _verify_socket_path(self) -> Tuple[int, int]:
        try:
            info = os.lstat(self.path)
        except FileNotFoundError as exc:
            raise BrokerProtocolError("wake socket pathname disappeared") from exc
        identity = (info.st_dev, info.st_ino)
        if (
            not stat.S_ISSOCK(info.st_mode)
            or self._expected_socket_identity is None
            or identity != self._expected_socket_identity
        ):
            raise BrokerProtocolError("wake socket pathname identity changed")
        return identity

    def verify_registered(self) -> None:
        if not self.registered or self._listener is None:
            raise BrokerProtocolError("wake receiver is not registered")
        self._verify_socket_path()

    def verify_send_target(self) -> None:
        self._verify_socket_path()

    def sender_endpoint(self) -> "UnixWakeEndpoint":
        self.verify_registered()
        return UnixWakeEndpoint(
            self.path,
            key=self._key,
            channel_nonce=self._channel_nonce,
            expected_socket_identity=self._socket_identity,
            peer_timeout=self._peer_timeout,
        )

    def build_wake_frame(self, *, sequence: int, payload: Any) -> bytes:
        return self._codec.encode(sequence=sequence, payload=payload)

    def send_frame(self, frame: bytes, *, commit: Optional[Callable[[], Any]] = None) -> Any:
        self.verify_send_target()
        request_payload = self._codec.decode(frame)
        body_size = struct.unpack(">I", frame[:4])[0]
        request_body = json.loads(frame[4 : 4 + body_size].decode("utf-8"))
        sequence = request_body["sequence"]
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(self._peer_timeout)
        try:
            client.connect(str(self.path))
            self.verify_send_target()
            client.sendall(frame)
            prefix = self._recv_exact(client, 4)
            ack_size = struct.unpack(">I", prefix)[0]
            if ack_size > StrictFrameCodec.MAX_BODY:
                raise BrokerProtocolError("wake acknowledgement too large")
            acknowledgement = prefix + self._recv_exact(client, ack_size + 32)
            ack_payload = self._codec.decode(acknowledgement, expected_sequence=sequence)
            expected_ack = {
                "schema": "taskpool.wake-ready.v1",
                "request_sha256": hashlib.sha256(frame).hexdigest(),
                "identity": request_payload.get("identity") if type(request_payload) is dict else None,
            }
            if ack_payload != expected_ack:
                raise BrokerProtocolError("wake readiness acknowledgement mismatch")
            committed = commit() if commit is not None else None
            self._send_commit_marker(client)
            client.shutdown(socket.SHUT_WR)
            return committed
        except socket.timeout as exc:
            raise BrokerProtocolError("wake readiness acknowledgement timed out") from exc
        finally:
            client.close()

    @staticmethod
    def _send_commit_marker(client: socket.socket) -> None:
        client.sendall(b"\x01")

    def send_wake(
        self,
        *,
        sequence: int,
        payload: Any,
        commit: Optional[Callable[[], Any]] = None,
    ) -> Any:
        return self.send_frame(
            self.build_wake_frame(sequence=sequence, payload=payload), commit=commit
        )

    @staticmethod
    def _recv_exact(connection: socket.socket, size: int) -> bytes:
        chunks = []
        remaining = size
        while remaining:
            chunk = connection.recv(remaining)
            if not chunk:
                raise BrokerProtocolError("truncated wake frame")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def receive_once(
        self, *, timeout: Optional[float], minimum_sequence: int = 1
    ) -> Dict[str, Any]:
        self.verify_registered()
        if type(minimum_sequence) is not int or not (1 <= minimum_sequence <= MAX_WORK_EPOCH):
            raise BrokerProtocolError("minimum wake sequence is invalid")
        self._listener.settimeout(timeout)
        connection, _ = self._listener.accept()
        try:
            peer_budget = self._peer_timeout if timeout is None else min(float(timeout), self._peer_timeout)
            connection.settimeout(peer_budget)
            prefix = self._recv_exact(connection, 4)
            size = struct.unpack(">I", prefix)[0]
            if size > StrictFrameCodec.MAX_BODY:
                raise BrokerProtocolError("wake frame too large")
            frame = prefix + self._recv_exact(connection, size + 32)
            payload = self._codec.decode(frame)
            body = json.loads(frame[4 : 4 + size].decode("utf-8"))
            sequence = body["sequence"]
            if not (minimum_sequence <= sequence <= MAX_WORK_EPOCH):
                raise BrokerProtocolError("wake frame replayed, reordered, or exhausted")
            if type(payload) is not dict or set(payload) != {"reason", "identity"}:
                raise BrokerProtocolError("wake payload schema mismatch")
            identity = payload["identity"]
            if (
                payload["reason"] != "post_commit"
                or type(identity) is not dict
                or set(identity) != {"db_generation", "work_epoch"}
                or type(identity["db_generation"]) is not str
                or not identity["db_generation"]
                or type(identity["work_epoch"]) is not int
                or identity["work_epoch"] != sequence
            ):
                raise BrokerProtocolError("wake payload is not bound to durable identity")
            acknowledgement = self._codec.encode(
                sequence=sequence,
                payload={
                    "schema": "taskpool.wake-ready.v1",
                    "request_sha256": hashlib.sha256(frame).hexdigest(),
                    "identity": identity,
                },
            )
            try:
                connection.sendall(acknowledgement)
                marker = connection.recv(1)
                if marker == b"\x01":
                    if connection.recv(1):
                        raise BrokerProtocolError("wake commit marker has trailing bytes")
                elif marker != b"":
                    raise BrokerProtocolError("wake commit marker is invalid")
            except socket.timeout:
                # A sender that dies or stalls after READY still releases the waiter,
                # which then resolves commit truth from the durable runtime inode.
                pass
            except OSError:
                pass
            return payload
        except socket.timeout as exc:
            raise TimeoutError("wake peer stalled") from exc
        finally:
            connection.close()

    def close(self) -> None:
        if self._listener is None:
            self.registered = False
            return
        self._listener.close()
        self._listener = None
        self.registered = False
        try:
            info = os.lstat(self.path)
        except FileNotFoundError:
            self._socket_identity = None
            return
        identity = (info.st_dev, info.st_ino)
        if not stat.S_ISSOCK(info.st_mode) or identity != self._socket_identity:
            raise BrokerProtocolError("wake pathname identity changed; refusing unlink")
        self.path.unlink()
        self._socket_identity = None


class DeterministicConsumerBroker:
    """Claim-gated deterministic subprocess consumer with durable wake epochs."""

    MIN_LEASE_SECONDS = 0.1

    def __init__(
        self,
        *,
        outbox: DurableTaskpoolEventOutbox,
        runtime_state: BrokerRuntimeState,
        wake_endpoint: UnixWakeEndpoint,
        worker_argv: Sequence[str],
        lease_seconds: Union[int, float],
        worker_timeout: Union[int, float],
        clock: Callable[[], float] = time.time,
        popen_factory: Callable[..., subprocess.Popen] = subprocess.Popen,
        max_attempts: int = 3,
        output_limit: int = StrictFrameCodec.MAX_BODY + 36,
    ):
        if not worker_argv or any(type(item) is not str or not item for item in worker_argv):
            raise ValueError("worker_argv must be a non-empty exact string sequence")
        if (
            type(lease_seconds) not in (int, float)
            or not math.isfinite(lease_seconds)
            or lease_seconds < self.MIN_LEASE_SECONDS
        ):
            raise ValueError(
                f"lease_seconds must be finite and at least {self.MIN_LEASE_SECONDS}"
            )
        if type(worker_timeout) not in (int, float) or not math.isfinite(worker_timeout) or worker_timeout <= 0:
            raise ValueError("worker_timeout must be positive")
        if type(max_attempts) is not int or max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if type(output_limit) is not int or output_limit <= 36:
            raise ValueError("output_limit must be a positive exact bound")
        self.outbox = outbox
        self.runtime_state = runtime_state
        self.wake_endpoint = wake_endpoint
        self.worker_argv = tuple(worker_argv)
        self.lease_seconds = float(lease_seconds)
        self.worker_timeout = float(worker_timeout)
        self.clock = clock
        self.popen_factory = popen_factory
        self.max_attempts = max_attempts
        self.output_limit = output_limit
        self.worker_start_count = 0
        self.last_worker_pid: Optional[int] = None
        self._watchdog_ready = True
        self._last_timer_token: Optional[Dict[str, Any]] = None

    def runtime_identity(self) -> Dict[str, Any]:
        return self.runtime_state.snapshot()

    def notify_post_commit(self) -> Dict[str, Any]:
        self.wake_endpoint.verify_send_target()
        current = self.runtime_state.snapshot()
        proposed = {
            "db_generation": current["db_generation"],
            "work_epoch": current["work_epoch"] + 1,
        }

        def commit_epoch() -> Dict[str, Any]:
            published = self.runtime_state.advance(expected=current)
            if published != proposed:
                raise RuntimeStateError("runtime advance diverged from prepared wake identity")
            return published

        return self.wake_endpoint.send_wake(
            sequence=proposed["work_epoch"],
            payload={"reason": "post_commit", "identity": proposed},
            commit=commit_epoch,
        )

    def wait_for_work(
        self, *, observed: Mapping[str, Any], timeout: Optional[float]
    ) -> Dict[str, Any]:
        frozen = {
            "db_generation": observed.get("db_generation"),
            "work_epoch": observed.get("work_epoch"),
        }
        if (
            type(frozen["db_generation"]) is not str
            or not frozen["db_generation"]
            or type(frozen["work_epoch"]) is not int
            or not (0 <= frozen["work_epoch"] < MAX_WORK_EPOCH)
            or (timeout is not None and (
                type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout < 0
            ))
        ):
            raise RuntimeStateError("observed identity or wait timeout is invalid")
        deadline = None if timeout is None else time.monotonic() + float(timeout)
        current = self.runtime_state.snapshot()
        if current != frozen:
            return {"reason": "epoch_changed", "identity": current}
        while True:
            remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
            if remaining == 0.0:
                current = self.runtime_state.snapshot()
                reason = "epoch_changed" if current != frozen else "timeout"
                return {"reason": reason, "identity": current}
            try:
                wake = self.wake_endpoint.receive_once(
                    timeout=remaining, minimum_sequence=frozen["work_epoch"] + 1
                )
            except BrokerProtocolError:
                continue
            except (TimeoutError, socket.timeout):
                current = self.runtime_state.snapshot()
                if current != frozen:
                    return {"reason": "epoch_changed", "identity": current}
                return {"reason": "timeout", "identity": current}
            current = self.runtime_state.snapshot()
            if current == frozen:
                # READY was authenticated, but the sender closed or failed before
                # committing its prepared epoch. Re-arm without a periodic timer.
                continue
            if wake["identity"] != current:
                raise RuntimeStateError("wake identity does not match durable runtime state")
            return {"reason": "epoch_changed", "identity": current}

    @staticmethod
    def _counts(status: Mapping[str, Any]) -> Tuple[int, int]:
        if type(status) is not dict or "counts" not in status or "events" not in status:
            raise RuntimeStateError("outbox status envelope is incomplete")
        counts = status["counts"]
        events = status["events"]
        allowed = {"pending", "claimed", "completed", "failed"}
        if type(counts) is not dict or type(events) is not list or not set(counts).issubset(allowed):
            raise RuntimeStateError("outbox status shape is invalid")
        if any(type(value) is not int or value < 0 for value in counts.values()):
            raise RuntimeStateError("outbox count is not an exact non-negative integer")
        actual = {name: 0 for name in allowed}
        for event in events:
            if type(event) is not dict or event.get("status") not in allowed:
                raise RuntimeStateError("outbox event status is invalid")
            actual[event["status"]] += 1
        for name in allowed:
            if counts.get(name, 0) != actual[name]:
                raise RuntimeStateError("outbox counts do not match canonical events")
        return counts.get("pending", 0), counts.get("claimed", 0)

    def _earliest_claim_deadline(self, status: Mapping[str, Any]) -> Optional[float]:
        events = status.get("events")
        if type(events) is not list:
            raise RuntimeStateError("outbox events are unavailable for deadline scheduling")
        deadlines = []
        now = self.clock()
        for event in events:
            if type(event) is not dict:
                raise RuntimeStateError("outbox event is malformed")
            if event.get("status") != "claimed":
                continue
            deadline = event.get("lease_deadline")
            if type(deadline) not in (int, float) or not math.isfinite(deadline):
                raise RuntimeStateError("claimed lease deadline is not finite")
            if deadline > now:
                deadlines.append(float(deadline))
        return min(deadlines) if deadlines else None

    def _advance_runtime(self) -> Dict[str, Any]:
        current = self.runtime_state.snapshot()
        return self.runtime_state.advance(expected=current)

    @staticmethod
    def _group_exists(pgid: int) -> bool:
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False

    def _wait_for_group_exit(self, pgid: int, *, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if not self._group_exists(pgid):
                    return True
            except PermissionError:
                # macOS can transiently report EPERM while an exited session
                # leader and its descendants are being reaped. Never convert
                # that ambiguity into a signal against a potentially reused
                # process-group identity; wait boundedly for a definitive read.
                pass
            time.sleep(0.01)
        try:
            return not self._group_exists(pgid)
        except PermissionError as exc:
            raise BrokerProtocolError("worker process group could not be verified") from exc

    @staticmethod
    def _terminate_process_directly(process: subprocess.Popen, *, timeout: float) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                raise BrokerProtocolError("worker process survived bounded direct cleanup") from exc
        except ProcessLookupError:
            return

    def _cleanup_process_group(self, process: subprocess.Popen) -> None:
        pgid = process.pid
        # poll() reaps an exited direct child, but cleanup must still inspect the
        # process group because descendants can outlive that child.
        process.poll()
        try:
            group_exists = self._group_exists(pgid)
        except PermissionError:
            grace = min(0.5, self.worker_timeout)
            self._terminate_process_directly(process, timeout=grace)
            if not self._wait_for_group_exit(pgid, timeout=grace):
                raise BrokerProtocolError("worker process group survived direct cleanup")
            return
        if not group_exists:
            return
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return
        grace = min(0.5, self.worker_timeout)
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        if self._wait_for_group_exit(pgid, timeout=grace):
            return
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            return
        if not self._wait_for_group_exit(pgid, timeout=0.5):
            raise BrokerProtocolError("worker process group survived bounded cleanup")

    def _renew_claim(self, event: Dict[str, Any]) -> Dict[str, Any]:
        now = self.clock()
        renewed = self.outbox.renew(
            event_id=event["event_id"],
            claim_token=event["claim_token"],
            generation=event["generation"],
            lease_seconds=self.lease_seconds,
            now=now,
        )
        event.update(renewed)
        identity = self._advance_runtime()
        self._last_timer_token = {
            "event_id": event["event_id"],
            "generation": event["generation"],
            "lease_deadline": event["lease_deadline"],
            "runtime_identity": identity,
        }
        return event

    def _claim_renewal_time(self, event: Mapping[str, Any]) -> float:
        lease_deadline = event.get("lease_deadline")
        if type(lease_deadline) is int:
            deadline = float(lease_deadline)
        elif type(lease_deadline) is float and math.isfinite(lease_deadline):
            deadline = lease_deadline
        else:
            raise BrokerProtocolError("worker claim lease deadline is invalid")
        return deadline - self.lease_seconds / 2.0

    def _bounded_exchange(
        self, process: subprocess.Popen, *, request: bytes, event: Dict[str, Any]
    ) -> bytes:
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise BrokerProtocolError("worker pipes are unavailable")
        selector = selectors.DefaultSelector()
        streams = {
            "stdin": process.stdin,
            "stdout": process.stdout,
            "stderr": process.stderr,
        }
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        request_view = memoryview(request)
        request_offset = 0
        for name, stream in streams.items():
            os.set_blocking(stream.fileno(), False)
            selector.register(
                stream.fileno(),
                selectors.EVENT_WRITE if name == "stdin" else selectors.EVENT_READ,
                data=name,
            )
        deadline = time.monotonic() + self.worker_timeout
        renew_at = self._claim_renewal_time(event)
        try:
            while True:
                monotonic_now = time.monotonic()
                if monotonic_now >= deadline:
                    raise BrokerProtocolError("worker timed out")
                now = self.clock()
                if now >= renew_at:
                    self._renew_claim(event)
                    renew_at = self._claim_renewal_time(event)
                select_timeout = min(
                    0.02,
                    max(0.0, deadline - time.monotonic()),
                    max(0.0, renew_at - self.clock()),
                )
                for key, _mask in selector.select(timeout=select_timeout):
                    name = key.data
                    fd = key.fd
                    if name == "stdin":
                        try:
                            written = os.write(fd, request_view[request_offset:])
                        except BlockingIOError:
                            continue
                        except BrokenPipeError:
                            written = 0
                            selector.unregister(fd)
                            process.stdin.close()
                        else:
                            request_offset += written
                            if request_offset == len(request):
                                selector.unregister(fd)
                                process.stdin.close()
                        continue
                    chunk = os.read(fd, 65536)
                    if chunk:
                        buffers[name].extend(chunk)
                        if sum(len(buffer) for buffer in buffers.values()) > self.output_limit:
                            raise BrokerProtocolError("worker aggregate output exceeded byte limit")
                    else:
                        selector.unregister(fd)
                active = {registered.data for registered in selector.get_map().values()}
                if process.poll() is not None and not ({"stdout", "stderr"} & active):
                    break
            process.wait(timeout=0.1)
            if process.returncode != 0:
                raise BrokerProtocolError("worker exited without an accepted intent")
            if buffers["stderr"]:
                raise BrokerProtocolError("worker wrote unexpected stderr")
            return bytes(buffers["stdout"])
        finally:
            selector.close()
            if not process.stdin.closed:
                process.stdin.close()

    def _start_worker_channel(self) -> Tuple[subprocess.Popen, StrictFrameCodec, str]:
        nonce = secrets.token_hex(24)
        key = secrets.token_bytes(32)
        codec = StrictFrameCodec(key=key, channel_nonce=nonce)
        self.worker_start_count += 1
        process = self.popen_factory(
            self.worker_argv,
            text=False,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            start_new_session=True,
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONDONTWRITEBYTECODE": "1",
                "TASKPOOL_WORKER_KEY_HEX": key.hex(),
            },
        )
        self.last_worker_pid = process.pid
        return process, codec, nonce

    def _worker_intent(
        self,
        event: Dict[str, Any],
        *,
        process: subprocess.Popen,
        codec: StrictFrameCodec,
        nonce: str,
    ) -> Dict[str, Any]:
        request = codec.encode(
            sequence=1,
            payload={"schema": "taskpool.worker-request.v1", "event": dict(event)},
        )
        frame = self._bounded_exchange(process, request=request, event=event)
        intent = codec.decode(frame, expected_sequence=1)
        if type(intent) is not dict or set(intent) != _INTENT_KEYS:
            raise BrokerProtocolError("worker intent schema mismatch")
        if (
            intent["schema"] != "taskpool.worker-intent.v1"
            or intent["channel_nonce"] != nonce
            or type(intent["sequence"]) is not int
            or intent["sequence"] != 1
            or intent["event_id"] != event["event_id"]
            or type(intent["generation"]) is not int
            or intent["generation"] != event["generation"]
            or intent["kind"] != "complete"
        ):
            raise BrokerProtocolError("worker intent identity mismatch")
        _canonical_json(intent["result"])
        return intent

    def _work_is_due(self, status: Mapping[str, Any], *, now: float) -> bool:
        self._counts(status)
        if type(now) is not float or not math.isfinite(now):
            raise RuntimeStateError("work eligibility time is invalid")
        due = False
        for event in status["events"]:
            if event["status"] == "pending":
                due = True
                continue
            if event["status"] != "claimed":
                continue
            lease_deadline = event.get("lease_deadline")
            if type(lease_deadline) is int:
                deadline = float(lease_deadline)
            elif type(lease_deadline) is float and math.isfinite(lease_deadline):
                deadline = lease_deadline
            else:
                raise RuntimeStateError("claimed lease deadline is invalid")
            if deadline <= now:
                due = True
        return due

    def _claim_and_run_once(self) -> str:
        eligibility_time = self.clock()
        if type(eligibility_time) is int:
            eligibility_time = float(eligibility_time)
        if not self._work_is_due(self.outbox.status(), now=eligibility_time):
            return "idle"

        process, codec, nonce = self._start_worker_channel()
        try:
            event = self.outbox.claim(lease_seconds=self.lease_seconds, now=self.clock())
            if event is None:
                return "idle"
            event = dict(event)
            identity = self._advance_runtime()
            self._last_timer_token = {
                "event_id": event["event_id"],
                "generation": event["generation"],
                "lease_deadline": event["lease_deadline"],
                "runtime_identity": identity,
            }
            try:
                intent = self._worker_intent(
                    event, process=process, codec=codec, nonce=nonce
                )
                self.outbox.complete(
                    event_id=event["event_id"],
                    claim_token=event["claim_token"],
                    generation=event["generation"],
                    result=intent["result"],
                    now=self.clock(),
                )
                self._advance_runtime()
                return "completed"
            except Exception as exc:
                try:
                    self.outbox.fail(
                        event_id=event["event_id"],
                        claim_token=event["claim_token"],
                        generation=event["generation"],
                        error={"class": type(exc).__name__, "retryable": True},
                        retryable=True,
                        max_attempts=self.max_attempts,
                        now=self.clock(),
                    )
                    self._advance_runtime()
                except Exception:
                    # A stale/expired lease remains a canonical claimed obligation and
                    # is reconciled from status; failure reporting must not hide it.
                    pass
                return "worker_failure"
        finally:
            self._cleanup_process_group(process)

    def timer_fire(self, token: Mapping[str, Any]) -> str:
        if type(token) is not dict or set(token) != {
            "event_id", "generation", "lease_deadline", "runtime_identity"
        }:
            raise RuntimeStateError("timer token schema mismatch")
        if self.runtime_state.snapshot() != token["runtime_identity"]:
            return "stale"
        status = self.outbox.status()
        self._counts(status)
        matches = [
            event for event in status["events"]
            if event.get("event_id") == token["event_id"]
            and event.get("status") == "claimed"
            and event.get("generation") == token["generation"]
            and event.get("lease_deadline") == token["lease_deadline"]
        ]
        return "current" if len(matches) == 1 else "stale"

    def startup_drain(self, *, max_cycles: int) -> Dict[str, Any]:
        if type(max_cycles) is not int or max_cycles <= 0:
            raise ValueError("max_cycles must be a positive exact integer")
        ordering = ["watchdog_ready"]
        if not self._watchdog_ready:
            raise RuntimeStateError("watchdog is not ready")
        if not self.wake_endpoint.registered:
            self.wake_endpoint.register()
        self.wake_endpoint.verify_registered()
        ordering.append("wake_registered")
        ordering.append("startup_drain")
        processed = 0
        failures = 0
        for _ in range(max_cycles):
            outcome = self._claim_and_run_once()
            if outcome == "completed":
                processed += 1
                continue
            if outcome == "worker_failure":
                failures += 1
                break
            break
        status = self.outbox.status()
        pending, claimed = self._counts(status)
        return {
            "ordering": ordering,
            "processed": processed,
            "worker_failures": failures,
            "pending": pending,
            "claimed": claimed,
            "quiescent": pending == 0 and claimed == 0,
            "next_wake_deadline": self._earliest_claim_deadline(status),
            "runtime_identity": self.runtime_state.snapshot(),
            "last_timer_token": self._last_timer_token,
        }


__all__ = [
    "BrokerProtocolError",
    "BrokerRuntimeState",
    "DeterministicConsumerBroker",
    "MAX_WORK_EPOCH",
    "RuntimeStateError",
    "StrictFrameCodec",
    "UnixWakeEndpoint",
]
