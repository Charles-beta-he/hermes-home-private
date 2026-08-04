from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from loop_a_protected.canonical import with_self_digest


TX = "12345678-1234-5678-9234-567812345678"
NONCE = "a" * 64
SOURCE = "b" * 64
MANIFEST = "c" * 64
INVENTORY = "d" * 64
CANDIDATE = b"candidate-bytes"


def _result(**updates):
    value = {
        "schema": 1,
        "nonce": NONCE,
        "child_pid": 1234,
        "transaction_uuid": TX,
        "source_digest": SOURCE,
        "runtime_manifest_digest": MANIFEST,
        "runtime_inventory_digest": INVENTORY,
        "candidate_sha256": hashlib.sha256(CANDIDATE).hexdigest(),
        "candidate_byte_count": len(CANDIDATE),
        "result_digest": None,
    }
    value.update(updates)
    return with_self_digest(value, "result_digest")


class Gate:
    def __init__(self, events, fail_at=None):
        self.events = events
        self.fail_at = fail_at
        self.calls = 0

    def assert_live(self):
        self.calls += 1
        self.events.append("gate")
        if self.fail_at == self.calls:
            raise RuntimeError("root gate failed")


class Transaction:
    def __init__(self, events, binding, second_binding=None):
        self.events = events
        self.binding = binding
        self.second_binding = binding if second_binding is None else second_binding
        self.snapshots = 0
        self.commits = []

    def snapshot(self):
        self.events.append("snapshot")
        self.snapshots += 1
        return self.binding if self.snapshots == 1 else self.second_binding

    def commit_candidate(self, candidate_bytes, candidate_sha256, gate):
        gate.assert_live()
        self.events.append("commit")
        self.commits.append((candidate_bytes, candidate_sha256))
        from loop_a_protected.broker_coordinator import CommittedCandidate
        return CommittedCandidate(len(candidate_bytes), candidate_sha256)


def _binding():
    from loop_a_protected.broker_coordinator import TransactionBinding

    return TransactionBinding(
        transaction_uuid=TX,
        state="CANDIDATE_STAGED",
        source_digest=SOURCE,
        runtime_manifest_digest=MANIFEST,
        runtime_inventory_digest=INVENTORY,
        skill_name="demo-skill",
    )


def _accept(transaction, gate, record=None, candidate=CANDIDATE):
    from loop_a_protected.broker_coordinator import accept_worker_candidate

    return accept_worker_candidate(
        gate=gate,
        transaction=transaction,
        record=_result() if record is None else record,
        candidate_bytes=candidate,
        expected_nonce=NONCE,
        expected_child_pid=1234,
        expected_binding=_binding(),
    )


def test_broker_revalidates_gate_and_transaction_before_fixed_commit():
    events = []
    transaction = Transaction(events, _binding())
    accepted = _accept(transaction, Gate(events))
    assert accepted.candidate_sha256 == hashlib.sha256(CANDIDATE).hexdigest()
    assert transaction.commits == [(CANDIDATE, accepted.candidate_sha256)]
    assert events == ["gate", "snapshot", "gate", "snapshot", "gate", "gate", "commit"]


def test_no_post_commit_gate_can_turn_durable_success_into_reported_failure():
    events = []
    transaction = Transaction(events, _binding())
    gate = Gate(events, fail_at=5)
    accepted = _accept(transaction, gate)
    assert accepted.candidate_sha256 == hashlib.sha256(CANDIDATE).hexdigest()
    assert gate.calls == 4
    assert transaction.commits == [(CANDIDATE, accepted.candidate_sha256)]


def test_invalid_worker_result_has_zero_commit_calls():
    from loop_a_protected.broker_coordinator import BrokerCoordinatorError

    events = []
    transaction = Transaction(events, _binding())
    with pytest.raises(BrokerCoordinatorError, match="worker result"):
        _accept(transaction, Gate(events), _result(path="attacker"))
    assert transaction.commits == []
    assert "commit" not in events


@pytest.mark.parametrize("field,value", [
    ("state", "SOURCE_CAPTURED"),
    ("transaction_uuid", "12345678-1234-5678-9234-567812345679"),
    ("source_digest", "e" * 64),
    ("runtime_manifest_digest", "e" * 64),
    ("runtime_inventory_digest", "e" * 64),
])
def test_wrong_precommit_transaction_binding_has_zero_commit_calls(field, value):
    from loop_a_protected.broker_coordinator import BrokerCoordinatorError

    events = []
    transaction = Transaction(events, replace(_binding(), **{field: value}))
    with pytest.raises(BrokerCoordinatorError, match="transaction binding"):
        _accept(transaction, Gate(events))
    assert transaction.commits == []


def test_transaction_drift_after_validation_has_zero_commit_calls():
    from loop_a_protected.broker_coordinator import BrokerCoordinatorError

    events = []
    transaction = Transaction(events, _binding(), replace(_binding(), state="ABORTED"))
    with pytest.raises(BrokerCoordinatorError, match="changed"):
        _accept(transaction, Gate(events))
    assert transaction.commits == []


def test_commit_readback_mismatch_fails_closed():
    from loop_a_protected.broker_coordinator import BrokerCoordinatorError, CommittedCandidate

    events = []
    transaction = Transaction(events, _binding())
    transaction.commit_candidate = lambda candidate_bytes, candidate_sha256, gate: CommittedCandidate(
        len(candidate_bytes), "f" * 64,
    )
    with pytest.raises(BrokerCoordinatorError, match="readback"):
        _accept(transaction, Gate(events))
