from __future__ import annotations

import hashlib
import os
import threading

import pytest

from loop_a_protected.canonical import canonical_bytes, with_self_digest
from loop_a_protected.darwin_broker_worker import WorkerExecution
from loop_a_protected.darwin_executor import (
    DarwinExecutionPlan,
    DarwinExecutorError,
    DarwinLauncherExecutor,
)
from loop_a_protected.darwin_handshake import DarwinHandshakeError
from loop_a_protected.darwin_launchd_transport import PROTECTED_ROLES, ReceivedFdBundle
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.manifests import finalize_inventory, finalize_manifest


TX = "123e4567-e89b-42d3-a456-426614174000"
LINEAGE = "123e4567-e89b-42d3-a456-426614174001"


class Metadata(CleanMetadataAdapter):
    def acl_entries(self, fd):
        return ()

    def xattrs(self, fd):
        return ()

    def flags(self, fd):
        return 0


class Handshake:
    def __init__(self, pid, nonce):
        self.pid = pid
        self.nonce = nonce

    def complete(self):
        return with_self_digest({
            "schema": 1,
            "nonce": self.nonce,
            "child_pid": self.pid,
            "capability": "attestation-only",
            "ack_digest": None,
        }, "ack_digest")


class Pending:
    def __init__(self, pid, nonce):
        self.pid = pid
        self.handshake = Handshake(pid, nonce)


def _entry(path, data, executable=False):
    return {
        "relative_path": path,
        "type": "file",
        "mode": 0o555 if executable else 0o444,
        "uid": 0,
        "gid": 0,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "executable": executable,
    }


def _bundle(tmp_path):
    entrypoint = b"print('fixed worker')\n"
    executable = b"vendored-python"
    entries = [
        {"relative_path": "bin", "type": "directory", "mode": 0o555, "uid": 0, "gid": 0,
         "size": None, "sha256": None, "executable": False},
        _entry("bin/python3", executable, executable=True),
        {"relative_path": "libexec", "type": "directory", "mode": 0o555, "uid": 0, "gid": 0,
         "size": None, "sha256": None, "executable": False},
        _entry("libexec/worker.py", entrypoint),
    ]
    inventory = finalize_inventory("runtime", LINEAGE, 1, entries)
    closure = {
        "protected_roles": ["bin/python3", "libexec/worker.py"],
        "external_dependencies": [],
        "platform_build": "26A123",
        "snapshot_uuid": "123e4567-e89b-42d3-a456-426614174010",
        "seal_identity": "sealed-root",
        "cryptex_generation": "cryptex-1",
        "dyld_cache_uuid": "123e4567-e89b-42d3-a456-426614174011",
        "sip_enabled": True,
    }
    manifest = finalize_manifest(
        "runtime", LINEAGE, 1, "2026-08-03T01:02:03Z", 1,
        entries, inventory["inventory_digest"], closure,
    )
    values = {
        "entrypoint": entrypoint,
        "retained-executable": executable,
        "runtime-manifest": canonical_bytes(manifest),
        "runtime-inventory": canonical_bytes(inventory),
        "source": b"source skill bytes",
    }
    descriptors = {}
    for role in PROTECTED_ROLES:
        path = tmp_path / role
        if role == "version-root":
            path.mkdir()
            descriptors[role] = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        else:
            path.write_bytes(values[role])
            descriptors[role] = os.open(path, os.O_RDONLY)
    return ReceivedFdBundle(TX, os.getpid(), "a" * 64, descriptors, {}), entrypoint, manifest, inventory


def _plan(tmp_path):
    return DarwinExecutionPlan(
        version_root_path=f"/private/var/db/hermes-loop-a/runtime/versions/{'b' * 64}",
        entrypoint_relative_path="libexec/worker.py",
        uid=0,
        gid=0,
        worker_uid=max(1, os.geteuid()),
        metadata=Metadata(),
        physical_ancestors=(),
        mutation_root_identities=frozenset({(90, 91)}),
        timeout_seconds=2.0,
    )


