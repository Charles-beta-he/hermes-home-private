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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def active_task_rows() -> list[dict[str, Any]]:
    data = run_json(["python3", str(SCRIPTS / "brain_task_orchestrator.py"), "list", "--json"], timeout=180)
    if not isinstance(data, dict):
        return []
    rows = data.get("rows") or data.get("tasks") or []
    return [r for r in rows if isinstance(r, dict)]


def multimodel_jobs_summary() -> dict[str, Any]:
    data = run_json(["python3", str(SCRIPTS / "brain_task_orchestrator.py"), "multimodel-intervention-jobs", "--json"], timeout=180)
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    alive = [j for j in jobs if isinstance(j, dict) and j.get("alive")]
    return {
        "status": data.get("status") if isinstance(data, dict) else None,
        "job_count": data.get("job_count") if isinstance(data, dict) else None,
        "alive_count": data.get("alive_count", len(alive)) if isinstance(data, dict) else len(alive),
        "alive_tasks": sorted({str(j.get("task_id") or "") for j in alive if j.get("task_id")}),
    }


def infer_completion_profile(task: dict[str, Any]) -> str:
    explicit = str(task.get("completion_profile") or task.get("completion_boundary") or "").strip()
    if explicit in {"static_intake", "design_only", "implementation_cli", "implementation_api", "implementation_browser", "implementation_desktop", "deployment"}:
        return explicit
    haystack = "\n".join(str(task.get(k) or "") for k in (
        "title", "objective", "mission_objective", "workflow_contract", "required_artifacts",
        "acceptance_evidence", "evidence_bundle", "target_surface", "integration_level",
    )).lower()
    if any(token in haystack for token in ("desktop", "tui", "voice", "mic", "hud", "语音", "麦克风")):
        return "implementation_desktop"
    if any(token in haystack for token in ("browser", "dom", "playwright", "网页", "页面", "前端", "ui")):
        return "implementation_browser"
    if any(token in haystack for token in ("api", "backend", "curl", "接口", "后端", "readback")):
        return "implementation_api"
    if any(token in haystack for token in ("deploy", "railway", "production", "live readback")):
        return "deployment"
    if any(token in haystack for token in ("repo", "intake", "evaluate", "watch", "gap map", "source inspection", "静态", "评估", "吸收")):
        return "static_intake"
    return "design_only" if task.get("lane") == "evolution" else "implementation_cli"


