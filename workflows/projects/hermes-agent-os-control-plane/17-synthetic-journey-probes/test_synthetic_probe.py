from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "synthetic_probe.py"


def load_module():
    spec = importlib.util.spec_from_file_location("synthetic_probe", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load synthetic_probe module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SyntheticProbeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        (self.root / "state" / "doctor.json").write_text(
            json.dumps({"ok": True, "findings": [], "nested": {"count": 2}}),
            encoding="utf-8",
        )
        self.probe = {
            "schema": "hermes_synthetic_probe_v1",
            "probe_id": "test.doctor",
            "enabled": False,
            "mode": "local_read_only",
            "steps": [{
                "id": "doctor",
                "adapter": "json_readback",
                "target": "state/doctor.json",
                "assertions": {"ok": True, "findings": [], "nested.count": 2},
            }],
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_validate_only_is_default_off_and_does_not_read_target(self):
        (self.root / "state" / "doctor.json").unlink()
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=False)
        self.assertTrue(receipt["ok"])
        self.assertFalse(receipt["would_execute"])
        self.assertFalse(receipt["executed"])
        self.assertEqual(receipt["steps"], [])
        self.assertEqual(receipt["journey_target_read_attempts"], 0)
        self.assertEqual(receipt["journey_target_reads_succeeded"], 0)
        self.assertEqual(receipt["side_effects_observed"], ["local_read"])

    def test_explicit_run_reads_real_json_and_emits_digest_only(self):
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertTrue(receipt["ok"])
        self.assertTrue(receipt["executed"])
        self.assertEqual(receipt["status"], "pass")
        self.assertEqual(len(receipt["steps"][0]["target_sha256"]), 64)
        self.assertEqual(receipt["journey_target_read_attempts"], 1)
        self.assertEqual(receipt["journey_target_reads_succeeded"], 1)
        self.assertNotIn("source", receipt["steps"][0])
        self.assertTrue(receipt["negative_assertions"]["no_external_dispatch"])
        self.assertTrue(receipt["negative_assertions"]["no_lifecycle_write"])
        self.assertTrue(receipt["exclude_from_learning"])

    def test_assertion_mismatch_fails_closed(self):
        self.probe["steps"][0]["assertions"]["ok"] = False
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertFalse(receipt["ok"])
        self.assertEqual(receipt["status"], "fail")
        self.assertIn("assertion_mismatch:ok", receipt["findings"])

    def test_parent_escape_is_rejected(self):
        self.probe["steps"][0]["target"] = "../secret.json"
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertFalse(receipt["ok"])
        self.assertIn("target_outside_project_root", receipt["findings"])

    def test_absolute_target_is_rejected(self):
        self.probe["steps"][0]["target"] = "/tmp/secret.json"
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertFalse(receipt["ok"])
        self.assertIn("target_must_be_relative", receipt["findings"])

    def test_symlink_target_is_rejected(self):
        outside = self.root / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        (self.root / "state" / "link.json").symlink_to(outside)
        self.probe["steps"][0]["target"] = "state/link.json"
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertFalse(receipt["ok"])
        self.assertIn("target_symlink_forbidden", receipt["findings"])

    def test_unknown_adapter_is_rejected_before_execution(self):
        self.probe["steps"][0]["adapter"] = "shell"
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertFalse(receipt["ok"])
        self.assertFalse(receipt["executed"])
        self.assertIn("unsupported_adapter:shell", receipt["findings"])

    def test_explicit_output_is_atomic_and_scoped(self):
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        out = HERE / "runtime" / "test-receipt.json"
        try:
            self.module._write_scoped_atomic(out, receipt)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(payload["ok"])
            self.assertFalse(any(out.parent.glob(f".{out.name}.*.tmp")))
        finally:
            out.unlink(missing_ok=True)

    def test_oversized_target_is_rejected(self):
        (self.root / "state" / "doctor.json").write_bytes(b"0" * (self.module.MAX_TARGET_BYTES + 1))
        receipt = self.module.evaluate_probe(self.probe, project_root=self.root, execute=True)
        self.assertFalse(receipt["ok"])
        self.assertIn("target_too_large", receipt["findings"])

    def test_output_path_traversal_is_rejected(self):
        escaped = HERE / "runtime" / ".." / ".." / "escaped-receipt.json"
        with self.assertRaisesRegex(ValueError, "output_outside_allowed_receipt_dirs"):
            self.module._write_scoped_atomic(escaped, {"ok": True})
        self.assertFalse((HERE.parent / "escaped-receipt.json").exists())

    def test_output_cannot_overwrite_capability_source(self):
        before = MODULE_PATH.read_bytes()
        with self.assertRaisesRegex(ValueError, "output_outside_allowed_receipt_dirs"):
            self.module._write_scoped_atomic(MODULE_PATH, {"ok": True})
        self.assertEqual(MODULE_PATH.read_bytes(), before)

    def test_source_has_no_network_model_or_command_adapter(self):
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    called_names.add(f"{node.func.value.id}.{node.func.attr}")
        self.assertTrue(imported_roots.isdisjoint({"boto3", "requests", "urllib", "http", "socket", "subprocess"}))
        self.assertTrue(called_names.isdisjoint({"eval", "exec", "compile", "os.system", "os.popen", "os.execv", "os.spawnv"}))

    def test_output_outside_capability_root_is_rejected(self):
        outside = self.root / "receipt.json"
        with self.assertRaisesRegex(ValueError, "output_outside_allowed_receipt_dirs"):
            self.module._write_scoped_atomic(outside, {"ok": True})
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