def test_executor_maps_exact_six_outer_inputs_to_launcher_and_reaps(monkeypatch, tmp_path):
    import loop_a_protected.darwin_executor as module

    bundle, entrypoint, manifest, inventory = _bundle(tmp_path)
    captured = {}
    candidate = b"candidate-output"

    def fake_spawn(**kwargs):
        captured.update(kwargs)
        entry_read = os.dup(kwargs["entrypoint_fd"])
        result_write = os.dup(kwargs["result_fd"])
        diagnostic_write = os.dup(kwargs["diagnostics_fd"])

        def child():
            observed = bytearray()
            while True:
                chunk = os.read(entry_read, 4096)
                if not chunk:
                    break
                observed.extend(chunk)
            captured["entrypoint_bytes"] = bytes(observed)
            os.write(result_write, candidate)
            os.close(entry_read)
            os.close(result_write)
            os.close(diagnostic_write)

        thread = threading.Thread(target=child)
        thread.start()
        captured["thread"] = thread
        return Pending(4321, kwargs["challenge_nonce"].hex())

    monkeypatch.setattr(module, "spawn_pending_handshake_after_adjacent_executable", fake_spawn)
    monkeypatch.setattr(module, "_wait_success", lambda pid, deadline: None)
    monkeypatch.setattr(module, "_verify_file_descriptor", lambda *args, **kwargs: None)
    try:
        outcome = DarwinLauncherExecutor(_plan(tmp_path)).execute(bundle)
        captured["thread"].join(timeout=2)
        assert isinstance(outcome, WorkerExecution)
        assert outcome.child_pid == 4321
        assert outcome.candidate_bytes == candidate
        assert outcome.handshake_ack["nonce"] == bundle.nonce
        assert captured["entrypoint_bytes"] == entrypoint
        assert captured["manifest_digest"] == manifest["version_digest"]
        assert captured["inventory_digest"] == inventory["inventory_digest"]
        assert captured["challenge_nonce"] == bytes.fromhex(bundle.nonce)
        assert captured["manifest_fd"] == bundle.descriptors["runtime-manifest"]
        assert captured["inventory_fd"] == bundle.descriptors["runtime-inventory"]
        assert captured["source_fd"] == bundle.descriptors["source"]
    finally:
        bundle.close()


def _replace_role_bytes(bundle, tmp_path, role, data):
    os.close(bundle.descriptors[role])
    path = tmp_path / f"replacement-{role}"
    path.write_bytes(data)
    bundle.descriptors[role] = os.open(path, os.O_RDONLY)


def test_executor_rejects_noncanonical_manifest_and_invalid_timeout_before_spawn(monkeypatch, tmp_path):
    import loop_a_protected.darwin_executor as module

    bundle, _entrypoint, _manifest, _inventory = _bundle(tmp_path)
    called = []
    monkeypatch.setattr(module, "spawn_pending_handshake_after_adjacent_executable", lambda **kwargs: called.append(kwargs))
    try:
        for timeout in (True, 0, 31, "2"):
            plan = DarwinExecutionPlan(**{**_plan(tmp_path).__dict__, "timeout_seconds": timeout})
            with pytest.raises(DarwinExecutorError, match="timeout"):
                DarwinLauncherExecutor(plan).execute(bundle)
        _replace_role_bytes(bundle, tmp_path, "runtime-manifest", b'{"not":"canonical"}')
        with pytest.raises(DarwinExecutorError, match="canonical JSON"):
            DarwinLauncherExecutor(_plan(tmp_path)).execute(bundle)
        assert called == []
    finally:
        bundle.close()


def test_executor_rejects_wrong_outer_order_and_entrypoint_inventory_mismatch(monkeypatch, tmp_path):
    import loop_a_protected.darwin_executor as module

    bundle, _entrypoint, _manifest, _inventory = _bundle(tmp_path)
    called = []
    monkeypatch.setattr(module, "spawn_pending_handshake_after_adjacent_executable", lambda **kwargs: called.append(kwargs))
    try:
        reordered = dict(reversed(tuple(bundle.descriptors.items())))
        wrong = ReceivedFdBundle(bundle.transaction_uuid, bundle.broker_pid, bundle.nonce, reordered, bundle.record)
        with pytest.raises(DarwinExecutorError, match="order"):
            DarwinLauncherExecutor(_plan(tmp_path)).execute(wrong)
        _replace_role_bytes(bundle, tmp_path, "entrypoint", b"different-entrypoint\n")
        with pytest.raises(DarwinExecutorError, match="entrypoint descriptor"):
            DarwinLauncherExecutor(_plan(tmp_path)).execute(bundle)
        assert called == []
    finally:
        bundle.close()


