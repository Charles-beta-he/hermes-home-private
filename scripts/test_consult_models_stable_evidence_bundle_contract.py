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

    def test_postpublication_readback_failure_is_quarantined_with_receipt(self):
        """A published-but-unverified bundle must not remain at its success path."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            stable = root / "stable"
            final = stable / "providers-quorum-contract"
            real_sha256_path = consult._sha256_path
            hash_calls = 0

            def fail_only_first_final_artifact_readback(path):
                nonlocal hash_calls
                hash_calls += 1
                # Four hashes validate the source artifacts. The fifth is the
                # first copied-artifact readback after atomic publication.
                if hash_calls == 5:
                    return "0" * 64
                return real_sha256_path(Path(path))

            with mock.patch.object(
                consult,
                "_sha256_path",
                side_effect=fail_only_first_final_artifact_readback,
            ):
                with self.assertRaisesRegex(RuntimeError, "stable evidence artifact readback mismatch"):
                    self.persist(tick, stable)

            self.assertFalse(final.exists(), "unverified bundle must not remain at the success path")
            quarantine = sorted((stable / ".quarantine").glob("providers-quorum-contract-*"))
            self.assertEqual(len(quarantine), 1)
            self.assertTrue((quarantine[0] / "manifest.json").is_file())

            receipts = sorted((stable / ".failure-receipts").glob("providers-quorum-contract-*.json"))
            self.assertEqual(len(receipts), 1)
            receipt = json.loads(receipts[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema_version"], "consult_models_stable_evidence_failure_v1")
            self.assertEqual(receipt["bundle_id"], "providers-quorum-contract")
            self.assertEqual(receipt["status"], "quarantined")
            self.assertEqual(receipt["failure_kind"], "postpublication_readback_failed")
            self.assertEqual(Path(receipt["quarantine_dir"]).resolve(), quarantine[0].resolve())
            self.assertNotIn("readback_verified", receipt)

    def test_quarantine_rename_failure_preserves_primary_and_secondary_diagnostics(self):
        """A quarantine failure must not erase the verification failure that triggered it."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            stable = root / "stable"
            final = stable / "providers-quorum-contract"
            real_sha256_path = consult._sha256_path
            real_rename = consult.os.rename
            hash_calls = 0

            def fail_only_first_final_artifact_readback(path):
                nonlocal hash_calls
                hash_calls += 1
                if hash_calls == 5:
                    return "0" * 64
                return real_sha256_path(Path(path))

            def fail_only_quarantine_rename(source, destination):
                # stable_root is canonicalized by the helper; on macOS a
                # TemporaryDirectory may be spelled through /var while its
                # resolved path is /private/var. Match the operation boundary,
                # not the caller's non-canonical path spelling.
                if (
                    Path(source).name == final.name
                    and Path(destination).parent.name == ".quarantine"
                ):
                    raise OSError("injected quarantine rename failure")
                return real_rename(source, destination)

            with mock.patch.object(
                consult,
                "_sha256_path",
                side_effect=fail_only_first_final_artifact_readback,
            ), mock.patch.object(consult.os, "rename", side_effect=fail_only_quarantine_rename):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "postpublication verification failed.*stable evidence artifact readback mismatch.*"
                    "quarantine failed.*injected quarantine rename failure",
                ):
                    self.persist(tick, stable)

            self.assertTrue(final.is_dir(), "failed quarantine leaves bytes outside verified success semantics")
            self.assertEqual(list((stable / ".quarantine").glob("providers-quorum-contract-*")), [])
            self.assertFalse((stable / ".failure-receipts").exists())

    def test_failure_receipt_publication_failure_preserves_primary_and_secondary_diagnostics(self):
        """Receipt failure is diagnostic-only after quarantine, but must be visible to the caller."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tick = self.make_tick(root)
            stable = root / "stable"
            final = stable / "providers-quorum-contract"
            real_sha256_path = consult._sha256_path
            real_rename = consult.os.rename
            hash_calls = 0

            def fail_only_first_final_artifact_readback(path):
                nonlocal hash_calls
                hash_calls += 1
                if hash_calls == 5:
                    return "0" * 64
                return real_sha256_path(Path(path))

            def fail_only_receipt_publication(source, destination):
                if Path(destination).parent.name == ".failure-receipts":
                    raise OSError("injected failure receipt publication failure")
                return real_rename(source, destination)

            with mock.patch.object(
                consult,
                "_sha256_path",
                side_effect=fail_only_first_final_artifact_readback,
            ), mock.patch.object(consult.os, "rename", side_effect=fail_only_receipt_publication):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "postpublication verification failed.*stable evidence artifact readback mismatch.*"
                    "failure receipt publication failed.*injected failure receipt publication failure",
                ):
                    self.persist(tick, stable)

            self.assertFalse(final.exists())
            quarantine = list((stable / ".quarantine").glob("providers-quorum-contract-*"))
            self.assertEqual(len(quarantine), 1, "quarantine remains authoritative without a receipt")
            receipt_root = stable / ".failure-receipts"
            self.assertEqual(list(receipt_root.glob("providers-quorum-contract-*.json")), [])
            self.assertEqual(list(receipt_root.glob(".*.tmp-*")), [])


if __name__ == "__main__":
    unittest.main()
