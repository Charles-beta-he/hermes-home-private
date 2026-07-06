#!/usr/bin/env python3
"""Reversible snapshot GC and evolve.log archive for cron.

- Moves snapshots older than retention days into a timestamped quarantine instead
  of deleting them outright.
- Copies evolve.log into a month archive and truncates only after the copy is
  written and fsynced.
- Emits a concise JSON receipt. No network or external side effects.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HERMES = HOME / ".hermes"
SNAPSHOTS = HERMES / "snapshots"
QUARANTINE_ROOT = HERMES / "archive" / "snapshot-gc-quarantine"
EVOLVE_LOG = HERMES / "logs" / "evolve.log"
EVOLVE_ARCHIVE = HERMES / "archive" / "evolve-log"


def fsync_file(path: Path) -> None:
    with path.open("rb") as fh:
        os.fsync(fh.fileno())


def move_old_snapshots(retention_days: int, dry_run: bool) -> list[dict[str, str]]:
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - retention_days * 86400
    moved: list[dict[str, str]] = []
    if not SNAPSHOTS.exists():
        return moved
    quarantine = QUARANTINE_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for path in sorted(SNAPSHOTS.glob("pre_*")):
        try:
            if not path.is_dir() or path.stat().st_mtime > cutoff:
                continue
            dest = quarantine / path.name
            moved.append({"from": str(path), "to": str(dest)})
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(dest))
        except FileNotFoundError:
            continue
    return moved


def archive_evolve_log(dry_run: bool) -> dict[str, object]:
    if not EVOLVE_LOG.exists() or EVOLVE_LOG.stat().st_size == 0:
        return {"archived": False, "reason": "missing_or_empty"}
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    target = EVOLVE_ARCHIVE / f"evolve-{month}.log"
    info = {"archived": True, "source": str(EVOLVE_LOG), "target": str(target), "bytes": EVOLVE_LOG.stat().st_size}
    if dry_run:
        return info
    target.parent.mkdir(parents=True, exist_ok=True)
    with EVOLVE_LOG.open("rb") as src, target.open("ab") as dst:
        shutil.copyfileobj(src, dst)
        dst.flush()
        os.fsync(dst.fileno())
    fsync_file(target)
    # Truncate only after archive copy exists.
    with EVOLVE_LOG.open("w", encoding="utf-8") as fh:
        fh.write("")
        fh.flush()
        os.fsync(fh.fileno())
    return info


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retention-days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    receipt = {
        "schema": "snapshot_gc_archive_noagent_v1",
        "ok": True,
        "ts": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "retention_days": args.retention_days,
        "snapshot_moves": move_old_snapshots(args.retention_days, args.dry_run),
        "evolve_log": archive_evolve_log(args.dry_run),
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
