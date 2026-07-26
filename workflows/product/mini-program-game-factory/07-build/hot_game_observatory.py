"""Fail-closed evaluator for time-bounded mini-game market observations."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


SOURCE_TYPES = {
    "direct_app_rank_capture",
    "direct_gameplay_capture",
    "official_platform_case",
    "first_party_creator_report",
    "third_party_rank_report",
    "search_or_social_lead",
}
PLATFORMS = {"douyin", "wechat", "kuaishou", "multi_platform"}
MECHANIC_FIELDS = {
    "core_action",
    "state_transition",
    "session_loop",
    "goal_or_exit",
    "failure_pressure",
    "randomness",
    "spectator_hook",
    "social_hook",
    "content_burden",
    "reusable_mechanics",
    "non_copyable_expression",
}
DIRECT_RANK_SOURCE_TYPES = {"direct_app_rank_capture"}
DIRECT_EVIDENCE_SOURCE_TYPES = {"direct_app_rank_capture", "direct_gameplay_capture"}
CURRENT_RANK_DAYS = 7
RECENT_SIGNAL_DAYS = 60


class ObservationError(ValueError):
    """Raised when evidence is incomplete or internally inconsistent."""


def _parse_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ObservationError(f"{field} must be a non-empty ISO datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationError(f"{field} is not a valid ISO datetime: {value}") from exc
    if parsed.tzinfo is None:
        raise ObservationError(f"{field} must include a timezone")
    return parsed


def _age_days(as_of: datetime, value: Any, field: str) -> float:
    observed = _parse_datetime(value, field)
    seconds = (as_of - observed).total_seconds()
    if seconds < 0:
        raise ObservationError(f"{field} cannot be later than as_of")
    return seconds / 86400.0


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ObservationError(f"{field} must be an object")
    return value


def _require_list(value: Any, field: str) -> List[Any]:
    if not isinstance(value, list):
        raise ObservationError(f"{field} must be an array")
    return value


def _validate_sources(snapshot: Mapping[str, Any], as_of: datetime) -> Dict[str, Mapping[str, Any]]:
    source_index: Dict[str, Mapping[str, Any]] = {}
    for index, raw_source in enumerate(_require_list(snapshot.get("sources"), "sources")):
        source = _require_mapping(raw_source, f"sources[{index}]")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise ObservationError(f"sources[{index}].source_id must be non-empty")
        if source_id in source_index:
            raise ObservationError(f"duplicate source_id: {source_id}")
        source_type = source.get("source_type")
        if source_type not in SOURCE_TYPES:
            raise ObservationError(f"unsupported source_type for {source_id}: {source_type}")
        publisher = source.get("publisher")
        if not isinstance(publisher, str) or not publisher.strip():
            raise ObservationError(f"source {source_id} must name its publisher")
        independence_key = source.get("independence_key")
        if not isinstance(independence_key, str) or not independence_key.strip():
            raise ObservationError(f"source {source_id} must declare an independence_key")
        url = source.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ObservationError(f"source {source_id} must use a replayable https URL")
        if source_type in DIRECT_EVIDENCE_SOURCE_TYPES:
            digest = source.get("evidence_digest")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ObservationError(f"direct source {source_id} must include a lowercase SHA-256 evidence_digest")
        _age_days(as_of, source.get("published_at"), f"source {source_id}.published_at")
        _age_days(as_of, source.get("accessed_at"), f"source {source_id}.accessed_at")
        source_index[source_id] = source
    if not source_index:
        raise ObservationError("at least one source is required")
    return source_index


def _source(source_index: Mapping[str, Mapping[str, Any]], source_id: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(source_id, str) or source_id not in source_index:
        raise ObservationError(f"{field} references unknown source_id: {source_id}")
    return source_index[source_id]


def _independent_lineages(source_ids: Iterable[str], source_index: Mapping[str, Mapping[str, Any]]) -> set:
    return {str(source_index[source_id]["independence_key"]).strip().lower() for source_id in source_ids}


def _evaluate_observation(
    raw_observation: Any,
    index: int,
    source_index: Mapping[str, Mapping[str, Any]],
    as_of: datetime,
) -> Dict[str, Any]:
    observation = _require_mapping(raw_observation, f"observations[{index}]")
    observation_id = observation.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id:
        raise ObservationError(f"observations[{index}].observation_id must be non-empty")
    if observation.get("platform") not in PLATFORMS:
        raise ObservationError(f"observation {observation_id} has unsupported platform")
    if not isinstance(observation.get("game_name"), str) or not observation["game_name"].strip():
        raise ObservationError(f"observation {observation_id} must name the game")

    rank_signals = _require_list(observation.get("rank_signals", []), f"{observation_id}.rank_signals")
    popularity_signals = _require_list(
        observation.get("popularity_signals", []), f"{observation_id}.popularity_signals"
    )
    mechanics = _require_list(observation.get("mechanic_evidence", []), f"{observation_id}.mechanic_evidence")

    signal_ages: List[float] = []
    signal_source_ids: List[str] = []
    fresh_direct_rank = False

    for signal_index, raw_signal in enumerate(rank_signals):
        signal = _require_mapping(raw_signal, f"{observation_id}.rank_signals[{signal_index}]")
        source_id = signal.get("source_id")
        if not isinstance(source_id, str):
            raise ObservationError(f"{observation_id}.rank_signals[{signal_index}] source_id must be a string")
        source = _source(source_index, source_id, f"{observation_id}.rank_signals[{signal_index}]")
        rank = signal.get("rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            raise ObservationError(f"{observation_id} rank must be a positive integer")
        age = _age_days(as_of, signal.get("captured_at"), f"{observation_id}.rank captured_at")
        signal_ages.append(age)
        signal_source_ids.append(source_id)
        if (
            signal.get("direct_readback") is True
            and source.get("source_type") in DIRECT_RANK_SOURCE_TYPES
            and age <= CURRENT_RANK_DAYS
        ):
            fresh_direct_rank = True

    for signal_index, raw_signal in enumerate(popularity_signals):
        signal = _require_mapping(raw_signal, f"{observation_id}.popularity_signals[{signal_index}]")
        source_id = signal.get("source_id")
        if not isinstance(source_id, str):
            raise ObservationError(f"{observation_id}.popularity_signals[{signal_index}] source_id must be a string")
        _source(source_index, source_id, f"{observation_id}.popularity_signals[{signal_index}]")
        age = _age_days(as_of, signal.get("captured_at"), f"{observation_id}.popularity captured_at")
        signal_ages.append(age)
        signal_source_ids.append(source_id)

    direct_gameplay = False
    mechanic_source_ids: List[str] = []
    for mechanic_index, raw_mechanic in enumerate(mechanics):
        mechanic = _require_mapping(raw_mechanic, f"{observation_id}.mechanic_evidence[{mechanic_index}]")
        source_id = mechanic.get("source_id")
        if not isinstance(source_id, str):
            raise ObservationError(f"{observation_id}.mechanic_evidence[{mechanic_index}] source_id must be a string")
        source = _source(source_index, source_id, f"{observation_id}.mechanic_evidence[{mechanic_index}]")
        missing = sorted(field for field in MECHANIC_FIELDS if field not in mechanic)
        if missing:
            raise ObservationError(f"{observation_id} mechanic evidence missing: {', '.join(missing)}")
        mechanic_source_ids.append(source_id)
        if mechanic.get("direct_playback") is True and source.get("source_type") == "direct_gameplay_capture":
            direct_gameplay = True

    independent_lineages = _independent_lineages(signal_source_ids, source_index)
    recent_signal = bool(signal_ages) and min(signal_ages) <= RECENT_SIGNAL_DAYS

    if fresh_direct_rank and len(independent_lineages) >= 2 and direct_gameplay:
        status = "verified_current_hot"
    elif recent_signal:
        status = "recent_market_lead"
    elif signal_ages:
        status = "stale_lead"
    else:
        status = "unranked_lead"

    blockers = []
    if status != "verified_current_hot":
        if not fresh_direct_rank:
            blockers.append("no_direct_rank_readback_within_7_days")
        if len(independent_lineages) < 2:
            blockers.append("fewer_than_2_independent_signal_lineages")
        if not direct_gameplay:
            blockers.append("no_direct_gameplay_capture")

    return {
        "observation_id": observation_id,
        "game_name": observation["game_name"],
        "platform": observation["platform"],
        "status": status,
        "rank_signal_count": len(rank_signals),
        "popularity_signal_count": len(popularity_signals),
        "mechanic_evidence_count": len(mechanics),
        "independent_signal_lineages": len(independent_lineages),
        "fresh_direct_rank": fresh_direct_rank,
        "direct_gameplay": direct_gameplay,
        "blockers": blockers,
    }


def evaluate_snapshot(snapshot: Any, as_of_value: str) -> Dict[str, Any]:
    snapshot = _require_mapping(snapshot, "snapshot")
    if snapshot.get("schema_version") != 1:
        raise ObservationError("schema_version must equal 1")
    snapshot_id = snapshot.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ObservationError("snapshot_id must be non-empty")
    as_of = _parse_datetime(as_of_value, "as_of")
    observed_at = _parse_datetime(snapshot.get("observed_at"), "observed_at")
    if observed_at > as_of:
        raise ObservationError("observed_at cannot be later than as_of")

    source_index = _validate_sources(snapshot, as_of)
    raw_observations = _require_list(snapshot.get("observations"), "observations")
    if not raw_observations:
        raise ObservationError("at least one observation is required")
    observation_ids = set()
    evaluated = []
    for index, raw_observation in enumerate(raw_observations):
        item = _evaluate_observation(raw_observation, index, source_index, as_of)
        if item["observation_id"] in observation_ids:
            raise ObservationError(f"duplicate observation_id: {item['observation_id']}")
        observation_ids.add(item["observation_id"])
        evaluated.append(item)

    receipt_without_digest = {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "as_of": as_of_value,
        "source_count": len(source_index),
        "observations": evaluated,
        "summary": {
            status: sum(1 for item in evaluated if item["status"] == status)
            for status in ("verified_current_hot", "recent_market_lead", "stale_lead", "unranked_lead")
        },
        "may_freeze_kernel": False,
        "authority_boundary": "market evidence may nominate hypotheses; it cannot freeze kernels or publish",
    }
    canonical = json.dumps(receipt_without_digest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    receipt = dict(receipt_without_digest)
    receipt["digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--as-of", required=True, help="timezone-aware ISO datetime")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        receipt = evaluate_snapshot(snapshot, args.as_of)
    except (OSError, json.JSONDecodeError, ObservationError) as exc:
        parser.error(str(exc))

    rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
