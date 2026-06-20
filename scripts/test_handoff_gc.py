#!/usr/bin/env python3
"""Focused tests for read-only handoff-gc report."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path.home() / ".hermes" / "scripts"
SCRIPT = SCRIPTS / "handoff-gc.py"


def load_module():
    spec = importlib.util.spec_from_file_location("handoff_gc_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HandoffGcReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.dir_a = self.root / "auto"
        self.dir_b = self.root / "parallel"
        self.dir_a.mkdir()
        self.dir_b.mkdir()
        self.gc = load_module()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_build_report_includes_counts_bytes_and_sha_manifest(self) -> None:
        first = self.dir_a / "first.json"
        second = self.dir_b / "second.json"
        first.write_text("alpha", encoding="utf-8")
        second.write_text("beta-beta", encoding="utf-8")

        report = self.gc.build_report([self.dir_a, self.dir_b], manifest_limit=5, largest_limit=5)

        self.assertEqual(report["schema"], "handoff_backlog_report_v1")
        self.assertIn("read-only", report["safety"])
        self.assertEqual(report["total_count"], 2)
        self.assertEqual(report["total_bytes"], len("alpha") + len("beta-beta"))
        manifest = report["dirs"][0]["manifest_sample"]
        self.assertEqual(manifest[0]["name"], "first.json")
        self.assertEqual(len(manifest[0]["sha256"]), 64)

    def test_report_is_read_only(self) -> None:
        path = self.dir_a / "keep.json"
        path.write_text("keep", encoding="utf-8")

        self.gc.build_report([self.dir_a], manifest_limit=1, largest_limit=1)

        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(encoding="utf-8"), "keep")

    def test_missing_directory_reports_zero(self) -> None:
        missing = self.root / "missing"

        report = self.gc.build_report([missing])

        self.assertEqual(report["total_count"], 0)
        self.assertFalse(report["dirs"][0]["exists"])

    def test_archive_plan_keeps_newest_and_apply_moves_with_manifest(self) -> None:
        files = []
        for i in range(5):
            path = self.dir_a / f"handoff-{i}.md"
            path.write_text(f"handoff {i}", encoding="utf-8")
            files.append(path)

        plan = self.gc.plan_archive(self.dir_a, keep_newest=2)
        self.assertEqual(plan["current_count"], 5)
        self.assertEqual(plan["archive_count"], 3)

        dry = self.gc.apply_archive(plan, dry_run=True)
        self.assertEqual(dry["planned_count"], 3)
        self.assertTrue(all(path.exists() for path in files))

        applied = self.gc.apply_archive(plan, dry_run=False)
        self.assertEqual(applied["moved_count"], 3)
        self.assertTrue(Path(applied["manifest_path"]).exists())
        self.assertEqual(len(list(self.dir_a.glob("*.md"))), 2)


if __name__ == "__main__":
    unittest.main()
