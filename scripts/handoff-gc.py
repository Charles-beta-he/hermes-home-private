#!/usr/bin/env python3
"""Handoff backlog report and reversible archive tool for Hermes taskpool artifacts.

Default mode is read-only. With --apply, old handoff files are moved into an
archive subdirectory with a JSON manifest. The script never deletes artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
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
        "safety": "read-only unless --apply is set; apply moves files into archive subdirectories and never deletes",
        "total_count": sum(int(r["count"]) for r in dir_reports),
        "total_bytes": sum(int(r["total_bytes"]) for r in dir_reports),
        "dirs": dir_reports,
    }


def plan_archive(directory: Path, *, keep_newest: int = 80) -> dict[str, Any]:
    files = sorted([p for p in directory.glob("*.md") if p.is_file()], key=lambda p: (p.stat().st_mtime, p.name)) if directory.exists() else []
    archive_count = max(0, len(files) - max(0, keep_newest))
    candidates = files[:archive_count]
    return {
        "path": str(directory),
        "keep_newest": max(0, keep_newest),
        "current_count": len(files),
        "archive_count": len(candidates),
        "candidates": [_file_record(p, include_hash=True) for p in candidates],
    }


def apply_archive(plan: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    directory = Path(str(plan["path"]))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = directory / "archived" / stamp
    moved: list[dict[str, Any]] = []
    for record in plan.get("candidates", []):
        src = Path(str(record["path"]))
        dst = archive_dir / src.name
        item = {**record, "archive_path": str(dst)}
        if not dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.move(str(src), str(dst))
                item["moved"] = True
            else:
                item["moved"] = False
                item["reason"] = "source_missing"
        moved.append(item)
    manifest_path = archive_dir / "manifest.json"
    result = {
        "schema": "handoff_archive_apply_v1",
        "dry_run": dry_run,
        "path": str(directory),
        "archive_dir": str(archive_dir),
        "planned_count": len(plan.get("candidates", [])),
        "moved_count": sum(1 for x in moved if x.get("moved")) if not dry_run else 0,
        "manifest_path": str(manifest_path),
        "items": moved,
    }
    if not dry_run and moved:
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return result


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
    parser.add_argument("--archive", action="store_true", help="include archive plan for each directory")
    parser.add_argument("--apply", action="store_true", help="move archive candidates into archived/<timestamp>/")
    parser.add_argument("--keep-newest", type=int, default=80, help="number of newest *.md handoffs to keep in each source directory")
    args = parser.parse_args()

    dirs = _parse_dirs(args.dir)
    report = build_report(
        dirs,
        manifest_limit=max(0, args.manifest_limit),
        largest_limit=max(0, args.largest_limit),
    )
    if args.archive or args.apply:
        plans = [plan_archive(d, keep_newest=max(0, args.keep_newest)) for d in dirs]
        report["archive_plans"] = plans
        report["archive_results"] = [apply_archive(plan, dry_run=not args.apply) for plan in plans]
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
