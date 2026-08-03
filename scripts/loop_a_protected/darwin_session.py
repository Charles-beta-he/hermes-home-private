from __future__ import annotations

import hashlib
import re
import select
import socket
import struct
import time
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest
from .schema_bundle import SchemaBundleError, validate_instance
from .validation import ProtocolValidationError, validate_uuid


class DarwinSessionError(RuntimeError):
    pass


_MAX_METADATA = 65_536
_MAX_CANDIDATE = 8_388_608
_DIGEST = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class LaunchReceipt:
    transaction_uuid: str
    nonce: str
    launcher_pid: int
    child_pid: int
    record: Dict[str, Any]


def _deadline(timeout_seconds: float) -> float:
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 0 < timeout_seconds <= 30):
        raise DarwinSessionError("session timeout is outside the fixed bound")
    return time.monotonic() + float(timeout_seconds)


def _read_ready(sock: socket.socket, count: int, deadline: float) -> bytes:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DarwinSessionError("worker session deadline expired")
    try:
        ready, _, _ = select.select([sock], [], [], remaining)
        if not ready:
            raise DarwinSessionError("worker session deadline expired")
        return sock.recv(count)
    except OSError as exc:
        raise DarwinSessionError("worker session read failed") from exc


def _read_exact(sock: socket.socket, count: int, deadline: float) -> bytes:
    result = bytearray()
    while len(result) < count:
        chunk = _read_ready(sock, count - len(result), deadline)
        if not chunk:
            raise DarwinSessionError("worker session frame is truncated")
        result.extend(chunk)
    return bytes(result)


def _read_record(sock: socket.socket, deadline: float) -> Dict[str, Any]:
    length = struct.unpack(">I", _read_exact(sock, 4, deadline))[0]
    if not 1 <= length <= _MAX_METADATA:
        raise DarwinSessionError("worker session metadata length is outside the fixed bound")
    try:
        value = parse_canonical_bytes(_read_exact(sock, length, deadline))
    except CanonicalJSONError as exc:
        raise DarwinSessionError("worker session metadata is not canonical JSON") from exc
    if not isinstance(value, dict):
        raise DarwinSessionError("worker session metadata is not an object")
    return value


def _send_record(sock: socket.socket, value: Dict[str, Any]) -> None:
    if not isinstance(sock, socket.socket) or sock.family != socket.AF_UNIX or (sock.type & 0xF) != socket.SOCK_STREAM:
        raise DarwinSessionError("worker session channel is not AF_UNIX stream")
    payload = canonical_bytes(value)
    if not 1 <= len(payload) <= _MAX_METADATA:
        raise DarwinSessionError("worker session metadata length is outside the fixed bound")
    try:
        sock.sendall(struct.pack(">I", len(payload)) + payload)
    except OSError as exc:
        raise DarwinSessionError("worker session send failed") from exc


def build_launch_receipt(*, transaction_uuid: str, nonce: str,
                         launcher_pid: int, child_pid: int) -> Dict[str, Any]:
    try:
        validate_uuid(transaction_uuid)
    except ProtocolValidationError as exc:
        raise DarwinSessionError("launch receipt transaction UUID is invalid") from exc
    if not isinstance(nonce, str) or _DIGEST.fullmatch(nonce) is None:
        raise DarwinSessionError("launch receipt nonce is invalid")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
           for value in (launcher_pid, child_pid)):
        raise DarwinSessionError("launch receipt PID is invalid")
    finalized = with_self_digest({
        "schema": 1,
        "kind": "launch-receipt",
        "transaction_uuid": transaction_uuid,
        "nonce": nonce,
        "launcher_pid": launcher_pid,
        "child_pid": child_pid,
        "capability": "attestation-only",
        "record_digest": None,
    }, "record_digest")
    try:
        validate_instance("launch-receipt-final-v1", finalized)
    except SchemaBundleError as exc:
        raise DarwinSessionError("launch receipt schema is invalid") from exc
    return finalized


def send_launch_receipt(sock: socket.socket, *, transaction_uuid: str, nonce: str,
                        launcher_pid: int, child_pid: int) -> Dict[str, Any]:
    value = build_launch_receipt(
        transaction_uuid=transaction_uuid, nonce=nonce,
        launcher_pid=launcher_pid, child_pid=child_pid,
    )
    _send_record(sock, value)
    return value


