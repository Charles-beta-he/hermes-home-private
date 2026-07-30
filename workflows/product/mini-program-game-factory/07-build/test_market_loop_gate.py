import copy
import json
import unittest
from pathlib import Path

from market_loop_gate import GateError, gate_market_hypotheses
from test_hot_game_observatory import AS_OF, observation


class MarketLoopGateTests(unittest.TestCase):
    def setUp(self):
        self.routing = json.loads((Path(__file__).parents[1] / "model-routing.json").read_text(encoding="utf-8"))
        self.hypothesis = {
            "hypothesis_id": "reveal-risk-stop-v1",
            "source_observation_ids": ["game-a-douyin"],
            "abstract_mechanics": ["progressive reveal", "risk escalation", "voluntary cash-out"],
            "proposed_changes": ["replace collectible valuation"],
            "differentiation": "Replace collectible valuation with an original repair-diagnosis decision loop.",
            "non_copyable_exclusions": ["name", "art", "level layout"],
        }

    def test_unverified_market_lead_cannot_nominate_kernel_hypothesis(self):
        snapshot = observation(["rank-direct"], direct_gameplay=True)
        receipt = gate_market_hypotheses(snapshot, [self.hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["summary"], {"accepted": 0, "rejected": 1, "total": 1})
        self.assertEqual(receipt["rejected"][0]["reason"], "source_observation_not_verified_current_hot")

    def test_verified_observation_only_opens_kernel_hypothesis_state(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        receipt = gate_market_hypotheses(snapshot, [self.hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["summary"], {"accepted": 1, "rejected": 0, "total": 1})
        self.assertEqual(receipt["accepted"][0]["state"], "kernel_hypothesis")
        self.assertFalse(receipt["authority"]["may_freeze_kernel"])
        self.assertFalse(receipt["authority"]["may_compile_work_package"])
        self.assertFalse(receipt["authority"]["may_publish"])

    def test_unknown_observation_reference_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        hypothesis = copy.deepcopy(self.hypothesis)
        hypothesis["source_observation_ids"] = ["missing"]
        receipt = gate_market_hypotheses(snapshot, [hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["rejected"][0]["reason"], "unknown_source_observation")

    def test_protected_surface_claim_is_rejected(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        hypothesis = copy.deepcopy(self.hypothesis)
        hypothesis["proposed_changes"] = ["win_condition"]
        receipt = gate_market_hypotheses(snapshot, [hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["rejected"][0]["reason"], "protected_surface_requires_separate_spec_gate")

    def test_noncanonical_routing_is_rejected(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        routing = copy.deepcopy(self.routing)
        routing["protected_surfaces"] = ["unrelated"]
        with self.assertRaisesRegex(GateError, "canonical routing"):
            gate_market_hypotheses(snapshot, [self.hypothesis], routing, AS_OF)

    def test_missing_proposed_changes_is_rejected(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        hypothesis = copy.deepcopy(self.hypothesis)
        hypothesis.pop("proposed_changes")
        receipt = gate_market_hypotheses(snapshot, [hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["summary"]["accepted"], 0)
        self.assertEqual(receipt["rejected"][0]["reason"], "missing_proposed_changes")

    def test_protected_surface_embedded_in_abstract_mechanics_is_rejected(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        hypothesis = copy.deepcopy(self.hypothesis)
        hypothesis["proposed_changes"] = ["replace collectible valuation"]
        hypothesis["abstract_mechanics"] = ["change win condition"]
        receipt = gate_market_hypotheses(snapshot, [hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["summary"]["accepted"], 0)
        self.assertEqual(
            receipt["rejected"][0]["reason"],
            "protected_surface_requires_separate_spec_gate",
        )

    def test_protected_surface_claim_normalizes_case_whitespace_and_hyphens(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        for claim in (
            "Win_Condition",
            " win_condition ",
            "win-condition",
            "win__condition",
            "win_-condition",
            "win–condition",
            "ｗｉｎ＿ｃｏｎｄｉｔｉｏｎ",
        ):
            hypothesis = copy.deepcopy(self.hypothesis)
            hypothesis["proposed_changes"] = [claim]
            receipt = gate_market_hypotheses(snapshot, [hypothesis], self.routing, AS_OF)
            self.assertEqual(receipt["summary"]["accepted"], 0, claim)
            self.assertEqual(
                receipt["rejected"][0]["reason"],
                "protected_surface_requires_separate_spec_gate",
            )

    def test_missing_copy_exclusions_is_rejected(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        hypothesis = copy.deepcopy(self.hypothesis)
        hypothesis["non_copyable_exclusions"] = []
        receipt = gate_market_hypotheses(snapshot, [hypothesis], self.routing, AS_OF)
        self.assertEqual(receipt["rejected"][0]["reason"], "missing_non_copyable_exclusions")

    def test_receipt_is_deterministic(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        first = gate_market_hypotheses(copy.deepcopy(snapshot), [copy.deepcopy(self.hypothesis)], self.routing, AS_OF)
        second = gate_market_hypotheses(copy.deepcopy(snapshot), [copy.deepcopy(self.hypothesis)], self.routing, AS_OF)
        self.assertEqual(first["digest"], second["digest"])

    def test_receipt_digest_binds_rejected_hypothesis_input(self):
        snapshot = observation(["rank-direct"], direct_gameplay=True)
        first_hypothesis = copy.deepcopy(self.hypothesis)
        second_hypothesis = copy.deepcopy(self.hypothesis)
        second_hypothesis["abstract_mechanics"] = ["different mechanism"]
        first = gate_market_hypotheses(snapshot, [first_hypothesis], self.routing, AS_OF)
        second = gate_market_hypotheses(snapshot, [second_hypothesis], self.routing, AS_OF)
        self.assertEqual(first["rejected"], second["rejected"])
        self.assertNotEqual(first["hypotheses_digest"], second["hypotheses_digest"])
        self.assertNotEqual(first["digest"], second["digest"])

    def test_real_snapshot_yields_no_accepted_hypotheses(self):
        root = Path(__file__).parents[1]
        snapshot = json.loads((root / "evidence" / "hot-game-snapshot-2026-07-26.json").read_text(encoding="utf-8"))
        hypotheses = [{
            "hypothesis_id": "jade-risk-loop-v1",
            "source_observation_ids": ["lightly-handled-douyin-2026-06"],
            "abstract_mechanics": ["progressive reveal", "risk escalation", "voluntary exit"],
            "differentiation": "Original diagnostic-repair theme and state machine.",
            "non_copyable_exclusions": ["game names", "art", "levels", "numbers"],
        }]
        receipt = gate_market_hypotheses(snapshot, hypotheses, self.routing, AS_OF)
        self.assertEqual(receipt["summary"]["accepted"], 0)
        self.assertFalse(receipt["authority"]["may_freeze_kernel"])


if __name__ == "__main__":
    unittest.main()
