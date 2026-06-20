import json
import unittest
from unittest.mock import patch

import v_state


class VStateKanbanCoverageTests(unittest.TestCase):
    def test_f_kanban_uses_spawnability_aware_coverage_score(self):
        with patch.object(v_state, "kanban_coverage_live_report", return_value={"score": 0.45}):
            self.assertEqual(v_state.f_kanban(), 0.45)

    def test_compute_v_includes_kanban_coverage_diagnostics_when_available(self):
        fake_report = {
            "score": 0.45,
            "bottleneck": "kanban_ready_spawnability",
            "counts": {"ready_nonspawnable": 8, "kanban_ready": 8},
            "coverage": {"kanban_ready_spawnability": 0.0},
        }
        fake_envelope = {"score": 1.0, "policy": "test"}
        with patch.object(v_state, "kanban_coverage_live_report", return_value=fake_report):
            with patch.object(v_state, "envelope_diagnostics", return_value=fake_envelope):
                with patch.dict(v_state.FUNCTIONS, {"kanban": v_state.f_kanban}, clear=True):
                    with patch.dict(v_state.WEIGHTS, {"kanban": 1.0}, clear=True):
                        result = v_state.compute_v()

        self.assertEqual(result["components"]["kanban"], 0.45)
        self.assertEqual(result["diagnostics"]["kanban_coverage"], fake_report)
        self.assertEqual(result["diagnostics"]["envelope"], fake_envelope)

    def test_envelope_score_ignores_historical_terminal_debt_after_ack(self):
        stats = {
            "total": 100,
            "by_status": {"FAILED": 40, "BLOCKED": 10, "DONE": 50},
            "timeouts": 0,
            "human_escape_triggered": False,
            "escape_info": {
                "since_ack": {"failures": 0, "blocks": 0, "invalid_timestamps": 0},
                "historical": {"failures": 40, "blocks": 10, "invalid_timestamps": 0},
            },
        }
        with patch.object(v_state, "safe_run", return_value=json.dumps(stats)):
            self.assertEqual(v_state.f_envelope(), 1.0)
            self.assertEqual(v_state.envelope_diagnostics()["historical"]["failures"], 40)

    def test_envelope_score_penalizes_since_ack_and_live_risk(self):
        stats = {
            "total": 100,
            "by_status": {"PENDING": 5, "RUNNING": 5, "FAILED": 20},
            "timeouts": 1,
            "human_escape_triggered": False,
            "escape_info": {
                "since_ack": {"failures": 1, "blocks": 1, "invalid_timestamps": 0},
                "historical": {"failures": 20, "blocks": 0, "invalid_timestamps": 0},
            },
        }
        with patch.object(v_state, "safe_run", return_value=json.dumps(stats)):
            score = v_state.f_envelope()

        self.assertLess(score, 1.0)
        self.assertGreater(score, 0.0)


if __name__ == "__main__":
    unittest.main()
