#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path.home() / ".hermes" / "scripts"
SCRIPT = SCRIPTS / "cron_static_projection.py"


def load_module():
    spec = importlib.util.spec_from_file_location("cron_static_projection_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CronStaticProjectionTest(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_projection_removes_runtime_churn_but_keeps_static_config(self):
        data = {
            "updated_at": "2026-06-09T00:00:00Z",
            "jobs": [
                {
                    "id": "b",
                    "name": "job-b",
                    "prompt": "run b",
                    "schedule": "every 1h",
                    "enabled": True,
                    "state": "scheduled",
                    "next_run_at": "2026-06-09T01:00:00Z",
                    "last_run_at": "2026-06-09T00:00:00Z",
                    "last_status": "ok",
                    "last_error": None,
                    "repeat": {"times": 3, "completed": 2},
                }
            ],
        }

        projected = self.mod.static_projection(data)

        self.assertNotIn("updated_at", projected)
        job = projected["jobs"][0]
        self.assertEqual(job["id"], "b")
        self.assertEqual(job["prompt"], "run b")
        self.assertEqual(job["repeat"], {"times": 3})
        self.assertNotIn("state", job)
        self.assertNotIn("next_run_at", job)
        self.assertNotIn("last_run_at", job)
        self.assertNotIn("last_status", job)
        self.assertNotIn("last_error", job)

    def test_runtime_only_changes_have_same_static_hash(self):
        base = {
            "jobs": [
                {"id": "a", "name": "job-a", "schedule": "30m", "next_run_at": "t1", "repeat": {"times": 5, "completed": 1}}
            ],
            "updated_at": "u1",
        }
        changed = {
            "jobs": [
                {"id": "a", "name": "job-a", "schedule": "30m", "next_run_at": "t2", "last_status": "ok", "repeat": {"times": 5, "completed": 2}}
            ],
            "updated_at": "u2",
        }

        self.assertEqual(self.mod.projection_sha256(base), self.mod.projection_sha256(changed))

    def test_static_changes_have_different_static_hash(self):
        base = {"jobs": [{"id": "a", "name": "job-a", "schedule": "30m"}]}
        changed = {"jobs": [{"id": "a", "name": "job-a", "schedule": "45m"}]}

        self.assertNotEqual(self.mod.projection_sha256(base), self.mod.projection_sha256(changed))

    def test_cli_report_counts_runtime_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            jobs = Path(tmp) / "jobs.json"
            jobs.write_text(json.dumps({"updated_at": "u", "jobs": [{"id": "a", "next_run_at": "n", "repeat": {"completed": 1}}]}), encoding="utf-8")

            report = self.mod.build_report(jobs)

        self.assertEqual(report["job_count"], 1)
        self.assertEqual(report["runtime_field_counts"]["updated_at"], 1)
        self.assertEqual(report["runtime_field_counts"]["next_run_at"], 1)
        self.assertEqual(report["runtime_field_counts"]["repeat.completed"], 1)


if __name__ == "__main__":
    unittest.main()
