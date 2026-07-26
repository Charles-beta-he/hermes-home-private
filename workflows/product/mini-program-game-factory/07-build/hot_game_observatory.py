"""Fail-closed evaluator for time-bounded mini-game market observations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple


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
CURRENT_CORROBORATION_SOURCE_TYPES = {
    "direct_app_rank_capture",
    "official_platform_case",
    "first_party_creator_report",
    "third_party_rank_report",
}
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


def _stable_identity(stat_result: os.stat_result) -> Tuple[int, int, int, int]:
    return (stat_result.st_dev, stat_result.st_ino, stat_result.st_size, stat_result.st_mtime_ns)


def _digest_file(path: Path) -> Tuple[str, int]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    if _stable_identity(before) != _stable_identity(after):
        raise ObservationError(f"local media changed while hashing: {path}")
    if _stable_identity(path.stat()) != _stable_identity(after):
        raise ObservationError(f"local media path changed while hashing: {path}")
    return digest.hexdigest(), after.st_size


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
        type_is_direct = source_type in DIRECT_EVIDENCE_SOURCE_TYPES
        is_direct = source.get("evidence_level") == "direct"
        if type_is_direct != is_direct:
            raise ObservationError(
                f"source {source_id} direct source_type and evidence_level must agree"
            )
        local_media_path = source.get("local_media_path")
        has_local_media = (
            isinstance(local_media_path, str)
            and local_media_path.startswith("/")
            and "replace" not in local_media_path
        )
        if url is not None and (not isinstance(url, str) or not url.startswith("https://")):
            raise ObservationError(f"source {source_id} must use a replayable https URL when url is provided")
        if not is_direct and not isinstance(url, str):
            raise ObservationError(f"source {source_id} must use a replayable https URL")
        if not is_direct and local_media_path is not None:
            raise ObservationError(f"non-direct source {source_id} may not declare local_media_path")
        if is_direct and not isinstance(url, str) and not has_local_media:
            raise ObservationError(f"direct source {source_id} requires https url or absolute local_media_path")

        local_digest_verified = False
        digest = source.get("evidence_digest")
        if digest is not None and (
            not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise ObservationError(f"source {source_id} evidence_digest must be lowercase sha256")

        if is_direct:
            if digest is None:
                raise ObservationError(f"direct source {source_id} missing evidence_digest")
            if local_media_path is not None:
                if not has_local_media:
                    raise ObservationError(f"direct source {source_id} local_media_path must be an absolute non-placeholder path")
                media_path = Path(local_media_path)
                if not media_path.exists() or not media_path.is_file():
                    raise ObservationError(f"direct source {source_id} local media is not a readable regular file")
                actual_digest, actual_size = _digest_file(media_path)
                if actual_digest != digest:
                    raise ObservationError(f"direct source {source_id} evidence_digest does not match local media")
                declared_size = source.get("media_size_bytes")
                if declared_size is not None and (
                    not isinstance(declared_size, int)
                    or isinstance(declared_size, bool)
                    or declared_size != actual_size
                ):
                    raise ObservationError(f"direct source {source_id} media_size_bytes does not match local media")
                local_digest_verified = True
        _age_days(as_of, source.get("published_at"), f"source {source_id}.published_at")
        _age_days(as_of, source.get("accessed_at"), f"source {source_id}.accessed_at")
        validated_source = dict(source)
        validated_source["_local_digest_verified"] = local_digest_verified
        source_index[source_id] = validated_source
    if not source_index:
        raise ObservationError("at least one source is required")
    return source_index


def _source(source_index: Mapping[str, Mapping[str, Any]], source_id: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(source_id, str) or source_id not in source_index:
        raise ObservationError(f"{field} references unknown source_id: {source_id}")
    return source_index[source_id]


def _independent_lineages(source_ids: Iterable[str], source_index: Mapping[str, Mapping[str, Any]]) -> set:
    ids = list(source_ids)
    parent = list(range(len(ids)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    lineage_owner: Dict[str, int] = {}
    digest_owner: Dict[str, int] = {}
    for index, source_id in enumerate(ids):
        source = source_index[source_id]
        lineage = str(source["independence_key"]).strip().lower()
        if lineage in lineage_owner:
            union(index, lineage_owner[lineage])
        else:
            lineage_owner[lineage] = index
        digest = source.get("evidence_digest")
        if isinstance(digest, str):
            digest_key = digest.strip().lower()
            if digest_key in digest_owner:
                union(index, digest_owner[digest_key])
            else:
                digest_owner[digest_key] = index

    return {find(index) for index in range(len(ids))}


def _source_within_days(source: Mapping[str, Any], as_of: datetime, max_days: int) -> bool:
    return (
        _age_days(as_of, source.get("published_at"), f"source {source.get('source_id')}.published_at") <= max_days
        and _age_days(as_of, source.get("accessed_at"), f"source {source.get('source_id')}.accessed_at") <= max_days
    )


def _source_binds_subject(
    source: Mapping[str, Any], platform: str, game_name: str, chart: Any = None
) -> bool:
    bindings = source.get("subject_bindings")
    if not isinstance(bindings, list):
        return False
    for binding in bindings:
        if not isinstance(binding, Mapping):
            continue
        if binding.get("platform") != platform or binding.get("game_name") != game_name:
            continue
        if chart is None:
            return True
        charts = binding.get("charts")
        if isinstance(charts, list) and chart in charts:
            return True
    return False


def _mechanic_field_has_evidence(field: str, value: Any) -> bool:
    if field in {"reusable_mechanics", "non_copyable_expression"}:
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and bool(item.strip()) for item in value)
        )
    return isinstance(value, str) and bool(value.strip())


def _snapshot_digest(snapshot: Mapping[str, Any]) -> str:
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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

    market_signal_ages: List[float] = []
    current_source_ids: List[str] = []
    fresh_direct_rank = False
    recent_signal = False

    for signal_index, raw_signal in enumerate(rank_signals):
        signal = _require_mapping(raw_signal, f"{observation_id}.rank_signals[{signal_index}]")
        source_id = signal.get("source_id")
        if not isinstance(source_id, str):
            raise ObservationError(f"{observation_id}.rank_signals[{signal_index}] source_id must be a string")
        source = _source(source_index, source_id, f"{observation_id}.rank_signals[{signal_index}]")
        rank = signal.get("rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            raise ObservationError(f"{observation_id} rank must be a positive integer")
        chart = signal.get("chart")
        if not isinstance(chart, str) or not chart.strip():
            raise ObservationError(f"{observation_id} rank chart must be non-empty")
        if not _source_binds_subject(source, observation["platform"], observation["game_name"], chart):
            raise ObservationError(f"{observation_id} rank source {source_id} is not bound to the game/platform/chart")
        age = _age_days(as_of, signal.get("captured_at"), f"{observation_id}.rank captured_at")
        eligible_type = source.get("source_type") in CURRENT_CORROBORATION_SOURCE_TYPES
        if eligible_type:
            market_signal_ages.append(age)
        if eligible_type and age <= RECENT_SIGNAL_DAYS and _source_within_days(source, as_of, RECENT_SIGNAL_DAYS):
            recent_signal = True
        current_eligible = (
            eligible_type
            and age <= CURRENT_RANK_DAYS
            and _source_within_days(source, as_of, CURRENT_RANK_DAYS)
            and (
                source.get("source_type") not in DIRECT_EVIDENCE_SOURCE_TYPES
                or source.get("_local_digest_verified") is True
            )
        )
        if current_eligible:
            current_source_ids.append(source_id)
        if (
            current_eligible
            and signal.get("direct_readback") is True
            and source.get("source_type") in DIRECT_RANK_SOURCE_TYPES
        ):
            fresh_direct_rank = True

    for signal_index, raw_signal in enumerate(popularity_signals):
        signal = _require_mapping(raw_signal, f"{observation_id}.popularity_signals[{signal_index}]")
        source_id = signal.get("source_id")
        if not isinstance(source_id, str):
            raise ObservationError(f"{observation_id}.popularity_signals[{signal_index}] source_id must be a string")
        source = _source(source_index, source_id, f"{observation_id}.popularity_signals[{signal_index}]")
        if not _source_binds_subject(source, observation["platform"], observation["game_name"]):
            raise ObservationError(f"{observation_id} popularity source {source_id} is not bound to the game/platform")
        age = _age_days(as_of, signal.get("captured_at"), f"{observation_id}.popularity captured_at")
        value = signal.get("value")
        kind = signal.get("kind")
        qualified = (
            isinstance(kind, str)
            and bool(kind.strip())
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
            and source.get("source_type") in CURRENT_CORROBORATION_SOURCE_TYPES
        )
        if qualified:
            market_signal_ages.append(age)
        if qualified and age <= RECENT_SIGNAL_DAYS and _source_within_days(source, as_of, RECENT_SIGNAL_DAYS):
            recent_signal = True
        if (
            qualified
            and age <= CURRENT_RANK_DAYS
            and _source_within_days(source, as_of, CURRENT_RANK_DAYS)
            and (
                source.get("source_type") not in DIRECT_EVIDENCE_SOURCE_TYPES
                or source.get("_local_digest_verified") is True
            )
        ):
            current_source_ids.append(source_id)

    direct_gameplay = False
    for mechanic_index, raw_mechanic in enumerate(mechanics):
        mechanic = _require_mapping(raw_mechanic, f"{observation_id}.mechanic_evidence[{mechanic_index}]")
        source_id = mechanic.get("source_id")
        if not isinstance(source_id, str):
            raise ObservationError(f"{observation_id}.mechanic_evidence[{mechanic_index}] source_id must be a string")
        source = _source(source_index, source_id, f"{observation_id}.mechanic_evidence[{mechanic_index}]")
        if not _source_binds_subject(source, observation["platform"], observation["game_name"]):
            raise ObservationError(f"{observation_id} mechanic source {source_id} is not bound to the game/platform")
        missing = sorted(
            field
            for field in MECHANIC_FIELDS
            if field not in mechanic or not _mechanic_field_has_evidence(field, mechanic.get(field))
        )
        if missing:
            raise ObservationError(f"{observation_id} mechanic evidence missing: {', '.join(missing)}")
        if (
            mechanic.get("direct_playback") is True
            and source.get("source_type") == "direct_gameplay_capture"
            and source.get("_local_digest_verified") is True
            and _source_within_days(source, as_of, CURRENT_RANK_DAYS)
        ):
            direct_gameplay = True

    independent_lineages = _independent_lineages(current_source_ids, source_index)

    if fresh_direct_rank and len(independent_lineages) >= 2 and direct_gameplay:
        status = "verified_current_hot"
    elif recent_signal:
        status = "recent_market_lead"
    elif market_signal_ages:
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
        "snapshot_digest": _snapshot_digest(snapshot),
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
