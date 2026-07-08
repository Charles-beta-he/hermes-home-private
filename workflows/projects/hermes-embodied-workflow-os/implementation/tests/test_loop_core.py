import ast
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.loop_core import (
    EXIT_BUDGET_EXHAUSTED,
    EXIT_ERROR,
    EXIT_HUMAN_GATE,
    EXIT_STABLE,
    RECEIPT_SCHEMA,
    assert_no_side_effect_flags,
    run_loop_core,
)


class EgoNeuroLoopCoreTest(unittest.TestCase):
    def neuro_state(self, **overrides):
        state = {
            "state_id": "world.fixture.1",
            "confidence": 0.65,
            "uncertainty": 0.2,
            "risk_level": "low",
            "evidence_refs": ["evidence:obs.local.1"],
            "derived": {"posture": "standing", "goal": "safe_next_step"},
            "contradictions": [],
        }
        state.update(overrides)
        return state

    def action_intent(self, **overrides):
        intent = {
            "intent_id": "intent.local.1",
            "session_id": "session.fixture",
            "taskgraph_node_id": "node.next-step",
            "actor_id": "hermes.local",
            "capability_id": "capability.local_projection",
            "verb": "advise",
            "target": {"surface": "workbench"},
            "parameters": {"text": "low-risk next step"},
            "risk_level": "low",
            "preconditions": ["evidence_present"],
            "expected_observation_delta": {"user_has_advice": True},
            "verification_plan": ["receipt_readback"],
            "evidence_refs": ["evidence:intent.local.1"],
            "requested_authority": ["local_projection"],
            "dry_run": True,
            "idempotency_key": "intent-local-1",
            "rollback_or_abort": "discard projection",
        }
        intent.update(overrides)
        return intent

    def test_stable_early_exit_emits_receipt_with_prediction_label(self):
        receipt = run_loop_core(self.neuro_state(), self.action_intent(), loop_budget=4)
        self.assertEqual(receipt["schema"], RECEIPT_SCHEMA)
        self.assertEqual(receipt["exit_reason"], EXIT_STABLE)
        self.assertLess(receipt["loop_count"], 4)
        self.assertEqual(receipt["deferred_decode_label"], "prediction_not_verified_fact")
        self.assertEqual(receipt["predicted_next_state"]["prediction_status"], "prediction_not_evidence")
        self.assertIn("evidence:obs.local.1", receipt["evidence_refs"])
        self.assertIn("evidence:intent.local.1", receipt["evidence_refs"])
        self.assertTrue(assert_no_side_effect_flags(receipt))

    def test_high_risk_requested_authority_exits_human_gate_and_flags_false(self):
        receipt = run_loop_core(
            self.neuro_state(risk_level="high"),
            self.action_intent(requested_authority=["hardware_actuation"], risk_level="high"),
            loop_budget=4,
        )
        self.assertEqual(receipt["exit_reason"], EXIT_HUMAN_GATE)
        self.assertEqual(receipt["risk_level"], "blocked")
        self.assertIn("side_effect_or_authority_boundary_not_opened", receipt["known_limits"])
        self.assertTrue(assert_no_side_effect_flags(receipt))

    def test_missing_evidence_returns_error_receipt(self):
        state = self.neuro_state(evidence_refs=[])
        receipt = run_loop_core(state, self.action_intent(), loop_budget=2)
        self.assertEqual(receipt["exit_reason"], EXIT_ERROR)
        self.assertEqual(receipt["risk_level"], "blocked")
        self.assertIn("evidence_refs", receipt["known_limits"][0])
        self.assertTrue(assert_no_side_effect_flags(receipt))

    def test_budget_exhaustion_is_explicit_when_state_never_stabilizes(self):
        receipt = run_loop_core(
            self.neuro_state(confidence=0.05, uncertainty=1.0, contradictions=["vision_vs_goal"]),
            self.action_intent(),
            loop_budget=2,
            stable_delta_threshold=0.01,
            confidence_threshold=0.99,
        )
        self.assertEqual(receipt["exit_reason"], EXIT_BUDGET_EXHAUSTED)
        self.assertIn("input_state_contains_contradictions", receipt["known_limits"])
        self.assertIn("loop_budget_exhausted_before_stability", receipt["known_limits"])
        self.assertTrue(assert_no_side_effect_flags(receipt))

    def test_loop_core_has_no_adapter_or_platform_imports(self):
        module_path = ROOT / "hewos_core" / "loop_core.py"
        tree = ast.parse(module_path.read_text())
        banned_roots = {
            "requests",
            "httpx",
            "subprocess",
            "socket",
            "workbench_runtime",
            "mock_adapters",
            "ordered_live_boundaries",
            "high_risk_boundaries",
        }
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & banned_roots, imported & banned_roots)


if __name__ == "__main__":
    unittest.main()
