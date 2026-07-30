import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))

from gameplay_architecture_profiles import (
    ArchitectureProfileError,
    load_canonical_registry,
    validate_kernel_architecture,
    validate_registry,
)
from work_package_compiler import CompileError, compile_work_package, route_task


class GameplayArchitectureProfileTests(unittest.TestCase):
    def setUp(self):
        self.registry = load_canonical_registry()
        self.routing = json.loads((PROJECT / "model-routing.json").read_text(encoding="utf-8"))
        self.seed = json.loads((ROOT / "sample-seed.json").read_text(encoding="utf-8"))

    def test_registry_has_shared_shell_and_required_primary_profiles(self):
        validate_registry(self.registry)
        self.assertTrue(
            {
                "grid-turn",
                "board-resolver",
                "wave-path",
                "real-time-physics",
                "card-event-stack",
                "economy-time-simulation",
                "authoritative-replication",
            }.issubset({profile["profile_id"] for profile in self.registry["profiles"]}),
        )
        self.assertIn("lifecycle", self.registry["shared_shell"]["capabilities"])
        self.assertIn("visual_style", self.registry["presentation_only_fields"])

    def test_sample_kernel_binds_exact_canonical_grid_turn_profile(self):
        result = validate_kernel_architecture(self.seed["kernel"])
        self.assertEqual(result["primary_profile_id"], "grid-turn")
        self.assertEqual(len(result["profile_digest"]), 64)
        self.assertEqual(len(result["registry_digest"]), 64)

    def test_compiler_binds_profile_identity_and_digest(self):
        package = compile_work_package(self.seed, self.routing)
        self.assertEqual(package["schema_version"], 2)
        self.assertEqual(package["architecture_profile"]["primary_profile_id"], "grid-turn")
        self.assertEqual(package["architecture_profile"]["registry_id"], self.registry["registry_id"])
        self.assertEqual(len(package["architecture_profile"]["profile_digest"]), 64)

    def test_missing_architecture_profile_fails_closed(self):
        invalid = copy.deepcopy(self.seed)
        invalid["kernel"].pop("architecture_profile", None)
        with self.assertRaisesRegex(CompileError, "architecture_profile"):
            compile_work_package(invalid, self.routing)

    def test_binding_rejects_extra_visual_style_field(self):
        invalid = copy.deepcopy(self.seed["kernel"])
        invalid["architecture_profile"]["visual_style"] = "pixel"
        with self.assertRaisesRegex(ArchitectureProfileError, "exact fields"):
            validate_kernel_architecture(invalid)

    def test_binding_rejects_unknown_profile(self):
        invalid = copy.deepcopy(self.seed["kernel"])
        invalid["architecture_profile"]["profile_id"] = "pixel-cartoon"
        with self.assertRaisesRegex(ArchitectureProfileError, "unknown primary profile"):
            validate_kernel_architecture(invalid)

    def test_binding_rejects_missing_and_unknown_fields(self):
        missing = copy.deepcopy(self.seed["kernel"])
        missing["architecture_profile"].pop("auxiliary_systems")
        with self.assertRaisesRegex(ArchitectureProfileError, "exact fields"):
            validate_kernel_architecture(missing)

        extra = copy.deepcopy(self.seed["kernel"])
        extra["architecture_profile"]["trusted"] = False
        with self.assertRaisesRegex(ArchitectureProfileError, "exact fields"):
            validate_kernel_architecture(extra)

    def test_binding_rejects_non_string_profile_id_and_boolean_version(self):
        invalid_id = copy.deepcopy(self.seed["kernel"])
        invalid_id["architecture_profile"]["profile_id"] = []
        with self.assertRaisesRegex(ArchitectureProfileError, "profile_id"):
            validate_kernel_architecture(invalid_id)

        invalid_version = copy.deepcopy(self.seed["kernel"])
        invalid_version["architecture_profile"]["profile_version"] = True
        with self.assertRaisesRegex(ArchitectureProfileError, "version"):
            validate_kernel_architecture(invalid_version)

    def test_binding_rejects_topology_mismatch(self):
        invalid = copy.deepcopy(self.seed["kernel"])
        invalid["architecture_profile"]["topology"]["time_model"] = "fixed_tick_real_time"
        with self.assertRaisesRegex(ArchitectureProfileError, "topology"):
            validate_kernel_architecture(invalid)

    def test_auxiliary_system_cannot_repeat_primary_or_duplicate(self):
        primary = copy.deepcopy(self.seed["kernel"])
        primary["architecture_profile"]["auxiliary_systems"] = ["grid-turn"]
        with self.assertRaisesRegex(ArchitectureProfileError, "primary profile"):
            validate_kernel_architecture(primary)

        duplicate = copy.deepcopy(self.seed["kernel"])
        duplicate["architecture_profile"]["auxiliary_systems"] = ["card-event-stack", "card-event-stack"]
        with self.assertRaisesRegex(ArchitectureProfileError, "duplicate"):
            validate_kernel_architecture(duplicate)

    def test_auxiliary_system_rejects_unknown_profile(self):
        invalid = copy.deepcopy(self.seed["kernel"])
        invalid["architecture_profile"]["auxiliary_systems"] = ["unknown-system"]
        with self.assertRaisesRegex(ArchitectureProfileError, "unknown auxiliary"):
            validate_kernel_architecture(invalid)

    def test_registry_rejects_unknown_top_level_field(self):
        invalid = copy.deepcopy(self.registry)
        invalid["trusted"] = True
        with self.assertRaisesRegex(ArchitectureProfileError, "registry exact fields"):
            validate_registry(invalid)

    def test_registry_rejects_non_integer_schema_and_extra_profile(self):
        invalid_schema = copy.deepcopy(self.registry)
        invalid_schema["schema_version"] = 1.0
        with self.assertRaisesRegex(ArchitectureProfileError, "schema_version"):
            validate_registry(invalid_schema)

        invalid_inventory = copy.deepcopy(self.registry)
        extra = copy.deepcopy(invalid_inventory["profiles"][0])
        extra["profile_id"] = "unreviewed-extra-profile"
        invalid_inventory["profiles"].append(extra)
        with self.assertRaisesRegex(ArchitectureProfileError, "exactly canonical"):
            validate_registry(invalid_inventory)

    def test_content_cannot_override_architecture_profile(self):
        invalid = copy.deepcopy(self.seed)
        invalid["content"]["architecture_profile"] = "real-time-physics"
        with self.assertRaisesRegex(CompileError, "protected surface"):
            compile_work_package(invalid, self.routing)

    def test_visual_style_content_change_does_not_change_profile_digest(self):
        first = compile_work_package(self.seed, self.routing)
        alternate = copy.deepcopy(self.seed)
        alternate["content"]["content_id"] = "pixel-grid-variant"
        alternate["content"]["visual_style"] = "pixel"
        second = compile_work_package(alternate, self.routing)
        self.assertEqual(
            first["architecture_profile"]["profile_digest"],
            second["architecture_profile"]["profile_digest"],
        )
        self.assertNotEqual(first["content_digest"], second["content_digest"])

    def test_architecture_profile_is_a_protected_surface(self):
        route = route_task(
            self.routing,
            task_type="generate_theme_variants",
            touched_fields={"architecture_profile"},
            confidence=0.99,
            platform_contract_known=True,
            prior_gate_failures=0,
        )
        self.assertEqual(route, "high_reasoning")

    def test_rejects_secondary_or_extra_primary_architecture_in_kernel(self):
        from gameplay_architecture_profiles import validate_kernel_architecture, ArchitectureProfileError
        kernel = copy.deepcopy(self.seed["kernel"])
        for bad_key in ["secondary_architecture_profile", "primary_clock_count", "secondary_primary_clock"]:
            bad_kernel = copy.deepcopy(kernel)
            bad_kernel[bad_key] = 2 if "count" in bad_key else True
            with self.assertRaisesRegex(ArchitectureProfileError, "secondary|additional primary|architecture"):
                validate_kernel_architecture(bad_kernel)


if __name__ == "__main__":
    unittest.main()