def evidence_gate_risks(task: dict[str, Any]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    joined = "\n".join(str(x) for x in (task.get("evidence_refs") or []))
    joined += "\n" + str(task.get("body") or "")
    lower = joined.lower()
    diagnostic_phrases = (
        "requires_test-build-browser-curl-commit-verification",
        "multimodel_advisory_or_failed_not_completion",
        "advisory_or_failed_not_completion",
        "not_completion",
        "taskpool-review-gap",
    )
    impl_tokens = ("test", "build", "browser", "curl", "commit", "pytest", "vitest")
    if any(p in lower for p in diagnostic_phrases) and any(t in lower for t in impl_tokens):
        risks.append({
            "kind": "token_based_evidence_false_positive_risk",
            "severity": "high",
            "reason": "diagnostic/negative text contains implementation-proof tokens",
        })
    if str(task.get("multimodel_last_gate_status") or "") == "PASS_ADVISORY_ONLY":
        risks.append({
            "kind": "advisory_only_not_completion",
            "severity": "high",
            "reason": "PASS_ADVISORY_ONLY must not satisfy implementation closeout",
        })
    return risks


def flow_health_summary() -> dict[str, Any]:
    rows = active_task_rows()
    status_counts = Counter(str(r.get("status") or "unknown") for r in rows)
    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_id.setdefault(str(row.get("id") or row.get("task_id") or ""), []).append(row)
    duplicate_projection = []
    for task_id, variants in by_id.items():
        if not task_id or len(variants) <= 1:
            continue
        statuses = sorted({str(v.get("status") or "") for v in variants})
        claimed_by = sorted({str(v.get("claimed_by") or "") for v in variants if v.get("claimed_by")})
        if len(statuses) > 1 or len(variants) > 1:
            duplicate_projection.append({
                "task_id": task_id,
                "row_count": len(variants),
                "statuses": statuses,
                "claimed_by": claimed_by,
                "severity": "high" if len(statuses) > 1 else "medium",
            })
    review_gaps = run_json(["python3", str(SCRIPTS / "brain_task_orchestrator.py"), "review-gap-scan", "--json"], timeout=180)
    gaps = review_gaps.get("gaps", []) if isinstance(review_gaps, dict) else []
    retry_circuit_breakers = []
    completion_profiles = []
    evidence_risks = []
    for row in rows:
        task_id = str(row.get("id") or row.get("task_id") or "")
        status = str(row.get("status") or "")
        retry_count = _as_int(row.get("retry_count"))
        profile = infer_completion_profile(row)
        completion_profiles.append({
            "task_id": task_id,
            "status": status,
            "priority": row.get("priority"),
            "inferred_profile": profile,
            "explicit_profile": row.get("completion_profile") or row.get("completion_boundary") or "",
            "requires_multimodel": _as_bool(row.get("requires_multimodel")),
            "multimodel_gate": row.get("multimodel_last_gate_status") or "",
        })
        if status in {"retry", "running", "pending"} and retry_count >= 3:
            retry_circuit_breakers.append({
                "task_id": task_id,
                "status": status,
                "retry_count": retry_count,
                "severity": "high",
                "recommendation": "stop blind redispatch; classify root cause and create repair/human-required packet",
            })
        for risk in evidence_gate_risks(row):
            risk["task_id"] = task_id
            evidence_risks.append(risk)
    return {
        "schema": "taskpool_flow_health_v1",
        "active_count": len(rows),
        "status_counts": dict(status_counts),
        "dispatchable_count": sum(1 for r in rows if _as_bool(r.get("dispatchable"))),
        "duplicate_projection_count": len(duplicate_projection),
        "duplicate_projection": duplicate_projection,
        "review_gap_count": review_gaps.get("gap_count") if isinstance(review_gaps, dict) else None,
        "review_gaps": [
            {
                "task_id": g.get("task_id"),
                "gap_types": g.get("gap_types"),
                "failures": g.get("failures"),
                "repairable": g.get("repairable"),
            }
            for g in gaps
        ],
        "retry_circuit_breaker_count": len(retry_circuit_breakers),
        "retry_circuit_breakers": retry_circuit_breakers,
        "completion_profiles": completion_profiles,
        "evidence_gate_risk_count": len(evidence_risks),
        "evidence_gate_risks": evidence_risks,
        "multimodel_jobs": multimodel_jobs_summary(),
    }


def classify(report: dict[str, Any]) -> dict[str, Any]:
    envelope = report["envelope"]
    proof = report["proof_debt"]
    taskpool = report["taskpool"]
    continuation = report["continuation"]
    flow = report.get("flow_health", {})
    actions = []
    if envelope.get("human_escape_triggered"):
        actions.append({"priority": "P0", "class": "runtime_blocker", "action": "triage human_escape before dispatch"})
    since_ack = envelope.get("since_ack") or {}
    if int(since_ack.get("failures") or 0) > 0 or int(since_ack.get("blocks") or 0) > 0:
        actions.append({"priority": "P0", "class": "runtime_debt", "action": "classify post-ack envelope failures; do not ack/delete blindly"})
    counts = taskpool.get("counts") or {}
    if int(counts.get("dispatchable") or 0) == 0:
        actions.append({"priority": "P1", "class": "idle_boundary", "action": "do not tune concurrency; close review/retry/blocked queues first"})
    if int(flow.get("duplicate_projection_count") or 0) > 0:
        actions.append({"priority": "P1", "class": "projection_drift", "action": "reconcile duplicate task projections before lifecycle mutation"})
    if int(flow.get("review_gap_count") or 0) > 0:
        actions.append({"priority": "P1", "class": "review_closeout_gap", "action": "create deterministic evidence repair packet; do not close from model agreement alone"})
    if int(flow.get("retry_circuit_breaker_count") or 0) > 0:
        actions.append({"priority": "P1", "class": "retry_circuit_breaker", "action": "stop blind redispatch for retry_count>=3; classify root cause first"})
    if int(flow.get("evidence_gate_risk_count") or 0) > 0:
        actions.append({"priority": "P1", "class": "evidence_gate_type_risk", "action": "treat advisory/diagnostic text as non-completion evidence until typed bundle exists"})
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
    report["flow_health"] = flow_health_summary()
    report["continuation"] = continuation_summary()
    report["handoff"] = handoff_summary()
    report["classification"] = classify(report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
