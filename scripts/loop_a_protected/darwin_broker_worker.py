from __future__ import annotations

import os
import secrets
import socket
import time
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Mapping, Protocol, Tuple

from .broker_coordinator import CommittedCandidate, FixedCandidateTransaction, LiveGate, TransactionBinding, accept_worker_candidate
from .canonical import canonical_bytes, with_self_digest
from .darwin_launchd_transport import ReceivedFdBundle, receive_fd_bundle, send_fd_bundle
from .darwin_peer import validate_launchd_worker_peer, validate_root_broker_peer
from .darwin_session import (
    DarwinSessionError,
    build_worker_result,
    receive_launch_receipt,
    receive_worker_result,
    send_launch_receipt,
    send_worker_result,
)


class DarwinBrokerWorkerError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkerExecution:
    child_pid: int
    handshake_ack: Dict[str, Any]
    source_digest: str
    runtime_manifest_digest: str
    runtime_inventory_digest: str
    candidate_bytes: bytes


class WorkerExecutor(Protocol):
    def execute(self, bundle: ReceivedFdBundle) -> WorkerExecution: ...


def _validate_handshake_ack(value: Dict[str, Any], *, nonce: str, child_pid: int) -> None:
    expected = with_self_digest({
        "schema": 1,
        "nonce": nonce,
        "child_pid": child_pid,
        "capability": "attestation-only",
        "ack_digest": None,
    }, "ack_digest")
    if not isinstance(value, dict) or canonical_bytes(value) != canonical_bytes(expected):
        raise DarwinBrokerWorkerError("inner worker handshake acknowledgement differs")


def run_root_broker_session(*, sock: socket.socket, launchd_worker_pid: int,
                            worker_uid: int, worker_gid: int,
                            descriptors: Mapping[str, int], binding: TransactionBinding,
                            expected_descriptor_identities: Mapping[str, Tuple[int, int]],
                            mutation_root_identities: FrozenSet[Tuple[int, int]],
                            gate: LiveGate, transaction: FixedCandidateTransaction,
                            timeout_seconds: float = 10.0) -> CommittedCandidate:
    effective_broker_uid = os.geteuid()
    nonce = secrets.token_hex(32)
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 0 < timeout_seconds <= 30):
        raise DarwinBrokerWorkerError("root broker session timeout is outside the fixed bound")
    deadline = time.monotonic() + float(timeout_seconds)
    try:
        validate_launchd_worker_peer(
            sock,
            broker_euid=effective_broker_uid,
            expected_pid=launchd_worker_pid,
            expected_uid=worker_uid,
            expected_gid=worker_gid,
        )
        send_fd_bundle(
            sock,
            transaction_uuid=binding.transaction_uuid,
            broker_pid=os.getpid(),
            nonce=nonce,
            descriptors=descriptors,
            expected_identities=expected_descriptor_identities,
            mutation_root_identities=mutation_root_identities,
        )
        sock.shutdown(socket.SHUT_WR)
        receipt = receive_launch_receipt(
            sock,
            expected_transaction_uuid=binding.transaction_uuid,
            expected_nonce=nonce,
            expected_launcher_pid=launchd_worker_pid,
            timeout_seconds=max(deadline - time.monotonic(), 1e-9),
        )
        record, candidate = receive_worker_result(
            sock, timeout_seconds=max(deadline - time.monotonic(), 1e-9)
        )
        if record.get("child_pid") != receipt.child_pid:
            raise DarwinBrokerWorkerError("worker result PID differs from launch receipt")
        return accept_worker_candidate(
            gate=gate,
            transaction=transaction,
            record=record,
            candidate_bytes=candidate,
            expected_nonce=nonce,
            expected_child_pid=receipt.child_pid,
            expected_binding=binding,
        )
    except (OSError, DarwinSessionError) as exc:
        if isinstance(exc, DarwinBrokerWorkerError):
            raise
        raise DarwinBrokerWorkerError("root broker session failed closed") from exc
    finally:
        sock.close()


def run_launchd_worker_session(*, sock: socket.socket, executor: WorkerExecutor,
                               timeout_seconds: float = 10.0) -> WorkerExecution:
    bundle = None
    try:
        peer = validate_root_broker_peer(sock)
        bundle = receive_fd_bundle(sock)
        if bundle.broker_pid != peer.pid or bundle.broker_pid != peer.effective_pid:
            raise DarwinBrokerWorkerError("bundle broker PID differs from kernel peer")
        if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not 0 < timeout_seconds <= 30):
            raise DarwinBrokerWorkerError("worker session timeout is outside the fixed bound")
        sock.settimeout(float(timeout_seconds))
        if sock.recv(1):
            raise DarwinBrokerWorkerError("broker sent trailing bundle data")
        outcome = executor.execute(bundle)
        if not isinstance(outcome, WorkerExecution):
            raise DarwinBrokerWorkerError("worker executor returned an invalid outcome")
        if isinstance(outcome.child_pid, bool) or not isinstance(outcome.child_pid, int) or outcome.child_pid <= 0:
            raise DarwinBrokerWorkerError("worker executor child PID is invalid")
        _validate_handshake_ack(outcome.handshake_ack, nonce=bundle.nonce, child_pid=outcome.child_pid)
        record = build_worker_result(
            nonce=bundle.nonce,
            child_pid=outcome.child_pid,
            transaction_uuid=bundle.transaction_uuid,
            source_digest=outcome.source_digest,
            runtime_manifest_digest=outcome.runtime_manifest_digest,
            runtime_inventory_digest=outcome.runtime_inventory_digest,
            candidate_bytes=outcome.candidate_bytes,
        )
        send_launch_receipt(
            sock,
            transaction_uuid=bundle.transaction_uuid,
            nonce=bundle.nonce,
            launcher_pid=os.getpid(),
            child_pid=outcome.child_pid,
        )
        send_worker_result(sock, record=record, candidate_bytes=outcome.candidate_bytes)
        return outcome
    except (OSError, DarwinSessionError) as exc:
        if isinstance(exc, DarwinBrokerWorkerError):
            raise
        raise DarwinBrokerWorkerError("launchd worker session failed closed") from exc
    finally:
        if bundle is not None:
            bundle.close()
        sock.close()


def serve_launchd_worker_once(*, listener: socket.socket, executor: WorkerExecutor,
                              timeout_seconds: float = 10.0) -> WorkerExecution:
    if (not isinstance(listener, socket.socket) or listener.family != socket.AF_UNIX
            or (listener.type & 0xF) != socket.SOCK_STREAM
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1):
        raise DarwinBrokerWorkerError("launchd worker listener is invalid")
    connection = None
    try:
        listener.settimeout(float(timeout_seconds))
        connection, _ = listener.accept()
        os.set_inheritable(connection.fileno(), False)
        return run_launchd_worker_session(sock=connection, executor=executor, timeout_seconds=timeout_seconds)
    except OSError as exc:
        raise DarwinBrokerWorkerError("launchd worker accept failed closed") from exc
    finally:
        if connection is not None:
            connection.close()
        listener.close()
