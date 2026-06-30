#!/usr/bin/env python3
"""Tests for task_preflight local-brain constraint integration."""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parent / "task_preflight.py"
spec = importlib.util.spec_from_file_location("task_preflight", SCRIPT)
task_preflight = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(task_preflight)


class TaskPreflightLocalBrainIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / "brain"
        self.vault.mkdir()
        self.memory = self.root / "memory"
        self.memory.mkdir()
        self.preflight_dir = self.root / "task-preflight"
        self.observer_dir = self.root / "task-observer"
        note = self.vault / "05-实践与项目/实践方案/12-本地大脑全量自动约束层长期方案.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            "---\nstatus: active-stable\nstability_class: long_term_canonical_plan\n---\n\n"
            "# 本地大脑全量自动约束层最终长期稳定方案\n\n"
            "Current source: RouteReviewGate BrainConstraintRecord route_required_evidence。\n",
            encoding="utf-8",
        )
        self.env = patch.dict(
            os.environ,
            {
                "HERMES_BRAIN_PREFLIGHT_VAULTS": str(self.vault),
                "HERMES_LOCAL_BRAIN_PREFLIGHT_MEMORY_ROOT": str(self.memory),
                "HERMES_LOCAL_BRAIN_PREFLIGHT_ENABLED": "1",
                "HERMES_TASK_PREFLIGHT_DIR": str(self.preflight_dir),
                "HERMES_TASK_OBSERVER_DIR": str(self.observer_dir),
            },
            clear=False,
        )
        self.env.start()
        task_preflight.PREFLIGHT_DIR = self.preflight_dir
        task_preflight.OBSERVER_DIR = self.observer_dir

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_cmd_check_embeds_local_brain_constraint_record(self):
        pf = task_preflight.cmd_check(
            "task-1",
            "落地本地大脑全量自动约束层",
            "修改 scripts/local_brain_change_preflight.py 接入 RouteReviewGate",
        )

        self.assertIn("local_brain_constraint", pf)
        gate = pf["local_brain_constraint"]
        self.assertEqual(gate["schema"], "local_brain_change_preflight_v1")
        self.assertIn("brain_constraint_record", gate)
        self.assertIn("route_review_record", gate)
        self.assertFalse(gate["side_effects"]["external_dispatch"])
        saved = json.loads((self.preflight_dir / "task-1.json").read_text(encoding="utf-8"))
        self.assertIn("local_brain_constraint", saved)

    def test_local_brain_block_turns_preflight_into_blocked_status(self):
        pf = task_preflight.cmd_check(
            "task-2",
            "修改 taskpool lifecycle runtime hard gate",
            "修改 taskpool lifecycle done transition runtime hard gate",
        )

        self.assertEqual(pf["status"], "blocked_by_local_brain_constraint")
        self.assertTrue(any(issue["category"] == "local_brain_constraint" for issue in pf["ambiguity_issues"]))
        self.assertEqual(pf["local_brain_constraint"]["brain_constraint_record"]["verdict"]["status"], "block")


if __name__ == "__main__":
    unittest.main()
