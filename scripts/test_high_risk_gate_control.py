#!/usr/bin/env python3
"""Tests for high_risk_gate_control.py."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "high_risk_gate_control.py"
spec = importlib.util.spec_from_file_location("high_risk_gate_control", SCRIPT)
high_risk_gate_control = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(high_risk_gate_control)


class HighRiskGateControlTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_enable_all_opens_known_gates_with_fail_closed_live_boundaries(self):
        result = high_risk_gate_control.enable_all(self.home, actor="test", evidence_refs=["command:test"])
        self.assertTrue(result["ok"])
        gates = result["gates"]
        for gate in high_risk_gate_control.GATE_NAMES:
            self.assertIn(gate, gates)
            self.assertTrue(gates[gate]["enabled"])
        self.assertEqual(gates["runtime_hard_gate"]["mode"], "enforcing")
        self.assertEqual(gates["taskpool_lifecycle_write_through"]["mode"], "exact_local_target_required")
        self.assertEqual(gates["external_dispatch"]["mode"], "exact_allowlist_required")
        self.assertEqual(gates["publish_deploy_push"]["mode"], "exact_target_required")
        self.assertEqual(gates["destructive"]["mode"], "exact_target_and_backup_required")
        self.assertEqual(gates["credential_payment"]["mode"], "human_secret_entry_required")
        readback = high_risk_gate_control.status(self.home)
        self.assertTrue(readback["enabled_all_requested_gates"])
        self.assertTrue(Path(result["state_path"]).exists())

    def test_external_dispatch_without_exact_target_is_blocked(self):
        high_risk_gate_control.enable_all(self.home, actor="test", evidence_refs=["command:test"])
        result = high_risk_gate_control.authorize_action(
            self.home,
            gate="external_dispatch",
            target="",
            payload_hash="abc123",
            rollback="not applicable",
            readback="not applicable",
            evidence_refs=["command:test"],
        )
        self.assertFalse(result["allowed"])
        self.assertIn("missing_exact_target", result["blocked_reasons"])
        self.assertFalse(result["executed"])

    def test_local_destructive_canary_deletes_only_declared_file_and_records_readback(self):
        high_risk_gate_control.enable_all(self.home, actor="test", evidence_refs=["command:test"])
        result = high_risk_gate_control.destructive_canary(self.home, actor="test")
        self.assertTrue(result["ok"])
        self.assertEqual(result["gate"], "destructive")
        self.assertFalse(Path(result["target_path"]).exists())
        self.assertTrue(Path(result["backup_path"]).exists())
        self.assertTrue(result["readback"]["deleted"])

    def test_lifecycle_write_requires_exact_task_and_status(self):
        high_risk_gate_control.enable_all(self.home, actor="test", evidence_refs=["command:test"])
        blocked = high_risk_gate_control.taskpool_lifecycle_write(
            self.home,
            task_id="",
            status_value="done",
            evidence_refs=["command:test"],
            actor="test",
        )
        self.assertFalse(blocked["ok"])
        self.assertIn("missing_task_id", blocked["blocked_reasons"])
        ok = high_risk_gate_control.taskpool_lifecycle_write(
            self.home,
            task_id="task-1",
            status_value="blocked",
            evidence_refs=["command:test"],
            actor="test",
        )
        self.assertTrue(ok["ok"])
        ledger = Path(ok["ledger_path"])
        self.assertTrue(ledger.exists())
        last = json.loads(ledger.read_text().splitlines()[-1])
        self.assertEqual(last["task_id"], "task-1")
        self.assertEqual(last["status"], "blocked")
        self.assertTrue(last["write_executed"])


if __name__ == "__main__":
    unittest.main()
