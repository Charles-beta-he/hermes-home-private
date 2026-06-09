#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "telegram_send_harness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("telegram_send_harness", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harness = load_module()


class TelegramSendHarnessTests(unittest.TestCase):
    def test_mode_defaults_apply_with_escape_hatches(self):
        old = os.environ.pop("HERMES_TELEGRAM_SEND_MODE", None)
        try:
            self.assertEqual(harness.mode(), "apply")
            os.environ["HERMES_TELEGRAM_SEND_MODE"] = "shadow"
            self.assertEqual(harness.mode(), "shadow")
            os.environ["HERMES_TELEGRAM_SEND_MODE"] = "off"
            self.assertEqual(harness.mode(), "off")
        finally:
            if old is not None:
                os.environ["HERMES_TELEGRAM_SEND_MODE"] = old
            else:
                os.environ.pop("HERMES_TELEGRAM_SEND_MODE", None)

    def test_intent_auth_and_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            intent = harness.build_send_intent(task_id="t1", target="telegram:he cheng", message="smoke", purpose="verification", evidence=["user:approved"])
            auth = harness.authorize_send(intent=intent, actor_id="charles", actor_role="admin", approval_evidence=["approval:cli"])
            self.assertTrue(auth["approved"])
            self.assertEqual(auth["status"], "telegram_send_authorized")
            receipt = harness.record_receipt(intent=intent, authorization=auth, send_result={"success": True, "target": "telegram:he cheng", "message_id": 123}, receipt_evidence=["send_message:success"], base_dir=td)
            self.assertTrue(receipt["verified"])
            self.assertEqual(receipt["status"], "telegram_send_verified")
            self.assertTrue(Path(receipt["receipt_path"]).exists())

    def test_rejects_non_allowlisted_target_and_non_elevated(self):
        intent = harness.build_send_intent(task_id="t1", target="telegram:Ama Abokomah", message="smoke", purpose="verification", evidence=["user:approved"])
        auth = harness.authorize_send(intent=intent, actor_id="worker", actor_role="worker", approval_evidence=["approval:cli"])
        self.assertFalse(auth["approved"])
        self.assertIn("target_not_allowlisted", auth["reasons"])
        self.assertIn("actor_role_not_elevated", auth["reasons"])

    def test_rejects_tampered_message_missing_evidence_and_bad_receipt(self):
        intent = harness.build_send_intent(task_id="t1", target="telegram:he cheng", message="smoke", purpose="verification", evidence=[])
        intent["message"] = "tampered"
        auth = harness.authorize_send(intent=intent, actor_id="charles", actor_role="admin", approval_evidence=[])
        self.assertFalse(auth["approved"])
        self.assertIn("intent_evidence_required", auth["reasons"])
        self.assertIn("approval_evidence_required", auth["reasons"])
        self.assertIn("message_digest_mismatch", auth["reasons"])
        receipt = harness.record_receipt(intent=intent, authorization=auth, send_result={"success": False}, receipt_evidence=[])
        self.assertFalse(receipt["verified"])
        self.assertIn("authorization_not_approved", receipt["reasons"])
        self.assertIn("send_result_not_success", receipt["reasons"])

    def test_shadow_and_off_do_not_approve_send(self):
        intent = harness.build_send_intent(task_id="t1", target="telegram:he cheng", message="smoke", purpose="verification", evidence=["user:approved"])
        shadow = harness.authorize_send(intent=intent, actor_id="charles", actor_role="admin", approval_evidence=["approval"], mode_value="shadow")
        self.assertFalse(shadow["approved"])
        self.assertEqual(shadow["status"], "telegram_send_shadow_authorized_not_sent")
        off = harness.authorize_send(intent=intent, actor_id="charles", actor_role="admin", approval_evidence=["approval"], mode_value="off")
        self.assertFalse(off["approved"])
        self.assertIn("disabled_by_env", off["reasons"])


if __name__ == "__main__":
    unittest.main()
