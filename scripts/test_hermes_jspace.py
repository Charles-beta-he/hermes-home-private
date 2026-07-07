#!/usr/bin/env python3
"""Tests for hermes_jspace.py local External J-space P0 projection helper."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT = Path(__file__).parent / "hermes_jspace.py"
spec = importlib.util.spec_from_file_location("hermes_jspace", SCRIPT)
hermes_jspace = importlib.util.module_from_spec(spec)
sys.modules["hermes_jspace"] = hermes_jspace
spec.loader.exec_module(hermes_jspace)


class HermesJSpaceTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_init_status_and_objective_gate(self):
        result = hermes_jspace.init_workspace(self.root, "J-space P0", "prove local projection", workspace_id="jspace-test")
        self.assertTrue(result["ok"])
        status = hermes_jspace.status(self.root, "jspace-test")
        self.assertEqual(status["workspace_state"], "objective_model")
        self.assertEqual(status["verified_evidence_count"], 1)
        gate = hermes_jspace.gate_check(self.root, "jspace-test", "objective_defined")
        self.assertEqual(gate["result"], "pass")

    def test_reflection_gate_fails_until_reflect_then_passes(self):
        hermes_jspace.init_workspace(self.root, "J-space P0", "prove reflection", workspace_id="jspace-test")
        first = hermes_jspace.gate_check(self.root, "jspace-test", "reflection_readback")
        self.assertEqual(first["result"], "fail")
        hermes_jspace.reflect(self.root, "jspace-test")
        second = hermes_jspace.gate_check(self.root, "jspace-test", "reflection_readback")
        self.assertEqual(second["result"], "pass")

    def test_add_evidence_records_authority_and_completion_packet_stays_scoped(self):
        hermes_jspace.init_workspace(self.root, "J-space P0", "prove evidence", workspace_id="jspace-test")
        ev = hermes_jspace.add_evidence(self.root, "jspace-test", "command", "command:unit-test", "Focused unit test passed", authority="objective", status_value="verified")
        self.assertEqual(ev["evidence_id"], "E-002")
        packet = hermes_jspace.closure_packet(self.root, "jspace-test")["packet"]
        self.assertEqual(packet["status"], "verified_local")
        self.assertIn("no_hidden_state_access", packet["negative_evidence"])
        self.assertIn("not_taskpool_real_lifecycle_write", packet["excluded_claims"])

    def test_completion_claim_gate_requires_objective_evidence_for_completion_critical_claim(self):
        hermes_jspace.init_workspace(self.root, "J-space P0", "prove completion gate", workspace_id="jspace-test")
        wdir = self.root / "jspace-test"
        dag = hermes_jspace.read_json(wdir / "evidence_dag.json")
        dag["claims"].append({"id": "C-CRIT", "text": "complete", "criticality": "completion_critical", "status": "unverified"})
        hermes_jspace.write_json(wdir / "evidence_dag.json", dag)
        gate = hermes_jspace.gate_check(self.root, "jspace-test", "completion_claim")
        self.assertEqual(gate["result"], "fail")
        self.assertIn("objective_evidence_for_C-CRIT", gate["missing"])


    def test_attach_task_and_record_status_event_projects_workspace_state(self):
        hermes_jspace.init_workspace(self.root, "J-space P1", "project task events", workspace_id="jspace-test")
        attached = hermes_jspace.attach_task(self.root, "jspace-test", "task-123")
        self.assertTrue(attached["ok"])
        event = hermes_jspace.record_event(self.root, "jspace-test", {"source": "taskpool", "type": "task.status_changed", "from": "running", "to": "review"})
        self.assertEqual(event["workspace_state"], "reflective")
        self.assertIn("gate_check:before_review", event["derived_actions"])
        status = hermes_jspace.status(self.root, "jspace-test")
        self.assertEqual(status["event_count"], 2)

    def test_before_review_gate_requires_reflection_and_verified_objective_evidence(self):
        hermes_jspace.init_workspace(self.root, "J-space P1", "gate review", workspace_id="jspace-test")
        before = hermes_jspace.gate_check(self.root, "jspace-test", "before_review")
        self.assertEqual(before["result"], "fail")
        self.assertIn("reflection_log.readback", before["missing"])
        hermes_jspace.reflect(self.root, "jspace-test")
        after = hermes_jspace.gate_check(self.root, "jspace-test", "before_review")
        self.assertEqual(after["result"], "pass")


if __name__ == "__main__":
    unittest.main()
