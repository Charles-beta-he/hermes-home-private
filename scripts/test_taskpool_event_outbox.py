#!/usr/bin/env python3
"""Contract tests for the pure local durable taskpool event outbox."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from taskpool_event_outbox import (
    ALLOWED_EVENT_TYPES,
    ConflictError,
    DurableTaskpoolEventOutbox,
    PathSecurityError,
    StaleClaimError,
    ValidationError,
)


EVENT_TYPE = "taskpool.actionable.v1"


def _claim_worker(db_path: str, root: str, gate, output) -> None:
    outbox = DurableTaskpoolEventOutbox(db_path, allowed_root=root)
    gate.wait(10)
    output.put(outbox.claim(lease_seconds=30, now=20.0))


def _crash_after_claim(db_path: str, root: str, connection) -> None:
    outbox = DurableTaskpoolEventOutbox(db_path, allowed_root=root)
    connection.send(outbox.claim(lease_seconds=2, now=20.0))
    connection.close()
    os._exit(17)


class DurableTaskpoolEventOutboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.db = self.root / "state" / "outbox.sqlite3"
        self.outbox = DurableTaskpoolEventOutbox(self.db, allowed_root=self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def enqueue(self, *, key: str = "task-7:ready", payload=None, now: float = 10.0):
        return self.outbox.enqueue(
            idempotency_key=key,
            event_type=EVENT_TYPE,
            task_id="task-7",
            payload={"reason": "ready"} if payload is None else payload,
            now=now,
        )

    def test_schema_version_and_required_tables_are_durable(self) -> None:
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(outbox_events)")
            }
        self.assertTrue({"outbox_events", "attempt_receipts"}.issubset(tables))
        self.assertTrue(
            {
                "schema_version",
                "event_id",
                "idempotency_key",
                "event_type",
                "task_id",
                "payload_sha256",
                "status",
                "claim_token_sha256",
                "generation",
                "lease_deadline",
                "attempt_count",
                "completion_receipt_id",
                "created_at",
                "updated_at",
                "completed_at",
            }.issubset(columns)
        )

    def test_event_types_and_json_scalars_are_strict(self) -> None:
        self.assertEqual(ALLOWED_EVENT_TYPES, frozenset({EVENT_TYPE}))
        invalid = [
            {"value": math.nan},
            {"value": math.inf},
            {1: "non-string-key"},
            {"value": (1, 2)},
        ]
        for index, payload in enumerate(invalid):
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                self.outbox.enqueue(
                    idempotency_key=f"invalid-{index}",
                    event_type=EVENT_TYPE,
                    task_id="task-7",
                    payload=payload,
                    now=10.0,
                )
        with self.assertRaises(ValidationError):
            self.outbox.enqueue(
                idempotency_key="evidence",
                event_type="taskpool.evidence.v1",
                task_id="task-7",
                payload={},
                now=10.0,
            )
        for invalid_lease in (True, 0, -1, math.nan, math.inf):
            with self.subTest(lease=invalid_lease), self.assertRaises(ValidationError):
                self.outbox.claim(lease_seconds=invalid_lease, now=20.0)

    def test_exact_enqueue_replay_returns_original_row(self) -> None:
        first = self.enqueue(payload={"b": 2, "a": [True, None, 1.5]})
        replay = self.enqueue(payload={"a": [True, None, 1.5], "b": 2}, now=999.0)
        self.assertEqual(replay, first)
        self.assertEqual(replay["status"], "pending")

    def test_semantic_drift_under_same_key_fails_closed(self) -> None:
        self.enqueue()
        changed_requests = [
            ("taskpool.invalid.v1", "task-7", {"reason": "ready"}),
            (EVENT_TYPE, "task-8", {"reason": "ready"}),
            (EVENT_TYPE, "task-7", {"reason": "changed"}),
        ]
        for event_type, task_id, payload in changed_requests:
            with self.subTest(event_type=event_type, task_id=task_id), self.assertRaises(
                ConflictError
            ):
                self.outbox.enqueue(
                    idempotency_key="task-7:ready",
                    event_type=event_type,
                    task_id=task_id,
                    payload=payload,
                    now=11.0,
                )

    def test_pending_claim_and_fenced_completion(self) -> None:
        event = self.enqueue()
        claim = self.outbox.claim(lease_seconds=30, now=20.0)
        self.assertEqual(claim["event_id"], event["event_id"])
        self.assertEqual(claim["generation"], 1)
        self.assertEqual(claim["attempt_count"], 1)
        self.assertIsInstance(claim["claim_token"], str)
        self.assertGreaterEqual(len(claim["claim_token"]), 32)

        receipt = self.outbox.complete(
            event_id=event["event_id"],
            claim_token=claim["claim_token"],
            generation=claim["generation"],
            result={"effect_receipt_id": "effect-1"},
            now=21.0,
        )
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(self.outbox.claim(lease_seconds=30, now=22.0), None)
        status = self.outbox.status()
        self.assertEqual(status["counts"], {"completed": 1})
        self.assertNotIn(claim["claim_token"], json.dumps(status, sort_keys=True))

    def test_database_persists_only_token_verifier(self) -> None:
        event = self.enqueue()
        claim = self.outbox.claim(lease_seconds=30, now=20.0)
        with sqlite3.connect(self.db) as connection:
            stored = connection.execute(
                "SELECT claim_token_sha256 FROM outbox_events WHERE event_id = ?",
                (event["event_id"],),
            ).fetchone()[0]
        self.assertEqual(
            stored, hashlib.sha256(claim["claim_token"].encode("utf-8")).hexdigest()
        )
        self.assertNotEqual(stored, claim["claim_token"])

    def test_expired_lease_reclaim_increments_generation_and_fences_stale_owner(self) -> None:
        event = self.enqueue()
        old = self.outbox.claim(lease_seconds=2, now=20.0)
        new = self.outbox.claim(lease_seconds=5, now=23.0)
        self.assertEqual(new["event_id"], event["event_id"])
        self.assertEqual(new["generation"], 2)
        self.assertEqual(new["attempt_count"], 2)
        with self.assertRaises(StaleClaimError):
            self.outbox.complete(
                event_id=event["event_id"],
                claim_token=old["claim_token"],
                generation=old["generation"],
                result={},
                now=23.5,
            )
        receipt = self.outbox.complete(
            event_id=event["event_id"],
            claim_token=new["claim_token"],
            generation=new["generation"],
            result={"ok": True},
            now=24.0,
        )
        self.assertEqual(receipt["generation"], 2)
        self.assertEqual(
            [item["outcome"] for item in self.outbox.status()["attempt_receipts"]],
            ["expired", "completed"],
        )

    def test_exact_lease_deadline_is_expired_and_cannot_complete(self) -> None:
        event = self.enqueue()
        old = self.outbox.claim(lease_seconds=2, now=20.0)
        with self.assertRaises(StaleClaimError):
            self.outbox.complete(
                event_id=event["event_id"],
                claim_token=old["claim_token"],
                generation=old["generation"],
                result={},
                now=22.0,
            )
        reclaimed = self.outbox.claim(lease_seconds=3, now=22.0)
        self.assertEqual(reclaimed["generation"], 2)

    def test_live_owner_can_renew_but_expired_or_stale_owner_cannot(self) -> None:
        event = self.enqueue()
        claim = self.outbox.claim(lease_seconds=2, now=20.0)
        renewed = self.outbox.renew(
            event_id=event["event_id"],
            claim_token=claim["claim_token"],
            generation=claim["generation"],
            lease_seconds=5,
            now=21.0,
        )
        self.assertEqual(renewed["lease_deadline"], 26.0)
        with self.assertRaises(StaleClaimError):
            self.outbox.renew(
                event_id=event["event_id"],
                claim_token=claim["claim_token"],
                generation=claim["generation"],
                lease_seconds=5,
                now=26.0,
            )

    def test_retryable_failure_records_receipt_and_obeys_attempt_budget(self) -> None:
        event = self.enqueue()
        first = self.outbox.claim(lease_seconds=5, now=20.0)
        retry = self.outbox.fail(
            event_id=event["event_id"],
            claim_token=first["claim_token"],
            generation=1,
            error={"code": "temporary"},
            retryable=True,
            max_attempts=2,
            now=21.0,
        )
        self.assertEqual(retry["status"], "pending")
        second = self.outbox.claim(lease_seconds=5, now=22.0)
        exhausted = self.outbox.fail(
            event_id=event["event_id"],
            claim_token=second["claim_token"],
            generation=2,
            error={"code": "temporary-again"},
            retryable=True,
            max_attempts=2,
            now=23.0,
        )
        self.assertEqual(exhausted["status"], "failed")
        self.assertEqual(self.outbox.claim(lease_seconds=5, now=24.0), None)
        status = self.outbox.status()
        self.assertEqual(status["counts"], {"failed": 1})
        self.assertEqual(
            [receipt["outcome"] for receipt in status["attempt_receipts"]],
            ["retryable_failure", "attempts_exhausted"],
        )
        for invalid_max in (True, 0, -1, 1.5):
            with self.subTest(max_attempts=invalid_max), self.assertRaises(
                ValidationError
            ):
                self.outbox.fail(
                    event_id=event["event_id"],
                    claim_token="opaque",
                    generation=2,
                    error={},
                    retryable=True,
                    max_attempts=invalid_max,
                    now=25.0,
                )

    def test_status_is_read_only(self) -> None:
        self.enqueue()
        before = self.db.read_bytes()
        before_stat = self.db.stat()
        first = self.outbox.status()
        second = self.outbox.status()
        after_stat = self.db.stat()
        self.assertEqual(first, second)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual(after_stat.st_mtime_ns, before_stat.st_mtime_ns)

    def test_readonly_uri_metacharacters_do_not_redirect_database(self) -> None:
        victim = self.root / "victim"
        configured = self.root / "victim?ignored"
        other = DurableTaskpoolEventOutbox(victim, allowed_root=self.root)
        other.enqueue(
            idempotency_key="victim-key", event_type=EVENT_TYPE,
            task_id="victim-task", payload={}, now=1.0,
        )
        configured_box = DurableTaskpoolEventOutbox(configured, allowed_root=self.root)
        configured_box.enqueue(
            idempotency_key="configured-key", event_type=EVENT_TYPE,
            task_id="configured-task", payload={}, now=1.0,
        )
        self.assertEqual(
            configured_box.status()["events"][0]["task_id"], "configured-task"
        )

    def test_connection_rejects_database_substitution_after_path_check(self) -> None:
        original = self.root / "original.sqlite3"
        substitute = self.root / "substitute.sqlite3"
        box = DurableTaskpoolEventOutbox(original, allowed_root=self.root)
        other = DurableTaskpoolEventOutbox(substitute, allowed_root=self.root)
        box.enqueue(idempotency_key="a", event_type=EVENT_TYPE, task_id="A", payload={}, now=1)
        other.enqueue(idempotency_key="b", event_type=EVENT_TYPE, task_id="B", payload={}, now=1)
        real_verify = box._verify_path
        swapped = False

        def verify_then_swap():
            nonlocal swapped
            real_verify()
            if not swapped:
                parked = self.root / "parked.sqlite3"
                original.rename(parked)
                substitute.rename(original)
                swapped = True

        box._verify_path = verify_then_swap
        with self.assertRaises(PathSecurityError):
            box.status()

    def test_real_processes_produce_exactly_one_claim(self) -> None:
        self.enqueue()
        context = multiprocessing.get_context("spawn")
        gate = context.Event()
        output = context.Queue()
        workers = [
            context.Process(
                target=_claim_worker,
                args=(str(self.db), str(self.root), gate, output),
            )
            for _ in range(4)
        ]
        for worker in workers:
            worker.start()
        gate.set()
        results = [output.get(timeout=15) for _ in workers]
        for worker in workers:
            worker.join(15)
            self.assertFalse(worker.is_alive())
            self.assertEqual(worker.exitcode, 0)
        claims = [result for result in results if result is not None]
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["generation"], 1)

    def test_crashed_owner_is_reclaimed_after_lease_expiry(self) -> None:
        self.enqueue()
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe(duplex=False)
        worker = context.Process(
            target=_crash_after_claim,
            args=(str(self.db), str(self.root), child),
        )
        worker.start()
        self.assertTrue(parent.poll(15), "crash worker did not publish its claim")
        old_claim = parent.recv()
        worker.join(15)
        self.assertFalse(worker.is_alive())
        self.assertEqual(worker.exitcode, 17)
        self.assertEqual(self.outbox.claim(lease_seconds=3, now=21.0), None)
        reclaimed = self.outbox.claim(lease_seconds=3, now=23.0)
        self.assertEqual(reclaimed["generation"], old_claim["generation"] + 1)
        self.assertNotEqual(reclaimed["claim_token"], old_claim["claim_token"])

    def test_symlink_and_canonical_escape_paths_fail_closed(self) -> None:
        outside = self.root.parent / f"{self.root.name}-outside"
        outside.mkdir()
        self.addCleanup(lambda: outside.rmdir() if outside.exists() else None)
        linked_parent = self.root / "linked"
        linked_parent.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(PathSecurityError):
            DurableTaskpoolEventOutbox(
                linked_parent / "outbox.sqlite3", allowed_root=self.root
            )
        with self.assertRaises(PathSecurityError):
            DurableTaskpoolEventOutbox(
                outside / "outbox.sqlite3", allowed_root=self.root
            )

        victim = self.root / "victim.sqlite3"
        victim.write_bytes(b"sentinel")
        symlink_db = self.root / "symlink.sqlite3"
        symlink_db.symlink_to(victim)
        with self.assertRaises(PathSecurityError):
            DurableTaskpoolEventOutbox(symlink_db, allowed_root=self.root)
        self.assertEqual(victim.read_bytes(), b"sentinel")

    def test_symlink_allowed_root_fails_closed(self) -> None:
        real_root = self.root / "real-root"
        real_root.mkdir()
        linked_root = self.root / "linked-root"
        linked_root.symlink_to(real_root, target_is_directory=True)
        with self.assertRaises(PathSecurityError):
            DurableTaskpoolEventOutbox(
                linked_root / "outbox.sqlite3", allowed_root=linked_root
            )

    def test_existing_incompatible_schema_is_not_blessed(self) -> None:
        broken = self.root / "broken.sqlite3"
        with sqlite3.connect(broken) as connection:
            connection.execute("CREATE TABLE outbox_events (event_id TEXT PRIMARY KEY)")
            connection.commit()
        with self.assertRaisesRegex(Exception, "incompatible|schema"):
            DurableTaskpoolEventOutbox(broken, allowed_root=self.root)
        with sqlite3.connect(broken) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 0)

    def test_constraint_free_versioned_schema_is_rejected(self) -> None:
        broken = self.root / "constraint-free.sqlite3"
        with sqlite3.connect(broken) as connection:
            connection.executescript(
                """
                CREATE TABLE outbox_events (
                    schema_version,event_id,idempotency_key,event_type,task_id,
                    payload_json,payload_sha256,created_at,status,claim_token_sha256,
                    generation,lease_deadline,attempt_count,completion_receipt_id,
                    updated_at,completed_at
                );
                CREATE TABLE attempt_receipts (
                    receipt_id,event_id,generation,outcome,detail_json,
                    detail_sha256,created_at
                );
                PRAGMA user_version=1;
                """
            )
        with self.assertRaisesRegex(Exception, "incompatible schema"):
            DurableTaskpoolEventOutbox(broken, allowed_root=self.root)

    def test_extra_sqlite_master_object_is_rejected(self) -> None:
        with sqlite3.connect(self.db) as connection:
            connection.execute("CREATE TABLE unexpected_extension(value TEXT)")
            connection.commit()
        with self.assertRaisesRegex(Exception, "incompatible schema"):
            DurableTaskpoolEventOutbox(self.db, allowed_root=self.root)

    def test_sqlite_master_type_table_and_internal_objects_are_canonical(self) -> None:
        class InternalObjectDriftConnection:
            def __init__(self, connection):
                self.connection = connection

            def execute(self, sql, parameters=()):
                if "sqlite_master" in sql and "tbl_name" in sql:
                    return self.connection.execute(
                        """
                        SELECT type,name,
                               CASE WHEN name='sqlite_autoindex_outbox_events_1'
                                    THEN 'wrong_table' ELSE tbl_name END,
                               sql
                        FROM sqlite_master ORDER BY type,name
                        """
                    )
                return self.connection.execute(sql, parameters)

        with sqlite3.connect(self.db) as connection:
            with self.assertRaisesRegex(Exception, "incompatible schema"):
                DurableTaskpoolEventOutbox._validate_schema(
                    InternalObjectDriftConnection(connection)
                )

    def test_completed_readbacks_are_validated_inside_write_transaction(self) -> None:
        validation_transaction_states = []

        class TransactionInspectingOutbox(DurableTaskpoolEventOutbox):
            def _validated_event_dict(self, connection, event):
                validation_transaction_states.append(connection.in_transaction)
                return super()._validated_event_dict(connection, event)

        outbox = TransactionInspectingOutbox(self.db, allowed_root=self.root)
        first = outbox.enqueue(
            event_type=EVENT_TYPE,
            task_id="tx-validation-task",
            payload={"step": 1},
            idempotency_key="tx-validation-key",
            now=1.0,
        )
        claim = outbox.claim(lease_seconds=10.0, now=2.0)
        if claim is None:
            self.fail("expected a claim")
        self.assertEqual(claim["event_id"], first["event_id"])
        outbox.complete(
            event_id=claim["event_id"],
            generation=claim["generation"],
            claim_token=claim["claim_token"],
            result={"ok": True},
            now=3.0,
        )
        outbox.complete(
            event_id=claim["event_id"],
            generation=claim["generation"],
            claim_token=claim["claim_token"],
            result={"ok": True},
            now=3.5,
        )
        outbox.enqueue(
            event_type=EVENT_TYPE,
            task_id="tx-validation-task",
            payload={"step": 1},
            idempotency_key="tx-validation-key",
            now=4.0,
        )
        self.assertEqual(validation_transaction_states, [True, True, True])

    def test_enqueue_completed_replay_validates_completion_receipt_link(self) -> None:
        first = self.enqueue(key="enqueue-first", now=10.0)
        first_claim = self.outbox.claim(lease_seconds=10, now=20.0)
        self.outbox.complete(
            event_id=first["event_id"], claim_token=first_claim["claim_token"],
            generation=first_claim["generation"], result={"event": 1}, now=21.0,
        )
        second = self.enqueue(key="enqueue-second", now=22.0)
        second_claim = self.outbox.claim(lease_seconds=10, now=23.0)
        self.outbox.complete(
            event_id=second["event_id"], claim_token=second_claim["claim_token"],
            generation=second_claim["generation"], result={"event": 2}, now=24.0,
        )
        with sqlite3.connect(self.db) as connection:
            second_receipt_id = connection.execute(
                "SELECT completion_receipt_id FROM outbox_events WHERE event_id=?",
                (second["event_id"],),
            ).fetchone()[0]
            connection.execute(
                "UPDATE outbox_events SET completion_receipt_id=? WHERE event_id=?",
                (second_receipt_id, first["event_id"]),
            )
            connection.commit()
        with self.assertRaisesRegex(Exception, "completion receipt integrity"):
            self.enqueue(key="enqueue-first", now=25.0)

    def test_completed_replay_preserves_exact_canonical_json_type(self) -> None:
        event = self.enqueue()
        claim = self.outbox.claim(lease_seconds=10, now=20.0)
        self.outbox.complete(
            event_id=event["event_id"], claim_token=claim["claim_token"],
            generation=claim["generation"], result=True, now=21.0,
        )
        with self.assertRaisesRegex(StaleClaimError, "immutable receipt"):
            self.outbox.complete(
                event_id=event["event_id"], claim_token=claim["claim_token"],
                generation=claim["generation"], result=1, now=22.0,
            )

    def test_completion_receipt_pointer_must_match_event_generation_and_outcome(self) -> None:
        first = self.enqueue(key="first", now=10.0)
        first_claim = self.outbox.claim(lease_seconds=10, now=20.0)
        self.outbox.complete(
            event_id=first["event_id"], claim_token=first_claim["claim_token"],
            generation=first_claim["generation"], result={"event": 1}, now=21.0,
        )
        second = self.enqueue(key="second", now=22.0)
        second_claim = self.outbox.claim(lease_seconds=10, now=23.0)
        self.outbox.complete(
            event_id=second["event_id"], claim_token=second_claim["claim_token"],
            generation=second_claim["generation"], result={"event": 2}, now=24.0,
        )
        with sqlite3.connect(self.db) as connection:
            second_receipt_id = connection.execute(
                "SELECT completion_receipt_id FROM outbox_events WHERE event_id=?",
                (second["event_id"],),
            ).fetchone()[0]
            connection.execute(
                "UPDATE outbox_events SET completion_receipt_id=? WHERE event_id=?",
                (second_receipt_id, first["event_id"]),
            )
            connection.commit()
        with self.assertRaisesRegex(Exception, "receipt.*integrity|immutable receipt"):
            self.outbox.status()
        with self.assertRaisesRegex(Exception, "receipt.*integrity|immutable receipt"):
            self.outbox.complete(
                event_id=first["event_id"], claim_token=first_claim["claim_token"],
                generation=first_claim["generation"], result={"event": 1}, now=25.0,
            )

    def test_payload_and_receipt_digest_corruption_fail_closed(self) -> None:
        event = self.enqueue()
        claim = self.outbox.claim(lease_seconds=10, now=20.0)
        self.outbox.complete(
            event_id=event["event_id"], claim_token=claim["claim_token"],
            generation=claim["generation"], result={"ok": True}, now=21.0,
        )
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                "UPDATE attempt_receipts SET outcome='expired' WHERE outcome='completed'"
            )
            connection.commit()
        with self.assertRaisesRegex(Exception, "receipt.*integrity"):
            self.outbox.status()
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                "UPDATE attempt_receipts SET outcome='completed', detail_json=?",
                ('{"ok":false}',),
            )
            connection.commit()
        with self.assertRaisesRegex(Exception, "receipt.*integrity"):
            self.outbox.status()
        with self.assertRaisesRegex(Exception, "receipt.*integrity"):
            self.outbox.complete(
                event_id=event["event_id"], claim_token=claim["claim_token"],
                generation=claim["generation"], result={"ok": True}, now=22.0,
            )

        payload_db = self.root / "payload.sqlite3"
        payload_box = DurableTaskpoolEventOutbox(payload_db, allowed_root=self.root)
        payload_box.enqueue(
            idempotency_key="payload", event_type=EVENT_TYPE,
            task_id="task", payload={"ok": True}, now=1.0,
        )
        with sqlite3.connect(payload_db) as connection:
            connection.execute("UPDATE outbox_events SET payload_json='{}'")
            connection.commit()
        with self.assertRaisesRegex(Exception, "event payload integrity"):
            payload_box.status()

    def test_database_path_replacement_after_open_fails_closed(self) -> None:
        self.enqueue()
        original = self.db.with_suffix(".original")
        self.db.rename(original)
        self.db.symlink_to(original)
        with self.assertRaises(PathSecurityError):
            self.outbox.status()
        with self.assertRaises(PathSecurityError):
            self.outbox.claim(lease_seconds=3, now=20.0)


if __name__ == "__main__":
    unittest.main()