def test_executor_reaps_child_when_handshake_fails(monkeypatch, tmp_path):
    import loop_a_protected.darwin_executor as module

    bundle, _entrypoint, _manifest, _inventory = _bundle(tmp_path)
    reaped = []

    class BrokenHandshake:
        def complete(self):
            raise RuntimeError("injected handshake failure")

    class BrokenPending:
        pid = 4321
        handshake = BrokenHandshake()

    monkeypatch.setattr(module, "spawn_pending_handshake_after_adjacent_executable", lambda **kwargs: BrokenPending())
    monkeypatch.setattr(module, "_kill_and_reap", lambda pid: reaped.append(pid))
    monkeypatch.setattr(module, "_verify_file_descriptor", lambda *args, **kwargs: None)
    try:
        with pytest.raises(DarwinExecutorError, match="failed closed"):
            DarwinLauncherExecutor(_plan(tmp_path)).execute(bundle)
        assert reaped == [4321]
    finally:
        bundle.close()


def test_executor_does_not_double_reap_after_handshake_transfers_reaped_state(monkeypatch, tmp_path):
    import loop_a_protected.darwin_executor as module

    bundle, _entrypoint, _manifest, _inventory = _bundle(tmp_path)
    executor_reaps = []

    class SelfReapingHandshake:
        child_pid = 4321

        def complete(self):
            self.child_pid = -1
            raise DarwinHandshakeError(
                "handshake already killed and reaped child", child_reaped=True,
            )

    class Pending:
        pid = 4321
        handshake = SelfReapingHandshake()

    reader_threads = []

    def fake_spawn(**kwargs):
        read_fd = os.dup(kwargs["entrypoint_fd"])

        def drain_entrypoint():
            try:
                while os.read(read_fd, 65536):
                    pass
            finally:
                os.close(read_fd)

        thread = threading.Thread(target=drain_entrypoint)
        thread.start()
        reader_threads.append(thread)
        return Pending()

    monkeypatch.setattr(module, "spawn_pending_handshake_after_adjacent_executable", fake_spawn)
    monkeypatch.setattr(module, "_kill_and_reap", lambda pid: executor_reaps.append(pid))
    monkeypatch.setattr(module, "_verify_file_descriptor", lambda *args, **kwargs: None)
    try:
        with pytest.raises(DarwinExecutorError, match="failed closed"):
            DarwinLauncherExecutor(_plan(tmp_path)).execute(bundle)
        assert executor_reaps == []
    finally:
        for thread in reader_threads:
            thread.join(timeout=2)
        bundle.close()


def test_executor_rejects_manifest_inventory_mismatch_before_spawn(monkeypatch, tmp_path):
    import loop_a_protected.darwin_executor as module

    bundle, _entrypoint, _manifest, inventory = _bundle(tmp_path)
    forged = dict(inventory)
    forged["release_sequence"] = 2
    descriptors = dict(bundle.descriptors)
    os.close(descriptors["runtime-inventory"])
    path = tmp_path / "forged-inventory"
    path.write_bytes(canonical_bytes(forged))
    descriptors["runtime-inventory"] = os.open(path, os.O_RDONLY)
    bundle = ReceivedFdBundle(
        bundle.transaction_uuid, bundle.broker_pid, bundle.nonce, descriptors, bundle.record
    )
    called = []
    monkeypatch.setattr(module, "spawn_pending_handshake_after_adjacent_executable", lambda **kwargs: called.append(kwargs))
    try:
        with pytest.raises(DarwinExecutorError, match="manifest/inventory"):
            DarwinLauncherExecutor(_plan(tmp_path)).execute(bundle)
        assert called == []
    finally:
        bundle.close()
