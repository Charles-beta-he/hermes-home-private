#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from taskpool_command_gateway import TaskpoolCommandGateway
from taskpool_event_outbox import (
    ConflictError,
    DurableTaskpoolEventOutbox,
    OutboxError,
)


class TaskpoolCommandGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.gateway = TaskpoolCommandGateway(
            self.root / "state" / "taskpool.sqlite3",
            allowed_root=self.root,
        )

    def tearDown(self) -> None:
        self.gateway.close()
        self.tempdir.cleanup()

    def command(self) -> dict:
        return {
            "schema": "taskpool.command.v1",
            "idempotency_key": "task-7:create:v1",
            "operation": "put",
            "task_id": "task-7",
            "expected_revision": 0,
            "state": {
                "frontmatter": {
                    "type": "task",
                    "title": "Build command gateway",
                    "status": "pending",
                    "priority": "P1",
                },
                "body": "# Build command gateway\n",
            },
            "projection": {"relative_path": "05-实践与项目/tasks/task-7.md"},
            "event": {
                "event_type": "taskpool.actionable.v1",
                "payload": {"reason": "task_created"},
            },
        }

    def test_put_commits_canonical_task_projection_intent_and_outbox_atomically(self):
        result = self.gateway.submit(self.command(), now=10.0)

        self.assertEqual(result["status"], "durably_admitted")
        self.assertEqual(result["task_id"], "task-7")
        self.assertEqual(result["revision"], 1)
        self.assertEqual(result["work_epoch"], 1)
        self.assertRegex(result["drain_token"], r"^task-7:1:[0-9a-f-]{36}:1$")
        self.assertEqual(result["drain_token_scope"], "admission_registered_not_broker_acked")
        self.assertRegex(result["event_id"], r"^[0-9a-f-]{36}$")

        snapshot = self.gateway.read_task("task-7")
        self.assertEqual(snapshot["revision"], 1)
        self.assertEqual(snapshot["state"], self.command()["state"])
        self.assertEqual(snapshot["projection"]["status"], "pending")
        self.assertEqual(
            snapshot["projection"]["relative_path"],
            "05-实践与项目/tasks/task-7.md",
        )

        outbox = self.gateway.outbox_status()
        self.assertEqual(outbox["counts"], {"pending": 1})
        self.assertEqual(outbox["events"][0]["event_id"], result["event_id"])
        self.assertEqual(outbox["events"][0]["task_id"], "task-7")

        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            task_revision = connection.execute(
                "SELECT revision FROM canonical_tasks WHERE task_id='task-7'"
            ).fetchone()[0]
            projection_revision = connection.execute(
                "SELECT revision FROM projection_intents WHERE task_id='task-7'"
            ).fetchone()[0]
            receipt_event = connection.execute(
                "SELECT event_id FROM command_receipts WHERE idempotency_key='task-7:create:v1'"
            ).fetchone()[0]
            epoch = connection.execute("SELECT epoch FROM gateway_work_epoch WHERE id=1").fetchone()[0]
            drain = connection.execute(
                "SELECT work_epoch,drain_token,broker_ack_status FROM command_drain_tokens WHERE idempotency_key='task-7:create:v1'"
            ).fetchone()
        self.assertEqual((task_revision, projection_revision, receipt_event), (1, 1, result["event_id"]))
        self.assertEqual(epoch, 1)
        self.assertEqual((drain[0], drain[1], drain[2]), (1, result["drain_token"], "registered_not_broker_acked"))

    def test_work_epoch_and_drain_token_advance_in_same_transaction_as_command(self):
        first = self.gateway.submit(self.command(), now=10.0)
        update = self.command()
        update["idempotency_key"] = "task-7:block:v2"
        update["expected_revision"] = 1
        update["state"] = {
            **update["state"],
            "frontmatter": {**update["state"]["frontmatter"], "status": "blocked"},
        }

        second = self.gateway.submit(update, now=11.0)

        self.assertEqual((first["work_epoch"], second["work_epoch"]), (1, 2))
        self.assertEqual((first["revision"], second["revision"]), (1, 2))
        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            self.assertEqual(connection.execute("SELECT epoch FROM gateway_work_epoch WHERE id=1").fetchone()[0], 2)
            tokens = connection.execute(
                "SELECT revision,event_id,work_epoch,drain_token,broker_ack_status FROM command_drain_tokens ORDER BY revision"
            ).fetchall()
        self.assertEqual([row[2] for row in tokens], [1, 2])
        self.assertEqual([row[1] for row in tokens], [first["event_id"], second["event_id"]])
        self.assertEqual([row[3] for row in tokens], [first["drain_token"], second["drain_token"]])
        self.assertEqual([row[4] for row in tokens], ["registered_not_broker_acked", "registered_not_broker_acked"])

    def test_exact_command_replay_returns_original_admission_without_new_rows(self):
        first = self.gateway.submit(self.command(), now=10.0)
        replay = self.gateway.submit(self.command(), now=999.0)

        self.assertEqual(replay, first)
        self.assertEqual(self.gateway.read_task("task-7")["revision"], 1)
        self.assertEqual(self.gateway.outbox_status()["counts"], {"pending": 1})
        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM projection_intents").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0], 1)

    def test_idempotency_key_semantic_drift_fails_closed_without_mutation(self):
        first = self.gateway.submit(self.command(), now=10.0)
        changed = self.command()
        changed["state"] = {
            **changed["state"],
            "frontmatter": {**changed["state"]["frontmatter"], "status": "blocked"},
        }

        with self.assertRaisesRegex(ConflictError, "different command"):
            self.gateway.submit(changed, now=11.0)

        self.assertEqual(self.gateway.read_task("task-7")["state"]["frontmatter"]["status"], "pending")
        self.assertEqual(self.gateway.outbox_status()["counts"], {"pending": 1})
        self.assertEqual(self.gateway.outbox_status()["events"][0]["event_id"], first["event_id"])

    def test_restart_reopens_extended_schema_and_replays_original_receipt(self):
        first = self.gateway.submit(self.command(), now=10.0)
        self.gateway.close()

        reopened = TaskpoolCommandGateway(
            self.root / "state" / "taskpool.sqlite3",
            allowed_root=self.root,
        )
        self.gateway = reopened
        replay = reopened.submit(self.command(), now=999.0)

        self.assertEqual(replay, first)
        self.assertEqual(reopened.read_task("task-7")["revision"], 1)
        self.assertEqual(reopened.outbox_status()["counts"], {"pending": 1})

    def test_outbox_insert_failure_rolls_back_task_projection_and_receipt(self):
        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            connection.execute(
                """CREATE TRIGGER injected_outbox_failure
                BEFORE INSERT ON outbox_events
                BEGIN SELECT RAISE(ABORT, 'injected outbox failure'); END"""
            )

        with self.assertRaisesRegex(sqlite3.IntegrityError, "injected outbox failure"):
            self.gateway.submit(self.command(), now=10.0)

        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            counts = tuple(
                connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in (
                    "canonical_tasks",
                    "projection_intents",
                    "outbox_events",
                    "command_receipts",
                )
            )
        self.assertEqual(counts, (0, 0, 0, 0))
        with self.assertRaises(KeyError):
            self.gateway.read_task("task-7")

    def test_compare_and_swap_update_advances_revision_once(self):
        first = self.gateway.submit(self.command(), now=10.0)
        update = self.command()
        update["idempotency_key"] = "task-7:block:v2"
        update["expected_revision"] = 1
        update["state"] = {
            **update["state"],
            "frontmatter": {**update["state"]["frontmatter"], "status": "blocked"},
        }
        update["event"] = {
            "event_type": "taskpool.actionable.v1",
            "payload": {"reason": "task_blocked"},
        }

        second = self.gateway.submit(update, now=11.0)

        self.assertEqual((first["revision"], second["revision"]), (1, 2))
        self.assertEqual(self.gateway.read_task("task-7")["state"]["frontmatter"]["status"], "blocked")
        self.assertEqual(self.gateway.read_task("task-7")["projection"]["revision"], 2)
        self.assertEqual(self.gateway.outbox_status()["counts"], {"pending": 2})
        self.assertFalse((self.root / "05-实践与项目/tasks/task-7.md").exists())

    def test_stale_revision_fails_without_outbox_or_projection_growth(self):
        self.gateway.submit(self.command(), now=10.0)
        stale = self.command()
        stale["idempotency_key"] = "task-7:stale:v2"
        stale["state"] = {
            **stale["state"],
            "frontmatter": {**stale["state"]["frontmatter"], "status": "blocked"},
        }

        with self.assertRaisesRegex(Exception, "revision conflict"):
            self.gateway.submit(stale, now=11.0)

        self.assertEqual(self.gateway.read_task("task-7")["revision"], 1)
        self.assertEqual(self.gateway.outbox_status()["counts"], {"pending": 1})
        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM projection_intents").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0], 1)

    def test_nonfinite_admission_time_is_rejected_before_any_mutation(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(Exception, "finite"):
                    self.gateway.submit(self.command(), now=value)
        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM canonical_tasks").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM outbox_events").fetchone()[0], 0)

    def test_gateway_rejects_state_shape_that_authoritative_reader_cannot_load(self):
        incompatible = self.command()
        incompatible["state"] = {"title": "shape accepted by generic dict check only"}

        with self.assertRaisesRegex(Exception, "state must contain exact frontmatter/body schema"):
            self.gateway.submit(incompatible, now=10.0)

        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM canonical_tasks").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM projection_intents").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM outbox_events").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0], 0)

    def test_projection_admission_derives_replay_identity_and_current_revision(self):
        state = {
            "frontmatter": {"type": "task", "status": "pending"},
            "body": "# Task - Seven\n",
        }
        first = self.gateway.admit_projection(
            task_id="task-7",
            state=state,
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task", "status": "pending"},
            now=10.0,
        )
        replay = self.gateway.admit_projection(
            task_id="task-7",
            state=state,
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task", "status": "pending"},
            now=999.0,
        )
        changed = self.gateway.admit_projection(
            task_id="task-7",
            state={**state, "frontmatter": {"type": "task", "status": "claimed"}},
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task", "status": "claimed"},
            now=11.0,
        )

        self.assertEqual(replay, first)
        self.assertEqual((first["revision"], changed["revision"]), (1, 2))
        self.assertEqual(self.gateway.read_task("task-7")["state"]["frontmatter"]["status"], "claimed")
        self.assertEqual(self.gateway.outbox_status()["counts"], {"pending": 2})

    def test_projection_admission_reentry_after_intervening_revision_is_new_transition(self):
        pending_state = {
            "frontmatter": {"type": "task", "status": "pending"},
            "body": "# Task - Seven\n",
        }
        claimed_state = {
            "frontmatter": {"type": "task", "status": "claimed"},
            "body": "# Task - Seven\n",
        }
        first = self.gateway.admit_projection(
            task_id="task-7",
            state=pending_state,
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task", "status": "pending"},
            now=10.0,
        )
        second = self.gateway.admit_projection(
            task_id="task-7",
            state=claimed_state,
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task", "status": "claimed"},
            now=11.0,
        )
        third = self.gateway.admit_projection(
            task_id="task-7",
            state=pending_state,
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task", "status": "pending"},
            now=12.0,
        )

        self.assertEqual(
            (first["revision"], second["revision"], third["revision"]),
            (1, 2, 3),
        )
        self.assertEqual(self.gateway.read_task("task-7")["state"], pending_state)
        self.assertEqual(self.gateway.outbox_status()["counts"], {"pending": 3})

    def test_projection_publish_requires_exact_publisher_receipt_and_byte_readback_before_marking_published(self):
        result = self.gateway.admit_projection(
            task_id="task-7",
            state={"frontmatter": {"status": "pending"}, "body": "# Seven\n"},
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task"},
            now=10.0,
        )
        canonical = self.gateway.read_task("task-7")
        expected_bytes = b"---\nstatus: pending\n---\n# Seven\n"
        expected_projection_sha256 = hashlib.sha256(expected_bytes).hexdigest()

        with self.assertRaisesRegex(Exception, "publisher receipt"):
            self.gateway.publish_projection(
                task_id="task-7",
                revision=result["revision"],
                canonical_sha256=canonical["state_sha256"],
                publisher=lambda: None,
                projection_reader=lambda: expected_bytes,
            )
        self.assertEqual(self.gateway.read_task("task-7")["projection"]["status"], "pending")

        def lying_publisher() -> dict:
            return {
                "status": "projection_written",
                "task_id": "task-7",
                "revision": result["revision"],
                "canonical_sha256": canonical["state_sha256"],
                "relative_path": "tasks/task-7.md",
                "projection_sha256": expected_projection_sha256,
            }

        with self.assertRaisesRegex(Exception, "projection byte readback"):
            self.gateway.publish_projection(
                task_id="task-7",
                revision=result["revision"],
                canonical_sha256=canonical["state_sha256"],
                publisher=lying_publisher,
                projection_reader=lambda: b"wrong bytes",
            )
        self.assertEqual(self.gateway.read_task("task-7")["projection"]["status"], "pending")

    def test_projection_publish_is_revision_and_digest_fenced_and_idempotent(self):
        result = self.gateway.admit_projection(
            task_id="task-7",
            state={"frontmatter": {"status": "pending"}, "body": "# Seven\n"},
            relative_path="tasks/task-7.md",
            event_payload={"reason": "save_task"},
            now=10.0,
        )
        canonical = self.gateway.read_task("task-7")
        self.assertEqual(canonical["projection"]["status"], "pending")

        writes: list[str] = []
        projection_bytes = b"published projection bytes"
        projection_sha256 = hashlib.sha256(projection_bytes).hexdigest()

        def receipt(label: str) -> dict:
            writes.append(label)
            return {
                "status": "projection_written",
                "task_id": "task-7",
                "revision": result["revision"],
                "canonical_sha256": canonical["state_sha256"],
                "relative_path": "tasks/task-7.md",
                "projection_sha256": projection_sha256,
            }

        published = self.gateway.publish_projection(
            task_id="task-7",
            revision=result["revision"],
            canonical_sha256=canonical["state_sha256"],
            publisher=lambda: receipt("published"),
            projection_reader=lambda: projection_bytes,
        )
        replay = self.gateway.publish_projection(
            task_id="task-7",
            revision=result["revision"],
            canonical_sha256=canonical["state_sha256"],
            publisher=lambda: receipt("unexpected-replay-write"),
            projection_reader=lambda: projection_bytes,
        )

        self.assertEqual(published, replay)
        self.assertEqual(writes, ["published"])
        projection = self.gateway.read_task("task-7")["projection"]
        self.assertEqual(projection["status"], "published")
        self.assertEqual(projection["projection_sha256"], projection_sha256)
        with self.assertRaisesRegex(Exception, "projection byte readback mismatch"):
            self.gateway.publish_projection(
                task_id="task-7",
                revision=result["revision"],
                canonical_sha256=canonical["state_sha256"],
                publisher=lambda: receipt("unexpected-corrupt-replay-write"),
                projection_reader=lambda: b"unexpected-replay-read",
            )
        with self.assertRaisesRegex(Exception, "projection intent conflict"):
            self.gateway.publish_projection(
                task_id="task-7",
                revision=result["revision"],
                canonical_sha256="0" * 64,
                publisher=lambda: receipt("unexpected-conflict-write"),
                projection_reader=lambda: projection_bytes,
            )
        self.assertEqual(writes, ["published"])

    def test_projection_publish_retries_after_side_effect_before_marking_published(self):
        admitted = self.gateway.submit(self.command(), now=10.0)
        canonical = self.gateway.read_task("task-7")
        writes: list[str] = []
        projection_bytes = b"retry projection bytes"
        projection_sha256 = hashlib.sha256(projection_bytes).hexdigest()

        def receipt() -> dict:
            return {
                "status": "projection_written",
                "task_id": "task-7",
                "revision": admitted["revision"],
                "canonical_sha256": canonical["state_sha256"],
                "relative_path": "05-实践与项目/tasks/task-7.md",
                "projection_sha256": projection_sha256,
            }

        def write_then_crash() -> dict:
            writes.append("write")
            raise RuntimeError("crash after projection write")

        def write_receipt() -> dict:
            writes.append("write")
            return receipt()

        with self.assertRaisesRegex(RuntimeError, "crash after projection write"):
            self.gateway.publish_projection(
                task_id="task-7",
                revision=admitted["revision"],
                canonical_sha256=canonical["state_sha256"],
                publisher=write_then_crash,
                projection_reader=lambda: projection_bytes,
            )
        self.assertEqual(self.gateway.read_task("task-7")["projection"]["status"], "pending")

        self.gateway.publish_projection(
            task_id="task-7",
            revision=admitted["revision"],
            canonical_sha256=canonical["state_sha256"],
            publisher=write_receipt,
            projection_reader=lambda: projection_bytes,
        )
        self.assertEqual(writes, ["write", "write"])
        self.assertEqual(self.gateway.read_task("task-7")["projection"]["status"], "published")

    def test_concurrent_exact_admission_commits_once_and_replays_one_receipt(self):
        db_path = self.root / "state" / "taskpool.sqlite3"
        second = TaskpoolCommandGateway(db_path, allowed_root=self.root)
        barrier = threading.Barrier(2)
        results: list[dict] = []
        errors: list[Exception] = []

        def submit(gateway: TaskpoolCommandGateway) -> None:
            try:
                barrier.wait(timeout=2)
                results.append(gateway.submit(self.command(), now=10.0))
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=submit, args=(gateway,))
            for gateway in (self.gateway, second)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        second.close()

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])
        with sqlite3.connect(db_path) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM canonical_tasks").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM command_receipts").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM outbox_events").fetchone()[0], 1)

    def test_gateway_schema_rejects_unknown_objects_and_definition_drift(self):
        db_path = self.root / "state" / "taskpool.sqlite3"
        self.gateway.close()
        with sqlite3.connect(db_path) as connection:
            connection.execute("CREATE TABLE hostile_extra(value TEXT)")
            connection.commit()
        with self.assertRaisesRegex(OutboxError, "incompatible schema object inventory"):
            TaskpoolCommandGateway(db_path, allowed_root=self.root)

        drift_path = self.root / "drift" / "taskpool.sqlite3"
        drift_gateway = TaskpoolCommandGateway(drift_path, allowed_root=self.root)
        drift_gateway.close()
        with sqlite3.connect(drift_path) as connection:
            connection.execute("DROP TABLE command_receipts")
            connection.execute(
                "CREATE TABLE command_receipts("
                "idempotency_key TEXT PRIMARY KEY,command_sha256 TEXT,task_id TEXT,"
                "admitted_revision INTEGER,admitted_at REAL,result_json TEXT)"
            )
            connection.commit()
        with self.assertRaisesRegex(OutboxError, "incompatible schema"):
            TaskpoolCommandGateway(drift_path, allowed_root=self.root)

    def test_baseline_schema_upgrade_is_explicit_and_profiles_do_not_cross_accept(self):
        baseline_path = self.root / "baseline" / "outbox.sqlite3"
        DurableTaskpoolEventOutbox(baseline_path, allowed_root=self.root)
        upgraded = TaskpoolCommandGateway(baseline_path, allowed_root=self.root)
        upgraded.close()
        with self.assertRaisesRegex(OutboxError, "incompatible schema object inventory"):
            DurableTaskpoolEventOutbox(baseline_path, allowed_root=self.root)

        gateway_path = self.root / "state" / "taskpool.sqlite3"
        self.gateway.close()
        with self.assertRaisesRegex(OutboxError, "incompatible schema object inventory"):
            DurableTaskpoolEventOutbox(gateway_path, allowed_root=self.root)

    def test_canonical_row_tampering_is_rejected_on_read_and_iteration(self):
        self.gateway.submit(self.command(), now=10.0)
        with sqlite3.connect(self.root / "state" / "taskpool.sqlite3") as connection:
            connection.execute(
                "UPDATE canonical_tasks SET state_json=? WHERE task_id='task-7'",
                ('{"status":"tampered"}',),
            )
            connection.commit()

        with self.assertRaisesRegex(RuntimeError, "canonical state digest mismatch"):
            self.gateway.read_task("task-7")
        with self.assertRaisesRegex(RuntimeError, "canonical state digest mismatch"):
            self.gateway.iter_tasks()


if __name__ == "__main__":
    unittest.main()
