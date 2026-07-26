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


if __name__ == "__main__":
    unittest.main()
