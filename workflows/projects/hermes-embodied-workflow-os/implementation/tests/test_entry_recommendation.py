import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.recommendation import recommend_entry


class EntryRecommendationTest(unittest.TestCase):
    def test_recommends_glasses_or_mobile_for_first_person_visual_need(self):
        result = recommend_entry(
            required_observation="first_person_visual",
            available_capabilities={
                "adapter.web.mock": ["observe.image.single"],
                "adapter.glasses.mock": ["observe.image.single", "observe.first_person_view"],
            },
        )

        self.assertEqual(result["primary"], "adapter.glasses.mock")
        self.assertIn("first-person", result["reason"])

    def test_blocks_high_risk_physical_action_without_onsite_confirmation(self):
        result = recommend_entry(
            required_action="act.robot.grip",
            risk_level="physical_action",
            available_capabilities={"adapter.robot.mock": ["act.robot.grip"]},
        )

        self.assertEqual(result["status"], "blocked_human_gate")
        self.assertIn("onsite", result["reason"])

    def test_recommends_workbench_for_complex_editing(self):
        result = recommend_entry(
            required_action="edit.taskgraph",
            available_capabilities={
                "adapter.web.mock": ["display.workbench", "edit.taskgraph"],
                "adapter.glasses.mock": ["display.overlay"],
            },
        )

        self.assertEqual(result["primary"], "adapter.web.mock")


if __name__ == "__main__":
    unittest.main()
