#!/usr/bin/env python3
"""Focused tests for continuation-gc cap and dry-run behavior."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS = Path.home() / ".hermes" / "scripts"
SCRIPT = SCRIPTS / "continuation-gc.py"


def load_module():
    spec = importlib.util.spec_from_file_location("continuation_gc_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContinuationGcTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "active").mkdir(parents=True)
        (self.root / "archived").mkdir(parents=True)
        self.gc = load_module()
        self.now = datetime(2026, 6, 20, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_packet(self, subdir: str, name: str, *, days_old: int, task_id: str = "task") -> Path:
        path = self.root / subdir / name
        payload = {
            "created_at": (self.now - timedelta(days=days_old)).isoformat(),
            "task_id": task_id,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_dry_run_reports_without_moving_or_deleting(self) -> None:
        active_old = self.write_packet("active", "old.json", days_old=8)
        archived_old = self.write_packet("archived", "arch-old.json", days_old=31)

        result = self.gc.run(dry_run=True, now=self.now, root=self.root)

        self.assertEqual(result["archived_count"], 1)
        self.assertEqual(result["deleted_count"], 1)
        self.assertTrue(result["dry_run"])
        self.assertTrue(active_old.exists())
        self.assertTrue(archived_old.exists())

    def test_active_max_archives_oldest_surplus_only_when_configured(self) -> None:
        oldest = self.write_packet("active", "a.json", days_old=3, task_id="a")
        self.write_packet("active", "b.json", days_old=2, task_id="b")
        self.write_packet("active", "c.json", days_old=1, task_id="c")

        result = self.gc.run(dry_run=False, now=self.now, root=self.root, active_max=2)

        self.assertEqual(result["archived_count"], 1)
        self.assertFalse(oldest.exists())
        self.assertTrue((self.root / "archived" / "a.json").exists())
        self.assertEqual(result["reason_counts"], {"active_max_cap": 1})

    def test_keep_per_task_archives_older_duplicates(self) -> None:
        oldest = self.write_packet("active", "t1-old.json", days_old=3, task_id="same")
        self.write_packet("active", "t1-new.json", days_old=1, task_id="same")
        other = self.write_packet("active", "other.json", days_old=3, task_id="other")

        result = self.gc.run(dry_run=False, now=self.now, root=self.root, keep_per_task=1)

        self.assertEqual(result["archived_count"], 1)
        self.assertFalse(oldest.exists())
        self.assertTrue(other.exists())
        self.assertEqual(result["reason_counts"], {"active_per_task_cap": 1})

    def test_archived_max_deletes_oldest_surplus(self) -> None:
        oldest = self.write_packet("archived", "oldest.json", days_old=3)
        self.write_packet("archived", "middle.json", days_old=2)
        newest = self.write_packet("archived", "newest.json", days_old=1)

        result = self.gc.run(dry_run=False, now=self.now, root=self.root, archived_max=2)

        self.assertEqual(result["deleted_count"], 1)
        self.assertFalse(oldest.exists())
        self.assertTrue(newest.exists())
        self.assertEqual(result["reason_counts"], {"archived_max_cap": 1})


if __name__ == "__main__":
    unittest.main()
