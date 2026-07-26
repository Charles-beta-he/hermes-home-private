import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from hot_game_observatory import MECHANIC_FIELDS, ObservationError, evaluate_snapshot


AS_OF = "2026-07-26T12:00:00+08:00"


def source(source_id, source_type, published_at, url=None, game_name="Game A", platform="douyin"):
    result = {
        "source_id": source_id,
        "source_type": source_type,
        "publisher": source_id,
        "independence_key": source_id,
        "published_at": published_at,
        "accessed_at": AS_OF,
        "url": url or f"https://example.com/{source_id}",
        "evidence_level": "direct" if source_type.startswith("direct_") else "third_party_claim",
        "subject_bindings": [{
            "platform": platform,
            "game_name": game_name,
            "charts": ["hot", "grossing"],
        }],
    }
    if source_type.startswith("direct_"):
        media = Path(__file__).resolve()
        result.pop("url")
        result["local_media_path"] = str(media)
        result["evidence_digest"] = hashlib.sha256(media.read_bytes()).hexdigest()
        result["media_size_bytes"] = media.stat().st_size
    return result


def observation(rank_sources, direct_gameplay=False, rank_at="2026-07-24T12:00:00+08:00"):
    sources = [
        source("rank-direct", "direct_app_rank_capture", "2026-07-24T12:00:00+08:00"),
        source("rank-second", "official_platform_case", "2026-07-25T12:00:00+08:00"),
    ]
    if direct_gameplay:
        sources.append(source("play", "direct_gameplay_capture", "2026-07-25T12:00:00+08:00"))
    return {
        "schema_version": 1,
        "snapshot_id": "fixture",
        "observed_at": AS_OF,
        "sources": sources,
        "observations": [{
            "observation_id": "game-a-douyin",
            "platform": "douyin",
            "game_name": "Game A",
            "rank_signals": [
                {
                    "source_id": source_id,
                    "chart": "hot",
                    "rank": i + 1,
                    "captured_at": rank_at,
                    "direct_readback": source_id == "rank-direct",
                }
                for i, source_id in enumerate(rank_sources)
            ],
            "popularity_signals": [],
            "mechanic_evidence": ([{
                "source_id": "play",
                "direct_playback": True,
                "core_action": "tap",
                "state_transition": "hidden to revealed",
                "session_loop": "inspect-act-resolve",
                "goal_or_exit": "clear target",
                "failure_pressure": "timer",
                "randomness": "none observed",
                "spectator_hook": "reveal",
                "social_hook": "none observed",
                "content_burden": "levels",
                "reusable_mechanics": ["reveal"],
                "non_copyable_expression": ["name", "art", "level layout"],
            }] if direct_gameplay else []),
        }],
    }


