#!/usr/bin/env python3
"""Contract tests for durable consult_models evidence bundles.

These tests exercise only the isolated persistence helper; no live
model/provider call is made and no production retention root is selected.
"""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent / "consult_models.py"
spec = importlib.util.spec_from_file_location("consult_models_stable_contract", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"unable to load {SCRIPT}")
consult = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consult)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestStableEvidenceBundleContract(unittest.TestCase):
    def make_tick(self, root: Path) -> Path:
        tick = root / "tick-contract"
        (tick / "plans").mkdir(parents=True)
        (tick / "final").mkdir()
        artifacts = {
            "plans/model-a.json": {"meta": {"planner_model": "model-a"}, "patches": []},
            "merged_plan.json": {"patches": [], "fanout_certification": {"status": "certified"}},
            "discussion_result.json": {"status": "certified", "models_consulted": ["model-a"]},
            "final/certification_manifest.json": {"status": "certified", "can_claim_complete_certification": True},
        }
        for rel, payload in artifacts.items():
            path = tick / rel
            path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        return tick

    def persist(self, tick: Path, stable_root: Path):
        self.assertTrue(
            hasattr(consult, "persist_stable_evidence_bundle"),
            "contract not implemented: persist_stable_evidence_bundle(tick_dir, stable_root, bundle_id)",
        )
        return consult.persist_stable_evidence_bundle(
            str(tick), str(stable_root), bundle_id="providers-quorum-contract"
        )

    def test_copies_required_artifacts_and_records_content_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            result = self.persist(tick, root / "stable")
            bundle = Path(result["bundle_dir"])
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))

            expected = {
                "plans/model-a.json",
                "merged_plan.json",
                "discussion_result.json",
                "final/certification_manifest.json",
            }
            self.assertEqual(set(manifest["files"]), expected)
            for rel in expected:
                copied = bundle / rel
                self.assertTrue(copied.is_file())
                self.assertEqual(manifest["files"][rel]["sha256"], sha256_file(copied))
                self.assertEqual(manifest["files"][rel]["size_bytes"], copied.stat().st_size)

    def test_fails_closed_when_required_artifact_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            (tick / "discussion_result.json").unlink()

            with self.assertRaisesRegex(ValueError, "missing required artifact.*discussion_result.json"):
                self.persist(tick, root / "stable")
            self.assertFalse((root / "stable" / "providers-quorum-contract").exists())

    def test_manifest_readback_is_complete_and_atomic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            result = self.persist(tick, root / "stable")
            bundle = Path(result["bundle_dir"])
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["schema_version"], "consult_models_stable_evidence_bundle_v1")
            self.assertEqual(manifest["bundle_id"], "providers-quorum-contract")
            self.assertEqual(Path(manifest["source_tick_dir"]).resolve(), tick.resolve())
            self.assertTrue(result["readback_verified"])
            self.assertEqual(result["manifest_sha256"], sha256_file(bundle / "manifest.json"))
            self.assertEqual(list(bundle.parent.glob(".providers-quorum-contract.tmp-*")), [])

    def test_rejects_malformed_required_json_without_publication(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            (tick / "merged_plan.json").write_text("{not-json\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "malformed or unreadable required artifact.*merged_plan.json"):
                self.persist(tick, root / "stable")
            self.assertFalse((root / "stable" / "providers-quorum-contract").exists())

    def test_rejects_symlinked_required_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            external = root / "external.json"
            external.write_text('{"status": "external"}\n', encoding="utf-8")
            artifact = tick / "discussion_result.json"
            artifact.unlink()
            artifact.symlink_to(external)

            with self.assertRaisesRegex(ValueError, "invalid required artifact.*discussion_result.json"):
                self.persist(tick, root / "stable")
            self.assertFalse((root / "stable" / "providers-quorum-contract").exists())

    def test_rejects_unsafe_bundle_ids(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            stable = root / "stable"
            for bundle_id in ("", ".hidden", "../escape", "nested/name", "space name"):
                with self.subTest(bundle_id=bundle_id):
                    with self.assertRaisesRegex(ValueError, "bundle_id must be a filesystem-safe name"):
                        consult.persist_stable_evidence_bundle(str(tick), str(stable), bundle_id=bundle_id)
            self.assertFalse(stable.exists())

    def test_existing_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            existing = root / "stable" / "providers-quorum-contract"
            existing.mkdir(parents=True)
            sentinel = existing / "sentinel.txt"
            sentinel.write_text("preserve-me\n", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "stable evidence bundle already exists"):
                self.persist(tick, root / "stable")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve-me\n")
            self.assertEqual(sorted(path.name for path in existing.iterdir()), ["sentinel.txt"])

    def test_prepublication_copy_failure_cleans_temporary_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            stable = root / "stable"

            with mock.patch.object(consult.shutil, "copyfileobj", side_effect=OSError("injected copy failure")):
                with self.assertRaisesRegex(OSError, "injected copy failure"):
                    self.persist(tick, stable)
            self.assertFalse((stable / "providers-quorum-contract").exists())
            self.assertEqual(list(stable.glob(".providers-quorum-contract.tmp-*")), [])


if __name__ == "__main__":
    unittest.main()
