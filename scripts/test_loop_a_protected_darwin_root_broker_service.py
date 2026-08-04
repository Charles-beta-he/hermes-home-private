from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import ANY

import pytest

from loop_a_protected.broker_coordinator import TransactionBinding


TX = "12345678-1234-5678-9234-567812345678"
DIGEST = "a" * 64
ROLES = (
    "entrypoint",
    "retained-executable",
    "version-root",
    "runtime-manifest",
    "runtime-inventory",
    "source",
)


class FakeSocket:
    def __init__(self, events):
        self.events = events
        self.closed = False

    def close(self):
        self.closed = True
        self.events.append("close-socket")


class Admission:
    def __init__(self, events):
        self.events = events
        self.run = ServiceRun(events)

    def __enter__(self):
        self.events.append("enter-admission")
        return self.run

    def __exit__(self, exc_type, exc, traceback):
        self.events.append(("exit-admission", exc_type))


class ServiceRun:
    def __init__(self, events):
        self.events = events

    def assert_epoch_current(self):
        self.events.append("epoch-current")
        return {"epoch": 7}


@dataclass(frozen=True)
class Activation:
    socket: object
    launchd_pid: int


class Transaction:
    def __init__(self, events):
        self.events = events
        self.binding = TransactionBinding(
            transaction_uuid=TX,
            state="CANDIDATE_STAGED",
            source_digest="b" * 64,
            runtime_manifest_digest="c" * 64,
            runtime_inventory_digest=DIGEST,
            skill_name="example-skill",
        )

    def snapshot(self):
        self.events.append("snapshot")
        return self.binding


def _inputs(module):
    identities = {role: (1, index + 20) for index, role in enumerate(ROLES)}
    descriptors = module.RootBrokerDescriptorSet(
        protected={role: index + 10 for index, role in enumerate(ROLES)},
        expected_identities=identities,
        records_fd=40,
        candidates_fd=41,
        mutation_root_identities=frozenset({(1, 2)}),
        runtime_root_identity=(1, 2),
    )
    identity = module.RootBrokerIdentity(
        root_uid=0,
        root_gid=0,
        service_uid=222,
        service_gid=223,
        worker_uid=222,
        worker_gid=223,
    )
    transaction = module.RootBrokerTransaction(
        transaction_uuid=TX,
        skill_name="example-skill",
        runtime_manifest_digest="c" * 64,
        runtime_inventory_digest=DIGEST,
        source_sha256="b" * 64,
        source_byte_count=123,
    )
    return identity, descriptors, transaction


def test_root_broker_composes_admission_transaction_activation_and_one_session():
    import loop_a_protected.darwin_root_broker_service as module

    identity, descriptors, transaction_spec = _inputs(module)
    events = []
    sock = FakeSocket(events)

    def admission_factory(*args):
        events.append(("admission", args))
        return Admission(events)

    def transaction_factory(**kwargs):
        events.append(("transaction", kwargs))
        return Transaction(events)

    def activate(**kwargs):
        events.append(("activate", kwargs))
        return Activation(sock, 4321)

    def run_session(**kwargs):
        events.append(("session", kwargs))
        kwargs["gate"].assert_live()
        return "committed"

    result = module.run_root_broker_service_once(
        root_fd=9,
        expected_root_identity=(1, 1),
        identity=identity,
        descriptors=descriptors,
        transaction_spec=transaction_spec,
        metadata="metadata",
        timestamp=lambda: "2026-08-03T01:00:00Z",
        geteuid=lambda: 0,
        admission_factory=admission_factory,
        transaction_factory=transaction_factory,
        activate=activate,
        session_runner=run_session,
        timeout_seconds=7.0,
    )

    assert result == "committed"
    assert events[0] == (
        "admission",
        (9, (1, 1), 0, 0, 222, 223, "metadata"),
    )
    assert events[1] == "enter-admission"
    transaction_call = events[2]
    assert transaction_call[0] == "transaction"
    assert transaction_call[1] == {
        "records_fd": 40,
        "candidates_fd": 41,
        "uid": 0,
        "gid": 0,
        "worker_uid": 222,
        "metadata": "metadata",
        "transaction_uuid": TX,
        "skill_name": "example-skill",
        "runtime_inventory_digest": DIGEST,
        "source_byte_count": 123,
        "timestamp": ANY,
    }
    assert events[3:6] == ["snapshot", "epoch-current", (
        "activate", {"worker_uid": 222, "worker_gid": 223, "timeout_seconds": 7.0}
    )]
    assert events[6] == "epoch-current"
    session_call = events[7]
    assert session_call[0] == "session"
    assert session_call[1] == {
        "sock": sock,
        "launchd_worker_pid": 4321,
        "worker_uid": 222,
        "worker_gid": 223,
        "descriptors": descriptors.protected,
        "binding": ANY,
        "expected_descriptor_identities": descriptors.expected_identities,
        "mutation_root_identities": frozenset({(1, 2)}),
        "runtime_root_identity": (1, 2),
        "gate": ANY,
        "transaction": ANY,
        "timeout_seconds": 7.0,
    }
    assert events[8:] == ["epoch-current", "close-socket", ("exit-admission", None)]


