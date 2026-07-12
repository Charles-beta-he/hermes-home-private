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



    def test_learning_candidates_are_candidate_only_no_auto_apply(self):
        hermes_jspace.init_workspace(self.root, "J-space P1", "learning candidate", workspace_id="jspace-test")
        hermes_jspace.reflect(self.root, "jspace-test")
        hermes_jspace.gate_check(self.root, "jspace-test", "before_done")
        result = hermes_jspace.learning_candidates(self.root, "jspace-test")
        candidate = result["candidate"]
        self.assertTrue(candidate["requires_human_review"])
        self.assertFalse(candidate["auto_apply_executed"])
        self.assertFalse(candidate["global_memory_write_executed"])
        self.assertFalse(candidate["skill_patch_executed"])
        self.assertEqual(candidate["boundary"], "candidate_only_no_persistent_learning_write")



    def test_dashboard_data_is_read_only_summary(self):
        hermes_jspace.init_workspace(self.root, "J-space P2", "dashboard data", workspace_id="jspace-test")
        hermes_jspace.reflect(self.root, "jspace-test")
        hermes_jspace.learning_candidates(self.root, "jspace-test")
        data = hermes_jspace.dashboard_data(self.root)
        self.assertTrue(data["ok"])
        self.assertFalse(data["runtime_mutation"])
        self.assertFalse(data["external_side_effects_executed"])
        self.assertFalse(data["taskpool_lifecycle_write_executed"])
        self.assertEqual(data["aggregate_effects"]["runtime_mutation"], False)
        self.assertIsNone(data["current_workspace_effects"])
        self.assertEqual(len(data["active_jspaces"]), 1)
        self.assertEqual(len(data["learning_candidates"]), 1)

    def test_dashboard_data_can_filter_current_workspace_effects(self):
        hermes_jspace.init_workspace(self.root, "historical", "old write", workspace_id="old")
        old_dir = self.root / "old"
        hermes_jspace.append_event(old_dir, {"source": "taskpool_write_through", "returncode": 0, "taskpool_lifecycle_write_executed": True})
        hermes_jspace.init_workspace(self.root, "current", "current read only", workspace_id="current")
        data = hermes_jspace.dashboard_data(self.root, workspace_id="current")
        self.assertTrue(data["aggregate_effects"]["taskpool_lifecycle_write_executed"])
        self.assertFalse(data["current_workspace_effects"]["taskpool_lifecycle_write_executed"])
        self.assertFalse(data["current_workspace_effects"]["external_side_effects_executed"])
        self.assertEqual(len(data["active_jspaces"]), 1)



    def test_taskpool_transition_rejects_task_mismatch_and_bad_evidence(self):
        hermes_jspace.init_workspace(self.root, "J-space real", "write through", workspace_id="jspace-test", task_id="task-a")
        with self.assertRaises(SystemExit):
            hermes_jspace.taskpool_transition(self.root, "jspace-test", "task-b", "review", "artifact:x")
        with self.assertRaises(SystemExit):
            hermes_jspace.taskpool_transition(self.root, "jspace-test", "task-a", "review", "badprefix:x")



    def test_closure_packet_reflects_taskpool_write_through_event(self):
        hermes_jspace.init_workspace(self.root, "J-space real", "closure", workspace_id="jspace-test")
        wdir = self.root / "jspace-test"
        hermes_jspace.append_event(wdir, {"source": "taskpool_write_through", "returncode": 0, "taskpool_lifecycle_write_executed": True})
        packet = hermes_jspace.closure_packet(self.root, "jspace-test")["packet"]
        self.assertEqual(packet["scope"], "local_projection_with_exact_taskpool_write_through")
        self.assertNotIn("no_taskpool_lifecycle_write", packet["negative_evidence"])
        self.assertNotIn("not_taskpool_real_lifecycle_write", packet["excluded_claims"])



    def test_real_open_matrix_covers_all_boundaries_and_canary_is_disposable(self):
        hermes_jspace.init_workspace(self.root, "J-space real", "matrix", workspace_id="jspace-test")
        result = hermes_jspace.real_open_matrix(self.root, "jspace-test", run_destructive_canary=True)
        matrix = result["matrix"]
        self.assertEqual(matrix["governance_coverage_percent"], 100)
        self.assertFalse(matrix["unscoped_high_risk_execution"])
        ids = {b["id"] for b in matrix["boundaries"]}
        self.assertIn("external_dispatch", ids)
        self.assertIn("payment_credential_entry", ids)
        destructive = next(b for b in matrix["boundaries"] if b["id"] == "destructive_operation")
        self.assertTrue(destructive["canary"]["executed"])
        self.assertTrue(destructive["canary"]["hash_match"])
        self.assertFalse(destructive["canary"]["production_resource_touched"])
        payment = next(b for b in matrix["boundaries"] if b["id"] == "payment_credential_entry")
        self.assertFalse(payment["agent_may_type_secret"])


if __name__ == "__main__":
    unittest.main()
