#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "capability_lease_gate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("capability_lease_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_module()


class CapabilityLeaseGateTests(unittest.TestCase):
    def test_mode_default_apply_with_escape_hatches(self):
        old = os.environ.pop("HERMES_CAPABILITY_LEASE_MODE", None)
        try:
            self.assertEqual(gate.gate_mode(), "apply")
            os.environ["HERMES_CAPABILITY_LEASE_MODE"] = "shadow"
            self.assertEqual(gate.gate_mode(), "shadow")
            os.environ["HERMES_CAPABILITY_LEASE_MODE"] = "off"
            self.assertEqual(gate.gate_mode(), "off")
        finally:
            if old is not None:
                os.environ["HERMES_CAPABILITY_LEASE_MODE"] = old
            else:
                os.environ.pop("HERMES_CAPABILITY_LEASE_MODE", None)

    def test_issue_and_validate_run_command_lease(self):
        with tempfile.TemporaryDirectory() as td:
            lease = gate.issue_lease(actor_id="charles", actor_role="admin", task_id="t1", capability="run_command", scope="repo:/tmp/project", max_danger="moderate", ttl_seconds=300, evidence=["approval:cli"], base_dir=td)
            self.assertTrue(lease["authorized"])
            ok = gate.validate_request(lease_id=lease["lease_id"], capability="run_command", scope="repo:/tmp/project", danger="moderate", request_payload={"cmd":"pytest"}, evidence=["dry-run:ok"], base_dir=td)
            self.assertTrue(ok["allowed"])
            self.assertEqual(ok["status"], "allowed")
            self.assertIn("request_digest", ok)

    def test_rejects_scope_capability_danger_expiry_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            lease = gate.issue_lease(actor_id="charles", actor_role="admin", task_id="t1", capability="run_command", scope="repo:/tmp/project", max_danger="low", ttl_seconds=1, evidence=["approval:cli"], base_dir=td)
            self.assertIn("capability_mismatch", gate.validate_request(lease_id=lease["lease_id"], capability="deploy", scope="repo:/tmp/project", danger="low", request_payload={}, evidence=["e"], base_dir=td)["reasons"])
            self.assertIn("scope_mismatch", gate.validate_request(lease_id=lease["lease_id"], capability="run_command", scope="repo:/tmp/other", danger="low", request_payload={}, evidence=["e"], base_dir=td)["reasons"])
            self.assertIn("danger_exceeds_lease", gate.validate_request(lease_id=lease["lease_id"], capability="run_command", scope="repo:/tmp/project", danger="high", request_payload={}, evidence=["e"], base_dir=td)["reasons"])
            self.assertIn("request_evidence_required", gate.validate_request(lease_id=lease["lease_id"], capability="run_command", scope="repo:/tmp/project", danger="low", request_payload={}, evidence=[], base_dir=td)["reasons"])

    def test_shadow_and_off_do_not_allow_execution(self):
        with tempfile.TemporaryDirectory() as td:
            lease = gate.issue_lease(actor_id="charles", actor_role="admin", task_id="t1", capability="run_command", scope="repo:/tmp/project", max_danger="moderate", evidence=["approval:cli"], base_dir=td)
            shadow = gate.validate_request(lease_id=lease["lease_id"], capability="run_command", scope="repo:/tmp/project", danger="low", request_payload={}, evidence=["e"], base_dir=td, mode="shadow")
            self.assertFalse(shadow["allowed"])
            self.assertEqual(shadow["status"], "shadow_allowed_not_executed")
            off = gate.validate_request(lease_id=lease["lease_id"], capability="run_command", scope="repo:/tmp/project", danger="low", request_payload={}, evidence=["e"], base_dir=td, mode="off")
            self.assertFalse(off["allowed"])
            self.assertEqual(off["status"], "skipped_disabled_by_env")

    def test_issue_rejects_non_elevated_bad_scope_and_bad_capability(self):
        with tempfile.TemporaryDirectory() as td:
            denied = gate.issue_lease(actor_id="worker", actor_role="worker", task_id="t1", capability="run_command", scope="repo:/tmp/project", evidence=[], base_dir=td)
            self.assertFalse(denied["authorized"])
            self.assertIn("actor_role_not_elevated", denied["reasons"])
            self.assertIn("evidence_required", denied["reasons"])
            with self.assertRaises(ValueError):
                gate.issue_lease(actor_id="charles", actor_role="admin", task_id="t1", capability="run_command", scope="../bad", evidence=["e"], base_dir=td)
            denied_cap = gate.issue_lease(actor_id="charles", actor_role="admin", task_id="t1", capability="arbitrary_shell", scope="repo:/tmp/project", evidence=["e"], base_dir=td)
            self.assertIn("capability_not_allowlisted", denied_cap["reasons"])


if __name__ == "__main__":
    unittest.main()
