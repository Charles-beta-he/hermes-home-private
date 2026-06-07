#!/usr/bin/env python3
"""Taskpool debt ledger — read-only classification of long-lived Hermes debts.

This script intentionally does not mutate task notes, envelope state, cron jobs,
or continuation packets. It gives the control plane a single machine-readable
view of runtime blockers vs historical governance debt.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOME = Path.home()
HERMES = HOME / ".hermes"
SCRIPTS = HERMES / "scripts"
ENVELOPE_DB = HERMES / "state" / "envelope_bus.db"
CONTINUATIONS = HERMES / "state" / "continuations"
HANDOFF_DIRS = [
    HERMES / "state" / "auto_run_handoffs",
    HERMES / "state" / "parallel_handoffs",
]


def run_json(cmd: list[str], timeout: int = 90) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "cmd": cmd, "timeout": timeout}
    if proc.returncode != 0:
        return {
            "status": "ERROR",
            "cmd": cmd,
            "returncode": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-1000:],
            "stdout_tail": (proc.stdout or "")[-1000:],
        }
    out = (proc.stdout or "").strip()
    if not out:
        return {"status": "SILENT_OK", "cmd": cmd}
    try:
        return json.loads(out)
    except Exception:
        return {"status": "RAW", "cmd": cmd, "stdout_tail": out[-2000:]}


def envelope_summary() -> dict[str, Any]:
    if not ENVELOPE_DB.exists():
        return {"exists": False}
    conn = sqlite3.connect(str(ENVELOPE_DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, status, error, created_at, started_at, completed_at, updated_at FROM envelopes"
        ).fetchall()
    finally:
        conn.close()
    by_status = Counter(str(r["status"] or "unknown") for r in rows)
    terminal = [r for r in rows if str(r["status"] or "") in {"FAILED", "BLOCKED"}]
    terminal_errors = Counter(((r["error"] or "unknown").splitlines()[0])[:160] for r in terminal)
    live = [r for r in rows if str(r["status"] or "") in {"PENDING", "RUNNING"}]
    stats = run_json(["python3", str(SCRIPTS / "envelope_bus.py"), "stats"])
    escape = stats.get("escape_info", {}) if isinstance(stats, dict) else {}
    since_ack = escape.get("since_ack", {}) if isinstance(escape, dict) else {}
    return {
        "exists": True,
        "total": len(rows),
        "by_status": dict(by_status),
        "live_count": len(live),
        "terminal_debt_count": len(terminal),
        "top_terminal_errors": terminal_errors.most_common(20),
        "human_escape_triggered": bool(stats.get("human_escape_triggered")) if isinstance(stats, dict) else None,
        "since_ack": since_ack,
        "raw_stats_status": stats.get("status") if isinstance(stats, dict) else None,
    }


def proof_debt_summary() -> dict[str, Any]:
    data = run_json(["python3", str(SCRIPTS / "brain_task_orchestrator.py"), "proof-check", "--json"], timeout=180)
    warnings = data.get("warnings", []) if isinstance(data, dict) else []
    categories: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    for warning in warnings:
        text = str(warning)
        if "terminal mission envelope debt" in text:
            key = "terminal_mission_envelope_debt"
        elif "terminal invalid autorun proof hash debt" in text:
            key = "terminal_invalid_autorun_proof_hash_debt"
        elif "unstructured evidence" in text:
            key = "unstructured_evidence"
        else:
            key = "other"
        categories[key] += 1
        examples.setdefault(key, [])
        if len(examples[key]) < 5:
            examples[key].append(text[:240])
    return {
        "status": data.get("status") if isinstance(data, dict) else None,
        "checked_count": data.get("checked_count") if isinstance(data, dict) else None,
        "failure_count": len(data.get("failures", [])) if isinstance(data, dict) else None,
        "warning_count": len(warnings),
        "categories": dict(categories),
        "examples": examples,
    }


def taskpool_summary() -> dict[str, Any]:
    summary = run_json(["python3", str(SCRIPTS / "brain_task_dispatch_tick.py"), "--summary", "--print-always", "--no-state"], timeout=240)
    evidence = summary.get("evidence_spine", {}).get("summary", {}) if isinstance(summary, dict) else {}
    counts = evidence.get("counts", {}) if isinstance(evidence, dict) else {}
    return {
        "dispatch_summary_status": summary.get("status") if isinstance(summary, dict) else None,
        "dispatchable": summary.get("dispatchable") if isinstance(summary, dict) else None,
        "next_task_id": summary.get("next_task_id") if isinstance(summary, dict) else None,
        "counts": counts,
        "claim_state": summary.get("claim_state", {}) if isinstance(summary, dict) else {},
        "continuation": summary.get("continuation", {}) if isinstance(summary, dict) else {},
        "handoff_backlog": summary.get("handoff_backlog", {}) if isinstance(summary, dict) else {},
    }


def continuation_summary() -> dict[str, Any]:
    active_dir = CONTINUATIONS / "active"
    archived_dir = CONTINUATIONS / "archived"
    active = sorted(active_dir.glob("*.json")) if active_dir.exists() else []
    archived = sorted(archived_dir.glob("*.json")) if archived_dir.exists() else []
    by_scope: Counter[str] = Counter()
    by_task: Counter[str] = Counter()
    unreadable = 0
    for path in active:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            unreadable += 1
            continue
        by_scope[str(payload.get("scope") or "unknown")] += 1
        by_task[str(payload.get("task_id") or payload.get("brain_id") or "unknown")] += 1
    return {
        "active_count": len(active),
        "archived_count": len(archived),
        "unreadable_active": unreadable,
        "by_scope": dict(by_scope),
        "active_duplicate_top": by_task.most_common(20),
    }


def handoff_summary() -> dict[str, Any]:
    dirs = {}
    total = 0
    for directory in HANDOFF_DIRS:
        files = [p for p in directory.glob("*") if p.is_file()] if directory.exists() else []
        total += len(files)
        dirs[str(directory)] = {
            "count": len(files),
            "total_bytes": sum(p.stat().st_size for p in files),
            "oldest": min((p.stat().st_mtime for p in files), default=None),
            "newest": max((p.stat().st_mtime for p in files), default=None),
        }
    return {"total_count": total, "dirs": dirs}


def classify(report: dict[str, Any]) -> dict[str, Any]:
    envelope = report["envelope"]
    proof = report["proof_debt"]
    taskpool = report["taskpool"]
    continuation = report["continuation"]
    actions = []
    if envelope.get("human_escape_triggered"):
        actions.append({"priority": "P0", "class": "runtime_blocker", "action": "triage human_escape before dispatch"})
    since_ack = envelope.get("since_ack") or {}
    if int(since_ack.get("failures") or 0) > 0 or int(since_ack.get("blocks") or 0) > 0:
        actions.append({"priority": "P0", "class": "runtime_debt", "action": "classify post-ack envelope failures; do not ack/delete blindly"})
    counts = taskpool.get("counts") or {}
    if int(counts.get("dispatchable") or 0) == 0:
        actions.append({"priority": "P1", "class": "idle_boundary", "action": "do not tune concurrency; close review/retry/blocked queues first"})
    if proof.get("warning_count", 0) > 0:
        actions.append({"priority": "P2", "class": "historical_proof_debt", "action": "migrate existing proof in small batches; keep warnings visible"})
    if continuation.get("active_count", 0) >= 100:
        actions.append({"priority": "P2", "class": "continuation_backlog", "action": "classify active packets by live/stale/duplicate/human-needed before archive"})
    return {"recommended_actions": actions}


def main() -> None:
    report: dict[str, Any] = {
        "schema": "taskpool_debt_ledger_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety": "read-only; no task, cron, envelope, continuation, memory, skill, or profile mutation",
    }
    report["envelope"] = envelope_summary()
    report["proof_debt"] = proof_debt_summary()
    report["taskpool"] = taskpool_summary()
    report["continuation"] = continuation_summary()
    report["handoff"] = handoff_summary()
    report["classification"] = classify(report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
