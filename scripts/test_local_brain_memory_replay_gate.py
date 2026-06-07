#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
GATE_SCRIPT = SCRIPT_DIR / "local_brain_memory_replay_gate.py"
BRAINCTL = SCRIPT_DIR / "brainctl.py"

spec = importlib.util.spec_from_file_location("local_brain_memory_replay_gate", GATE_SCRIPT)
assert spec is not None
assert spec.loader is not None
gate = importlib.util.module_from_spec(spec)
sys.modules["local_brain_memory_replay_gate"] = gate
spec.loader.exec_module(gate)


class LocalBrainMemoryReplayGateTest(unittest.TestCase):
    def test_default_fixture_gate_covers_at_least_three_memory_replay_classes(self) -> None:
        report = gate.run_gate(gate.default_fixtures())
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["gate_effective"])
        self.assertGreaterEqual(report["fixture_count"], 3)
        self.assertGreaterEqual(len(report["fixture_classes"]), 3)
        self.assertEqual(report["fixture_class_gate"], "PASS")

    def test_records_adopted_and_rejected_mempalace_walrus_evidence(self) -> None:
        decisions = gate.run_gate(gate.default_fixtures())["evidence_decisions"]
        adopted = {(item["source"], item["id"]) for item in decisions["adopted"]}
        rejected = {(item["source"], item["id"]) for item in decisions["rejected"]}
        self.assertIn(("MemPalace", "mempalace_p10_strategy"), adopted)
        self.assertIn(("Walrus Memory", "daily_report_walrus_boundary"), adopted)
        self.assertIn(("Walrus Memory", "walrus_marketing_claim"), rejected)
        walrus_reject = [item for item in decisions["rejected"] if item["id"] == "walrus_marketing_claim"][0]
        self.assertIn("missing_benchmark_schema_or_rollback_evidence", walrus_reject["reasons"])

    def test_brainctl_memory_replay_gate_json_surfaces_effective_gate(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(BRAINCTL), "--json", "memory-replay-gate"],
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], "local_brain_memory_replay_gate_v1")
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["gate_effective"])
        self.assertGreaterEqual(len(payload["fixture_classes"]), 3)


if __name__ == "__main__":
    unittest.main()
