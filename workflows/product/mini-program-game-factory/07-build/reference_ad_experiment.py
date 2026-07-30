#!/usr/bin/env python3
"""Deterministic validator/receipt builder for the reference-ad experiment lane.

A user-supplied reference advertisement may open a candidate-only clean-room
experiment. This validator binds the local media digest, enforces the market
and clean-room boundaries, and emits a deterministic receipt. It can never
promote `verified_current_hot`, freeze a kernel, compile a work package, or
open platform/submission/publish authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from work_package_compiler import digest


class ReferenceAdExperimentError(ValueError):
    """Raised when the reference-ad experiment input cannot be proven safe."""


REQUIRED_SOURCE_TYPE = "user_supplied_reference_ad"
REQUIRED_CARD_STATUS = "experimental_candidate_only"
REQUIRED_LEVELS = (("warm-up", "easy"), ("skill-gate", "skill_gate"))
RECOGNIZED_AUTHORITY_KEYS = (
    "candidate_only",
    "may_claim_verified_current_hot",
    "may_compile_work_package",
    "may_freeze_factory_kernel",
    "may_publish",
    "may_submit_platform",
)
ALLOWED_MARKET_STATUS_KEYS = ("verified_current_hot", "rank_claimed", "boundary")
CANNOT_SATISFY_GATES = (
    "verified-current-hot",
    "market-to-kernel-gate",
    "kernel-freeze",
    "work-package-compilation",
    "cocos-build",
    "platform-submission",
    "publish",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReferenceAdExperimentError(f"{field} must be an object")
    return value


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferenceAdExperimentError(f"{field} must be a non-empty string")
    return value


def _require_string_list(value: Any, field: str) -> List[str]:
    if not isinstance(value, list) or not value:
        raise ReferenceAdExperimentError(f"{field} must be a non-empty array")
    for index, item in enumerate(value):
        _require_string(item, f"{field}[{index}]")
    return list(value)


def _digest_file(path: Path) -> tuple[str, int]:
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


def _verify_media(source: Mapping[str, Any], base_dir: Path) -> Dict[str, Any]:
    media_value = _require_string(source.get("local_media_path"), "source.local_media_path")
    declared = source.get("sha256")
    if not isinstance(declared, str) or SHA256_RE.fullmatch(declared) is None:
        raise ReferenceAdExperimentError(
            "source.sha256 must be a declared lowercase 64-hex SHA-256"
        )

    declared_path = Path(media_value).expanduser()
    unresolved = declared_path if declared_path.is_absolute() else base_dir / declared_path
    if unresolved.is_symlink():
        raise ReferenceAdExperimentError(f"media must not be a symlink: {unresolved}")
    resolved = unresolved.resolve()
    if not resolved.exists():
        raise ReferenceAdExperimentError(f"media does not exist: {resolved}")
    if resolved.is_symlink() or not resolved.is_file():
        raise ReferenceAdExperimentError(f"media is not a regular file: {resolved}")

    computed, size = _digest_file(resolved)
    if computed != declared:
        raise ReferenceAdExperimentError(
            "declared source.sha256 does not match local media bytes"
        )
    return {
        "source_type": REQUIRED_SOURCE_TYPE,
        "local_media_path": str(resolved),
        "sha256": computed,
        "media_size_bytes": size,
    }


def _verify_market_status(observation: Mapping[str, Any]) -> None:
    status = _require_mapping(observation.get("market_status"), "market_status")
    unknown = sorted(str(key) for key in status if key not in ALLOWED_MARKET_STATUS_KEYS)
    if unknown:
        raise ReferenceAdExperimentError(
            "market_status accepts only verified_current_hot, rank_claimed and "
            f"boundary; unknown keys rejected: {', '.join(unknown)}"
        )
    if status.get("verified_current_hot") is not False:
        raise ReferenceAdExperimentError(
            "market_status.verified_current_hot must be exactly false"
        )
    if status.get("rank_claimed") is not False:
        raise ReferenceAdExperimentError("market_status.rank_claimed must be exactly false")
    _require_string(status.get("boundary"), "market_status.boundary")


def _verify_observation_content(observation: Mapping[str, Any]) -> None:
    visible = observation.get("visible_observations")
    if not isinstance(visible, list) or not visible:
        raise ReferenceAdExperimentError("visible_observations must be a non-empty array")
    for index, entry in enumerate(visible):
        entry_map = _require_mapping(entry, f"visible_observations[{index}]")
        _require_string_list(entry_map.get("facts"), f"visible_observations[{index}].facts")

    inferences = observation.get("inferences")
    if not isinstance(inferences, list) or not inferences:
        raise ReferenceAdExperimentError("inferences must be a non-empty array")
    for index, entry in enumerate(inferences):
        entry_map = _require_mapping(entry, f"inferences[{index}]")
        _require_string(entry_map.get("claim"), f"inferences[{index}].claim")
        confidence = entry_map.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not (
            0 < confidence <= 1
        ):
            raise ReferenceAdExperimentError(
                f"inferences[{index}].confidence must be a number in (0, 1]"
            )

    _require_string_list(observation.get("unknowns"), "unknowns")


def _verify_clean_room(observation: Mapping[str, Any]) -> Dict[str, List[str]]:
    boundary = _require_mapping(
        observation.get("clean_room_boundary"), "clean_room_boundary"
    )
    return {
        "reusable_mechanics": _require_string_list(
            boundary.get("reusable_mechanics"), "clean_room_boundary.reusable_mechanics"
        ),
        "non_copyable_expression": _require_string_list(
            boundary.get("non_copyable_expression"),
            "clean_room_boundary.non_copyable_expression",
        ),
    }


def _verify_levels(card: Mapping[str, Any]) -> List[Dict[str, str]]:
    levels = card.get("test_levels")
    if not isinstance(levels, list) or len(levels) != len(REQUIRED_LEVELS):
        raise ReferenceAdExperimentError(
            "test_levels must contain exactly a warm-up level then a skill-gate level"
        )
    normalized: List[Dict[str, str]] = []
    for index, (required_id, required_difficulty) in enumerate(REQUIRED_LEVELS):
        level = _require_mapping(levels[index], f"test_levels[{index}]")
        if level.get("id") != required_id or level.get("difficulty") != required_difficulty:
            raise ReferenceAdExperimentError(
                f"test_levels[{index}] must be id={required_id} difficulty={required_difficulty}"
            )
        normalized.append({"id": required_id, "difficulty": required_difficulty})
    return normalized


def _verify_authority(card: Mapping[str, Any]) -> None:
    authority = _require_mapping(card.get("authority"), "authority")
    unknown = sorted(str(key) for key in authority if key not in RECOGNIZED_AUTHORITY_KEYS)
    if unknown:
        raise ReferenceAdExperimentError(
            f"authority contains unrecognized keys: {', '.join(unknown)}; "
            "the reference-ad lane fails closed on undeclared authority"
        )
    for key in RECOGNIZED_AUTHORITY_KEYS:
        if key not in authority:
            raise ReferenceAdExperimentError(f"authority.{key} must be declared")
    if authority["candidate_only"] is not True:
        raise ReferenceAdExperimentError("authority.candidate_only must be exactly true")
    for key in RECOGNIZED_AUTHORITY_KEYS:
        if key == "candidate_only":
            continue
        if authority[key] is not False:
            raise ReferenceAdExperimentError(
                f"authority.{key} must be exactly false; the lane stays candidate-only"
            )


def build_reference_ad_experiment_receipt(
    observation: Any,
    mechanic_card: Any,
    base_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Validate the observation + mechanic card pair and build a receipt.

    Fails closed on digest mismatch, rank claims, missing clean-room
    boundaries, malformed levels, or any open authority.
    """
    observation_map = _require_mapping(observation, "observation")
    card = _require_mapping(mechanic_card, "mechanic_card")
    root = (base_dir or Path.cwd()).resolve()

    observation_id = _require_string(
        observation_map.get("observation_id"), "observation_id"
    )
    source = _require_mapping(observation_map.get("source"), "source")
    if source.get("source_type") != REQUIRED_SOURCE_TYPE:
        raise ReferenceAdExperimentError(
            f"source.source_type must be {REQUIRED_SOURCE_TYPE}"
        )

    media = _verify_media(source, root)
    _verify_market_status(observation_map)
    _verify_observation_content(observation_map)
    clean_room = _verify_clean_room(observation_map)

    mechanic_id = _require_string(card.get("mechanic_id"), "mechanic_card.mechanic_id")
    if card.get("status") != REQUIRED_CARD_STATUS:
        raise ReferenceAdExperimentError(
            f"mechanic_card.status must be {REQUIRED_CARD_STATUS}"
        )
    if card.get("source_observation") != observation_id:
        raise ReferenceAdExperimentError(
            "mechanic_card.source_observation must bind to observation_id"
        )
    levels = _verify_levels(card)
    _verify_authority(card)

    receipt: Dict[str, Any] = {
        "schema_version": 1,
        "closure_state": "reference_ad_experiment_candidate",
        "observation_id": observation_id,
        "mechanic_id": mechanic_id,
        "source": media,
        "market_status": {"verified_current_hot": False, "rank_claimed": False},
        "observation_digest": digest(observation_map),
        "mechanic_card_digest": digest(card),
        "clean_room_boundary": clean_room,
        "levels": levels,
        "authority": {
            "candidate_only": True,
            "may_claim_verified_current_hot": False,
            "may_freeze_factory_kernel": False,
            "may_compile_work_package": False,
            "may_submit_platform": False,
            "may_publish": False,
        },
        "cannot_satisfy_gates": list(CANNOT_SATISFY_GATES),
        "boundary": (
            "user-supplied reference-ad evidence permits a local clean-room browser "
            "experiment only; it proves no market rank, no popularity, no Cocos or "
            "platform runtime, and opens no freeze/build/submission/publish authority"
        ),
    }
    receipt["digest"] = digest(receipt)
    return receipt


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation", required=True, type=Path)
    parser.add_argument("--mechanic-card", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        observation_path = args.observation.resolve()
        receipt = build_reference_ad_experiment_receipt(
            json.loads(observation_path.read_text(encoding="utf-8")),
            json.loads(args.mechanic_card.read_text(encoding="utf-8")),
            base_dir=observation_path.parent,
        )
    except (OSError, json.JSONDecodeError, ReferenceAdExperimentError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    rendered = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
