#!/usr/bin/env python3
"""Regression tests for self-improvement priority ghost suppression."""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "self-improvement-pipeline.py"


def load_module():
    spec = importlib.util.spec_from_file_location("self_improvement_pipeline", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestSelfImprovementPipeline(unittest.TestCase):
    def test_stale_tool_failure_is_suppressed_when_ops_are_green(self):
        mod = load_module()
        old_health = mod.current_ops_healthy
        try:
            mod.current_ops_healthy = lambda: True
            signals = [{
                "signals": [{
                    "type": "tool_failures",
                    "count": 9,
                    "detail": "terminal failed historically",
                    "_parent_timestamp": "2000-01-01T00:00:00",
                }]
            }]
            items = mod.aggregate_items(signals, [], {}, [])
            self.assertFalse(any(it.act_type == "fix_tool_config" for it in items))
        finally:
            mod.current_ops_healthy = old_health

    def test_low_skill_detection_uses_latest_score_per_skill(self):
        mod = load_module()
        darwin = [
            {"skill": "p10", "new_score": "51", "status": "baseline"},
            {"skill": "p10", "new_score": "100", "status": "accepted"},
            {"skill": "p9", "new_score": "46", "status": "baseline"},
            {"skill": "p9", "new_score": "100", "status": "accepted"},
        ]
        items = mod.aggregate_items([], [], {}, darwin)
        self.assertFalse(any(it.act_type == "improve_low_skills" for it in items))


if __name__ == "__main__":
    unittest.main(verbosity=2)
