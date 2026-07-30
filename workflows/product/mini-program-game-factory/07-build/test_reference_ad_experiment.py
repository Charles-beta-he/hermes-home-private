import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))

from reference_ad_experiment import (
    ReferenceAdExperimentError,
    build_reference_ad_experiment_receipt,
)

MEDIA_BYTES = b"reference-ad-test-bytes"
MEDIA_SHA256 = hashlib.sha256(MEDIA_BYTES).hexdigest()


def make_observation(media_path: str, sha256: str = MEDIA_SHA256) -> dict:
    return {
        "schema_version": 1,
        "observation_id": "douyin-test-observation",
        "observed_at": "2026-07-30T13:43:24+08:00",
        "source": {
            "platform": "douyin",
            "source_type": "user_supplied_reference_ad",
            "local_media_path": media_path,
            "sha256": sha256,
        },
        "market_status": {
            "verified_current_hot": False,
            "rank_claimed": False,
            "boundary": "user-supplied reference-ad test data only",
        },
        "visible_observations": [
            {
                "time_range_seconds": [0, 30],
                "certainty": "high",
                "facts": ["a character collects stackable path pieces"],
            }
        ],
        "inferences": [
            {"claim": "collect then spend a stack across gaps", "confidence": 0.9}
        ],
        "unknowns": ["exact touch controls are not visible"],
        "clean_room_boundary": {
            "reusable_mechanics": ["collect stackable traversal resources"],
            "non_copyable_expression": ["source art, audio, geometry and colors"],
        },
    }


def make_card(observation_id: str = "douyin-test-observation") -> dict:
    return {
        "schema_version": 1,
        "mechanic_id": "stack-path-runner",
        "status": "experimental_candidate_only",
        "source_observation": observation_id,
        "test_levels": [
            {"id": "warm-up", "difficulty": "easy"},
            {"id": "skill-gate", "difficulty": "skill_gate"},
        ],
        "authority": {
            "candidate_only": True,
            "may_claim_verified_current_hot": False,
            "may_compile_work_package": False,
            "may_freeze_factory_kernel": False,
            "may_publish": False,
            "may_submit_platform": False,
        },
    }


class ReferenceAdExperimentTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.media = self.root / "ad.mp4"
        self.media.write_bytes(MEDIA_BYTES)

    def build(self, observation=None, card=None):
        return build_reference_ad_experiment_receipt(
            observation if observation is not None else make_observation(str(self.media)),
            card if card is not None else make_card(),
            base_dir=self.root,
        )

    def test_valid_input_produces_candidate_receipt(self):
        receipt = self.build()
        self.assertEqual(receipt["closure_state"], "reference_ad_experiment_candidate")
        self.assertEqual(receipt["observation_id"], "douyin-test-observation")
        self.assertEqual(receipt["mechanic_id"], "stack-path-runner")
        self.assertEqual(receipt["source"]["sha256"], MEDIA_SHA256)
        self.assertEqual(receipt["source"]["media_size_bytes"], len(MEDIA_BYTES))
        self.assertEqual(receipt["source"]["local_media_path"], str(self.media.resolve()))
        self.assertEqual(
            [level["id"] for level in receipt["levels"]], ["warm-up", "skill-gate"]
        )

    def test_receipt_authority_is_fully_closed(self):
        receipt = self.build()
        authority = receipt["authority"]
        self.assertTrue(authority["candidate_only"])
        for key, value in authority.items():
            if key == "candidate_only":
                continue
            self.assertFalse(value, f"authority.{key} must be closed")
        self.assertFalse(receipt["market_status"]["verified_current_hot"])
        self.assertFalse(receipt["market_status"]["rank_claimed"])

    def test_receipt_declares_gates_it_cannot_satisfy(self):
        receipt = self.build()
        cannot = set(receipt["cannot_satisfy_gates"])
        self.assertIn("verified-current-hot", cannot)
        self.assertIn("market-to-kernel-gate", cannot)
        self.assertIn("kernel-freeze", cannot)
        self.assertIn("platform-submission", cannot)
        self.assertIn("publish", cannot)

    def test_receipt_is_deterministic(self):
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(first["digest"], second["digest"])

    def test_input_is_not_mutated(self):
        observation = make_observation(str(self.media))
        card = make_card()
        before = json.dumps([observation, card], sort_keys=True)
        self.build(observation, card)
        self.assertEqual(json.dumps([observation, card], sort_keys=True), before)

    def test_digest_mismatch_fails_closed(self):
        observation = make_observation(str(self.media), sha256="0" * 64)
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_missing_or_malformed_declared_digest_fails_closed(self):
        for bad in (None, "", "not-a-digest", MEDIA_SHA256.upper()):
            observation = make_observation(str(self.media))
            observation["source"]["sha256"] = bad
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_missing_media_fails_closed(self):
        observation = make_observation(str(self.root / "missing.mp4"))
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_symlink_media_fails_closed(self):
        link = self.root / "link.mp4"
        os.symlink(self.media, link)
        observation = make_observation(str(link))
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_directory_media_fails_closed(self):
        directory = self.root / "media-dir"
        directory.mkdir()
        observation = make_observation(str(directory))
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_wrong_source_type_fails_closed(self):
        observation = make_observation(str(self.media))
        observation["source"]["source_type"] = "direct_gameplay_capture"
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_verified_current_hot_true_or_missing_fails_closed(self):
        for status in (
            {"verified_current_hot": True, "rank_claimed": False},
            {"rank_claimed": False},
            {"verified_current_hot": None, "rank_claimed": False},
        ):
            observation = make_observation(str(self.media))
            observation["market_status"] = status
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_rank_claim_fails_closed(self):
        observation = make_observation(str(self.media))
        observation["market_status"]["rank_claimed"] = True
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_numeric_rank_field_fails_closed(self):
        observation = make_observation(str(self.media))
        observation["market_status"]["rank"] = 1
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(observation)

    def test_contradictory_hot_claim_keys_fail_closed(self):
        for extra_key, extra_value in (("current_hot", True), ("chart_position", 1)):
            observation = make_observation(str(self.media))
            observation["market_status"][extra_key] = extra_value
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_unknown_market_status_key_fails_closed(self):
        for extra_key, extra_value in (
            ("popularity", "very high"),
            ("notes", "harmless-looking"),
            ("top_chart", False),
        ):
            observation = make_observation(str(self.media))
            observation["market_status"][extra_key] = extra_value
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_missing_or_empty_market_boundary_fails_closed(self):
        for broken_boundary in (None, "", "   "):
            observation = make_observation(str(self.media))
            if broken_boundary is None:
                del observation["market_status"]["boundary"]
            else:
                observation["market_status"]["boundary"] = broken_boundary
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_empty_visible_facts_fails_closed(self):
        for broken in ([], [{"facts": []}], [{"facts": ["", "  "]}]):
            observation = make_observation(str(self.media))
            observation["visible_observations"] = broken
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_empty_inferences_fails_closed(self):
        for broken in ([], [{"claim": "", "confidence": 0.9}], [{"claim": "x", "confidence": 0}]):
            observation = make_observation(str(self.media))
            observation["inferences"] = broken
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_empty_unknowns_fails_closed(self):
        for broken in ([], [""], None):
            observation = make_observation(str(self.media))
            observation["unknowns"] = broken
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_missing_clean_room_boundary_fails_closed(self):
        for broken in (
            None,
            {},
            {"reusable_mechanics": [], "non_copyable_expression": ["x"]},
            {"reusable_mechanics": ["x"], "non_copyable_expression": []},
            {"reusable_mechanics": ["x"]},
        ):
            observation = make_observation(str(self.media))
            observation["clean_room_boundary"] = broken
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(observation)

    def test_levels_must_be_exactly_warm_up_then_skill_gate(self):
        for broken in (
            [],
            [{"id": "warm-up", "difficulty": "easy"}],
            [
                {"id": "skill-gate", "difficulty": "skill_gate"},
                {"id": "warm-up", "difficulty": "easy"},
            ],
            [
                {"id": "warm-up", "difficulty": "easy"},
                {"id": "warm-up", "difficulty": "easy"},
            ],
            [
                {"id": "warm-up", "difficulty": "easy"},
                {"id": "skill-gate", "difficulty": "easy"},
            ],
        ):
            card = make_card()
            card["test_levels"] = broken
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(card=card)

    def test_open_authority_fails_closed(self):
        for key in ("may_freeze_factory_kernel", "may_publish", "may_submit_platform"):
            card = make_card()
            card["authority"][key] = True
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(card=card)

    def test_missing_or_non_candidate_authority_fails_closed(self):
        card = make_card()
        card["authority"]["candidate_only"] = False
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(card=card)
        card = make_card()
        del card["authority"]
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(card=card)
        card = make_card()
        del card["authority"]["may_publish"]
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(card=card)

    def test_extra_authority_grant_fails_closed(self):
        for key in ("may_compile_work_package", "may_claim_verified_current_hot"):
            card = make_card()
            card["authority"][key] = True
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(card=card)

    def test_unknown_authority_key_fails_closed(self):
        for extra_value in (True, False):
            card = make_card()
            card["authority"]["may_run_arbitrary_commands"] = extra_value
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(card=card)

    def test_every_recognized_authority_field_must_be_declared(self):
        for key in (
            "may_claim_verified_current_hot",
            "may_compile_work_package",
            "may_freeze_factory_kernel",
            "may_publish",
            "may_submit_platform",
        ):
            card = make_card()
            del card["authority"][key]
            with self.assertRaises(ReferenceAdExperimentError):
                self.build(card=card)

    def test_card_must_bind_to_observation_id(self):
        card = make_card(observation_id="some-other-observation")
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(card=card)

    def test_card_status_must_be_experimental_candidate_only(self):
        card = make_card()
        card["status"] = "frozen_kernel"
        with self.assertRaises(ReferenceAdExperimentError):
            self.build(card=card)

    def test_real_evidence_bundle_validates(self):
        evidence = (
            PROJECT
            / "evidence"
            / "ad-tests"
            / "2026-07-30-douyin-7665976730670091561"
        )
        observation = json.loads(
            (evidence / "reference-ad-observation.json").read_text(encoding="utf-8")
        )
        card = json.loads((evidence / "mechanic-card.json").read_text(encoding="utf-8"))
        receipt = build_reference_ad_experiment_receipt(
            observation, card, base_dir=evidence
        )
        self.assertEqual(receipt["closure_state"], "reference_ad_experiment_candidate")
        self.assertEqual(
            receipt["source"]["sha256"],
            "0e4c03d6049f29b559e57acf544220803b52ccf15b146b424201cf9f5e64a44d",
        )


