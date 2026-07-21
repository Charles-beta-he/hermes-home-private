#!/usr/bin/env python3
"""Failing contract tests for durable consult_models evidence bundles.

These tests intentionally describe the next implementation boundary. They must
remain red until consult_models.persist_stable_evidence_bundle() is implemented;
no live model/provider call is made.
"""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
