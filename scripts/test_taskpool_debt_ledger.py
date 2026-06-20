#!/usr/bin/env python3
"""Focused tests for taskpool_debt_ledger read-only flow/debt classification."""
from __future__ import annotations

import unittest
from unittest.mock import patch

import taskpool_debt_ledger as ledger


class TaskpoolDebtLedgerTests(unittest.TestCase):
    def test_infer_completion_profile_prefers_voice_desktop(self) -> None:
        task = {
            "title": "全盘落地 HoloJarvis 1:1 语音交互体验到 Hermes",
            "objective": "常开麦克风 default-off，desktop HUD 状态可见",
            "lane": "evolution",
        }
        self.assertEqual(ledger.infer_completion_profile(task), "implementation_desktop")

    def test_infer_completion_profile_static_intake_for_repo_evaluate(self) -> None:
        task = {
            "title": "吸收 Dark-Moon 的 MCP 执行闸门",
            "source_type": "repo",
            "integration_level": "evaluate",
            "objective": "Produce source inspection and gap map",
            "lane": "evolution",
        }
        self.assertEqual(ledger.infer_completion_profile(task), "static_intake")

    def test_evidence_gate_risks_flags_negative_diagnostic_tokens(self) -> None:
        task = {
            "evidence_refs": [
                "artifact:taskpool-review-gap multimodel_advisory_or_failed_not_completion "
                "requires_test-build-browser-curl-commit-verification"
            ]
        }
        risks = ledger.evidence_gate_risks(task)
        kinds = {r["kind"] for r in risks}
        self.assertIn("token_based_evidence_false_positive_risk", kinds)

    def test_evidence_gate_risks_flags_advisory_only(self) -> None:
        risks = ledger.evidence_gate_risks({"multimodel_last_gate_status": "PASS_ADVISORY_ONLY"})
        self.assertEqual(risks[0]["kind"], "advisory_only_not_completion")

    def test_flow_health_detects_duplicate_projection_and_retry_breaker(self) -> None:
        rows = [
            {
                "id": "task-a",
                "status": "review",
                "priority": "P1",
                "dispatchable": False,
                "retry_count": "0",
                "title": "voice desktop task",
            },
            {
                "id": "task-b",
                "status": "running",
                "priority": "P2",
                "dispatchable": False,
                "retry_count": "3",
                "claimed_by": "worker",
                "title": "Vercel skill graph intake",
            },
            {
                "id": "task-b",
                "status": "review",
                "priority": "P2",
                "dispatchable": False,
                "retry_count": "3",
                "title": "Vercel skill graph intake",
            },
        ]

        def fake_run_json(cmd, timeout=90):  # noqa: ANN001
            if "review-gap-scan" in cmd:
                return {"gap_count": 1, "gaps": [{"task_id": "task-a", "gap_types": ["missing_ui"], "failures": ["missing"], "repairable": True}]}
            if "multimodel-intervention-jobs" in cmd:
                return {"status": "OK", "job_count": 1, "alive_count": 0, "jobs": []}
            raise AssertionError(f"unexpected command: {cmd}")

        with patch.object(ledger, "active_task_rows", return_value=rows), patch.object(ledger, "run_json", side_effect=fake_run_json):
            result = ledger.flow_health_summary()

        self.assertEqual(result["duplicate_projection_count"], 1)
        self.assertEqual(result["duplicate_projection"][0]["task_id"], "task-b")
        self.assertEqual(result["retry_circuit_breaker_count"], 1)
        self.assertEqual(result["review_gap_count"], 1)


if __name__ == "__main__":
    unittest.main()
