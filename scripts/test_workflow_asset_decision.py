#!/usr/bin/env python3
"""Tests for workflow_asset_decision.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "workflow_asset_decision.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_asset_decision", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowAssetDecisionTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_keyword_workflow_one_off_stays_session_plan(self):
        result = self.mod.decide_assetization(
            "创建工作流：今天把这三个文件整理一下",
            context={"task_scope": "one_off"},
        )
        self.assertEqual(result["decision"], "session_plan")
        self.assertNotEqual(result["decision"], "reusable_candidate")
        self.assertIn("one_off", result["reasons"])
        self.assertLess(result["score"], 5)

    def test_repeated_high_reuse_without_keyword_becomes_candidate(self):
        result = self.mod.decide_assetization(
            "以后我给你一个项目链接，你自动做商机、竞品、客群、变现、风险、入池判断，并保留证据",
            context={"observed_repetition": 3},
        )
        self.assertEqual(result["decision"], "reusable_candidate")
        self.assertGreaterEqual(result["score"], 6)
        self.assertIn("reuse_value", result["reasons"])
        self.assertIn("evidence_gap", result["reasons"])

    def test_external_side_effect_requires_authority_boundary(self):
        result = self.mod.decide_assetization(
            "以后自动把分析结果发到 Telegram 并关闭任务",
            context={"observed_repetition": 2},
        )
        self.assertEqual(result["side_effect_class"], "external_or_lifecycle")
        self.assertIn("authority_boundary", result["stop_only_on"])
        self.assertIn("exact_authority_required", result["warnings"])

    def test_compile_asset_includes_lifecycle_output_contract_and_gates(self):
        decision = self.mod.decide_assetization(
            "以后我给你一个项目链接，你自动做商机、竞品、客群、变现、风险、入池判断，并保留证据",
            context={"observed_repetition": 3},
        )
        asset = self.mod.compile_workflow_asset(decision)
        self.assertEqual(asset["schema"], "hermes_workflow_asset_v1")
        self.assertEqual(asset["classification"]["maturity"], "draft")
        self.assertIn("applies_when", asset["routing"])
        self.assertIn("ordering_rule", asset["output_contract"])
        self.assertTrue(asset["output_contract"]["evidence_required"])
        self.assertTrue(asset["gates"])
        self.assertIn("promote_when", asset["lifecycle_policy"])

    def test_validator_rejects_canonical_without_validation(self):
        asset = self.mod.default_workflow_asset("unsafe", "unsafe seed")
        asset["classification"]["maturity"] = "canonical"
        issues = self.mod.validate_workflow_asset(asset)
        self.assertTrue(any("canonical_without_validation" in i for i in issues))

    def test_scaffold_writes_expected_files_and_receipt(self):
        decision = self.mod.decide_assetization(
            "以后给我外链就做事实、商业、技术、人群、风险、入池判断",
            context={"observed_repetition": 2},
        )
        asset = self.mod.compile_workflow_asset(decision)
        with tempfile.TemporaryDirectory() as td:
            receipt = self.mod.scaffold_workspace(asset, root=Path(td))
            workdir = Path(receipt["workdir"])
            self.assertTrue((workdir / "workflow.json").exists())
            self.assertTrue((workdir / "state.json").exists())
            self.assertTrue((workdir / "eval-cases.json").exists())
            self.assertTrue((workdir / "evidence.jsonl").exists())
            saved = json.loads((workdir / "workflow.json").read_text())
            self.assertEqual(saved["id"], asset["id"])
            self.assertFalse(receipt["side_effects"]["external"])
            self.assertFalse(receipt["side_effects"]["cron"])


if __name__ == "__main__":
    unittest.main()
