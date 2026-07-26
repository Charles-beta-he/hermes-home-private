import copy
import json
import tempfile
import unittest
from pathlib import Path

from hot_game_observatory import ObservationError, evaluate_snapshot


AS_OF = "2026-07-26T12:00:00+08:00"


def source(source_id, source_type, published_at, url=None):
    result = {
        "source_id": source_id,
        "source_type": source_type,
        "publisher": source_id,
        "independence_key": source_id,
        "published_at": published_at,
        "accessed_at": AS_OF,
        "url": url or f"https://example.com/{source_id}",
        "evidence_level": "direct" if source_type.startswith("direct_") else "third_party_claim",
    }
    if source_type.startswith("direct_"):
        result["evidence_digest"] = "a" * 64
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

    def test_direct_evidence_without_digest_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        del snapshot["sources"][0]["evidence_digest"]
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

    def test_unknown_source_reference_fails_closed(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        snapshot["observations"][0]["rank_signals"][0]["source_id"] = "missing"
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_direct_playback_requires_complete_mechanic_fields(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        del snapshot["observations"][0]["mechanic_evidence"][0]["state_transition"]
        with self.assertRaises(ObservationError):
            evaluate_snapshot(snapshot, AS_OF)

    def test_same_input_has_deterministic_digest(self):
        snapshot = observation(["rank-direct", "rank-second"], direct_gameplay=True)
        first = evaluate_snapshot(copy.deepcopy(snapshot), AS_OF)
        second = evaluate_snapshot(copy.deepcopy(snapshot), AS_OF)
        self.assertEqual(first["digest"], second["digest"])

    def test_real_snapshot_remains_recent_lead_not_verified_hot(self):
        path = Path(__file__).parents[1] / "evidence" / "hot-game-snapshot-2026-07-26.json"
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        receipt = evaluate_snapshot(snapshot, AS_OF)
        statuses = {item["status"] for item in receipt["observations"]}
        self.assertNotIn("verified_current_hot", statuses)
        self.assertIn("recent_market_lead", statuses)


if __name__ == "__main__":
    unittest.main()
