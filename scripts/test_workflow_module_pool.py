#!/usr/bin/env python3
"""Tests for workflow_module_pool.py."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "workflow_module_pool.py"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_module_pool", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WorkflowModulePoolTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_default_module_validates_with_negative_space_and_contracts(self):
        module = self.mod.default_capability_module(
            module_id="evidence_collector",
            responsibility="Collect objective evidence for workflow claims",
            produces=["evidence_refs"],
        )
        issues = self.mod.validate_capability_module(module)
        self.assertEqual(issues, [])
        self.assertIn("does_not_apply_when", module["routing"])
        self.assertEqual(module["authority"]["side_effects"], "none")

    def test_validator_rejects_external_side_effect_without_authority_gate(self):
        module = self.mod.default_capability_module("telegram_sender", "Send external messages")
        module["authority"]["side_effects"] = "external_write"
        module["authority"]["required_authority"] = []
        issues = self.mod.validate_capability_module(module)
        self.assertIn("external_side_effect_without_authority", issues)

    def test_registry_registers_and_retrieves_matching_modules(self):
        with tempfile.TemporaryDirectory() as td:
            registry_path = Path(td) / "module_registry.json"
            registry = self.mod.load_registry(registry_path)
            module = self.mod.default_capability_module(
                "competitor_scan",
                "Compare competitors for business analysis",
                consumes=["seed"],
                produces=["competitor_map"],
            )
            module["routing"]["applies_when"] = ["竞品", "business analysis", "商机"]
            self.mod.register_module(registry, module)
            self.mod.save_registry(registry_path, registry)
            reloaded = self.mod.load_registry(registry_path)
            matches = self.mod.retrieve_modules("以后做商机和竞品分析", reloaded, needs=["competitor_map"])
            self.assertEqual(matches[0]["id"], "competitor_scan")

    def test_plan_from_seed_assembles_graph_and_gap_candidates(self):
        registry = {"schema": "hermes_capability_module_registry_v1", "modules": []}
        registry["modules"].append(self.mod.default_capability_module("evidence_collector", "Collect evidence", produces=["evidence_refs"]))
        registry["modules"].append(self.mod.default_capability_module("presentation_builder", "Format output", produces=["presentation_contract"]))
        plan = self.mod.plan_workflow_from_seed(
            "以后给我外链就自动做事实、商业、风险分析，并保留证据和美化输出",
            registry,
        )
        self.assertEqual(plan["schema"], "hermes_workflow_module_plan_v1")
        self.assertTrue(plan["graph"]["nodes"])
        self.assertIn("source_evidence_collector", plan["capability_needs"])
        self.assertIn("business_analysis", plan["missing_capability_needs"])
        self.assertFalse(plan["side_effects"]["external"])

    def test_four_core_kernel_terms_infer_dedicated_needs(self):
        registry = {"schema": "hermes_capability_module_registry_v1", "modules": []}
        for mid, produces in [
            ("intent_normalization_kernel", "workflow_seed"),
            ("landing_zone_kernel", "landing_decision"),
            ("authority_evidence_gate_kernel", "authority_decision"),
            ("lifecycle_promotion_cleanup_kernel", "lifecycle_transition_decision"),
        ]:
            registry["modules"].append(self.mod.default_capability_module(mid, mid, produces=[produces]))
        seed = "固化意图归一化、落点判定、权限证据门、生命周期晋级清理四个内核"
        plan = self.mod.plan_workflow_from_seed(seed, registry)
        self.assertEqual(
            plan["capability_needs"],
            [
                "intent_normalization_kernel",
                "landing_zone_kernel",
                "authority_evidence_gate_kernel",
                "lifecycle_promotion_cleanup_kernel",
            ],
        )
        self.assertEqual(plan["missing_capability_needs"], [])

    def test_registry_defined_module_can_add_new_need_without_static_rule(self):
        registry = {"schema": "hermes_capability_module_registry_v1", "modules": []}
        custom = self.mod.default_capability_module(
            "custom_decoupled_kernel",
            "Custom decoupled kernel loaded from registry routing only",
            produces=["custom_contract"],
        )
        custom["routing"]["applies_when"] = ["自定义解耦内核"]
        registry["modules"].append(custom)
        plan = self.mod.plan_workflow_from_seed("以后遇到自定义解耦内核就纳入模块图", registry)
        self.assertIn("custom_decoupled_kernel", plan["capability_needs"])
        self.assertIn("custom_decoupled_kernel", plan["selected_modules"])

    def test_default_profile_module_registry_points_to_workflow_kernel_loop(self):
        default_dir = self.mod.default_module_pool_dir()
        self.assertEqual(
            default_dir,
            Path.home() / ".hermes" / "workflows" / "workflow-kernel-loop" / "module-pool",
        )
        registry = self.mod.load_registry(default_dir / "module_registry.json")
        self.assertEqual(registry["schema"], "hermes_capability_module_registry_v1")
        module_ids = {m["id"] for m in registry["modules"]}
        self.assertTrue(
            {
                "intent_normalization_kernel",
                "landing_zone_kernel",
                "authority_evidence_gate_kernel",
                "lifecycle_promotion_cleanup_kernel",
            }.issubset(module_ids)
        )

    def test_default_planner_consumes_four_core_registry_without_registry_arg(self):
        registry = self.mod.load_registry(self.mod.default_module_pool_dir() / "module_registry.json")
        plan = self.mod.plan_workflow_from_seed(
            "固化意图归一化、落点判定、权限证据门、生命周期晋级清理四个内核",
            registry,
        )
        self.assertEqual(
            plan["selected_modules"],
            [
                "intent_normalization_kernel",
                "landing_zone_kernel",
                "authority_evidence_gate_kernel",
                "lifecycle_promotion_cleanup_kernel",
            ],
        )
        self.assertEqual(plan["missing_capability_needs"], [])
        self.assertEqual(plan["authority_boundary"], "local_only")

    def test_usage_ledger_synthesizes_candidate_only_with_quality_signals(self):
        events = []
        combo = ["evidence_collector", "business_analysis", "presentation_builder"]
        for i in range(3):
            events.append(self.mod.usage_event("wf", combo, outcome="success", evidence_passed=True, human_intervention=False))
        candidates = self.mod.synthesize_module_candidates(events)
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate["status"], "candidate")
        self.assertEqual(candidate["composed_from"], combo)
        self.assertIn("frequency_plus_quality", candidate["reason"])
        self.assertFalse(candidate["side_effects_enabled"])

    def test_frequency_alone_does_not_synthesize_candidate(self):
        events = []
        combo = ["evidence_collector", "business_analysis"]
        for i in range(5):
            events.append(self.mod.usage_event("wf", combo, outcome="blocked", evidence_passed=False, human_intervention=True))
        candidates = self.mod.synthesize_module_candidates(events)
        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
