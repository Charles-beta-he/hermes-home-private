import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from work_package_compiler import CompileError, compile_work_package, route_task


class WorkPackageCompilerTests(unittest.TestCase):
    def setUp(self):
        self.routing = json.loads((ROOT.parent / "model-routing.json").read_text(encoding="utf-8"))
        self.seed = json.loads((ROOT / "sample-seed.json").read_text(encoding="utf-8"))

    def test_routes_allowlisted_content_generation_to_low_cost(self):
        route = route_task(
            self.routing,
            task_type="generate_theme_variants",
            touched_fields={"theme", "copy"},
            confidence=0.92,
            platform_contract_known=True,
            prior_gate_failures=0,
        )
        self.assertEqual(route, "low_cost")

    def test_routes_protected_surface_change_to_high_reasoning(self):
        route = route_task(
            self.routing,
            task_type="generate_theme_variants",
            touched_fields={"theme", "win_condition"},
            confidence=0.99,
            platform_contract_known=True,
            prior_gate_failures=0,
        )
        self.assertEqual(route, "high_reasoning")

    def test_routes_low_confidence_to_high_reasoning(self):
        route = route_task(
            self.routing,
            task_type="generate_theme_variants",
            touched_fields={"theme"},
            confidence=0.4,
            platform_contract_known=True,
            prior_gate_failures=0,
        )
        self.assertEqual(route, "high_reasoning")

    def test_noncanonical_routing_is_rejected(self):
        routing = copy.deepcopy(self.routing)
        routing["protected_surfaces"] = ["unrelated"]
        with self.assertRaisesRegex(CompileError, "canonical routing"):
            compile_work_package(self.seed, routing)

    def test_blocks_unknown_platform_contract(self):
        route = route_task(
            self.routing,
            task_type="platform_doc_extraction",
            touched_fields={"platform_api"},
            confidence=0.99,
            platform_contract_known=False,
            prior_gate_failures=0,
        )
        self.assertEqual(route, "blocked")

    def test_compile_is_deterministic(self):
        first = compile_work_package(self.seed, self.routing)
        second = compile_work_package(copy.deepcopy(self.seed), self.routing)
        self.assertEqual(first, second)
        self.assertEqual(first["compile_digest"], second["compile_digest"])

    def test_rejects_content_override_of_protected_surface(self):
        invalid = copy.deepcopy(self.seed)
        invalid["content"]["win_condition"] = "always_win"
        with self.assertRaisesRegex(CompileError, "protected surface"):
            compile_work_package(invalid, self.routing)

    def test_rejects_out_of_bounds_level_parameter(self):
        invalid = copy.deepcopy(self.seed)
        invalid["content"]["level_parameters"]["grid_size"] = 99
        with self.assertRaisesRegex(CompileError, "out of bounds"):
            compile_work_package(invalid, self.routing)

    def test_content_swap_keeps_kernel_digest(self):
        first = compile_work_package(self.seed, self.routing)
        alternate = copy.deepcopy(self.seed)
        alternate["content"]["content_id"] = "space-station-repair-zh-cn"
        alternate["content"]["theme"] = "太空站供能"
        alternate["content"]["copy"]["title"] = "轨道供能"
        second = compile_work_package(alternate, self.routing)
        self.assertEqual(first["kernel_digest"], second["kernel_digest"])
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_low_cost_output_remains_candidate_only(self):
        result = compile_work_package(self.seed, self.routing)
        self.assertEqual(result["model_route"], "low_cost")
        self.assertEqual(result["closure_state"], "work_package_compiled")
        self.assertFalse(result["authority"]["may_publish"])
        self.assertFalse(result["authority"]["may_submit_platform"])
    def test_standard_route_output_also_remains_candidate_only_without_promotion_receipt(self):
        seed = copy.deepcopy(self.seed)
        seed["generation"]["task_type"] = "implement_frozen_spec"
        result = compile_work_package(seed, self.routing)
        self.assertEqual(result["model_route"], "standard")
        self.assertTrue(result["accuracy_contract"]["candidate_only"])

    def test_rejects_secondary_architecture_declarations(self):
        for bad_key in ["secondary_architecture_profile", "primary_clock_count", "secondary_primary_clock"]:
            bad = copy.deepcopy(self.seed)
            bad["kernel"][bad_key] = 2 if "count" in bad_key else "evil"
            with self.assertRaisesRegex(CompileError, "secondary|additional primary|architecture"):
                compile_work_package(bad, self.routing)

    def test_rejects_unreviewed_seed_kernel_content_and_generation_fields(self):
        for section in ["seed", "kernel", "content", "generation"]:
            bad = copy.deepcopy(self.seed)
            target = bad if section == "seed" else bad[section]
            target["unreviewed_extra"] = False
            with self.subTest(section=section), self.assertRaisesRegex(CompileError, "exact field inventory"):
                compile_work_package(bad, self.routing)

    def test_rejects_hostile_generation_semantics(self):
        for field, value in [
            ("task_type", False),
            ("confidence", True),
            ("confidence", -0.1),
            ("confidence", 1.1),
            ("template_version", 1),
        ]:
            bad = copy.deepcopy(self.seed)
            bad["generation"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(CompileError):
                compile_work_package(bad, self.routing)

    def test_rejects_hostile_kernel_and_content_nested_types(self):
        mutations = [
            ("kernel", "kernel_id", False),
            ("kernel", "version", 1),
            ("kernel", "state_fields", "grid"),
            ("kernel", "actions", ["rotate_node", 1]),
            ("kernel", "win_condition", []),
            ("kernel", "seed_policy", {}),
            ("kernel", "golden_cases", [""]),
            ("content", "content_id", False),
            ("content", "theme", []),
            ("content", "locale", {}),
            ("content", "copy", []),
            ("content", "level_parameters", []),
            ("content", "assets", {}),
        ]
        for section, field, value in mutations:
            bad = copy.deepcopy(self.seed)
            bad[section][field] = value
            with self.subTest(section=section, field=field), self.assertRaises(CompileError):
                compile_work_package(bad, self.routing)

        for mutation in [
            lambda seed: seed["kernel"]["tunable_parameters"]["grid_size"].update(min=True),
            lambda seed: seed["kernel"]["tunable_parameters"]["grid_size"].update(min=float("nan")),
            lambda seed: seed["kernel"]["tunable_parameters"]["grid_size"].update(max=float("inf")),
            lambda seed: seed["content"]["copy"].update(title=False),
            lambda seed: seed["content"]["level_parameters"].update(grid_size=True),
            lambda seed: seed["content"]["level_parameters"].update(grid_size=float("nan")),
            lambda seed: seed["content"]["level_parameters"].update(grid_size=float("inf")),
            lambda seed: seed["content"]["assets"][0].update(extra="x"),
            lambda seed: seed["content"]["assets"][0].update(ref=False),
            lambda seed: seed["content"]["level_parameters"].pop("moves"),
        ]:
            bad = copy.deepcopy(self.seed)
            mutation(bad)
            with self.assertRaises(CompileError):
                compile_work_package(bad, self.routing)


if __name__ == "__main__":
    unittest.main()
