#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT = SCRIPT_DIR / "skill_writer_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("skill_writer_harness", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


writer = load_module()


SKILL = """---
name: generated-test-skill
description: Use when testing the digest-bound generated skill writer.
---

## Procedure

1. Validate the intent digest.
2. Write only a new skill.
3. Verify readback and rollback.
"""


class SkillWriterHarnessTests(unittest.TestCase):
    def test_writer_mode_default_apply_with_escape_hatches(self):
        old_mode = os.environ.pop("HERMES_SKILL_WRITER_MODE", None)
        old_short = os.environ.pop("HERMES_CANONICAL_SKILL_WRITER", None)
        try:
            self.assertEqual(writer.writer_mode(), "apply")
            os.environ["HERMES_SKILL_WRITER_MODE"] = "shadow"
            self.assertEqual(writer.writer_mode(), "shadow")
            os.environ["HERMES_SKILL_WRITER_MODE"] = "off"
            self.assertEqual(writer.writer_mode(), "off")
        finally:
            if old_mode is not None:
                os.environ["HERMES_SKILL_WRITER_MODE"] = old_mode
            else:
                os.environ.pop("HERMES_SKILL_WRITER_MODE", None)
            if old_short is not None:
                os.environ["HERMES_CANONICAL_SKILL_WRITER"] = old_short
            else:
                os.environ.pop("HERMES_CANONICAL_SKILL_WRITER", None)

    def test_skill_write_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            intent = writer.build_intent(name="generated-test-skill", content=SKILL, category="agent-generated", base_dir=td, evidence=["cert:sha256:abc"])
            auth = writer.authorize(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            self.assertTrue(auth["authorized"])
            execution = writer.execute(intent, auth, mode="apply")
            self.assertEqual(execution["status"], "skill_write_verified")
            self.assertTrue(Path(execution["skill_file"]).exists())
            self.assertTrue(execution["readback_verified"])
            denied_second = writer.execute(intent, auth, mode="apply")
            self.assertEqual(denied_second["reason"], "skill_already_exists_no_overwrite")
            rb = writer.rollback(execution, expected_request_digest=execution["request_digest"], evidence=["rollback:cli"])
            self.assertEqual(rb["status"], "skill_write_rollback_verified")
            self.assertFalse(Path(execution["skill_dir"]).exists())

    def test_shadow_and_off_do_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            intent = writer.build_intent(name="generated-test-skill", content=SKILL, category="agent-generated", base_dir=td, evidence=["cert:sha256:abc"])
            auth = writer.authorize(intent, actor_id="charles", actor_role="admin", evidence=["approval:cli"])
            shadow = writer.execute(intent, auth, mode="shadow")
            self.assertEqual(shadow["status"], "shadow_authorized_not_executed")
            self.assertFalse(Path(intent["skill_dir"]).exists())
            off = writer.execute(intent, auth, mode="off")
            self.assertEqual(off["reason"], "disabled_by_env")
            self.assertFalse(Path(intent["skill_dir"]).exists())

    def test_rejects_overwrite_tamper_bad_name_and_non_elevated(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                writer.build_intent(name="../bad", content=SKILL, base_dir=td, evidence=["cert"])
            intent = writer.build_intent(name="generated-test-skill", content=SKILL, base_dir=td, evidence=["cert"])
            tampered = dict(intent)
            tampered["payload"] = dict(intent["payload"], name="other")
            denied = writer.authorize(tampered, actor_id="charles", actor_role="admin", evidence=["approval"])
            self.assertFalse(denied["authorized"])
            self.assertIn("payload_digest_mismatch", denied["reasons"])
            denied_role = writer.authorize(intent, actor_id="worker", actor_role="worker", evidence=[])
            self.assertFalse(denied_role["authorized"])
            self.assertIn("actor_role_not_elevated", denied_role["reasons"])
            self.assertIn("authorization_evidence_required", denied_role["reasons"])


if __name__ == "__main__":
    unittest.main()
