#!/usr/bin/env python3
"""Hostile contract tests for the deterministic N2 consumer harness."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import taskpool_event_broker as broker_module
from taskpool_event_broker import (
    BrokerProtocolError,
    BrokerRuntimeState,
    DeterministicConsumerBroker,
    MAX_WORK_EPOCH,
    RuntimeStateError,
    StrictFrameCodec,
    UnixWakeEndpoint,
)
from taskpool_event_outbox import DurableTaskpoolEventOutbox

EVENT_TYPE = "taskpool.actionable.v1"

_WORKER_COMMON = r'''
import hashlib, hmac, json, os, struct, sys, time
key = bytes.fromhex(os.environ["TASKPOOL_WORKER_KEY_HEX"])
raw = sys.stdin.buffer.read()
size = struct.unpack(">I", raw[:4])[0]
body, tag = raw[4:4+size], raw[4+size:]
assert len(raw) == 4 + size + 32
assert hmac.compare_digest(tag, hmac.new(key, body, hashlib.sha256).digest())
request = json.loads(body.decode("utf-8"))
'''
_WORKER_RESPONSE = r'''
intent = {
    "schema": "taskpool.worker-intent.v1",
    "channel_nonce": request["channel_nonce"],
    "sequence": 1,
    "event_id": request["payload"]["event"]["event_id"],
    "generation": request["payload"]["event"]["generation"],
    "kind": "complete",
    "result": {"handled": request["payload"]["event"]["task_id"]},
}
response = json.dumps({"channel_nonce": request["channel_nonce"], "sequence": 1, "payload": intent}, sort_keys=True, separators=(",", ":")).encode()
sys.stdout.buffer.write(struct.pack(">I", len(response)) + response + hmac.new(key, response, hashlib.sha256).digest())
'''
_WORKER = _WORKER_COMMON + _WORKER_RESPONSE
_BAD_WORKER = _WORKER_COMMON + "sys.stdout.buffer.write(b'{}')"
_CRASH_WORKER = _WORKER_COMMON + "os._exit(23)"
_SLOW_WORKER = _WORKER_COMMON + "time.sleep(0.35)\n" + _WORKER_RESPONSE
_FORK_WORKER = _WORKER_COMMON + "\npid=os.fork()\nif pid == 0:\n time.sleep(30); os._exit(0)\n" + _WORKER_RESPONSE
_OVERSIZE_WORKER = _WORKER_COMMON + "sys.stdout.buffer.write(b'x' * (1024 * 1024 + 100)); sys.stdout.buffer.flush(); time.sleep(30)"
_NO_READ_WORKER = "import time; time.sleep(30)"
_DUAL_OUTPUT_WORKER = "import os,time; os.write(1,b'o'*60); os.write(2,b'e'*60); time.sleep(30)"


class CountingPopen:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.delegate(*args, **kwargs)


class DeterministicConsumerBrokerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.outbox = DurableTaskpoolEventOutbox(
            self.root / "state" / "outbox.sqlite3", allowed_root=self.root
        )
        self.state = BrokerRuntimeState(
            self.root / "runtime" / "broker.sqlite3", allowed_root=self.root
        )
        self.wake = UnixWakeEndpoint(self.root / "wake.sock", key=b"w" * 32)

    def tearDown(self) -> None:
        if self.wake.registered:
            self.wake.close()
        self.state.close()
        self.tempdir.cleanup()

    def enqueue(self, key: str = "task-7:ready"):
        return self.outbox.enqueue(
            idempotency_key=key,
            event_type=EVENT_TYPE,
            task_id="task-7",
            payload={"reason": "ready"},
            now=10.0,
        )

    def broker(self, worker=_WORKER, **kwargs):
        worker_timeout = kwargs.pop("worker_timeout", 3.0)
        wake_endpoint = kwargs.pop("wake_endpoint", self.wake)
        return DeterministicConsumerBroker(
            outbox=self.outbox,
            runtime_state=self.state,
            wake_endpoint=wake_endpoint,
            worker_argv=(sys.executable, "-I", "-c", worker),
            lease_seconds=30.0,
            worker_timeout=worker_timeout,
            clock=lambda: 20.0,
            **kwargs,
        )

    def test_startup_registers_before_drain_and_completes_durable_row(self):
        self.enqueue()
        broker = self.broker()
        report = broker.startup_drain(max_cycles=4)
        self.assertEqual(report["ordering"], ["watchdog_ready", "wake_registered", "startup_drain"])
        self.assertEqual(report["processed"], 1)
        self.assertTrue(report["quiescent"])
        status = self.outbox.status()
        self.assertEqual(status["counts"], {"completed": 1})
        self.assertEqual(status["events"][0]["payload"], {"reason": "ready"})

    def test_empty_startup_and_idle_wait_never_construct_worker(self):
        import subprocess
        counter = CountingPopen(subprocess.Popen)
        broker = self.broker(popen_factory=counter)
        report = broker.startup_drain(max_cycles=2)
        observed = broker.runtime_identity()
        wait = broker.wait_for_work(observed=observed, timeout=0.02)
        self.assertTrue(report["quiescent"])
        self.assertEqual(wait["reason"], "timeout")
        self.assertEqual(counter.calls, 0)
        self.assertEqual(broker.worker_start_count, 0)

    def test_post_commit_notification_cannot_be_lost_between_zero_and_wait(self):
        broker = self.broker()
        broker.startup_drain(max_cycles=1)
        observed = broker.runtime_identity()
        barrier = threading.Barrier(2)
        result = {}

        def waiter():
            barrier.wait()
            result.update(broker.wait_for_work(observed=observed, timeout=1.0))

        thread = threading.Thread(target=waiter)
        thread.start()
        barrier.wait()
        self.enqueue()
        published = broker.notify_post_commit()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result["reason"], "epoch_changed")
        self.assertEqual(result["identity"], published)

    def test_child_crash_preserves_obligation_as_pending(self):
        self.enqueue()
        report = self.broker(worker=_CRASH_WORKER).startup_drain(max_cycles=1)
        self.assertEqual(report["processed"], 0)
        self.assertEqual(report["worker_failures"], 1)
        self.assertEqual(self.outbox.status()["counts"], {"pending": 1})
        recovered = self.broker().startup_drain(max_cycles=3)
        self.assertEqual(recovered["processed"], 1)
        self.assertEqual(self.outbox.status()["counts"], {"completed": 1})

    def test_changed_or_malformed_worker_intent_fails_closed(self):
        self.enqueue()
        report = self.broker(worker=_BAD_WORKER).startup_drain(max_cycles=1)
        self.assertEqual(report["worker_failures"], 1)
        self.assertEqual(self.outbox.status()["counts"], {"pending": 1})

    def test_unexpired_claim_is_not_quiescent_and_arms_earliest_deadline(self):
        self.enqueue()
        claimed = self.outbox.claim(lease_seconds=10, now=20.0)
        self.assertIsNotNone(claimed)
        broker = self.broker()
        report = broker.startup_drain(max_cycles=1)
        self.assertFalse(report["quiescent"])
        self.assertEqual(report["pending"], 0)
        self.assertEqual(report["claimed"], 1)
        self.assertEqual(report["next_wake_deadline"], 30.0)
        self.assertEqual(broker.worker_start_count, 0)

    def test_expired_claim_is_due_before_worker_start_and_is_recovered(self):
        self.enqueue(key="expired-before-start:ready")
        claimed = self.outbox.claim(lease_seconds=1.0, now=10.0)
        self.assertIsNotNone(claimed)
        broker = self.broker()
        report = broker.startup_drain(max_cycles=2)
        self.assertEqual(report["processed"], 1)
        self.assertEqual(report["worker_failures"], 0)
        self.assertEqual(broker.worker_start_count, 1)
        self.assertEqual(self.outbox.status()["counts"], {"completed": 1})

    def test_claim_race_after_prestart_cleans_unused_worker(self):
        self.enqueue(key="claim-race:ready")
        captured = {}

        def stealing_popen(*args, **kwargs):
            process = subprocess.Popen(*args, **kwargs)
            captured["process"] = process
            stolen = self.outbox.claim(lease_seconds=30.0, now=20.0)
            self.assertIsNotNone(stolen)
            self.assertIsNone(process.poll())
            self.assertEqual(os.getpgid(process.pid), process.pid)
            return process

        broker = self.broker(worker=_NO_READ_WORKER, popen_factory=stealing_popen)
        report = broker.startup_drain(max_cycles=1)
        self.assertEqual(report["processed"], 0)
        self.assertEqual(report["worker_failures"], 0)
        self.assertEqual(report["claimed"], 1)
        self.assertEqual(broker.worker_start_count, 1)
        process = captured["process"]
        with self.assertRaises(ProcessLookupError):
            os.killpg(process.pid, 0)

    def test_runtime_epoch_persists_rejects_stale_generation_and_fails_closed_at_max(self):
        first = self.state.snapshot()
        second = self.state.advance(expected=first)
        reopened = BrokerRuntimeState(self.state.path, allowed_root=self.root)
        self.assertEqual(reopened.snapshot(), second)
        with self.assertRaises(RuntimeStateError):
            reopened.advance(expected=first)
        with sqlite3.connect(self.state.path) as connection:
            connection.execute("UPDATE broker_runtime SET work_epoch=?", (MAX_WORK_EPOCH,))
        with self.assertRaises(RuntimeStateError):
            reopened.advance(expected=reopened.snapshot())
        with sqlite3.connect(self.state.path) as connection:
            connection.execute("UPDATE broker_runtime SET work_epoch='corrupt'")
        with self.assertRaises(RuntimeStateError):
            reopened.snapshot()

    def test_strict_frames_bind_nonce_sequence_length_and_digest(self):
        key = b"k" * 32
        codec = StrictFrameCodec(key=key, channel_nonce="nonce-1")
        frame = codec.encode(sequence=1, payload={"kind": "wake"})
        self.assertEqual(codec.decode(frame, expected_sequence=1), {"kind": "wake"})
        with self.assertRaises(BrokerProtocolError):
            codec.decode(frame, expected_sequence=2)
        changed = bytearray(frame)
        changed[-1] ^= 1
        with self.assertRaises(BrokerProtocolError):
            codec.decode(bytes(changed), expected_sequence=1)
        with self.assertRaises(BrokerProtocolError):
            codec.decode(frame[:-1], expected_sequence=1)

    def test_unix_wake_endpoint_registers_then_delivers_one_authenticated_wake(self):
        key = b"z" * 32
        endpoint = UnixWakeEndpoint(self.root / "wake-standalone.sock", key=key)
        endpoint.register()
        self.assertTrue(endpoint.registered)
        identity = {"db_generation": "g", "work_epoch": 1}
        result = {}
        thread = threading.Thread(
            target=lambda: result.update(endpoint.receive_once(timeout=1.0, minimum_sequence=1))
        )
        thread.start()
        endpoint.sender_endpoint().send_wake(
            sequence=1, payload={"reason": "post_commit", "identity": identity}
        )
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result, {"reason": "post_commit", "identity": identity})
        endpoint.close()
        self.assertFalse((self.root / "wake-standalone.sock").exists())

    def test_registration_failure_prevents_any_claim(self):
        class FailingEndpoint:
            registered = False
            def register(self):
                raise OSError("injected register failure")

        calls = []
        original = self.outbox.claim
        self.outbox.claim = lambda **kwargs: calls.append(kwargs) or original(**kwargs)
        broker = self.broker(wake_endpoint=FailingEndpoint())
        with self.assertRaises(OSError):
            broker.startup_drain(max_cycles=1)
        self.assertEqual(calls, [])

    def test_durable_epoch_is_rechecked_when_post_commit_wake_is_lost(self):
        receiver = UnixWakeEndpoint(self.root / "lost.sock", key=b"l" * 32, peer_timeout=0.05)
        receiver.register()
        waiter = self.broker(wake_endpoint=receiver)
        sender = receiver.sender_endpoint()
        notifier = self.broker(wake_endpoint=sender)
        observed = self.state.snapshot()
        result = {}
        thread = threading.Thread(
            target=lambda: result.update(waiter.wait_for_work(observed=observed, timeout=None))
        )
        thread.start()
        time.sleep(0.03)
        sender.__dict__["_send_commit_marker"] = lambda client: (_ for _ in ()).throw(
            BrokerProtocolError("injected crash after durable commit")
        )
        with self.assertRaises(BrokerProtocolError):
            notifier.notify_post_commit()
        published = self.state.snapshot()
        self.assertEqual(published["work_epoch"], observed["work_epoch"] + 1)
        thread.join(timeout=0.5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result["reason"], "epoch_changed")
        receiver.close()

    def test_sender_requires_authenticated_ack_from_connected_peer(self):
        receiver = UnixWakeEndpoint(self.root / "ack.sock", key=b"a" * 32, peer_timeout=0.05)
        receiver.register()
        sender = receiver.sender_endpoint()
        original = receiver.path.with_name("ack-original.sock")
        substitute_path = receiver.path.with_name("ack-substitute.sock")
        receiver.path.rename(original)
        substitute = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        substitute.bind(str(receiver.path))
        substitute.listen(1)
        calls = []
        real_verify = sender._verify_socket_path

        def race_verify():
            calls.append(1)
            if len(calls) == 1:
                return sender._expected_socket_identity
            if len(calls) == 2:
                receiver.path.rename(substitute_path)
                original.rename(receiver.path)
            return real_verify()

        sender._verify_socket_path = race_verify
        accepted = []

        def swallow_without_ack():
            peer, _ = substitute.accept()
            accepted.append(peer.recv(65536))
            peer.close()

        thread = threading.Thread(target=swallow_without_ack)
        thread.start()
        with self.assertRaises(BrokerProtocolError):
            sender.send_wake(
                sequence=1,
                payload={"reason": "post_commit", "identity": {"db_generation": "g", "work_epoch": 1}},
            )
        thread.join(timeout=0.5)
        self.assertTrue(accepted)
        substitute.close()
        substitute_path.unlink()
        receiver.close()

    def test_invalid_peer_is_drained_before_valid_durable_wake(self):
        receiver = UnixWakeEndpoint(self.root / "queue.sock", key=b"q" * 32, peer_timeout=0.05)
        receiver.register()
        broker = self.broker(wake_endpoint=receiver)
        observed = self.state.snapshot()
        bad = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        bad.connect(str(receiver.path))
        bad.sendall(b"bad")
        bad.close()
        result = {}
        thread = threading.Thread(
            target=lambda: result.update(broker.wait_for_work(observed=observed, timeout=0.5))
        )
        thread.start()
        time.sleep(0.03)
        broker.notify_post_commit()
        thread.join(timeout=1.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result["reason"], "epoch_changed")
        receiver.close()

    def test_two_brokers_use_distinct_endpoint_instances_for_socket_wake(self):
        receiver = UnixWakeEndpoint(self.root / "cross.sock", key=b"c" * 32)
        receiver.register()
        sender = receiver.sender_endpoint()
        self.assertIsNot(receiver, sender)
        waiter = self.broker(wake_endpoint=receiver)
        notifier = self.broker(wake_endpoint=sender)
        waiter.startup_drain(max_cycles=1)
        observed = waiter.runtime_identity()
        result = {}
        thread = threading.Thread(
            target=lambda: result.update(waiter.wait_for_work(observed=observed, timeout=1.0))
        )
        thread.start()
        time.sleep(0.03)
        published = notifier.notify_post_commit()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result, {"reason": "epoch_changed", "identity": published})
        receiver.close()

    def test_wake_replay_partial_peer_and_sequence_poison_are_rejected_boundedly(self):
        endpoint = UnixWakeEndpoint(self.root / "replay.sock", key=b"r" * 32, peer_timeout=0.05)
        endpoint.register()
        sender = endpoint.sender_endpoint()
        payload1 = {"reason": "post_commit", "identity": {"db_generation": "g", "work_epoch": 1}}
        frame = sender.build_wake_frame(sequence=1, payload=payload1)

        def exchange(outbound, *, minimum_sequence, error=False):
            sender_errors = []
            received = None
            # Capture sender-side refusal without leaking a thread exception into pytest.
            def transmit():
                try:
                    sender.send_frame(outbound)
                except BrokerProtocolError as exc:
                    sender_errors.append(exc)
            thread = threading.Thread(target=transmit)
            thread.start()
            if error:
                with self.assertRaises(BrokerProtocolError):
                    endpoint.receive_once(timeout=0.5, minimum_sequence=minimum_sequence)
            else:
                received = endpoint.receive_once(timeout=0.5, minimum_sequence=minimum_sequence)
            thread.join(timeout=0.5)
            self.assertFalse(thread.is_alive())
            if error:
                self.assertTrue(sender_errors)
                return None
            self.assertEqual(sender_errors, [])
            return received

        self.assertEqual(exchange(frame, minimum_sequence=1), payload1)
        exchange(frame, minimum_sequence=2, error=True)

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(str(endpoint.path))
        client.sendall(b"\x00\x00\x01")
        started = time.monotonic()
        with self.assertRaises((BrokerProtocolError, TimeoutError, socket.timeout)):
            endpoint.receive_once(timeout=None, minimum_sequence=2)
        self.assertLess(time.monotonic() - started, 0.5)
        client.close()

        poisoned = {"reason": "post_commit", "identity": {"db_generation": "g", "work_epoch": MAX_WORK_EPOCH + 1}}
        poisoned_frame = sender.build_wake_frame(sequence=MAX_WORK_EPOCH + 1, payload=poisoned)
        exchange(poisoned_frame, minimum_sequence=2, error=True)

        payload2 = {"reason": "post_commit", "identity": {"db_generation": "g", "work_epoch": 2}}
        frame2 = sender.build_wake_frame(sequence=2, payload=payload2)
        self.assertEqual(exchange(frame2, minimum_sequence=2), payload2)
        endpoint.close()

    def test_worker_uses_authenticated_frame_and_noncanonical_frame_is_rejected(self):
        noncanonical = _WORKER_COMMON + r'''
payload = {"schema":"taskpool.worker-intent.v1","channel_nonce":request["channel_nonce"],"sequence":1,"event_id":request["payload"]["event"]["event_id"],"generation":request["payload"]["event"]["generation"],"kind":"complete","result":{}}
response = json.dumps({"payload":payload,"sequence":1,"channel_nonce":request["channel_nonce"]}, indent=1).encode()
sys.stdout.buffer.write(struct.pack(">I", len(response)) + response + hmac.new(key, response, hashlib.sha256).digest())
'''
        self.enqueue()
        report = self.broker(worker=noncanonical).startup_drain(max_cycles=1)
        self.assertEqual(report["worker_failures"], 1)
        self.assertEqual(self.outbox.status()["counts"], {"pending": 1})

    def test_process_group_exit_wait_tolerates_transient_eperm_but_bounds_ambiguity(self):
        broker = self.broker(worker_timeout=0.1)
        checks: list[object] = [PermissionError("transient"), False]

        def transient(_pgid: int) -> bool:
            outcome = checks.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return bool(outcome)

        broker._group_exists = transient  # type: ignore[method-assign]
        self.assertTrue(broker._wait_for_group_exit(1234, timeout=0.05))

        def persistent(_pgid: int) -> bool:
            raise PermissionError("persistent")

        broker._group_exists = persistent  # type: ignore[method-assign]
        with self.assertRaisesRegex(BrokerProtocolError, "could not be verified"):
            broker._wait_for_group_exit(1234, timeout=0.02)

    def test_worker_timeout_oversize_and_residual_descendants_are_bounded(self):
        import subprocess

        for index, worker in enumerate((_OVERSIZE_WORKER, _FORK_WORKER)):
            if index:
                self.outbox = DurableTaskpoolEventOutbox(
                    self.root / f"state-{index}" / "outbox.sqlite3", allowed_root=self.root
                )
            self.enqueue(key=f"task-{index}:ready")
            capture = CountingPopen(subprocess.Popen)
            broker = self.broker(worker=worker, popen_factory=capture, worker_timeout=0.4)
            report = broker.startup_drain(max_cycles=1)
            self.assertEqual(capture.calls, 1)
            self.assertEqual(report["worker_failures"], 1)
            self.assertEqual(report["pending"], 1)
            pid = broker.last_worker_pid
            with self.assertRaises(ProcessLookupError):
                os.killpg(pid, 0)

    def test_total_worker_output_limit_is_aggregate_across_both_pipes(self):
        self.enqueue(key="dual-output:ready")
        broker = DeterministicConsumerBroker(
            outbox=self.outbox,
            runtime_state=self.state,
            wake_endpoint=self.wake,
            worker_argv=(sys.executable, "-I", "-c", _DUAL_OUTPUT_WORKER),
            output_limit=100,
            lease_seconds=0.5,
            worker_timeout=3.0,
            clock=time.time,
        )
        started = time.monotonic()
        report = broker.startup_drain(max_cycles=1)
        self.assertLess(time.monotonic() - started, 0.75)
        self.assertEqual(report["worker_failures"], 1)
        self.assertEqual(report["pending"], 1)

    def test_nonreading_worker_cannot_block_stdin_deadline_renewal_or_cleanup(self):
        large = {"blob": "x" * 300000}
        self.outbox.enqueue(
            event_type=EVENT_TYPE,
            task_id="task-large",
            idempotency_key="task-large:ready",
            payload=large,
            now=time.time(),
        )
        renewals = []
        original = self.outbox.renew
        self.outbox.renew = lambda **kwargs: renewals.append(dict(kwargs)) or original(**kwargs)
        broker = DeterministicConsumerBroker(
            outbox=self.outbox,
            runtime_state=self.state,
            wake_endpoint=self.wake,
            worker_argv=(sys.executable, "-I", "-c", _NO_READ_WORKER),
            lease_seconds=0.1,
            worker_timeout=0.3,
            clock=time.time,
        )
        started = time.monotonic()
        report = broker.startup_drain(max_cycles=1)
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertEqual(report["worker_failures"], 1)
        self.assertGreaterEqual(len(renewals), 1)
        with self.assertRaises(ProcessLookupError):
            os.killpg(broker.last_worker_pid, 0)

    def test_unsupported_short_lease_is_rejected_before_any_worker_start(self):
        with self.assertRaisesRegex(ValueError, "at least 0.1"):
            DeterministicConsumerBroker(
                outbox=self.outbox,
                runtime_state=self.state,
                wake_endpoint=self.wake,
                worker_argv=(sys.executable, "-I", "-c", _WORKER),
                lease_seconds=0.01,
                worker_timeout=2.0,
            )

    def test_minimum_lease_is_not_held_during_delayed_worker_startup(self):
        self.enqueue(key="short-lease:ready")
        renewals = []
        original = self.outbox.renew
        self.outbox.renew = lambda **kwargs: renewals.append(dict(kwargs)) or original(**kwargs)

        def delayed_popen(*args, **kwargs):
            time.sleep(0.2)
            return subprocess.Popen(*args, **kwargs)

        broker = DeterministicConsumerBroker(
            outbox=self.outbox,
            runtime_state=self.state,
            wake_endpoint=self.wake,
            worker_argv=(sys.executable, "-I", "-c", _SLOW_WORKER),
            lease_seconds=0.1,
            worker_timeout=2.0,
            clock=time.time,
            popen_factory=delayed_popen,
        )
        report = broker.startup_drain(max_cycles=2)
        self.assertEqual(report["processed"], 1)
        self.assertEqual(report["worker_failures"], 0)
        self.assertGreaterEqual(len(renewals), 1)
        self.assertEqual(self.outbox.status()["counts"], {"completed": 1})

    def test_long_worker_renews_and_old_timer_token_is_fenced(self):
        self.enqueue()
        renewals = []
        original = self.outbox.renew
        self.outbox.renew = lambda **kwargs: renewals.append(dict(kwargs)) or original(**kwargs)
        broker = DeterministicConsumerBroker(
            outbox=self.outbox,
            runtime_state=self.state,
            wake_endpoint=self.wake,
            worker_argv=(sys.executable, "-I", "-c", _SLOW_WORKER),
            lease_seconds=0.15,
            worker_timeout=2.0,
            clock=time.time,
        )
        report = broker.startup_drain(max_cycles=2)
        self.assertEqual(report["processed"], 1)
        self.assertGreaterEqual(len(renewals), 1)
        token = report["last_timer_token"]
        self.state.advance(expected=self.state.snapshot())
        self.assertEqual(broker.timer_fire(token), "stale")

    def test_corrupt_counts_fail_closed_instead_of_reporting_quiescence(self):
        bad = (
            {},
            {"counts": {}},
            {"counts": {"pending": "0"}, "events": []},
            {"counts": {"pending": False}, "events": []},
            {"counts": {"pending": -1}, "events": []},
            {"counts": {"alien": 0}, "events": []},
        )
        for status in bad:
            with self.subTest(status=status):
                with self.assertRaises(RuntimeStateError):
                    DeterministicConsumerBroker._counts(status)

    def test_endpoint_close_never_unlinks_replacement_path(self):
        endpoint = UnixWakeEndpoint(self.root / "replace.sock", key=b"x" * 32)
        endpoint.register()
        endpoint.path.unlink()
        endpoint.path.write_text("replacement", encoding="utf-8")
        with self.assertRaises(BrokerProtocolError):
            endpoint.close()
        self.assertEqual(endpoint.path.read_text(encoding="utf-8"), "replacement")

    def test_runtime_state_rejects_hardlink_and_parent_identity_replacement(self):
        linked = BrokerRuntimeState(self.root / "linked" / "state.sqlite3", allowed_root=self.root)
        os.link(linked.path, self.root / "linked-copy.sqlite3")
        with self.assertRaises(RuntimeStateError):
            linked.snapshot()

        original_parent = self.root / "parent"
        guarded = BrokerRuntimeState(original_parent / "state.sqlite3", allowed_root=self.root)
        moved_parent = self.root / "parent-moved"
        original_parent.rename(moved_parent)
        original_parent.mkdir(mode=0o700)
        replacement = original_parent / "state.sqlite3"
        replacement.write_bytes((moved_parent / "state.sqlite3").read_bytes())
        os.chmod(replacement, 0o600)
        with self.assertRaises(RuntimeStateError):
            guarded.snapshot()

    def test_runtime_close_serializes_with_inflight_snapshot(self):
        entered = threading.Event()
        release = threading.Event()
        errors = []
        original_verify = self.state._verify_connection

        def paused_verify():
            if not entered.is_set():
                entered.set()
                if not release.wait(timeout=0.5):
                    raise AssertionError("snapshot pause timed out")
            original_verify()

        self.state._verify_connection = paused_verify
        reader = threading.Thread(target=lambda: self._capture_thread_error(self.state.snapshot, errors))
        reader.start()
        self.assertTrue(entered.wait(timeout=0.5))
        closer = threading.Thread(target=self.state.close)
        closer.start()
        time.sleep(0.02)
        self.assertTrue(closer.is_alive())
        release.set()
        reader.join(timeout=0.5)
        closer.join(timeout=0.5)
        self.assertFalse(reader.is_alive())
        self.assertFalse(closer.is_alive())
        self.assertEqual(errors, [])

    @staticmethod
    def _capture_thread_error(operation, errors):
        try:
            operation()
        except BaseException as exc:
            errors.append(exc)

    def test_runtime_operations_use_the_frozen_connected_file_not_path_reopen(self):
        state = BrokerRuntimeState(self.root / "persistent" / "state.sqlite3", allowed_root=self.root)
        expected = state.snapshot()
        original_connect = broker_module.sqlite3.connect
        broker_module.sqlite3.connect = lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("runtime operation reopened pathname")
        )
        try:
            advanced = state.advance(expected=expected)
            self.assertEqual(advanced["work_epoch"], expected["work_epoch"] + 1)
            self.assertEqual(state.snapshot(), advanced)
        finally:
            broker_module.sqlite3.connect = original_connect
            state.close()

    def test_runtime_advance_and_wake_send_fail_closed_on_path_replacement(self):
        parent = self.root / "tx-parent"
        guarded = BrokerRuntimeState(parent / "state.sqlite3", allowed_root=self.root)
        expected = guarded.snapshot()
        original_verify = guarded._verify_path
        calls = []

        def swap_before_commit():
            calls.append(1)
            if len(calls) == 3:
                moved = self.root / "tx-parent-moved"
                parent.rename(moved)
                parent.mkdir(mode=0o700)
                target = parent / "state.sqlite3"
                target.write_bytes((moved / "state.sqlite3").read_bytes())
                os.chmod(target, 0o600)
            original_verify()

        guarded._verify_path = swap_before_commit
        with self.assertRaises(RuntimeStateError):
            guarded.advance(expected=expected)

        receiver = UnixWakeEndpoint(self.root / "swap.sock", key=b"s" * 32)
        receiver.register()
        sender = receiver.sender_endpoint()
        receiver.path.unlink()
        substitute = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        substitute.bind(str(receiver.path))
        substitute.listen(1)
        with self.assertRaises(BrokerProtocolError):
            sender.send_wake(
                sequence=1,
                payload={"reason": "post_commit", "identity": {"db_generation": "g", "work_epoch": 1}},
            )
        substitute.close()
        receiver.path.unlink()
        receiver.close()

    def test_orphan_deadline_is_finite_and_only_unexpired(self):
        broker = self.broker()
        with self.assertRaises(RuntimeStateError):
            broker._earliest_claim_deadline({"events": [{"status": "claimed", "lease_deadline": float("nan")} ]})
        self.assertIsNone(
            broker._earliest_claim_deadline({"events": [{"status": "claimed", "lease_deadline": 19.0}]})
        )


if __name__ == "__main__":
    unittest.main()