class HotGameObservatoryTests(unittest.TestCase):
    def test_verified_current_hot_requires_fresh_direct_rank_independent_source_and_playback(self):
        receipt = evaluate_snapshot(observation(["rank-direct", "rank-second"], direct_gameplay=True), AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "verified_current_hot")

    def test_duplicate_source_does_not_satisfy_independence(self):
        receipt = evaluate_snapshot(observation(["rank-direct", "rank-direct"], direct_gameplay=True), AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "recent_market_lead")

    def test_syndicated_sources_share_one_independence_lineage(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][1]["independence_key"] = "rank-direct"
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "recent_market_lead")

    def test_same_direct_media_digest_cannot_inflate_independent_lineages(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        second = snapshot["sources"][1]
        direct_fixture = source("second-direct", "direct_app_rank_capture", "2026-07-25T12:00:00+08:00")
        second.clear()
        second.update(direct_fixture)
        second["source_id"] = "rank-second"
        second["independence_key"] = "claimed-separate-lineage"
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "recent_market_lead")
        self.assertEqual(receipt["observations"][0]["independent_signal_lineages"], 1)

    def test_same_digest_cannot_escape_through_direct_indirect_mix(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][1]["evidence_digest"] = snapshot["sources"][0]["evidence_digest"]
        snapshot["sources"][1]["independence_key"] = "claimed-separate-indirect-lineage"
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "recent_market_lead")
        self.assertEqual(receipt["observations"][0]["independent_signal_lineages"], 1)

    def test_direct_evidence_without_digest_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        del snapshot["sources"][0]["evidence_digest"]
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_direct_source_type_cannot_downgrade_its_evidence_level(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][0]["evidence_level"] = "third_party_claim"
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_local_direct_digest_mismatch_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][0]["evidence_digest"] = "0" * 64
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_local_direct_media_size_mismatch_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][0]["media_size_bytes"] += 1
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_direct_evidence_may_use_local_media_instead_of_https_url(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        direct = snapshot["sources"][0]
        direct.pop("url", None)
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "verified_current_hot")

    def test_direct_url_without_local_digest_readback_cannot_verify_current(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        direct = snapshot["sources"][0]
        direct.pop("local_media_path")
        direct.pop("media_size_bytes")
        direct["url"] = "https://example.com/rank-capture"
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertNotEqual(receipt["observations"][0]["status"], "verified_current_hot")

    def test_indirect_source_still_requires_https_url(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][1].pop("url")
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_indirect_source_declared_digest_must_be_valid_sha256(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][1]["evidence_digest"] = "not-a-digest"
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_unknown_source_reference_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["observations"][0]["rank_signals"][0]["source_id"] = "missing"
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_missing_direct_playback_blocks_verified_hot(self):
        receipt = evaluate_snapshot(observation(["rank-direct", "rank-second"], direct_gameplay=False), AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "recent_market_lead")

    def test_old_signal_expires_to_stale(self):
        receipt = evaluate_snapshot(
            observation(["rank-direct", "rank-second"], direct_gameplay=True, rank_at="2026-04-01T12:00:00+08:00"),
            AS_OF,
        )
        self.assertEqual(receipt["observations"][0]["status"], "stale_lead")

    def test_direct_playback_requires_complete_mechanic_fields(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        del snapshot["observations"][0]["mechanic_evidence"][0]["state_transition"]
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_direct_playback_rejects_empty_mechanic_values(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        mechanic = snapshot["observations"][0]["mechanic_evidence"][0]
        for field in (
            "core_action",
            "state_transition",
            "session_loop",
            "goal_or_exit",
            "failure_pressure",
            "randomness",
            "spectator_hook",
            "social_hook",
            "content_burden",
        ):
            mechanic[field] = ""
        mechanic["reusable_mechanics"] = []
        mechanic["non_copyable_expression"] = [""]
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_same_input_has_deterministic_digest(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        first = evaluate_snapshot(copy.deepcopy(snapshot), AS_OF)
        second = evaluate_snapshot(copy.deepcopy(snapshot), AS_OF)
        self.assertEqual(first["digest"], second["digest"])

    def test_receipt_digest_binds_material_snapshot_fields(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        mutated = copy.deepcopy(snapshot)
        mutated["observations"][0]["rank_signals"][0]["rank"] = 9
        first = evaluate_snapshot(snapshot, AS_OF)
        second = evaluate_snapshot(mutated, AS_OF)
        self.assertEqual(first["observations"][0]["status"], second["observations"][0]["status"])
        self.assertNotEqual(first["snapshot_digest"], second["snapshot_digest"])
        self.assertNotEqual(first["digest"], second["digest"])

    def test_old_direct_source_with_fresh_asserted_signal_cannot_verify_current(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][0]["published_at"] = "2026-04-01T12:00:00+08:00"
        snapshot["sources"][0]["accessed_at"] = "2026-04-01T12:00:00+08:00"
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertNotEqual(receipt["observations"][0]["status"], "verified_current_hot")
        self.assertFalse(receipt["observations"][0]["fresh_direct_rank"])

    def test_discovery_only_source_cannot_satisfy_current_quorum(self):
        snapshot = observation(["rank-direct"], direct_gameplay=True)
        snapshot["sources"][1]["source_type"] = "search_or_social_lead"
        snapshot["observations"][0]["popularity_signals"] = [{
            "source_id": "rank-second",
            "kind": "topic_views",
            "value": 999999,
            "captured_at": "2026-07-25T12:00:00+08:00",
        }]
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertEqual(receipt["observations"][0]["status"], "recent_market_lead")
        self.assertEqual(receipt["observations"][0]["independent_signal_lineages"], 1)

    def test_subject_mismatch_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["sources"][0]["subject_bindings"][0]["game_name"] = "Different Game"
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_stale_direct_gameplay_cannot_verify_current(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        play = next(item for item in snapshot["sources"] if item["source_id"] == "play")
        play["published_at"] = "2026-04-01T12:00:00+08:00"
        play["accessed_at"] = "2026-04-01T12:00:00+08:00"
        receipt = evaluate_snapshot(snapshot, AS_OF)
        self.assertNotEqual(receipt["observations"][0]["status"], "verified_current_hot")
        self.assertFalse(receipt["observations"][0]["direct_gameplay"])

    def test_real_snapshot_remains_recent_lead_not_verified_hot(self):
        path = Path(__file__).parents[1] / "evidence" / "hot-game-snapshot-2026-07-26.json"
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        receipt = evaluate_snapshot(snapshot, AS_OF)
        statuses = {item["status"] for item in receipt["observations"]}
        self.assertNotIn("verified_current_hot", statuses)
        self.assertIn("recent_market_lead", statuses)

    def test_all_emitted_states_are_registered_in_capability_graph(self):
        graph_path = Path(__file__).parents[1] / "capability-graph.json"
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        emitted_states = {
            "verified_current_hot",
            "recent_market_lead",
            "stale_lead",
            "unranked_lead",
        }
        self.assertTrue(emitted_states <= set(graph["closure_states"]))

    def test_schema_required_mechanic_fields_match_validator(self):
        schema_path = Path(__file__).parents[1] / "hot-game-observation-schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required_mechanic_fields"]), MECHANIC_FIELDS)


if __name__ == "__main__":
    unittest.main()
