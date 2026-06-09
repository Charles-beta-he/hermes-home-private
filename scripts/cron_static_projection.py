#!/usr/bin/env python3
"""Canonical static projection for Hermes cron jobs.

The scheduler intentionally writes runtime fields (next_run_at, last_run_at,
repeat.completed, etc.) into cron/jobs.json today.  This helper gives audits a
stable config-only view so scheduler ticks do not look like real cron config
changes.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
JOBS_PATH = HERMES_HOME / "cron" / "jobs.json"

TOP_LEVEL_RUNTIME_FIELDS = {"updated_at"}
JOB_RUNTIME_FIELDS = {
    "next_run_at",
    "last_run_at",
    "last_status",
    "last_error",
    "last_delivery_error",
    "paused_at",
}
REPEAT_RUNTIME_FIELDS = {"completed"}
RUNTIME_STATES = {"scheduled", "running", "error", "completed"}


def _strip_empty(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {k: _strip_empty(v) for k, v in sorted(value.items())}
        return {k: v for k, v in cleaned.items() if v not in ({}, [], None)}
    if isinstance(value, list):
        return [_strip_empty(v) for v in value]
    return value


def static_job(job: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(job)
    for field in JOB_RUNTIME_FIELDS:
        out.pop(field, None)
    repeat = out.get("repeat")
    if isinstance(repeat, dict):
        for field in REPEAT_RUNTIME_FIELDS:
            repeat.pop(field, None)
        if not repeat:
            out.pop("repeat", None)
    state = str(out.get("state") or "").lower()
    if state in RUNTIME_STATES:
        out.pop("state", None)
    return _strip_empty(out)


def static_projection(data: dict[str, Any]) -> dict[str, Any]:
    jobs = data.get("jobs", [])
    if not isinstance(jobs, list):
        jobs = []
    projected = [static_job(j) for j in jobs if isinstance(j, dict)]
    projected.sort(key=lambda j: str(j.get("id") or j.get("name") or ""))
    out = {k: copy.deepcopy(v) for k, v in data.items() if k not in TOP_LEVEL_RUNTIME_FIELDS and k != "jobs"}
    out["jobs"] = projected
    return _strip_empty(out)


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def projection_sha256(data: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(static_projection(data)).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_git_head_jobs(repo: Path) -> dict[str, Any] | None:
    proc = subprocess.run(
        ["git", "show", "HEAD:cron/jobs.json"],
        cwd=str(repo),
        text=True,
        capture_output=True,
        timeout=10,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return json.loads(proc.stdout)


def runtime_field_counts(data: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if any(field in data for field in TOP_LEVEL_RUNTIME_FIELDS):
        for field in TOP_LEVEL_RUNTIME_FIELDS:
            if field in data:
                counts[field] = counts.get(field, 0) + 1
    for job in data.get("jobs", []) if isinstance(data.get("jobs"), list) else []:
        if not isinstance(job, dict):
            continue
        for field in JOB_RUNTIME_FIELDS:
            if field in job:
                counts[field] = counts.get(field, 0) + 1
        repeat = job.get("repeat")
        if isinstance(repeat, dict):
            for field in REPEAT_RUNTIME_FIELDS:
                if field in repeat:
                    counts[f"repeat.{field}"] = counts.get(f"repeat.{field}", 0) + 1
    return counts


def build_report(path: Path = JOBS_PATH, *, compare_git: bool = False, repo: Path | None = None) -> dict[str, Any]:
    data = load_json(path)
    projection = static_projection(data)
    report = {
        "path": str(path),
        "job_count": len(projection.get("jobs", [])),
        "static_sha256": hashlib.sha256(canonical_json(projection).encode("utf-8")).hexdigest(),
        "runtime_field_counts": runtime_field_counts(data),
        "static_projection": projection,
    }
    if compare_git:
        repo = repo or HERMES_HOME
        head = load_git_head_jobs(repo)
        if head is None:
            report["git_compare"] = {"status": "unavailable"}
        else:
            head_sha = projection_sha256(head)
            current_sha = report["static_sha256"]
            report["git_compare"] = {
                "status": "same_static" if head_sha == current_sha else "static_changed",
                "head_static_sha256": head_sha,
                "current_static_sha256": current_sha,
            }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", default=str(JOBS_PATH), help="Path to cron jobs.json")
    parser.add_argument("--compare-git", action="store_true", help="Compare static projection against HEAD:cron/jobs.json")
    parser.add_argument("--repo", default=str(HERMES_HOME), help="Git repo for --compare-git")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report")
    args = parser.parse_args(argv)

    report = build_report(Path(args.jobs).expanduser(), compare_git=args.compare_git, repo=Path(args.repo).expanduser())
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        compare = report.get("git_compare") or {}
        suffix = f" git_compare={compare.get('status')}" if compare else ""
        print(f"cron_static_projection jobs={report['job_count']} sha256={report['static_sha256']}{suffix}")
    if (report.get("git_compare") or {}).get("status") == "static_changed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