def test_root_broker_closes_activated_socket_when_injected_session_fails():
    import loop_a_protected.darwin_root_broker_service as module

    identity, descriptors, transaction_spec = _inputs(module)
    events = []
    sock = FakeSocket(events)

    with pytest.raises(module.DarwinRootBrokerServiceError, match="failed closed"):
        module.run_root_broker_service_once(
            root_fd=9,
            expected_root_identity=(1, 1),
            identity=identity,
            descriptors=descriptors,
            transaction_spec=transaction_spec,
            metadata="metadata",
            timestamp=lambda: "2026-08-03T01:00:00Z",
            geteuid=lambda: 0,
            admission_factory=lambda *args: Admission(events),
            transaction_factory=lambda **kwargs: Transaction(events),
            activate=lambda **kwargs: Activation(sock, 4321),
            session_runner=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
        )

    assert sock.closed is True
    assert events[-2:] == ["close-socket", ("exit-admission", RuntimeError)]


def test_root_broker_rejects_identity_or_descriptor_contract_before_admission():
    import loop_a_protected.darwin_root_broker_service as module

    identity, descriptors, transaction_spec = _inputs(module)
    calls = []
    with pytest.raises(module.DarwinRootBrokerServiceError, match="root identity"):
        module.RootBrokerIdentity(
            root_uid=501,
            root_gid=0,
            service_uid=222,
            service_gid=223,
            worker_uid=222,
            worker_gid=223,
        )

    with pytest.raises(module.DarwinRootBrokerServiceError, match="root identity"):
        module.run_root_broker_service_once(
            root_fd=9,
            expected_root_identity=(1, 1),
            identity=identity,
            descriptors=descriptors,
            transaction_spec=transaction_spec,
            metadata="metadata",
            timestamp=lambda: "2026-08-03T01:00:00Z",
            geteuid=lambda: 501,
            admission_factory=lambda *args: calls.append(args),
        )
    assert calls == []

    with pytest.raises(module.DarwinRootBrokerServiceError, match="protected descriptor roles"):
        module.RootBrokerDescriptorSet(
            protected={"source": 10},
            expected_identities={"source": (1, 2)},
            records_fd=40,
            candidates_fd=41,
            mutation_root_identities=frozenset({(1, 2)}),
            runtime_root_identity=(1, 2),
        )


def test_root_broker_rejects_nonstaged_transaction_before_activation():
    import loop_a_protected.darwin_root_broker_service as module

    identity, descriptors, transaction_spec = _inputs(module)
    events = []

    class WrongTransaction(Transaction):
        def snapshot(self):
            events.append("snapshot")
            return object()

    with pytest.raises(module.DarwinRootBrokerServiceError, match="staged transaction"):
        module.run_root_broker_service_once(
            root_fd=9,
            expected_root_identity=(1, 1),
            identity=identity,
            descriptors=descriptors,
            transaction_spec=transaction_spec,
            metadata="metadata",
            timestamp=lambda: "2026-08-03T01:00:00Z",
            geteuid=lambda: 0,
            admission_factory=lambda *args: Admission(events),
            transaction_factory=lambda **kwargs: WrongTransaction(events),
            activate=lambda **kwargs: events.append("activate"),
        )
    assert "activate" not in events
