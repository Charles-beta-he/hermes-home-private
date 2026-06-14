#!/usr/bin/env python3
"""Tests for local_brain_turbovec_adapter.py."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent / "local_brain_turbovec_adapter.py"
spec = importlib.util.spec_from_file_location("local_brain_turbovec_adapter", SCRIPT)
assert spec is not None and spec.loader is not None
adapter = importlib.util.module_from_spec(spec)
sys.modules["local_brain_turbovec_adapter"] = adapter
spec.loader.exec_module(adapter)


class BackendResolutionTestCase(unittest.TestCase):
    def test_default_backend_is_tfidf(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            resolution = adapter.resolve_backend()
        self.assertEqual(resolution.requested, "tfidf")
        self.assertEqual(resolution.active, "tfidf")
        self.assertIsNone(resolution.fallback_reason)

    def test_turbovec_request_falls_back_without_prototype_flag(self) -> None:
        env = {
            adapter.BACKEND_ENV_VAR: "turbovec",
            adapter.PROTOTYPE_ENV_VAR: "0",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            resolution = adapter.resolve_backend()
        self.assertEqual(resolution.requested, "turbovec")
        self.assertEqual(resolution.active, "tfidf")
        self.assertEqual(resolution.fallback_reason, "prototype-disabled")

    def test_invalid_backend_raises(self) -> None:
        with self.assertRaises(ValueError):
            adapter.resolve_backend("bogus")


@unittest.skipUnless(adapter.turbovec_available(), "turbovec dependency not installed")
class TurboVecAdapterRoundTripTestCase(unittest.TestCase):
    DIM = 8

    def _docs(self):
        return [
            {
                "key": "doc-a",
                "title": "Alpha",
                "path": "synthetic/a.md",
                "vector": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "metadata": {"tenant": "alpha", "kind": "note"},
            },
            {
                "key": "doc-b",
                "title": "Beta",
                "path": "synthetic/b.md",
                "vector": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "metadata": {"tenant": "beta", "kind": "note"},
            },
            {
                "key": "doc-c",
                "title": "Gamma",
                "path": "synthetic/c.md",
                "vector": [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "metadata": {"tenant": "alpha", "kind": "plan"},
            },
        ]

    def test_add_search_filter_persist_load_remove(self) -> None:
        index = adapter.TurboVecAdapter(dim=self.DIM, bit_width=4)
        report = index.add(self._docs())
        self.assertEqual(report["added"], 3)

        results = index.search([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], top_k=2)
        self.assertEqual(results[0]["key"], "doc-a")

        filtered = index.search(
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            top_k=3,
            metadata_filter={"tenant": "alpha"},
        )
        self.assertTrue(filtered)
        self.assertTrue(all(item["metadata"]["tenant"] == "alpha" for item in filtered))

        allowlisted = index.search(
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            top_k=2,
            allow_keys=["doc-c"],
        )
        self.assertEqual([item["key"] for item in allowlisted], ["doc-c"])

        with tempfile.TemporaryDirectory() as td:
            persisted = index.persist(td)
            self.assertTrue(Path(persisted["index_path"]).exists())
            self.assertTrue(Path(persisted["manifest_path"]).exists())
            loaded = adapter.TurboVecAdapter.load(td)
            loaded_results = loaded.search([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], top_k=2)
            self.assertEqual(loaded_results[0]["key"], "doc-a")
            self.assertTrue(loaded.remove("doc-b"))
            self.assertFalse(loaded.contains("doc-b"))

    def test_benchmark_reports_all_verifications(self) -> None:
        with mock.patch.dict(os.environ, {adapter.PROTOTYPE_ENV_VAR: "1"}, clear=False):
            report = adapter.run_synthetic_benchmark(num_docs=32, dim=8, queries=2, top_k=3, bit_width=4)
        self.assertEqual(report["schema"], adapter.SCHEMA_VERSION)
        self.assertTrue(all(report["verifications"].values()))
        self.assertEqual(report["resolution"]["active"], "tfidf")

    def test_status_cli_emits_json(self) -> None:
        proc = __import__("subprocess").run(
            [sys.executable, str(SCRIPT), "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], adapter.SCHEMA_VERSION)
        self.assertIn("resolution", payload)


if __name__ == "__main__":
    unittest.main()
