from __future__ import annotations

import socket
import threading

import pytest

from loop_a_protected.canonical import with_self_digest
from loop_a_protected.darwin_session import (
    DarwinSessionError,
    build_worker_result,
    receive_launch_receipt,
    receive_worker_result,
    send_launch_receipt,
    send_worker_result,
)


TX = "12345678-1234-5678-9234-567812345678"
NONCE = "a" * 64
SOURCE = "b" * 64
MANIFEST = "c" * 64
INVENTORY = "d" * 64
CANDIDATE = b"candidate"


def test_launch_receipt_and_result_form_one_exact_half_closed_session():
    broker, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    errors = []

    def worker_main():
        try:
            send_launch_receipt(
                worker, transaction_uuid=TX, nonce=NONCE,
                launcher_pid=111, child_pid=222,
            )
            record = build_worker_result(
                nonce=NONCE, child_pid=222, transaction_uuid=TX,
                source_digest=SOURCE, runtime_manifest_digest=MANIFEST,
                runtime_inventory_digest=INVENTORY, candidate_bytes=CANDIDATE,
            )
            send_worker_result(worker, record=record, candidate_bytes=CANDIDATE)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=worker_main)
    thread.start()
    try:
        receipt = receive_launch_receipt(
            broker, expected_transaction_uuid=TX, expected_nonce=NONCE,
            expected_launcher_pid=111, timeout_seconds=2.0,
        )
        record, candidate = receive_worker_result(broker, timeout_seconds=2.0)
        assert receipt.child_pid == 222
        assert record["child_pid"] == receipt.child_pid
        assert record["nonce"] == NONCE
        assert candidate == CANDIDATE
        thread.join(timeout=2.0)
        assert not thread.is_alive()
        assert errors == []
    finally:
        broker.close()
        worker.close()


@pytest.mark.parametrize("field,value,message", [
    ("nonce", "e" * 64, "session binding"),
    ("launcher_pid", 112, "session binding"),
    ("transaction_uuid", "12345678-1234-5678-9234-567812345679", "session binding"),
    ("child_pid", 0, "receipt PID"),
])
def test_launch_receipt_wrong_binding_fails_closed(field, value, message):
    broker, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        kwargs = dict(transaction_uuid=TX, nonce=NONCE, launcher_pid=111, child_pid=222)
        kwargs[field] = value
        if field == "child_pid":
            with pytest.raises(DarwinSessionError, match=message):
                send_launch_receipt(worker, **kwargs)
        else:
            send_launch_receipt(worker, **kwargs)
            with pytest.raises(DarwinSessionError, match=message):
                receive_launch_receipt(
                    broker, expected_transaction_uuid=TX, expected_nonce=NONCE,
                    expected_launcher_pid=111, timeout_seconds=1.0,
                )
    finally:
        broker.close()
        worker.close()


def test_result_trailing_data_and_missing_half_close_fail_closed():
    broker, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    record = build_worker_result(
        nonce=NONCE, child_pid=222, transaction_uuid=TX,
        source_digest=SOURCE, runtime_manifest_digest=MANIFEST,
        runtime_inventory_digest=INVENTORY, candidate_bytes=CANDIDATE,
    )
    try:
        send_worker_result(worker, record=record, candidate_bytes=CANDIDATE + b"x")
        with pytest.raises(DarwinSessionError, match="trailing"):
            receive_worker_result(broker, timeout_seconds=1.0)
    finally:
        broker.close()
        worker.close()

    broker, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        # Keep the write direction open after an otherwise complete result.
        from loop_a_protected.canonical import canonical_bytes
        import struct
        payload = canonical_bytes(record)
        worker.sendall(struct.pack(">I", len(payload)) + payload + CANDIDATE)
        with pytest.raises(DarwinSessionError, match="deadline"):
            receive_worker_result(broker, timeout_seconds=0.02)
    finally:
        broker.close()
        worker.close()


def test_worker_result_builder_rejects_extra_authority_fields_by_construction():
    record = build_worker_result(
        nonce=NONCE, child_pid=222, transaction_uuid=TX,
        source_digest=SOURCE, runtime_manifest_digest=MANIFEST,
        runtime_inventory_digest=INVENTORY, candidate_bytes=CANDIDATE,
    )
    assert not ({"path", "operation", "destination", "authorization"} & set(record))
    mutated = dict(record, path="/attacker")
    mutated["result_digest"] = None
    mutated = with_self_digest(mutated, "result_digest")
    assert "path" in mutated
