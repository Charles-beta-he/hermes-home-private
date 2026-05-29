#!/usr/bin/env python3
"""Continuation garbage collector for the Hermes self-healing plane.

Archive active continuation packets older than 7 days into the archived/ tree
(preserving the original filename), then delete archived packets older than 30
days. Pure stdlib so it can run from a bare cron context with no venv.

Output contract:
  - JSON {"archived_count": N, "deleted_count": N, "remaining_count": N}
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
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def _created_at(path: Path) -> datetime | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return _parse_created_at(payload.get("created_at"))


def run(*, dry_run: bool, now: datetime, root: Path) -> dict[str, int]:
    active_dir = root / "active"
    archived_dir = root / "archived"
    archive_cutoff = now - timedelta(days=ARCHIVE_AFTER_DAYS)
    delete_cutoff = now - timedelta(days=DELETE_AFTER_DAYS)

    archived_count = 0
    deleted_count = 0

    active_files = sorted(active_dir.glob("*.json")) if active_dir.exists() else []
    remaining_count = len(active_files)
    for path in active_files:
        created = _created_at(path)
        if created is None or created >= archive_cutoff:
            continue
        if not dry_run:
            archived_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(archived_dir / path.name))
        archived_count += 1
        remaining_count -= 1

    archived_files = sorted(archived_dir.glob("*.json")) if archived_dir.exists() else []
    for path in archived_files:
        created = _created_at(path)
        if created is None or created >= delete_cutoff:
            continue
        if not dry_run:
            try:
                path.unlink()
            except OSError:
                continue
        deleted_count += 1

    return {
        "archived_count": archived_count,
        "deleted_count": deleted_count,
        "remaining_count": remaining_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without moving or deleting")
    args = parser.parse_args()

    report = run(dry_run=args.dry_run, now=datetime.now(timezone.utc), root=continuation_root())

    if report["archived_count"] or report["deleted_count"]:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
