#!/usr/bin/env python3
"""Explicit local Experience Ratchet lifecycle reconciler.

The default mode is dry-run. ``--apply`` mutates only ExperienceAtom files inside
the selected store. It never promotes an atom, writes a landing zone, sends
externally, touches credentials, or erases history.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROMOTION_STATES = {"promoted_candidate", "promoted"}
FAILURE_REOPEN_STATES = {"validated", "promoted_candidate", "promoted"}
RETENTION_STATES = {"deprecated", "rolled_back", "revoked"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def last_atom_time(atom: dict[str, Any]) -> datetime | None:
    for item in reversed(atom.get("history") or []):
        if isinstance(item, dict):
            parsed = parse_iso(item.get("at"))
            if parsed is not None:
                return parsed
    return parse_iso((atom.get("source") or {}).get("captured_at"))


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"atom must be an object: {path}")
    return payload


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def plan_actions(
    atom: dict[str, Any],
    *,
    now: datetime,
    stale_days: int,
    failure_threshold: int,
    retention_days: int,
) -> list[dict[str, Any]]:
    status = str(atom.get("status") or "")
    actions: list[dict[str, Any]] = []
    failures = int((atom.get("metrics") or {}).get("failure_count") or 0)
    last_at = last_atom_time(atom)

    if status in FAILURE_REOPEN_STATES and failures >= failure_threshold:
        actions.append({
            "action": "failure_reopened",
            "from": status,
            "to": "deprecated",
            "reason": f"failure_count={failures} reached threshold={failure_threshold}; reopened for review",
        })
        return actions

    if status in PROMOTION_STATES and last_at is not None and last_at < now - timedelta(days=stale_days):
        actions.append({
            "action": "stale_demoted",
            "from": status,
            "to": "validated" if status == "promoted_candidate" else "deprecated",
            "reason": f"freshness exceeded stale_days={stale_days}",
        })
        return actions

    retention = atom.get("retention") or {}
    if (
        status in RETENTION_STATES
        and retention.get("state") != "retained_for_audit"
        and last_at is not None
        and last_at < now - timedelta(days=retention_days)
    ):
        actions.append({
            "action": "retention_applied",
            "from": status,
            "to": status,
            "reason": f"terminal state retained after retention_days={retention_days}",
        })
    return actions


def apply_action(atom: dict[str, Any], action: dict[str, Any], *, now: datetime, retention_days: int) -> None:
    event = action["action"]
    if event in {"stale_demoted", "failure_reopened"}:
        atom["status"] = action["to"]
        atom.setdefault("lifecycle", {})["last_action"] = event
        atom["lifecycle"]["last_action_at"] = iso(now)
        if event == "failure_reopened":
            atom["lifecycle"]["review_state"] = "reopened_after_failure"
        if action["to"] == "deprecated":
            atom.setdefault("rollback", {})["revoked_reason"] = action["reason"]
    elif event == "retention_applied":
        atom["retention"] = {
            "state": "retained_for_audit",
            "applied_at": iso(now),
            "policy_days": retention_days,
            "deletion_permitted": False,
            "history_preserved": True,
        }
    else:  # pragma: no cover - internal contract guard
        raise ValueError(f"unknown lifecycle action: {event}")
    atom.setdefault("history", []).append({
        "at": iso(now),
        "event": f"lifecycle:{event}",
        "reason": action["reason"],
        "from": action["from"],
        "to": action["to"],
    })


def reconcile_store(
    home: Path,
    *,
    now: datetime | None = None,
    stale_days: int = 14,
    failure_threshold: int = 1,
    retention_days: int = 30,
    apply: bool = False,
) -> dict[str, Any]:
    if min(stale_days, failure_threshold, retention_days) < 1:
        raise ValueError("stale_days, failure_threshold and retention_days must be >= 1")
    home = Path(home).expanduser().resolve()
    atoms_dir = home / "atoms"
    current = now or utc_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    decisions: list[dict[str, Any]] = []
    summary = {
        "atoms_checked": 0,
        "stale_demoted": 0,
        "failure_reopened": 0,
        "retention_applied": 0,
        "promotion_actions": 0,
        "history_erased": 0,
    }

    for path in sorted(atoms_dir.glob("*.json")) if atoms_dir.exists() else []:
        atom = read_json(path)
        summary["atoms_checked"] += 1
        before = json.loads(json.dumps(atom))
        actions = plan_actions(
            atom,
            now=current,
            stale_days=stale_days,
            failure_threshold=failure_threshold,
            retention_days=retention_days,
        )
        for action in actions:
            summary[action["action"]] += 1
            if action["to"] in PROMOTION_STATES:
                summary["promotion_actions"] += 1
            if apply:
                apply_action(atom, action, now=current, retention_days=retention_days)
        before_history = before.get("history") or []
        after_history = atom.get("history") or []
        if after_history[: len(before_history)] != before_history:
            summary["history_erased"] += 1
            raise RuntimeError(f"history preservation violated: {path}")
        if apply and actions:
            write_json_atomic(path, atom)
        decisions.append({
            "atom_id": atom.get("atom_id"),
            "path": str(path),
            "before_sha256": digest(before),
            "after_sha256": digest(atom),
            "actions": actions,
            "history_before": len(before_history),
            "history_after": len(after_history),
        })

    return {
        "ok": summary["promotion_actions"] == 0 and summary["history_erased"] == 0,
        "schema": "hermes_experience_ratchet_lifecycle_v1",
        "generated_at": iso(current),
        "mode": "apply" if apply else "dry_run",
        "home": str(home),
        "policy": {
            "stale_days": stale_days,
            "failure_threshold": failure_threshold,
            "retention_days": retention_days,
            "promotion_permitted": False,
            "history_deletion_permitted": False,
        },
        "summary": summary,
        "decisions": decisions,
        "side_effects_observed": ["local_write"] if apply and any(d["actions"] for d in decisions) else ["local_read"],
        "forbidden_side_effects": ["landing_zone_write", "silent_promotion", "history_deletion", "external_send", "credential_entry"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explicit Experience Ratchet lifecycle reconciler")
    parser.add_argument("--home", default=os.path.expanduser("~/.hermes/experience-ratchet"))
    parser.add_argument("--stale-days", type=int, default=14)
    parser.add_argument("--failure-threshold", type=int, default=1)
    parser.add_argument("--retention-days", type=int, default=30)
    parser.add_argument("--apply", action="store_true", help="Apply local atom lifecycle changes; default is dry-run")
    args = parser.parse_args(argv)
    result = reconcile_store(
        Path(args.home),
        stale_days=args.stale_days,
        failure_threshold=args.failure_threshold,
        retention_days=args.retention_days,
        apply=args.apply,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
