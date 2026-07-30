import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from cocos_work_package_adapter import (
    IntegrationError,
    compile_cocos_integration,
    digest,
    materialize_candidate,
)


class CocosWorkPackageAdapterTests(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(
            (ROOT.parent / "evidence" / "sample-work-package.json").read_text(encoding="utf-8")
        )
        self.profile = json.loads(
            (ROOT.parent / "runtime" / "cocos" / "cocos-integration-profile.json").read_text(
                encoding="utf-8"
            )
        )

    def test_compiles_deterministic_candidate_only_packet(self):
        first = compile_cocos_integration(self.package, self.profile)
        second = compile_cocos_integration(copy.deepcopy(self.package), copy.deepcopy(self.profile))

        self.assertEqual(first, second)
        self.assertEqual(first["closure_state"], "cocos_integration_planned")
        self.assertEqual(first["engine"]["family"], "cocos-creator")
        self.assertEqual(first["engine"]["version_line"], "3.8")
        self.assertTrue(first["candidate_only"])
        self.assertEqual(
            {item["platform_id"] for item in first["platforms"]},
            {"douyin", "wechat"},
        )
        for value in first["authority"].values():
            self.assertFalse(value)

    def test_rejects_tampered_work_package_digest(self):
        with self.assertRaisesRegex(IntegrationError, "carrier must be an object"):
            compile_cocos_integration(cast(Any, []), self.profile)

        tampered = copy.deepcopy(self.package)
        tampered["content"]["theme"] = "tampered"

        with self.assertRaisesRegex(IntegrationError, "compile_digest"):
            compile_cocos_integration(tampered, self.profile)

    def test_rejects_rehashed_legacy_work_package_schema(self):
        legacy = copy.deepcopy(self.package)
        legacy["schema_version"] = 1
        legacy.pop("compile_digest")
        legacy["compile_digest"] = digest(legacy)
        with self.assertRaisesRegex(IntegrationError, "schema_version"):
            compile_cocos_integration(legacy, self.profile)

    def test_rejects_rehashed_noncanonical_architecture_binding(self):
        invalid = copy.deepcopy(self.package)
        invalid["kernel"]["architecture_profile"]["topology"]["time_model"] = "fixed_tick_real_time"
        invalid["kernel_digest"] = digest(invalid["kernel"])
        invalid.pop("compile_digest")
        invalid["compile_digest"] = digest(invalid)
        with self.assertRaisesRegex(IntegrationError, "architecture_profile"):
            compile_cocos_integration(invalid, self.profile)

        inconsistent = copy.deepcopy(self.package)
        inconsistent["architecture_profile"]["primary_profile_id"] = "real-time-physics"
        inconsistent.pop("compile_digest")
        inconsistent["compile_digest"] = digest(inconsistent)
        with self.assertRaisesRegex(IntegrationError, "architecture_profile"):
            compile_cocos_integration(inconsistent, self.profile)

    def test_rejects_rehashed_unknown_or_open_work_package_authority(self):
        unknown = copy.deepcopy(self.package)
        unknown["authority"]["may_freeze_kernel"] = False
        unknown.pop("compile_digest")
        unknown["compile_digest"] = digest(unknown)
        with self.assertRaisesRegex(IntegrationError, "authority"):
            compile_cocos_integration(unknown, self.profile)

        opened = copy.deepcopy(self.package)
        opened["authority"]["may_publish"] = True
        opened.pop("compile_digest")
        opened["compile_digest"] = digest(opened)
        with self.assertRaisesRegex(IntegrationError, "authority"):
            compile_cocos_integration(opened, self.profile)

    def test_rejects_unpinned_or_wrong_engine_profile(self):
        unpinned = copy.deepcopy(self.profile)
        unpinned["source_commit"] = ""
        with self.assertRaisesRegex(IntegrationError, "source_commit"):
            compile_cocos_integration(self.package, unpinned)

        wrong_engine = copy.deepcopy(self.profile)
        wrong_engine["engine_family"] = "godot"
        with self.assertRaisesRegex(IntegrationError, "cocos-creator"):
            compile_cocos_integration(self.package, wrong_engine)

        wrong_line = copy.deepcopy(self.profile)
        wrong_line["version_line"] = "4.0"
        with self.assertRaisesRegex(IntegrationError, "3.8"):
            compile_cocos_integration(self.package, wrong_line)

    def test_rejects_profile_that_opens_authority(self):
        unsafe = copy.deepcopy(self.profile)
        unsafe["authority"]["may_build_cocos"] = True
        with self.assertRaisesRegex(IntegrationError, "authority"):
            compile_cocos_integration(self.package, unsafe)

    def test_materializes_digest_bound_candidate_bundle(self):
        packet = compile_cocos_integration(self.package, self.profile)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "candidate"
            receipt = materialize_candidate(self.package, packet, root)
            manifest = json.loads((root / "candidate-manifest.json").read_text(encoding="utf-8"))
            disk_packet = json.loads((root / "integration-packet.json").read_text(encoding="utf-8"))

            self.assertEqual(receipt, manifest)
            self.assertEqual(disk_packet, packet)
            self.assertEqual(manifest["closure_state"], "cocos_candidate_materialized")
            self.assertFalse(manifest["authority"]["may_build_cocos"])
            self.assertEqual(
                set(manifest["files"]),
                {
                    "input/work-package.json",
                    "generated/gameplay-kernel.json",
                    "generated/content-pack.json",
                    "integration-packet.json",
                },
            )

    def test_rejects_rehashed_packet_that_opens_authority(self):
        packet = compile_cocos_integration(self.package, self.profile)
        packet["authority"]["may_build_cocos"] = True
        packet.pop("integration_digest")
        packet["integration_digest"] = digest(packet)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "candidate"
            with self.assertRaisesRegex(IntegrationError, "authority"):
                materialize_candidate(self.package, packet, root)
            self.assertFalse(root.exists())

    def test_rejects_rehashed_noncanonical_integration_packet_semantics(self):
        mutations = [
            lambda packet: packet["engine"].update(source_commit="0" * 40),
            lambda packet: packet["required_next_receipts"].clear(),
            lambda packet: packet.update(unreviewed_extra=False),
            lambda packet: packet["materialization_contract"].update(generated_files=False),
            lambda packet: packet["platforms"][0].update(authority={"may_publish": True}),
        ]
        for mutation in mutations:
            packet = compile_cocos_integration(self.package, self.profile)
            mutation(packet)
            packet.pop("integration_digest", None)
            packet["integration_digest"] = digest(packet)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "candidate"
                with self.assertRaises(IntegrationError):
                    materialize_candidate(self.package, packet, root)
                self.assertFalse(root.exists())

    def test_rejects_profile_with_unknown_nested_platform_authority(self):
        unsafe = copy.deepcopy(self.profile)
        unsafe["platforms"][0]["authority"] = {"may_publish": True}
        with self.assertRaisesRegex(IntegrationError, "platform"):
            compile_cocos_integration(self.package, unsafe)

    def test_rejects_symlink_materialization_root(self):
        packet = compile_cocos_integration(self.package, self.profile)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            target = base / "target"
            target.mkdir()
            link = base / "candidate"
            os.symlink(target, link)

            with self.assertRaisesRegex(IntegrationError, "symbolic link"):
                materialize_candidate(self.package, packet, link)
            self.assertEqual(list(target.iterdir()), [])

    def test_rejects_symlink_in_materialization_ancestor_chain(self):
        packet = compile_cocos_integration(self.package, self.profile)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            outside = base / "outside"
            outside.mkdir()
            link = base / "link"
            os.symlink(outside, link)
            parent = link / "parent"
            parent.mkdir()
            root = parent / "candidate"

            with self.assertRaisesRegex(IntegrationError, "symbolic link"):
                materialize_candidate(self.package, packet, root)
            self.assertFalse(root.exists())
            self.assertEqual(list(parent.iterdir()), [])

    def test_rejects_hostile_types_in_work_package_v2_fields(self):
        # work_package_id, model_route, generation, required_gates, accuracy_contract must have correct types
        for hostile in [False, True, 0, 1, 1.5, None, [], {}, ""]:
            # work_package_id
            bad = copy.deepcopy(self.package)
            bad["work_package_id"] = hostile
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.assertRaises(IntegrationError):
                compile_cocos_integration(bad, self.profile)

            # model_route
            bad = copy.deepcopy(self.package)
            bad["model_route"] = hostile
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.assertRaises(IntegrationError):
                compile_cocos_integration(bad, self.profile)

        # required_gates hostile
        for hostile in [False, 0, None, {}, "not-a-list", [""]]:
            bad = copy.deepcopy(self.package)
            bad["required_gates"] = hostile
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.assertRaises(IntegrationError):
                compile_cocos_integration(bad, self.profile)

        # accuracy_contract hostile / extra field
        bad = copy.deepcopy(self.package)
        bad["accuracy_contract"] = {"same_gates_for_all_models": True, "model_self_report_is_evidence": True, "candidate_only": True, "evil_extra": 1}
        bad.pop("compile_digest", None)
        bad["compile_digest"] = digest(bad)
        with self.assertRaises(IntegrationError):
            compile_cocos_integration(bad, self.profile)

        bad = copy.deepcopy(self.package)
        bad["accuracy_contract"]["candidate_only"] = False
        bad.pop("compile_digest", None)
        bad["compile_digest"] = digest(bad)
        with self.assertRaises(IntegrationError):
            compile_cocos_integration(bad, self.profile)

    def test_rejects_secondary_architecture_declarations_in_kernel(self):
        for bad_key in ["secondary_architecture_profile", "primary_clock_count", "secondary_primary_clock", "architecture_profiles"]:
            bad = copy.deepcopy(self.package)
            bad["kernel"][bad_key] = 2 if "count" in bad_key else "evil"
            bad["kernel_digest"] = digest(bad["kernel"])
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.assertRaisesRegex(IntegrationError, "secondary|additional primary|architecture"):
                compile_cocos_integration(bad, self.profile)

    def test_rejects_rehashed_noncanonical_compiler_semantics(self):
        mutations = [
            ("work_package_id", "forged-id"),
            ("model_route", "standard"),
            ("required_gates", []),
        ]
        for field, value in mutations:
            bad = copy.deepcopy(self.package)
            bad[field] = value
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.subTest(field=field), self.assertRaises(IntegrationError):
                compile_cocos_integration(bad, self.profile)

        for field, value in [
            ("template_version", 1),
            ("confidence", 2.0),
        ]:
            bad = copy.deepcopy(self.package)
            bad["generation"][field] = value
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.subTest(field=field), self.assertRaises(IntegrationError):
                compile_cocos_integration(bad, self.profile)

        for field, value in [
            ("same_gates_for_all_models", []),
            ("model_self_report_is_evidence", True),
        ]:
            bad = copy.deepcopy(self.package)
            bad["accuracy_contract"][field] = value
            bad.pop("compile_digest", None)
            bad["compile_digest"] = digest(bad)
            with self.subTest(field=field), self.assertRaises(IntegrationError):
                compile_cocos_integration(bad, self.profile)

    def test_rejects_rehashed_incomplete_or_extra_kernel_and_content(self):
        for section in ["kernel", "content"]:
            empty = copy.deepcopy(self.package)
            empty[section] = {}
            empty[f"{section}_digest"] = digest(empty[section])
            empty.pop("compile_digest", None)
            empty["compile_digest"] = digest(empty)
            with self.subTest(section=section, case="empty"), self.assertRaises(IntegrationError):
                compile_cocos_integration(empty, self.profile)

            extra = copy.deepcopy(self.package)
            extra[section]["unreviewed_extra"] = False
            extra[f"{section}_digest"] = digest(extra[section])
            extra.pop("compile_digest", None)
            extra["compile_digest"] = digest(extra)
            with self.subTest(section=section, case="extra"), self.assertRaises(IntegrationError):
                compile_cocos_integration(extra, self.profile)


if __name__ == "__main__":
    unittest.main()
