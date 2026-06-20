#!/usr/bin/env python3
"""Read-only handoff backlog report for Hermes taskpool artifacts.

This script intentionally does not delete, move, archive, or rewrite handoff
artifacts. It emits a compact manifest so operators can review redundancy and
blast radius before choosing a compaction policy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_HANDOFF_DIRS = [
    Path.home() / ".hermes" / "state" / "auto_run_handoffs",
    Path.home() / ".hermes" / "state" / "parallel_handoffs",
]


def _iso_from_mtime(value: float | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path, *, include_hash: bool = True) -> dict[str, Any]:
    stat = path.stat()
    record: dict[str, Any] = {
        "path": str(path),
        "name": path.name,
        "bytes": stat.st_size,
        "mtime": _iso_from_mtime(stat.st_mtime),
    }
    if include_hash:
        record["sha256"] = _sha256(path)
    return record


def scan_dir(directory: Path, *, manifest_limit: int = 20, largest_limit: int = 10) -> dict[str, Any]:
    files = sorted([p for p in directory.glob("*") if p.is_file()]) if directory.exists() else []
    total_bytes = sum(p.stat().st_size for p in files)
    mtimes = [p.stat().st_mtime for p in files]
    largest = sorted(files, key=lambda p: (p.stat().st_size, p.name), reverse=True)[:largest_limit]
    # Manifest favors oldest files first: best first review target for compaction.
    manifest = sorted(files, key=lambda p: (p.stat().st_mtime, p.name))[:manifest_limit]
    return {
        "path": str(directory),
        "exists": directory.exists(),
        "count": len(files),
        "total_bytes": total_bytes,
        "oldest": _iso_from_mtime(min(mtimes) if mtimes else None),
        "newest": _iso_from_mtime(max(mtimes) if mtimes else None),
        "largest": [_file_record(p, include_hash=False) for p in largest],
        "manifest_sample": [_file_record(p, include_hash=True) for p in manifest],
    }


def build_report(dirs: list[Path], *, manifest_limit: int = 20, largest_limit: int = 10) -> dict[str, Any]:
    dir_reports = [scan_dir(d, manifest_limit=manifest_limit, largest_limit=largest_limit) for d in dirs]
    return {
        "schema": "handoff_backlog_report_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety": "read-only; no handoff files are moved, deleted, archived, or rewritten",
        "total_count": sum(int(r["count"]) for r in dir_reports),
        "total_bytes": sum(int(r["total_bytes"]) for r in dir_reports),
        "dirs": dir_reports,
    }


def _parse_dirs(raw_dirs: list[str]) -> list[Path]:
    if raw_dirs:
        return [Path(p).expanduser() for p in raw_dirs]
    env_dirs = os.environ.get("HERMES_HANDOFF_DIRS", "").strip()
    if env_dirs:
        return [Path(p).expanduser() for p in env_dirs.split(os.pathsep) if p.strip()]
    return DEFAULT_HANDOFF_DIRS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", action="append", default=[], help="handoff directory to scan; repeatable")
    parser.add_argument("--manifest-limit", type=int, default=20, help="oldest file sha256 sample count per directory")
    parser.add_argument("--largest-limit", type=int, default=10, help="largest file sample count per directory")
    args = parser.parse_args()

    report = build_report(
        _parse_dirs(args.dir),
        manifest_limit=max(0, args.manifest_limit),
        largest_limit=max(0, args.largest_limit),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
