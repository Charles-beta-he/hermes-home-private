#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-disk-reclamation-receipt.py"


def load_module():
    spec = importlib.util.spec_from_file_location("disk_receipt_validator", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DiskReclamationReceiptValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.deleted = self.root / "deleted-artifact"
        self.preserved = self.root / "preserved.txt"
        self.preserved.write_text("keep", encoding="utf-8")
        stat = self.preserved.lstat()
        self.preserve_identity = {
            "path": str(self.preserved),
            "dev": stat.st_dev,
            "ino": stat.st_ino,
            "mode": stat.st_mode,
            "mtime_ns": stat.st_mtime_ns,
            "size": stat.st_size,
            "is_symlink": False,
            "sha256": sha256(self.preserved),
        }
        self.allowlist = self.root / "allowlist.json"
        self.allowlist.write_text(
            json.dumps(
                {
                    "schema": "hermes_disk_reclamation_allowlist_v1",
                    "root": str(self.root),
                    "preserve": [str(self.preserved)],
                    "delete_exact": [{"path": str(self.deleted), "allocated_bytes": 4096}],
                    "estimated_allocated_bytes": 4096,
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self.receipt = self.root / "receipt.json"
        self.receipt_data = {
            "schema": "hermes_disk_reclamation_receipt_v1",
            "status": "completed_verified",
            "authority": "test authority",
            "allowlist_path": str(self.allowlist),
            "allowlist_sha256": sha256(self.allowlist),
            "declared_root": str(self.root),
            "deleted_count": 1,
            "deleted": [
                {
                    "path": str(self.deleted),
                    "allocated_bytes": 4096,
                    "identity": {"path": str(self.deleted), "is_symlink": False},
                }
            ],
            "estimated_allocated_bytes": 4096,
            "free_bytes_before": 1000,
            "free_bytes_after": 5096,
            "free_bytes_delta": 4096,
            "parent_directories_fsynced": [str(self.root)],
            "preserve_before": [self.preserve_identity],
            "preserve_after": [self.preserve_identity],
            "residual_targets": [],
        }
        self.write_receipt()

    def tearDown(self):
        self.tempdir.cleanup()

    def write_receipt(self):
        self.receipt.write_text(json.dumps(self.receipt_data, sort_keys=True), encoding="utf-8")

    def test_valid_receipt_and_fresh_readback_pass(self):
        result = load_module().validate_receipt(
            self.receipt,
            expected_receipt_sha256=sha256(self.receipt),
            fresh=True,
        )
        self.assertEqual("pass", result["status"])
        self.assertTrue(result["historical_receipt_valid"])
        self.assertTrue(result["fresh_target_absence"])
        self.assertTrue(result["fresh_preserve_parity"])
        self.assertFalse(result["side_effects_performed"])

    def test_permission_only_mode_identity_is_supported(self):
        self.preserve_identity["mode"] = self.preserved.lstat().st_mode & 0o7777
        self.receipt_data["preserve_before"] = [self.preserve_identity]
        self.receipt_data["preserve_after"] = [self.preserve_identity]
        self.write_receipt()
        result = load_module().validate_receipt(self.receipt, fresh=True)
        self.assertEqual("pass", result["status"])
        self.assertTrue(result["fresh_preserve_parity"])

    def test_malformed_preserve_mode_fails_closed_without_exception(self):
        self.preserve_identity["mode"] = "not-an-int"
        self.receipt_data["preserve_before"] = [self.preserve_identity]
        self.receipt_data["preserve_after"] = [self.preserve_identity]
        self.write_receipt()
        result = load_module().validate_receipt(self.receipt, fresh=True)
        self.assertEqual("fail", result["status"])
        self.assertIn("fresh_preserve_identity_mismatch", result["errors"])

    def test_allowlist_hash_mismatch_fails_closed(self):
        changed = json.loads(self.allowlist.read_text(encoding="utf-8"))
        changed["purpose"] = "changed but still valid JSON"
        self.allowlist.write_text(json.dumps(changed, sort_keys=True), encoding="utf-8")
        result = load_module().validate_receipt(self.receipt)
        self.assertEqual("fail", result["status"])
        self.assertIn("allowlist_sha256_mismatch", result["errors"])

    def test_success_predicate_mismatches_fail_closed(self):
        self.receipt_data["deleted_count"] = 2
        self.receipt_data["residual_targets"] = [str(self.deleted)]
        self.receipt_data["preserve_after"] = []
        self.receipt_data["parent_directories_fsynced"] = []
        self.write_receipt()
        result = load_module().validate_receipt(self.receipt)
        self.assertEqual("fail", result["status"])
        self.assertIn("deleted_count_mismatch", result["errors"])
        self.assertIn("residual_targets_not_empty", result["errors"])
        self.assertIn("preserve_before_after_mismatch", result["errors"])
        self.assertIn("deleted_parent_not_fsynced", result["errors"])

    def test_fresh_existing_target_fails_without_deleting_it(self):
        self.deleted.mkdir()
        result = load_module().validate_receipt(self.receipt, fresh=True)
        self.assertEqual("fail", result["status"])
        self.assertFalse(result["fresh_target_absence"])
        self.assertTrue(self.deleted.is_dir())
        self.assertFalse(result["side_effects_performed"])

    def test_receipt_digest_mismatch_fails_closed(self):
        result = load_module().validate_receipt(
            self.receipt,
            expected_receipt_sha256="0" * 64,
        )
        self.assertEqual("fail", result["status"])
        self.assertIn("receipt_sha256_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