def receive_launch_receipt(sock: socket.socket, *, expected_transaction_uuid: str,
                           expected_nonce: str, expected_launcher_pid: int,
                           timeout_seconds: float) -> LaunchReceipt:
    deadline = _deadline(timeout_seconds)
    value = _read_record(sock, deadline)
    child_pid = value.get("child_pid")
    if isinstance(child_pid, bool) or not isinstance(child_pid, int):
        raise DarwinSessionError("launch receipt child PID is invalid")
    expected = build_launch_receipt(
        transaction_uuid=expected_transaction_uuid,
        nonce=expected_nonce,
        launcher_pid=expected_launcher_pid,
        child_pid=child_pid,
    )
    if canonical_bytes(value) != canonical_bytes(expected):
        raise DarwinSessionError("launch receipt differs from exact session binding")
    return LaunchReceipt(expected_transaction_uuid, expected_nonce, expected_launcher_pid, child_pid, expected)


def build_worker_result(*, nonce: str, child_pid: int, transaction_uuid: str,
                        source_digest: str, runtime_manifest_digest: str,
                        runtime_inventory_digest: str, candidate_bytes: bytes) -> Dict[str, Any]:
    if not isinstance(candidate_bytes, bytes) or not 1 <= len(candidate_bytes) <= _MAX_CANDIDATE:
        raise DarwinSessionError("worker candidate byte count is outside the fixed bound")
    for value, label in ((nonce, "nonce"), (source_digest, "source digest"),
                         (runtime_manifest_digest, "runtime manifest digest"),
                         (runtime_inventory_digest, "runtime inventory digest")):
        if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
            raise DarwinSessionError(f"worker {label} is invalid")
    try:
        validate_uuid(transaction_uuid)
    except ProtocolValidationError as exc:
        raise DarwinSessionError("worker result transaction UUID is invalid") from exc
    if isinstance(child_pid, bool) or not isinstance(child_pid, int) or child_pid <= 0:
        raise DarwinSessionError("worker result child PID is invalid")
    finalized = with_self_digest({
        "schema": 1,
        "nonce": nonce,
        "child_pid": child_pid,
        "transaction_uuid": transaction_uuid,
        "source_digest": source_digest,
        "runtime_manifest_digest": runtime_manifest_digest,
        "runtime_inventory_digest": runtime_inventory_digest,
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "candidate_byte_count": len(candidate_bytes),
        "result_digest": None,
    }, "result_digest")
    try:
        validate_instance("broker-result-final-v1", finalized)
    except SchemaBundleError as exc:
        raise DarwinSessionError("worker result schema is invalid") from exc
    return finalized


def send_worker_result(sock: socket.socket, *, record: Dict[str, Any], candidate_bytes: bytes) -> None:
    payload = canonical_bytes(record)
    if not 1 <= len(payload) <= _MAX_METADATA:
        raise DarwinSessionError("worker result metadata length is outside the fixed bound")
    if not isinstance(candidate_bytes, bytes) or not 1 <= len(candidate_bytes) <= _MAX_CANDIDATE:
        raise DarwinSessionError("worker candidate byte count is outside the fixed bound")
    try:
        sock.sendall(struct.pack(">I", len(payload)) + payload + candidate_bytes)
        sock.shutdown(socket.SHUT_WR)
    except OSError as exc:
        raise DarwinSessionError("worker result send failed") from exc


def receive_worker_result(sock: socket.socket, *, timeout_seconds: float) -> Tuple[Dict[str, Any], bytes]:
    deadline = _deadline(timeout_seconds)
    record = _read_record(sock, deadline)
    try:
        validate_instance("broker-result-final-v1", record)
    except SchemaBundleError as exc:
        raise DarwinSessionError("worker result schema is invalid") from exc
    count = record.get("candidate_byte_count")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= _MAX_CANDIDATE:
        raise DarwinSessionError("worker candidate length is outside the fixed bound")
    candidate = _read_exact(sock, count, deadline)
    if _read_ready(sock, 1, deadline):
        raise DarwinSessionError("worker session has trailing data")
    return record, candidate
