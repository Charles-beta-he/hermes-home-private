from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol

from .broker_result import BrokerResultError, validate_worker_result


class BrokerCoordinatorError(RuntimeError):
    pass


@dataclass(frozen=True)
class TransactionBinding:
    transaction_uuid: str
    state: str
    source_digest: str
    runtime_manifest_digest: str
    runtime_inventory_digest: str
    skill_name: str


@dataclass(frozen=True)
class CommittedCandidate:
    byte_count: int
    candidate_sha256: str


class LiveGate(Protocol):
    def assert_live(self) -> None: ...


class FixedCandidateTransaction(Protocol):
    def snapshot(self) -> TransactionBinding: ...
    def commit_candidate(self, candidate_bytes: bytes, candidate_sha256: str,
                         gate: LiveGate) -> CommittedCandidate: ...


def _require_staged_binding(observed: Any, expected: TransactionBinding) -> None:
    if (not isinstance(observed, TransactionBinding)
            or observed != expected
            or observed.state != "CANDIDATE_STAGED"):
        raise BrokerCoordinatorError("broker transaction binding is not the exact staged transaction")


def accept_worker_candidate(*, gate: LiveGate, transaction: FixedCandidateTransaction,
                            record: Dict[str, Any], candidate_bytes: bytes,
                            expected_nonce: str, expected_child_pid: int,
                            expected_binding: TransactionBinding) -> CommittedCandidate:
    gate.assert_live()
    first = transaction.snapshot()
    _require_staged_binding(first, expected_binding)
    try:
        validated = validate_worker_result(
            record=record,
            candidate_bytes=candidate_bytes,
            expected_nonce=expected_nonce,
            expected_child_pid=expected_child_pid,
            expected_transaction_uuid=expected_binding.transaction_uuid,
            expected_source_digest=expected_binding.source_digest,
            expected_runtime_manifest_digest=expected_binding.runtime_manifest_digest,
            expected_runtime_inventory_digest=expected_binding.runtime_inventory_digest,
        )
    except BrokerResultError as exc:
        raise BrokerCoordinatorError("worker result validation failed") from exc
    gate.assert_live()
    second = transaction.snapshot()
    if second != first:
        raise BrokerCoordinatorError("broker transaction binding changed before commit")
    _require_staged_binding(second, expected_binding)
    gate.assert_live()
    committed = transaction.commit_candidate(candidate_bytes, validated["candidate_sha256"], gate)
    if (not isinstance(committed, CommittedCandidate)
            or committed.byte_count != len(candidate_bytes)
            or committed.candidate_sha256 != validated["candidate_sha256"]):
        raise BrokerCoordinatorError("broker commit readback differs from validated candidate")
    return committed
