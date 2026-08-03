from __future__ import annotations

import os
import select
import stat
import struct
import time
from typing import Any, Dict, Tuple

from .canonical import CanonicalJSONError, parse_canonical_bytes


class BrokerTransportError(ValueError):
    pass


_HEADER_BYTES = 4
_MAXIMUM_METADATA_BYTES = 65_536
_MAXIMUM_CANDIDATE_BYTES = 8_388_608


def _read_ready(fd: int, count: int, deadline: float, label: str) -> bytes:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise BrokerTransportError("worker output deadline expired")
    try:
        ready, _, _ = select.select([fd], [], [], remaining)
    except OSError as exc:
        raise BrokerTransportError(f"cannot wait for worker {label}") from exc
    if not ready:
        raise BrokerTransportError("worker output deadline expired")
    try:
        return os.read(fd, count)
    except OSError as exc:
        raise BrokerTransportError(f"cannot read worker {label}") from exc


def _read_exact(fd: int, count: int, deadline: float, label: str) -> bytes:
    chunks = []
    remaining = count
    while remaining:
        chunk = _read_ready(fd, remaining, deadline, label)
        if not chunk:
            raise BrokerTransportError(f"worker {label} is truncated")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_worker_frame(fd: int, *, timeout_seconds: float,
                      maximum_metadata_bytes: int = _MAXIMUM_METADATA_BYTES,
                      maximum_candidate_bytes: int = _MAXIMUM_CANDIDATE_BYTES) -> Tuple[Dict[str, Any], bytes]:
    if (isinstance(fd, bool) or not isinstance(fd, int) or fd < 0
            or not stat.S_ISFIFO(os.fstat(fd).st_mode)):
        raise BrokerTransportError("worker output descriptor is not a pipe")
    if (not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0):
        raise BrokerTransportError("worker output deadline is invalid")
    if not 1 <= maximum_metadata_bytes <= _MAXIMUM_METADATA_BYTES:
        raise BrokerTransportError("worker metadata bound is invalid")
    if not 1 <= maximum_candidate_bytes <= _MAXIMUM_CANDIDATE_BYTES:
        raise BrokerTransportError("worker candidate bound is invalid")

    deadline = time.monotonic() + float(timeout_seconds)
    header = _read_exact(fd, _HEADER_BYTES, deadline, "header")
    metadata_length = struct.unpack(">I", header)[0]
    if not 1 <= metadata_length <= maximum_metadata_bytes:
        raise BrokerTransportError("worker metadata length is outside the fixed bound")
    metadata = _read_exact(fd, metadata_length, deadline, "metadata")
    try:
        record = parse_canonical_bytes(metadata)
    except CanonicalJSONError as exc:
        raise BrokerTransportError("worker metadata is not canonical JSON") from exc
    if not isinstance(record, dict):
        raise BrokerTransportError("worker metadata is not an object")
    candidate_length = record.get("candidate_byte_count")
    if (isinstance(candidate_length, bool) or not isinstance(candidate_length, int)
            or not 1 <= candidate_length <= maximum_candidate_bytes):
        raise BrokerTransportError("worker candidate length is outside the fixed bound")
    candidate = _read_exact(fd, candidate_length, deadline, "candidate")
    trailing = _read_ready(fd, 1, deadline, "trailing data")
    if trailing:
        raise BrokerTransportError("worker output has trailing data")
    return record, candidate