class ReferenceAdWorkflowBoundaryTests(unittest.TestCase):
    def test_capability_graph_declares_candidate_only_reference_ad_lane(self):
        graph = json.loads((PROJECT / "capability-graph.json").read_text(encoding="utf-8"))
        self.assertIn("reference_ad_experiment_candidate", graph["closure_states"])
        nodes = {node["id"]: node for node in graph["nodes"]}
        node = nodes["reference-ad-experiment"]
        for gate in (
            "local-digest-readback",
            "no-symlink-local-media",
            "verified-current-hot-false",
            "no-rank-claim",
            "clean-room-boundary",
            "candidate-only",
            "authority-closed",
        ):
            self.assertIn(gate, node["gates"])
        for closed in (
            "verified-current-hot",
            "market-to-kernel-gate",
            "kernel-freeze",
            "platform-submission",
            "publish",
        ):
            self.assertIn(closed, node["cannot_satisfy"])

    def test_market_to_kernel_gate_still_requires_verified_current_hot(self):
        graph = json.loads((PROJECT / "capability-graph.json").read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in graph["nodes"]}
        gate = nodes["market-to-kernel-gate"]
        self.assertIn("verified-current-hot", gate["gates"])
        self.assertNotIn("reference_ad_experiment_receipt", gate["consumes"])

    def test_readme_documents_reference_ad_boundary(self):
        readme = (PROJECT / "README.md").read_text(encoding="utf-8")
        self.assertIn("reference_ad_experiment.py", readme)
        self.assertIn("stack-path-runner", readme)
        self.assertIn("verified_current_hot", readme)

    def test_spec_packet_documents_reference_ad_lane(self):
        spec = (PROJECT / "spec-packet.md").read_text(encoding="utf-8")
        self.assertIn("reference-ad", spec.lower())

    def test_workflow_state_keeps_reference_ad_lane_candidate_only(self):
        state = (PROJECT / "workflow-state.yaml.md").read_text(encoding="utf-8")
        self.assertIn("reference-ad-experiment", state)
        self.assertIn("cannot satisfy", state)


if __name__ == "__main__":
    unittest.main()
