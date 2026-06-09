#!/usr/bin/env python3
import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPT_DIR / "external_adapter_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("external_adapter_harness", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harness = load_module()


class ExternalAdapterHarnessTests(unittest.TestCase):
    def test_harness_mode_defaults_apply_with_shadow_off_escape(self):
        old_mode = os.environ.pop("HERMES_EXTERNAL_ADAPTER_HARNESS_MODE", None)
        old_short = os.environ.pop("HERMES_EXTERNAL_ADAPTER_HARNESS", None)
        try:
            self.assertEqual(harness.harness_mode(), "apply")
            os.environ["HERMES_EXTERNAL_ADAPTER_HARNESS_MODE"] = "shadow"
            self.assertEqual(harness.harness_mode(), "shadow")
            os.environ["HERMES_EXTERNAL_ADAPTER_HARNESS_MODE"] = "off"
            self.assertEqual(harness.harness_mode(), "off")
        finally:
            if old_mode is not None:
                os.environ["HERMES_EXTERNAL_ADAPTER_HARNESS_MODE"] = old_mode
            else:
                os.environ.pop("HERMES_EXTERNAL_ADAPTER_HARNESS_MODE", None)
            if old_short is not None:
                os.environ["HERMES_EXTERNAL_ADAPTER_HARNESS"] = old_short
            else:
                os.environ.pop("HERMES_EXTERNAL_ADAPTER_HARNESS", None)

    def test_intent_and_authorization_are_digest_bound(self):
        with tempfile.TemporaryDirectory() as td:
            intent = harness.build_write_intent(
                task_id="t1",
                adapter_state_path="adapter.json",
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            self.assertEqual(intent["adapter"], "local_file")
            self.assertEqual(intent["target_status"], "done")
            auth = harness.authorize_write(
                intent,
                actor_id="charles",
                actor_role="admin",
                evidence=["approval:cli"],
            )
            self.assertTrue(auth["authorized"])
            self.assertEqual(auth["authority"], harness.ADAPTER_AUTHORITY)
            tampered = dict(intent)
            tampered["mutation_payload"] = dict(intent["mutation_payload"], target_status="archived")
            denied = harness.authorize_write(
                tampered,
                actor_id="charles",
                actor_role="admin",
                evidence=["approval:cli"],
            )
            self.assertFalse(denied["authorized"])
            self.assertIn("mutation_digest_mismatch", denied["reasons"])

    def test_execute_write_verifies_readback_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            intent = harness.build_write_intent(
                task_id="t1",
                adapter_state_path="adapter.json",
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            auth = harness.authorize_write(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            first = harness.execute_write(intent, auth, mode="apply")
            self.assertEqual(first["status"], "external_adapter_write_verified")
            self.assertTrue(first["write_executed"])
            self.assertTrue(first["readback_verified"])
            second = harness.execute_write(intent, auth, mode="apply")
            self.assertEqual(second["status"], "already_applied")
            self.assertFalse(second["write_executed"])
            self.assertTrue(second["readback_verified"])

    def test_shadow_does_not_write_and_off_skips(self):
        with tempfile.TemporaryDirectory() as td:
            intent = harness.build_write_intent(
                task_id="t1",
                adapter_state_path="adapter.json",
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            auth = harness.authorize_write(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            shadow = harness.execute_write(intent, auth, mode="shadow")
            self.assertEqual(shadow["status"], "shadow_authorized_not_executed")
            self.assertFalse(Path(intent["adapter_state_path"]).exists())
            off = harness.execute_write(intent, auth, mode="off")
            self.assertEqual(off["reason"], "disabled_by_env")
            self.assertFalse(Path(intent["adapter_state_path"]).exists())

    def test_rollback_requires_exact_digest_and_restores_previous_state(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "adapter.json"
            path.write_text('{"status":"review","x":1}\n', encoding="utf-8")
            intent = harness.build_write_intent(
                task_id="t1",
                adapter_state_path=str(path),
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            auth = harness.authorize_write(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            execution = harness.execute_write(intent, auth, mode="apply")
            bad = harness.rollback_write(execution, expected_request_digest="wrong", evidence=["rollback:cli"])
            self.assertEqual(bad["reason"], "request_digest_mismatch")
            rb = harness.rollback_write(execution, expected_request_digest=execution["request_digest"], evidence=["rollback:cli"])
            self.assertEqual(rb["status"], "external_adapter_rollback_verified")
            self.assertTrue(rb["readback_verified"])
            self.assertEqual(harness.read_state(path)["status"], "review")

    def test_rejects_path_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                harness.build_write_intent(
                    task_id="t1",
                    adapter_state_path="../escape.json",
                    canonical_done_authorization_id="auth-done-1",
                    evidence=["proof:sha256:abc"],
                    base_dir=td,
                )
            target = Path(td) / "real.json"
            target.write_text("{}", encoding="utf-8")
            link = Path(td) / "link.json"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                harness.safe_state_path(link, base_dir=td)

    def test_authorization_rejects_non_elevated_actor_or_missing_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            intent = harness.build_write_intent(
                task_id="t1",
                adapter_state_path="adapter.json",
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            denied = harness.authorize_write(intent, actor_id="worker", actor_role="worker", evidence=[])
            self.assertFalse(denied["authorized"])
            self.assertIn("actor_role_not_elevated", denied["reasons"])
            self.assertIn("authorization_evidence_required", denied["reasons"])
    def test_taskpool_note_closeout_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            note = Path(td) / "task.md"
            note.write_text("---\ntitle: Task\nstatus: review\n---\nBody\n", encoding="utf-8")
            intent = harness.build_write_intent(
                task_id="task.md",
                adapter="taskpool_note",
                adapter_state_path="task.md",
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            auth = harness.authorize_write(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            execution = harness.execute_write(intent, auth, mode="apply")
            self.assertEqual(execution["status"], "external_adapter_write_verified")
            self.assertTrue(execution["readback_verified"])
            self.assertEqual(harness.read_taskpool_note(note)["status"], "done")
            self.assertIn("hermes_external_adapter_taskpool_write", note.read_text(encoding="utf-8"))
            second = harness.execute_write(intent, auth, mode="apply")
            self.assertEqual(second["status"], "already_applied")
            rb = harness.rollback_write(execution, expected_request_digest=execution["request_digest"], evidence=["rollback:cli"])
            self.assertEqual(rb["status"], "external_adapter_rollback_verified")
            self.assertEqual(harness.read_taskpool_note(note)["status"], "review")

    def test_kanban_db_closeout_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "kanban.db"
            with sqlite3.connect(db) as conn:
                conn.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, status TEXT)")
                conn.execute("INSERT INTO tasks (id, status) VALUES (?, ?)", ("t1", "review"))
                conn.commit()
            intent = harness.build_write_intent(
                task_id="t1",
                adapter="kanban_db",
                adapter_state_path="kanban.db",
                canonical_done_authorization_id="auth-done-1",
                evidence=["proof:sha256:abc"],
                base_dir=td,
            )
            auth = harness.authorize_write(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            execution = harness.execute_write(intent, auth, mode="apply")
            self.assertEqual(execution["status"], "external_adapter_write_verified")
            self.assertEqual(harness.read_kanban_status(db, "t1")["status"], "done")
            second = harness.execute_write(intent, auth, mode="apply")
            self.assertEqual(second["status"], "already_applied")
            rb = harness.rollback_write(execution, expected_request_digest=execution["request_digest"], evidence=["rollback:cli"])
            self.assertEqual(rb["status"], "external_adapter_rollback_verified")
            self.assertEqual(harness.read_kanban_status(db, "t1")["status"], "review")


if __name__ == "__main__":
    unittest.main()
