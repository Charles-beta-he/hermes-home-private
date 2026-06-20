#!/usr/bin/env python3
"""Continuation garbage collector for the Hermes self-healing plane.

Archive active continuation packets older than 7 days into the archived/ tree
(preserving the original filename), then delete archived packets older than 30
days. Optional explicit caps can also compact active/archived backlog safely:

  - CONTINUATION_ACTIVE_MAX / --active-max: archive oldest active packets until
    active count is at or below the cap.
  - CONTINUATION_ARCHIVED_MAX / --archived-max: delete oldest archived packets
    until archived count is at or below the cap.
  - CONTINUATION_KEEP_PER_TASK / --keep-per-task: archive older active packets
    beyond the newest N for the same task/brain id.

Caps default to 0 (disabled). This avoids destructive surprise cleanup from cron;
operators should review --dry-run output, then apply gradual real caps.

Pure stdlib so it can run from a bare cron context with no venv.

Output contract:
  - JSON {"archived_count": N, "deleted_count": N, "remaining_count": N, ...}
  - Empty stdout means nothing happened (cron silent mode); any work emits the
    report.
  - --dry-run reports the projected result without moving or deleting files.

Usage:
  python3 ~/.hermes/scripts/continuation-gc.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ARCHIVE_AFTER_DAYS = 7
DELETE_AFTER_DAYS = 30


def continuation_root() -> Path:
    return Path(
        os.environ.get(
            "HERMES_CONTINUATION_DIR",
            str(Path.home() / ".hermes" / "state" / "continuations"),
        )
    ).expanduser()


def _parse_created_at(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _created_at(path: Path) -> datetime | None:
    return _parse_created_at(_payload(path).get("created_at"))


def _sort_key(path: Path) -> tuple[datetime, str]:
    created = _created_at(path)
    if created is None:
        try:
            created = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except OSError:
            created = datetime.fromtimestamp(0, timezone.utc)
    return created, path.name


def _task_key(path: Path) -> str:
    payload = _payload(path)
    for key in ("task_id", "brain_id", "mission_id", "source_task_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return "unknown"


def _positive_int(value: object, default: int = 0) -> int:
    try:
        parsed = int(str(value or 0))
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _archive_file(path: Path, archived_dir: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    archived_dir.mkdir(parents=True, exist_ok=True)
    target = archived_dir / path.name
    if target.exists():
        stem = path.stem
        suffix = path.suffix
        target = archived_dir / f"{stem}.duplicate-{int(datetime.now(timezone.utc).timestamp())}{suffix}"
    shutil.move(str(path), str(target))


def run(
    *,
    dry_run: bool,
    now: datetime,
    root: Path,
    active_max: int = 0,
    archived_max: int = 0,
    keep_per_task: int = 0,
) -> dict[str, Any]:
    active_dir = root / "active"
    archived_dir = root / "archived"
    archive_cutoff = now - timedelta(days=ARCHIVE_AFTER_DAYS)
    delete_cutoff = now - timedelta(days=DELETE_AFTER_DAYS)

    archived_count = 0
    deleted_count = 0
    reasons: Counter[str] = Counter()
    archived_candidates: set[Path] = set()
    deleted_candidates: set[Path] = set()

    active_files = sorted(active_dir.glob("*.json"), key=_sort_key) if active_dir.exists() else []

    # 1) Age-based active archival keeps the historical behavior.
    for path in active_files:
        created = _created_at(path)
        if created is None or created >= archive_cutoff:
            continue
        archived_candidates.add(path)
        reasons["active_age"] += 1

    # 2) Per-task active cap: keep newest N active packets per task, archive older.
    if keep_per_task > 0:
        by_task: dict[str, list[Path]] = defaultdict(list)
        for path in active_files:
            if path in archived_candidates:
                continue
            by_task[_task_key(path)].append(path)
        for task, paths in by_task.items():
            if len(paths) <= keep_per_task:
                continue
            oldest_first = sorted(paths, key=_sort_key)
            for path in oldest_first[: len(paths) - keep_per_task]:
                archived_candidates.add(path)
                reasons["active_per_task_cap"] += 1

    # 3) Global active cap: after other archival candidates, archive oldest surplus.
    if active_max > 0:
        projected_active = [p for p in active_files if p not in archived_candidates]
        if len(projected_active) > active_max:
            for path in sorted(projected_active, key=_sort_key)[: len(projected_active) - active_max]:
                archived_candidates.add(path)
                reasons["active_max_cap"] += 1

    for path in sorted(archived_candidates, key=_sort_key):
        _archive_file(path, archived_dir, dry_run=dry_run)
        archived_count += 1

    archived_files = sorted(archived_dir.glob("*.json"), key=_sort_key) if archived_dir.exists() else []

    # 4) Age-based archived deletion keeps the historical behavior.
    for path in archived_files:
        created = _created_at(path)
        if created is None or created >= delete_cutoff:
            continue
        deleted_candidates.add(path)
        reasons["archived_age"] += 1

    # 5) Explicit archived cap: delete oldest surplus only when configured.
    if archived_max > 0:
        projected_archived = [p for p in archived_files if p not in deleted_candidates]
        # Files archived in this dry-run would also enter archived/. Include them in
        # the projected count but never delete same-tick archive candidates.
        projected_count = len(projected_archived) + len(archived_candidates)
        if projected_count > archived_max:
            surplus = projected_count - archived_max
            for path in sorted(projected_archived, key=_sort_key)[:surplus]:
                deleted_candidates.add(path)
                reasons["archived_max_cap"] += 1

    for path in sorted(deleted_candidates, key=_sort_key):
        if not dry_run:
            try:
                path.unlink()
            except OSError:
                continue
        deleted_count += 1

    remaining_count = max(0, len(active_files) - archived_count)
    report: dict[str, Any] = {
        "archived_count": archived_count,
        "deleted_count": deleted_count,
        "remaining_count": remaining_count,
    }
    if dry_run:
        report["dry_run"] = True
    if active_max > 0 or archived_max > 0 or keep_per_task > 0:
        report["caps"] = {
            "active_max": active_max,
            "archived_max": archived_max,
            "keep_per_task": keep_per_task,
        }
    if reasons:
        report["reason_counts"] = dict(sorted(reasons.items()))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without moving or deleting")
    parser.add_argument("--active-max", type=int, default=_positive_int(os.environ.get("CONTINUATION_ACTIVE_MAX")), help="archive oldest active packets until active count is <= this cap; 0 disables")
    parser.add_argument("--archived-max", type=int, default=_positive_int(os.environ.get("CONTINUATION_ARCHIVED_MAX")), help="delete oldest archived packets until archived count is <= this cap; 0 disables")
    parser.add_argument("--keep-per-task", type=int, default=_positive_int(os.environ.get("CONTINUATION_KEEP_PER_TASK")), help="archive older active packets beyond newest N per task; 0 disables")
    args = parser.parse_args()

    report = run(
        dry_run=args.dry_run,
        now=datetime.now(timezone.utc),
        root=continuation_root(),
        active_max=_positive_int(args.active_max),
        archived_max=_positive_int(args.archived_max),
        keep_per_task=_positive_int(args.keep_per_task),
    )

    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
