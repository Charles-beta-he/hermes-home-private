from __future__ import annotations

import hashlib
import os
import socket
import threading

import pytest

from loop_a_protected.broker_coordinator import CommittedCandidate, TransactionBinding
from loop_a_protected.candidate_payload import canonical_candidate_payload
from loop_a_protected.canonical import with_self_digest
from loop_a_protected.darwin_launchd_transport import PROTECTED_ROLES


TX = "12345678-1234-5678-9234-567812345678"
SOURCE = "b" * 64
MANIFEST = "c" * 64
INVENTORY = "d" * 64
CANDIDATE = b"candidate"


class Gate:
    def __init__(self):
        self.calls = 0

    def assert_live(self):
        self.calls += 1


class Transaction:
    def __init__(self, binding):
        self.binding = binding
        self.commits = []

    def snapshot(self):
        return self.binding

    def commit_candidate(self, candidate_bytes, candidate_sha256, gate):
        gate.assert_live()
        self.commits.append((candidate_bytes, candidate_sha256))
        return CommittedCandidate(len(candidate_bytes), candidate_sha256)


class Executor:
    def __init__(self, *, source_digest=SOURCE, bad_ack=False):
        self.source_digest = source_digest
        self.bad_ack = bad_ack
        self.seen = None

    def execute(self, bundle):
        from loop_a_protected.darwin_broker_worker import WorkerExecution

        self.seen = bundle
        ack = with_self_digest({
            "schema": 1,
            "nonce": bundle.nonce,
            "child_pid": 444,
            "capability": "attestation-only" if not self.bad_ack else "mutation",
            "ack_digest": None,
        }, "ack_digest")
        return WorkerExecution(
            child_pid=444,
            handshake_ack=ack,
            source_digest=self.source_digest,
            runtime_manifest_digest=MANIFEST,
            runtime_inventory_digest=INVENTORY,
            candidate_bytes=CANDIDATE,
        )


def _binding():
    return TransactionBinding(TX, "CANDIDATE_STAGED", SOURCE, MANIFEST, INVENTORY, "demo-skill")


def _descriptors(tmp_path):
    result = {}
    for index, role in enumerate(PROTECTED_ROLES):
        path = tmp_path / f"{index}-{role}"
        if role == "version-root":
            path.mkdir()
            result[role] = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        else:
            path.write_bytes(role.encode())
            result[role] = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    return result


def _run(monkeypatch, tmp_path, executor):
    import loop_a_protected.darwin_broker_worker as runtime
    from loop_a_protected.darwin_peer import PeerCredentials

    broker, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    descriptors = _descriptors(tmp_path)
    binding = _binding()
    transaction = Transaction(binding)
    executor.transaction = transaction
    gate = Gate()
    worker_errors = []
    monkeypatch.setattr(runtime.os, "geteuid", lambda: 0)
    monkeypatch.setattr(runtime, "validate_launchd_worker_peer", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        runtime, "validate_root_broker_peer",
        lambda sock: PeerCredentials(os.getpid(), os.getpid(), 0, 0),
    )

    def worker_main():
        try:
            runtime.run_launchd_worker_session(sock=worker, executor=executor, timeout_seconds=2.0)
        except BaseException as exc:
            worker_errors.append(exc)

    thread = threading.Thread(target=worker_main)
    thread.start()
    try:
        result = runtime.run_root_broker_session(
            sock=broker,
            launchd_worker_pid=os.getpid(),
            worker_uid=os.getuid() + 1,
            worker_gid=os.getgid(),
            descriptors=descriptors,
            expected_descriptor_identities={
                role: (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
                for role, fd in descriptors.items()
            },
            mutation_root_identities=frozenset(),
            runtime_root_identity=None,
            binding=binding,
            gate=gate,
            transaction=transaction,
            timeout_seconds=2.0,
        )
        return result, transaction, gate, worker_errors, thread
    finally:
        thread.join(timeout=2.0)
        for fd in descriptors.values():
            os.close(fd)


def test_full_broker_launchd_worker_session_commits_only_after_exact_receipt_and_result(monkeypatch, tmp_path):
    executor = Executor()
    result, transaction, gate, worker_errors, thread = _run(monkeypatch, tmp_path, executor)
    assert not thread.is_alive()
    assert worker_errors == []
    envelope = canonical_candidate_payload(
        run_id=TX,
        skill_name="demo-skill",
        source_sha256=SOURCE,
        candidate_bytes=CANDIDATE,
    )
    assert result == CommittedCandidate(len(envelope), hashlib.sha256(envelope).hexdigest())
    assert transaction.commits == [(envelope, result.candidate_sha256)]
    assert gate.calls == 4
    assert executor.seen.transaction_uuid == TX
    assert executor.seen.broker_pid == os.getpid()
    assert len(executor.seen.nonce) == 64


def test_wrong_worker_binding_has_zero_commit(monkeypatch, tmp_path):
    import loop_a_protected.broker_coordinator as coordinator

    executor = Executor(source_digest="e" * 64)
    with pytest.raises(coordinator.BrokerCoordinatorError, match="worker result"):
        _run(monkeypatch, tmp_path, executor)
    assert executor.transaction.commits == []


def test_bad_inner_handshake_ack_closes_outer_session_with_zero_commit(monkeypatch, tmp_path):
    import loop_a_protected.darwin_broker_worker as runtime

    executor = Executor(bad_ack=True)
    with pytest.raises(runtime.DarwinBrokerWorkerError, match="failed closed"):
        _run(monkeypatch, tmp_path, executor)
    assert executor.transaction.commits == []
