import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

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
        tampered = copy.deepcopy(self.package)
        tampered["content"]["theme"] = "tampered"

        with self.assertRaisesRegex(IntegrationError, "compile_digest"):
            compile_cocos_integration(tampered, self.profile)

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


if __name__ == "__main__":
    unittest.main()
