#!/usr/bin/env python3
"""Tests for the unified execution-flow evaluator."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("execution_flow_evaluator.py")


def write_task(directory: Path, name: str, frontmatter: str, body: str = "") -> Path:
    path = directory / name
    path.write_text(f"---\n{frontmatter.strip()}\n---\n{body}", encoding="utf-8")
    return path


class ExecutionFlowEvaluatorTests(unittest.TestCase):
    def run_eval(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_json_payload_has_enterprise_schema_and_gate_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = write_task(
                Path(tmp),
                "ui-review.md",
                """
id: t-ui
title: Fix wallet UI
status: review
lane: work
priority: P1
evidence:
  - command:pnpm_build PASS
  - artifact:/tmp/wallet-report.md
  - proof:browser route=/wallet viewport=mobile-375 backend=real console_errors=0
""",
                "Acceptance Criteria: UI renders on wallet route.",
            )
            proc = self.run_eval("--task-file", str(task), "--json")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["schema_version"], "execution-flow/v1")
            self.assertEqual(payload["enterprise_gate"]["status"], "PASS")
            self.assertEqual(payload["summary"]["closeout_ready"], 1)
            self.assertTrue(payload["evaluations"][0]["closeout_ready"])

    def test_fail_on_blocked_returns_nonzero_for_missing_harness_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = write_task(
                Path(tmp),
                "missing-proof.md",
                """
id: t-missing
title: Implement backend API and browser UI
status: review
lane: work
priority: P1
""",
                "Needs backend API readback and browser proof.",
            )
            proc = self.run_eval("--task-file", str(task), "--json", "--fail-on-blocked")
            self.assertEqual(proc.returncode, 2)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["enterprise_gate"]["status"], "BLOCKED")
            self.assertEqual(payload["summary"]["blocked_or_missing_evidence"], 1)
            self.assertIn("missing_required_evidence", payload["enterprise_gate"]["reasons"])
            evaluation = payload["evaluations"][0]
            self.assertIn("api_or_backend_readback_proof", evaluation["missing_evidence"])
            self.assertIn("browser_or_ui_surface_proof", evaluation["missing_evidence"])

    def test_report_writes_markdown_with_intervention_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = write_task(
                tmp_path,
                "blocked.md",
                """
id: t-blocked
title: Evidence-only blocker
status: blocked
lane: work
priority: P0
""",
                "Blocked until proof is attached.",
            )
            report = tmp_path / "report.md"
            proc = self.run_eval("--task-file", str(task), "--json", "--report", str(report))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = report.read_text(encoding="utf-8")
            self.assertIn("# Unified Execution Flow Report", text)
            self.assertIn("## Human Gate / Intervention Packets", text)
            self.assertIn("t-blocked", text)
            self.assertIn("lifecycle_done_transition", text)

    def test_blocked_task_exposes_single_safe_auto_decision_option(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = write_task(
                Path(tmp),
                "blocked-evidence.md",
                """
id: t-auto-evidence
title: Need proof before closeout
status: blocked
lane: work
priority: P1
""",
                "Implementation task lacks proof/readback.",
            )
            proc = self.run_eval("--task-file", str(task), "--json")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            evaluation = json.loads(proc.stdout)["evaluations"][0]
            self.assertEqual(evaluation["safe_decision_options"], [
                {"decision": "needs_more_evidence", "label": "退回补证据", "resumeMode": "repair"}
            ])
            self.assertEqual(evaluation["auto_decision"], {"decision": "needs_more_evidence", "label": "退回补证据", "resumeMode": "repair", "reason": "single_safe_option"})

    def test_external_side_effect_exposes_single_hold_auto_decision_option(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = write_task(
                Path(tmp),
                "writeback.md",
                """
id: t-auto-hold
title: Publish external writeback
status: review
workflow_stage: writeback
lane: work
priority: P0
external_side_effects:
  - publish
""",
                "Needs external adapter writeback.",
            )
            proc = self.run_eval("--task-file", str(task), "--json")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            evaluation = json.loads(proc.stdout)["evaluations"][0]
            self.assertEqual(evaluation["safe_decision_options"], [
                {"decision": "hold", "label": "暂停", "resumeMode": "hold"}
            ])
            self.assertEqual(evaluation["auto_decision"], {"decision": "hold", "label": "暂停", "resumeMode": "hold", "reason": "single_safe_option"})

    def test_blocked_external_side_effect_still_exposes_hold_auto_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = write_task(
                Path(tmp),
                "blocked-external.md",
                """
id: t-blocked-external
title: Publish external writeback
status: blocked
lane: work
priority: P0
external_side_effects:
  - publish
""",
                "Blocked publish needs authority.",
            )
            proc = self.run_eval("--task-file", str(task), "--json")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            evaluation = json.loads(proc.stdout)["evaluations"][0]
            self.assertEqual(evaluation["boundary_class"], "external_side_effect")
            self.assertEqual(evaluation["safe_decision_options"], [
                {"decision": "hold", "label": "暂停", "resumeMode": "hold"}
            ])
            self.assertEqual(evaluation["auto_decision"]["decision"], "hold")

    def test_report_does_not_create_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task = write_task(
                tmp_path,
                "blocked.md",
                """
id: t-blocked
title: Publish external writeback
status: blocked
lane: work
priority: P0
""",
            )
            report = tmp_path / "missing-parent" / "report.md"
            proc = self.run_eval("--task-file", str(task), "--report", str(report))
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(report.parent.exists())


if __name__ == "__main__":
    unittest.main()
