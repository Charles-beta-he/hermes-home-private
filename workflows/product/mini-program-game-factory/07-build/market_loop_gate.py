#!/usr/bin/env python3
"""Deterministic market-evidence gate for mini-game kernel hypotheses.

This gate can nominate an abstract kernel hypothesis from verified market
observations. It never freezes a kernel, compiles a work package, or grants
release authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from hot_game_observatory import ObservationError, evaluate_snapshot
from work_package_compiler import digest


class GateError(ValueError):
    """Raised when the market-to-hypothesis input envelope is malformed."""


def _require_list(value: Any, field: str) -> List[Any]:
    if not isinstance(value, list):
        raise GateError(f"{field} must be an array")
    return value


def _non_empty_strings(value: Any, field: str) -> List[str]:
    items = _require_list(value, field)
    if not items or any(not isinstance(item, str) or not item.strip() for item in items):
        raise GateError(f"{field} must contain non-empty strings")
    return items


def _normalize_surface(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return re.sub(r"[\W_]+", "_", normalized, flags=re.UNICODE).strip("_")


def _mentions_protected_surface(value: str, protected: Iterable[str]) -> bool:
    candidate = f"_{_normalize_surface(value)}_"
    return any(f"_{surface}_" in candidate for surface in protected)


def _reject(hypothesis_id: str, reason: str, details: Iterable[str] = ()) -> Dict[str, Any]:
    return {
        "hypothesis_id": hypothesis_id,
        "state": "rejected",
        "reason": reason,
        "details": sorted(set(details)),
    }


def gate_market_hypotheses(
    snapshot: Any,
    hypotheses: Any,
    routing: Mapping[str, Any],
    as_of: str,
) -> Dict[str, Any]:
    """Evaluate hypotheses against a fresh market receipt and fail closed."""

    market_receipt = evaluate_snapshot(snapshot, as_of)
    raw_hypotheses = _require_list(hypotheses, "hypotheses")
    observation_index = {item["observation_id"]: item for item in market_receipt["observations"]}
    protected = {
        _normalize_surface(item)
        for item in _non_empty_strings(routing.get("protected_surfaces"), "routing.protected_surfaces")
    }

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    seen_ids = set()

    for index, raw in enumerate(raw_hypotheses):
        if not isinstance(raw, Mapping):
            raise GateError(f"hypotheses[{index}] must be an object")
        hypothesis_id = raw.get("hypothesis_id")
        if not isinstance(hypothesis_id, str) or not hypothesis_id.strip():
            raise GateError(f"hypotheses[{index}].hypothesis_id must be non-empty")
        if hypothesis_id in seen_ids:
            raise GateError(f"duplicate hypothesis_id: {hypothesis_id}")
        seen_ids.add(hypothesis_id)

        source_ids = _non_empty_strings(raw.get("source_observation_ids"), f"{hypothesis_id}.source_observation_ids")
        unknown = sorted(source_id for source_id in source_ids if source_id not in observation_index)
        if unknown:
            rejected.append(_reject(hypothesis_id, "unknown_source_observation", unknown))
            continue

        unverified = sorted(
            source_id
            for source_id in source_ids
            if observation_index[source_id]["status"] != "verified_current_hot"
        )
        if unverified:
            rejected.append(_reject(hypothesis_id, "source_observation_not_verified_current_hot", unverified))
            continue

        exclusions = raw.get("non_copyable_exclusions")
        if not isinstance(exclusions, list) or not exclusions or any(
            not isinstance(item, str) or not item.strip() for item in exclusions
        ):
            rejected.append(_reject(hypothesis_id, "missing_non_copyable_exclusions"))
            continue

        abstract_mechanics = _non_empty_strings(raw.get("abstract_mechanics"), f"{hypothesis_id}.abstract_mechanics")
        differentiation = raw.get("differentiation")
        if not isinstance(differentiation, str) or not differentiation.strip():
            raise GateError(f"{hypothesis_id}.differentiation must be non-empty")
        proposed_changes = raw.get("proposed_changes")
        if not isinstance(proposed_changes, list) or not proposed_changes or any(
            not isinstance(item, str) or not item.strip() for item in proposed_changes
        ):
            rejected.append(_reject(hypothesis_id, "missing_proposed_changes"))
            continue
        protected_claims = sorted(
            item
            for item in [*proposed_changes, *abstract_mechanics, differentiation]
            if _mentions_protected_surface(item, protected)
        )
        if protected_claims:
            rejected.append(
                _reject(hypothesis_id, "protected_surface_requires_separate_spec_gate", protected_claims)
            )
            continue

        accepted.append(
            {
                "hypothesis_id": hypothesis_id,
                "state": "kernel_hypothesis",
                "source_observation_ids": source_ids,
                "source_observation_statuses": {
                    source_id: observation_index[source_id]["status"] for source_id in source_ids
                },
                "abstract_mechanics": abstract_mechanics,
                "proposed_changes": proposed_changes,
                "differentiation": differentiation,
                "non_copyable_exclusions": exclusions,
                "required_next_gates": [
                    "kernel_spec_review",
                    "offline_rule_simulation",
                    "golden_and_negative_cases",
                    "human_playtest",
                ],
            }
        )

    result: Dict[str, Any] = {
        "schema_version": 1,
        "as_of": as_of,
        "closure_state": "market_to_kernel_gate_evaluated",
        "market_receipt_digest": market_receipt["digest"],
        "hypotheses_digest": digest(raw_hypotheses),
        "routing_digest": digest(routing),
        "market_summary": market_receipt["summary"],
        "summary": {
            "accepted": len(accepted),
            "rejected": len(rejected),
            "total": len(accepted) + len(rejected),
        },
        "accepted": accepted,
        "rejected": rejected,
        "authority": {
            "may_freeze_kernel": False,
            "may_compile_work_package": False,
            "may_submit_platform": False,
            "may_publish": False,
            "may_enter_credentials": False,
            "may_pay": False,
        },
        "authority_boundary": (
            "verified market evidence may nominate an abstract kernel hypothesis only; "
            "spec, simulation, golden cases, human playtest, platform, and release gates remain closed"
        ),
    }
    result["digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--hypotheses", required=True, type=Path)
    parser.add_argument("--routing", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        receipt = gate_market_hypotheses(
            json.loads(args.snapshot.read_text(encoding="utf-8")),
            json.loads(args.hypotheses.read_text(encoding="utf-8")),
            json.loads(args.routing.read_text(encoding="utf-8")),
            args.as_of,
        )
    except (OSError, json.JSONDecodeError, ObservationError, GateError, KeyError, TypeError, ValueError) as exc:
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
