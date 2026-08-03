from __future__ import annotations

import hashlib
import uuid

import pytest

from loop_a_protected.canonical import with_self_digest


NONCE = "a" * 64
SOURCE = "b" * 64
RUNTIME_MANIFEST = "c" * 64
RUNTIME_INVENTORY = "d" * 64
TX = str(uuid.UUID("12345678-1234-5678-9234-567812345678"))
CANDIDATE = b"candidate-bytes"


def _record():
    return with_self_digest({
        "schema": 1,
        "nonce": NONCE,
        "child_pid": 1234,
        "transaction_uuid": TX,
        "source_digest": SOURCE,
        "runtime_manifest_digest": RUNTIME_MANIFEST,
        "runtime_inventory_digest": RUNTIME_INVENTORY,
        "candidate_sha256": hashlib.sha256(CANDIDATE).hexdigest(),
        "candidate_byte_count": len(CANDIDATE),
        "result_digest": None,
    }, "result_digest")


def _validate(record, candidate=CANDIDATE):
    from loop_a_protected.broker_result import validate_worker_result

    return validate_worker_result(
        record=record, candidate_bytes=candidate, expected_nonce=NONCE,
        expected_child_pid=1234, expected_transaction_uuid=TX,
        expected_source_digest=SOURCE,
        expected_runtime_manifest_digest=RUNTIME_MANIFEST,
        expected_runtime_inventory_digest=RUNTIME_INVENTORY,
    )


def test_exact_worker_result_is_bound_to_candidate_and_transaction():
    assert _validate(_record())["candidate_byte_count"] == len(CANDIDATE)


@pytest.mark.parametrize("forbidden", ["path", "operation", "destination", "authorization", "state"])
def test_worker_cannot_supply_a_mutation_request_field_even_with_recomputed_digest(forbidden):
    from loop_a_protected.broker_result import BrokerResultError

    value = _record()
    value[forbidden] = "attacker-choice"
    value["result_digest"] = None
    value = with_self_digest(value, "result_digest")
    with pytest.raises(BrokerResultError, match="fields are not exact"):
        _validate(value)


@pytest.mark.parametrize("field,value,message", [
    ("nonce", "c" * 64, "nonce"),
    ("child_pid", 1235, "PID"),
    ("transaction_uuid", str(uuid.uuid4()), "transaction"),
    ("source_digest", "e" * 64, "source"),
    ("runtime_manifest_digest", "e" * 64, "runtime manifest"),
    ("runtime_inventory_digest", "e" * 64, "runtime inventory"),
    ("candidate_byte_count", len(CANDIDATE) + 1, "byte count"),
    ("candidate_sha256", "e" * 64, "candidate digest"),
])
def test_one_field_substitution_with_valid_self_digest_fails_at_semantic_binding(field, value, message):
    from loop_a_protected.broker_result import BrokerResultError

    record = _record()
    record[field] = value
    record["result_digest"] = None
    record = with_self_digest(record, "result_digest")
    with pytest.raises(BrokerResultError, match=message):
        _validate(record)


def test_candidate_bytes_and_result_self_digest_are_independently_checked():
    from loop_a_protected.broker_result import BrokerResultError

    with pytest.raises(BrokerResultError, match="candidate digest"):
        _validate(_record(), b"x" * len(CANDIDATE))
    record = _record()
    record["result_digest"] = "f" * 64
    with pytest.raises(BrokerResultError, match="self-digest"):
        _validate(record)


@pytest.mark.parametrize("candidate", [b"", b"x" * (8_388_608 + 1)])
def test_candidate_size_bound_fails_closed(candidate):
    from loop_a_protected.broker_result import BrokerResultError

    with pytest.raises(BrokerResultError, match="outside"):
        _validate(_record(), candidate)
