#!/usr/bin/env python3
"""Focused tests for proof-debt-migration-dry-run."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path.home() / ".hermes" / "scripts"
SCRIPT = SCRIPTS / "proof-debt-migration-dry-run.py"


def load_module():
    spec = importlib.util.spec_from_file_location("proof_debt_migration_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProofDebtMigrationDryRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tasks = Path(self.tmp.name)
        self.plan = load_module()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_parse_mission_warning(self) -> None:
        parsed = self.plan.parse_warning("terminal mission envelope debt: mission envelope missing ['evidence_refs:structured_ref']: task-one")

        self.assertEqual(parsed["category"], "terminal_mission_envelope_debt")
        self.assertEqual(parsed["task"], "task-one")
        self.assertIn("evidence_refs", parsed["missing_fields"])

    def test_parse_invalid_hash_warning(self) -> None:
        parsed = self.plan.parse_warning("terminal invalid autorun proof hash debt in task-two: proof:sha256:abc123")

        self.assertEqual(parsed["category"], "terminal_invalid_autorun_proof_hash_debt")
        self.assertEqual(parsed["task"], "task-two")
        self.assertEqual(parsed["proof_sha"], "abc123")

    def test_build_plan_classifies_existing_evidence_candidate(self) -> None:
        (self.tasks / "task-one.md").write_text("## Proof Log\ncommand:pytest", encoding="utf-8")
        warnings = ["terminal mission envelope debt: mission envelope missing ['evidence_refs:structured_ref']: task-one"]

        report = self.plan.build_plan(warnings, tasks_dir=self.tasks)

        self.assertEqual(report["schema"], "proof_debt_migration_dry_run_v1")
        self.assertIn("read-only", report["safety"])
        self.assertEqual(report["items"][0]["recommended_action"], "candidate_migratable_existing_evidence")

    def test_build_plan_classifies_invalid_hash_as_source_needed(self) -> None:
        (self.tasks / "task-two.md").write_text("proof:sha256:abc123", encoding="utf-8")
        warnings = ["terminal invalid autorun proof hash debt in task-two: proof:sha256:abc123"]

        report = self.plan.build_plan(warnings, tasks_dir=self.tasks)

        self.assertEqual(report["items"][0]["recommended_action"], "needs_source_artifact")

    def test_apply_plan_normalizes_existing_refs_without_fabricating(self) -> None:
        task = self.tasks / "task-three.md"
        task.write_text(
            "---\n"
            "evidence_refs:\n"
            "  - /tmp/evidence.json\n"
            "  - proof:already-structured\n"
            "ratification_artifact: review-result.json\n"
            "---\n"
            "body\n",
            encoding="utf-8",
        )
        plan = {
            "items": [
                {
                    "task": "task-three",
                    "task_file": str(task),
                    "recommended_action": "candidate_migratable_existing_evidence",
                }
            ]
        }

        dry = self.plan.apply_plan(plan, dry_run=True)
        self.assertEqual(dry["result_counts"], {"changed": 1})
        self.assertIn("/tmp/evidence.json", task.read_text(encoding="utf-8"))

        applied = self.plan.apply_plan(plan, dry_run=False)
        body = task.read_text(encoding="utf-8")
        self.assertEqual(applied["result_counts"], {"changed": 1})
        self.assertIn("artifact:/tmp/evidence.json", body)
        self.assertIn("ratification_artifact: proof:review-result.json", body)


if __name__ == "__main__":
    unittest.main()
