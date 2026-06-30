#!/usr/bin/env python3
"""Tests for local_brain_change_preflight.py dry-run constraint gate."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "local_brain_change_preflight.py"
spec = importlib.util.spec_from_file_location("local_brain_change_preflight", SCRIPT)
preflight = importlib.util.module_from_spec(spec)
sys.modules["local_brain_change_preflight"] = preflight
spec.loader.exec_module(preflight)


class LocalBrainChangePreflightTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.default_vault = self.root / "default-brain"
        self.notes_vault = self.root / "notes-brain"
        self.default_vault.mkdir()
        self.notes_vault.mkdir()
        self.memory_root = self.root / "memory"
        self.memory_root.mkdir()
        self.write_note(
            self.default_vault,
            "05-实践与项目/projects/Old/旧项目经验.md",
            "---\nstatus: stale\n---\n\n# 旧项目经验\n\n本地大脑全量自动约束层 RouteReviewGate without tests。旧结论，completed without tests。\n",
        )
        self.write_note(
            self.notes_vault,
            "05-实践与项目/实践方案/12-本地大脑全量自动约束层长期方案.md",
            "---\nstatus: active-stable\nstability_class: long_term_canonical_plan\n---\n\n# 本地大脑全量自动约束层最终长期稳定方案\n\nCurrent source: RouteReviewGate BrainConstraintRecord route_required_evidence。\n",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_note(self, vault: Path, rel: str, text: str) -> Path:
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_preflight_searches_multiple_vaults_and_prefers_current_canonical_knowledge(self):
        result = preflight.run_preflight(
            summary="强化本地大脑全量自动约束层 RouteReviewGate",
            files=["scripts/local_brain_change_preflight.py"],
            vaults=[self.default_vault, self.notes_vault],
            memory_root=self.memory_root,
            evidence=["test:fixture"],
            limit=5,
        )

        self.assertEqual(result["schema"], "local_brain_change_preflight_v1")
        record = result["brain_constraint_record"]
        accepted_paths = {hit["path"] for hit in record["retrieval"]["accepted_hits"]}
        filtered_paths = {hit["path"] for hit in record["retrieval"]["filtered_hits"]}
        self.assertIn("05-实践与项目/实践方案/12-本地大脑全量自动约束层长期方案.md", accepted_paths)
        self.assertIn("05-实践与项目/projects/Old/旧项目经验.md", filtered_paths)
        self.assertEqual(record["routing"]["route_review_ref"], "embedded:route_review_record")
        self.assertIn("route_required_evidence", record["routing"])

    def test_t3_lifecycle_change_without_evidence_degrades_not_certified_and_blocks(self):
        result = preflight.run_preflight(
            summary="修改 taskpool lifecycle done transition runtime hard gate",
            files=["scripts/taskpool_lifecycle.py"],
            vaults=[self.notes_vault],
            memory_root=self.memory_root,
            evidence=[],
            limit=5,
        )

        route = result["route_review_record"]
        verdict = result["brain_constraint_record"]["verdict"]
        self.assertEqual(route["classification"]["risk_tier"], "T3")
        self.assertEqual(route["verdict"]["status"], "degraded_not_certified")
        self.assertFalse(route["verdict"]["certified"])
        self.assertEqual(verdict["status"], "block")
        self.assertIn("missing_required_evidence", verdict["reasons"])

    def test_cli_json_emits_parseable_record_and_never_executes_side_effects(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--summary",
                "本地大脑全量自动约束层 RouteReviewGate dry-run",
                "--file",
                "scripts/local_brain_change_preflight.py",
                "--vault",
                str(self.notes_vault),
                "--memory-root",
                str(self.memory_root),
                "--evidence",
                "test:fixture",
                "--json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["dry_run"])
        self.assertEqual(data["side_effects"]["external_dispatch"], False)
        self.assertEqual(data["side_effects"]["lifecycle_write"], False)
        self.assertIn("brain_constraint_record", data)
        self.assertIn("route_review_record", data)


if __name__ == "__main__":
    unittest.main()
