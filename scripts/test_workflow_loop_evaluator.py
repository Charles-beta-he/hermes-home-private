#!/usr/bin/env python3
"""Fail-closed tests for workflow_loop_evaluator.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "workflow_loop_evaluator.py"
STAGE_IDS = ["observe", "orient", "compile", "simulate", "execute", "verify", "ratchet", "monitor", "cleanup"]
CONTROL_MOVES = ["discovery", "handoff", "verification", "persistence", "scheduling"]
SYSTEM_PARTS = ["automations", "worktrees", "skills", "connectors", "subagents", "memory"]


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_loop_evaluator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def complete_receipt(run_dir: Path) -> dict:
    evidence = run_dir / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    ref = str(evidence)
    return {
        "schema": "hermes_workflow_kernel_loop_receipt_v2",
        "status": "pending_evaluation",
        "run_dir": str(run_dir),
        "stages": [{"id": stage, "status": "PASS", "evidence_refs": [ref]} for stage in STAGE_IDS],
        "control_moves": {move: {"status": "covered", "evidence_refs": [ref]} for move in CONTROL_MOVES},
        "system_parts": {
            part: {"status": "enabled" if part == "skills" else "disabled", "reason": "local boundary", "evidence_refs": [ref]}
            for part in SYSTEM_PARTS
        },
        "budgets": {"max_iterations": 3, "max_runtime_seconds": 120, "max_retries": 2, "max_evidence_files": 64},
        "kill_switch": "HERMES_WORKFLOW_LOOP_DISABLE",
        "side_effects": {"external": False, "cron": False, "taskpool": False, "agentos": False},
    }


class WorkflowLoopEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_complete_evidenced_local_receipt_passes(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            result = self.mod.evaluate_receipt(receipt)
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["veto"])
            self.assertEqual(result["score_percent"], 100.0)
            self.assertEqual(result["evaluator"], "workflow_loop_evaluator_v1")

    def test_missing_stage_is_vetoed(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["stages"] = receipt["stages"][:-1]
            result = self.mod.evaluate_receipt(receipt)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(result["veto"])
            self.assertIn("missing_stage:cleanup", result["issues"])

    def test_missing_evidence_is_vetoed(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["stages"][0]["evidence_refs"] = []
            result = self.mod.evaluate_receipt(receipt)
            self.assertTrue(result["veto"])
            self.assertIn("missing_stage_evidence:observe", result["issues"])

    def test_enabled_side_effect_is_vetoed(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["side_effects"]["external"] = True
            result = self.mod.evaluate_receipt(receipt)
            self.assertTrue(result["veto"])
            self.assertIn("side_effect_enabled:external", result["issues"])

    def test_non_positive_budget_is_vetoed(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["budgets"]["max_retries"] = 0
            result = self.mod.evaluate_receipt(receipt)
            self.assertTrue(result["veto"])
            self.assertIn("invalid_budget:max_retries", result["issues"])

    def test_procedure_validation_is_projected_as_separate_axis_without_implicit_veto(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["claims"] = {"global_certification": False, "canonical_ratchet_promotion": False}
            registry = {
                "schema": "hermes_procedure_validation_registry_v1",
                "summary": {
                    "inventory_complete": True,
                    "can_claim_complete_procedure_validation": False,
                    "pending": 2,
                    "stale": 1,
                    "failed": 0,
                    "blocked_by_authority": 1,
                },
            }
            result = self.mod.evaluate_receipt(receipt, procedure_registry=registry)
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["veto"])
            self.assertEqual(result["procedure_validation"]["state"], "attention_required")
            self.assertFalse(result["procedure_validation"]["can_claim_complete"])

    def test_global_certification_claim_is_vetoed_when_procedures_are_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["claims"] = {"global_certification": True, "canonical_ratchet_promotion": False}
            registry = {
                "schema": "hermes_procedure_validation_registry_v1",
                "summary": {"inventory_complete": True, "can_claim_complete_procedure_validation": False},
            }
            result = self.mod.evaluate_receipt(receipt, procedure_registry=registry)
            self.assertTrue(result["veto"])
            self.assertIn("procedure_global_certification_not_allowed", result["issues"])

    def test_canonical_ratchet_promotion_is_vetoed_by_stale_procedure(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["claims"] = {"global_certification": False, "canonical_ratchet_promotion": True}
            registry = {
                "schema": "hermes_procedure_validation_registry_v1",
                "summary": {
                    "inventory_complete": True,
                    "can_claim_complete_procedure_validation": False,
                    "stale": 1,
                },
            }
            result = self.mod.evaluate_receipt(receipt, procedure_registry=registry)
            self.assertTrue(result["veto"])
            self.assertIn("procedure_canonical_promotion_not_allowed", result["issues"])

    def test_claim_without_procedure_registry_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            receipt = complete_receipt(Path(td))
            receipt["claims"] = {"global_certification": True, "canonical_ratchet_promotion": False}
            result = self.mod.evaluate_receipt(receipt)
            self.assertTrue(result["veto"])
            self.assertIn("procedure_registry_missing_for_claim", result["issues"])


if __name__ == "__main__":
    unittest.main()
