#!/usr/bin/env python3
"""Tests for workflow_kernel_loop.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "workflow_kernel_loop.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_kernel_loop", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowKernelLoopTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_run_once_produces_decision_plan_asset_and_receipt_without_side_effects(self):
        with tempfile.TemporaryDirectory() as td:
            result = self.mod.run_loop_once(
                seed="以后给我外链就自动做事实、商业、风险分析，并保留证据和美化输出",
                root=Path(td),
                observed_repetition=3,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["side_effects"], {"external": False, "cron": False, "taskpool": False, "agentos": False})
            run_dir = Path(result["run_dir"])
            self.assertTrue((run_dir / "decision.json").exists())
            self.assertTrue((run_dir / "module-plan.json").exists())
            self.assertTrue((run_dir / "asset-receipt.json").exists())
            self.assertTrue((run_dir / "loop-receipt.json").exists())
            decision = json.loads((run_dir / "decision.json").read_text())
            plan = json.loads((run_dir / "module-plan.json").read_text())
            self.assertEqual(decision["decision"], "reusable_candidate")
            self.assertIn("business_analysis", plan["capability_needs"])
            self.assertFalse(plan["side_effects"]["external"])
            self.assertEqual(result["engineering_coverage"]["kernel_stages"], {"covered": 9, "total": 9, "percent": 100.0})
            self.assertEqual(result["engineering_coverage"]["control_moves"], {"covered": 5, "total": 5, "percent": 100.0})
            self.assertEqual(result["engineering_coverage"]["system_parts"], {"covered": 6, "total": 6, "percent": 100.0})
            self.assertEqual(result["engineering_coverage"]["overall_percent"], 100.0)
            self.assertEqual([stage["id"] for stage in result["stages"]], [
                "observe", "orient", "compile", "simulate", "execute", "verify", "ratchet", "monitor", "cleanup"
            ])
            self.assertTrue(all(stage["status"] == "PASS" and stage["evidence_refs"] for stage in result["stages"]))
            self.assertEqual(result["evaluation"]["status"], "PASS")
            self.assertFalse(result["evaluation"]["veto"])
            self.assertTrue((run_dir / "evaluation.json").exists())
            self.assertTrue(all(value > 0 for value in result["budgets"].values()))
            self.assertTrue(result["kill_switch"])

    def test_one_off_seed_does_not_scaffold_durable_asset(self):
        with tempfile.TemporaryDirectory() as td:
            result = self.mod.run_loop_once(
                seed="创建工作流：今天把这三个文件整理一下",
                root=Path(td),
                task_scope="one_off",
            )
            self.assertEqual(result["decision"], "session_plan")
            self.assertIsNone(result["asset_workdir"])
            run_dir = Path(result["run_dir"])
            self.assertTrue((run_dir / "decision.json").exists())
            self.assertTrue((run_dir / "module-plan.json").exists())
            self.assertFalse((run_dir / "asset-receipt.json").exists())

    def test_repeated_successful_loop_runs_emit_synthesis_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(3):
                self.mod.run_loop_once(
                    seed="以后给我外链就自动做事实、商业、风险分析，并保留证据和美化输出",
                    root=root,
                    observed_repetition=3,
                )
            result = self.mod.synthesize_from_root(root)
            self.assertGreaterEqual(len(result["candidates"]), 1)
            self.assertFalse(result["side_effects"]["external"])
            self.assertTrue((root / "module-pool" / "usage_ledger.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
