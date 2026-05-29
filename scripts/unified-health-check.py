#!/usr/bin/env python3
"""Unified Hermes health check for the self-healing plane.

Collapses the scattered point checks into one score across three categories:
  - Core Services  : gateway process alive + file-descriptor headroom
  - Data Integrity : state.db readable and non-empty
  - Cron Health    : count of enabled cron jobs in error/failed state

Backlog pressure (continuation + handoff) feeds the score and the issue list.
The only auto-fix is pure infrastructure: when the continuation backlog exceeds
AUTOFIX_CONTINUATION_THRESHOLD, continuation-gc.py is invoked to sweep stale
packets.

Output:
  --format=terminal (default)  human summary
  --format=json                machine-readable report
  --silent                     print nothing when fully healthy (cron mode)

Pure stdlib so it runs from a bare cron context.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
HERMES = HOME / ".hermes"
STATE_DB = HERMES / "state.db"
CRON_JOBS = HERMES / "cron" / "jobs.json"
CONTINUATION_ACTIVE = HERMES / "state" / "continuations" / "active"
HANDOFF_DIRS = (
    HERMES / "state" / "parallel_handoffs",
    HERMES / "state" / "auto_run_handoffs",
)
GC_SCRIPT = HERMES / "scripts" / "continuation-gc.py"

# Thresholds.
FD_YELLOW, FD_RED = 200, 400
CRON_YELLOW, CRON_RED = 1, 10
CONTINUATION_YELLOW, CONTINUATION_RED = 200, 500
HANDOFF_YELLOW, HANDOFF_RED = 100, 300
AUTOFIX_CONTINUATION_THRESHOLD = 500

GREEN, YELLOW, RED = "GREEN", "YELLOW", "RED"


def _gateway_pid() -> int | None:
    try:
        out = subprocess.run(
            ["pgrep", "-f", "gateway run"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        if line.strip().isdigit():
            return int(line.strip())
    return None


def _fd_count(pid: int) -> int | None:
    try:
        out = subprocess.run(
            ["lsof", "-p", str(pid)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return max(0, len(lines) - 1)  # drop header row


def _count_glob(directory: Path, pattern: str) -> int:
    return len(list(directory.glob(pattern))) if directory.exists() else 0


def check_core_services() -> dict:
    pid = _gateway_pid()
    issues: list[str] = []
    if pid is None:
        return {
            "status": RED, "gateway_running": False, "gateway_pid": None,
            "fd_count": None, "issues": ["gateway process not running"],
        }
    fd = _fd_count(pid)
    status = GREEN
    if fd is None:
        issues.append("gateway fd count unavailable")
    elif fd >= FD_RED:
        status = RED
        issues.append(f"gateway fd count critical: {fd} >= {FD_RED}")
    elif fd >= FD_YELLOW:
        status = YELLOW
        issues.append(f"gateway fd count elevated: {fd} >= {FD_YELLOW}")
    return {
        "status": status, "gateway_running": True, "gateway_pid": pid,
        "fd_count": fd, "issues": issues,
    }


def check_data_integrity() -> dict:
    issues: list[str] = []
    if not STATE_DB.exists():
        return {"status": RED, "readable": False, "size_bytes": 0,
                "issues": [f"state.db missing: {STATE_DB}"]}
    try:
        size = STATE_DB.stat().st_size
        with STATE_DB.open("rb") as fh:
            fh.read(16)
        readable = True
    except OSError as exc:
        return {"status": RED, "readable": False, "size_bytes": 0,
                "issues": [f"state.db unreadable: {exc}"]}
    status = GREEN
    if size == 0:
        status = RED
        issues.append("state.db is empty (0 bytes)")
    return {"status": status, "readable": readable, "size_bytes": size, "issues": issues}


def check_cron_health() -> dict:
    issues: list[str] = []
    if not CRON_JOBS.exists():
        return {"status": GREEN, "broken_count": 0, "issues": []}
    try:
        data = json.loads(CRON_JOBS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": RED, "broken_count": None,
                "issues": [f"cron jobs.json unreadable: {exc}"]}
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    jobs = jobs if isinstance(jobs, list) else []
    broken = [
        j for j in jobs
        if isinstance(j, dict)
        and j.get("enabled", True)
        and str(j.get("last_status") or "").lower() in {"error", "failed"}
    ]
    count = len(broken)
    status = GREEN
    if count >= CRON_RED:
        status = RED
        issues.append(f"broken cron jobs critical: {count} >= {CRON_RED}")
    elif count >= CRON_YELLOW:
        status = YELLOW
        issues.append(f"broken cron jobs: {count}")
    return {"status": status, "broken_count": count, "issues": issues}


def _backlog_status(count: int, yellow: int, red: int, label: str) -> tuple[str, list[str]]:
    if count >= red:
        return RED, [f"{label} backlog critical: {count} >= {red}"]
    if count >= yellow:
        return YELLOW, [f"{label} backlog elevated: {count} >= {yellow}"]
    return GREEN, []


def autofix_continuation(active_count: int, *, dry_run: bool = False) -> dict | None:
    if active_count <= AUTOFIX_CONTINUATION_THRESHOLD or not GC_SCRIPT.exists():
        return None
    cmd = [sys.executable, str(GC_SCRIPT)]
    if dry_run:
        cmd.append("--dry-run")
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ran": False, "error": str(exc)}
    report = {}
    if proc.stdout.strip():
        try:
            report = json.loads(proc.stdout.strip().splitlines()[-1])
        except ValueError:
            report = {"raw": proc.stdout.strip()}
    return {"ran": True, "returncode": proc.returncode, "report": report}


WEIGHTS = {GREEN: 0, YELLOW: 5, RED: 15}


def collect(*, dry_run: bool = False) -> dict:
    core = check_core_services()
    data = check_data_integrity()
    cron = check_cron_health()

    active_count = _count_glob(CONTINUATION_ACTIVE, "*.json")
    handoff_count = sum(_count_glob(d, "*.md") for d in HANDOFF_DIRS)

    autofix = autofix_continuation(active_count, dry_run=dry_run)
    if autofix and autofix.get("ran") and not dry_run:
        # Re-read backlog after the sweep so the report reflects the fix.
        active_count = _count_glob(CONTINUATION_ACTIVE, "*.json")

    cont_status, cont_issues = _backlog_status(
        active_count, CONTINUATION_YELLOW, CONTINUATION_RED, "continuation")
    handoff_status, handoff_issues = _backlog_status(
        handoff_count, HANDOFF_YELLOW, HANDOFF_RED, "handoff")

    score = 100
    for section in (core, data, cron):
        score -= WEIGHTS[section["status"]]
    score -= WEIGHTS[cont_status]
    score -= WEIGHTS[handoff_status]
    if not core["gateway_running"]:
        score -= 25  # gateway down is the dominant failure
    score = max(0, score)

    issues = (
        core["issues"] + data["issues"] + cron["issues"] + cont_issues + handoff_issues
    )

    return {
        "schema": "hermes_unified_health_v1",
        "health_score": score,
        "core_services": core["status"],
        "data_integrity": data["status"],
        "cron_health": cron["status"],
        "active_issues": issues,
        "details": {
            "core_services": core,
            "data_integrity": data,
            "cron_health": cron,
            "continuation_backlog": {"status": cont_status, "active_count": active_count},
            "handoff_backlog": {"status": handoff_status, "count": handoff_count},
            "autofix": autofix,
        },
        "healthy": not issues and score == 100,
    }


def render_terminal(report: dict) -> str:
    lines = [
        f"Health Score: {report['health_score']}/100",
        f"Core Services: {report['core_services']}",
        f"Data Integrity: {report['data_integrity']}",
        f"Cron Health: {report['cron_health']}",
    ]
    if report["active_issues"]:
        lines.append("Active Issues:")
        lines.extend(f"  - {issue}" for issue in report["active_issues"])
    autofix = report["details"].get("autofix")
    if autofix and autofix.get("ran"):
        rpt = autofix.get("report", {})
        lines.append(
            f"Auto-fix: continuation-gc archived={rpt.get('archived_count', '?')} "
            f"deleted={rpt.get('deleted_count', '?')}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["terminal", "json"], default="terminal")
    parser.add_argument("--silent", action="store_true",
                        help="print nothing when fully healthy (cron mode)")
    parser.add_argument("--dry-run", action="store_true",
                        help="do not mutate; run any auto-fix in dry-run mode")
    args = parser.parse_args()

    report = collect(dry_run=args.dry_run)

    if args.silent and report["healthy"]:
        return 0

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_terminal(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
