from __future__ import annotations

import os
import struct
import threading

import pytest

from loop_a_protected.canonical import canonical_bytes


RECORD = {
    "schema": 1,
    "nonce": "a" * 64,
    "child_pid": 1234,
    "transaction_uuid": "12345678-1234-5678-9234-567812345678",
    "source_digest": "b" * 64,
    "runtime_manifest_digest": "c" * 64,
    "runtime_inventory_digest": "d" * 64,
    "candidate_sha256": "e" * 64,
    "candidate_byte_count": 9,
    "result_digest": "f" * 64,
}
CANDIDATE = b"candidate"


def _frame(metadata=canonical_bytes(RECORD), candidate=CANDIDATE, trailing=b""):
    return struct.pack(">I", len(metadata)) + metadata + candidate + trailing


def _read(payload: bytes, *, keep_open: bool = False, timeout_seconds: float = 0.5):
    from loop_a_protected.broker_transport import read_worker_frame

    read_fd, write_fd = os.pipe()

    def writer():
        try:
            if payload:
                os.write(write_fd, payload)
        finally:
            if not keep_open:
                os.close(write_fd)

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    try:
        return read_worker_frame(read_fd, timeout_seconds=timeout_seconds)
    finally:
        os.close(read_fd)
        if keep_open:
            os.close(write_fd)
        thread.join(timeout=1.0)


def test_exact_bounded_frame_returns_canonical_metadata_and_candidate_bytes():
    record, candidate = _read(_frame())
    assert record == RECORD
    assert candidate == CANDIDATE


@pytest.mark.parametrize("payload,message", [
    (b"", "header"),
    (b"\x00\x00", "header"),
    (struct.pack(">I", 65_537), "metadata length"),
    (struct.pack(">I", 10) + b"{}\n", "metadata"),
    (_frame(metadata=b'{"schema":1}'), "canonical"),
    (_frame(candidate=CANDIDATE[:-1]), "candidate"),
    (_frame(trailing=b"x"), "trailing"),
])
def test_malformed_truncated_oversized_or_extra_output_fails_closed(payload, message):
    from loop_a_protected.broker_transport import BrokerTransportError

    with pytest.raises(BrokerTransportError, match=message):
        _read(payload)


def test_open_silent_writer_hits_one_end_to_end_deadline():
    from loop_a_protected.broker_transport import BrokerTransportError

    with pytest.raises(BrokerTransportError, match="deadline"):
        _read(b"", keep_open=True, timeout_seconds=0.02)


def test_non_pipe_input_is_rejected_before_read(tmp_path):
    from loop_a_protected.broker_transport import BrokerTransportError, read_worker_frame

    path = tmp_path / "not-a-pipe"
    path.write_bytes(_frame())
    fd = os.open(path, os.O_RDONLY)
    try:
        with pytest.raises(BrokerTransportError, match="pipe"):
            read_worker_frame(fd, timeout_seconds=0.5)
    finally:
        os.close(fd)
