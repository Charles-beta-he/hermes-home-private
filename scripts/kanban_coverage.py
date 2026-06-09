#!/usr/bin/env python3
"""Kanban / agent coverage diagnostics for the Hermes local-brain control plane.

Schema v2 keeps the old v1 fields for compatibility, but separates the newer
agent-control-plane concerns:

1. profile coverage: referenced assignees exist on disk,
2. flow coverage: ready work is spawnable, or the backlog is explicitly classified,
3. projection coverage: Kanban projection state is not stale vs the source note,
4. provenance coverage: active brain notes have a Kanban/run reference or an explicit exemption,
5. blockage coverage: blocked Kanban cards carry enough source/workspace data to unblock/audit.

This prevents the false-green case where ready=0 returns 1.0 while all agent
work is actually stranded in blocked/stale projections.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

HOME = Path.home()
SCRIPTS = HOME / ".hermes" / "scripts"
TASKS_DIR = HOME / "Documents" / "brain" / "05-实践与项目" / "tasks"
KANBAN_DB = HOME / ".hermes" / "kanban.db"

ACTIVE_BRAIN_STATUSES = {"pending", "ready", "claimed", "running", "review", "blocked", "retry"}
KANBAN_ID_RE = re.compile(r"\bt_[0-9a-f]{8}\b")
KANBAN_WORKSPACE_RE = re.compile(r"\.hermes/kanban/workspaces/(t_[0-9a-f]{8})")
SOURCE_STATUS_RE = re.compile(r"^Status:\s*([^\n]+)", re.MULTILINE)
EXEMPT_RE = re.compile(r"\b(?:kanban_projection_exempt|agent_coverage_exempt)\b", re.IGNORECASE)


def _ratio(numerator: int, denominator: int, empty_value: float = 1.0) -> float:
    if denominator <= 0:
        return float(empty_value)
    return round(max(0.0, min(1.0, numerator / denominator)), 3)


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_json_cmd(cmd: Sequence[str], timeout: int = 120, default: Any = None) -> Any:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0 or not r.stdout.strip():
            return default
        return json.loads(r.stdout)
    except Exception:
        return default


def _norm_title(title: str) -> str:
    title = str(title or "").strip()
    if title.startswith("Task - "):
        title = title[len("Task - ") :]
    return re.sub(r"\s+", " ", title).lower()


def _source_status(text: str) -> str:
    m = SOURCE_STATUS_RE.search(text or "")
    return m.group(1).strip() if m else ""


def load_brain_rows() -> List[Dict[str, Any]]:
    payload = _safe_json_cmd(
        [sys.executable, str(SCRIPTS / "brain_task_orchestrator.py"), "list", "--json"],
        default={},
    )
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping):
        rows = payload.get("rows") or payload.get("tasks") or []
        return rows if isinstance(rows, list) else []
    return []


def load_kanban_stats() -> Dict[str, Any]:
    payload = _safe_json_cmd(["hermes", "kanban", "stats", "--json"], default={})
    return payload if isinstance(payload, dict) else {}


def load_kanban_assignees() -> List[Dict[str, Any]]:
    payload = _safe_json_cmd(["hermes", "kanban", "assignees", "--json"], default=[])
    return payload if isinstance(payload, list) else []


def load_dispatch_dry_run() -> Dict[str, Any]:
    payload = _safe_json_cmd(["hermes", "kanban", "dispatch", "--dry-run", "--json"], default={})
    return payload if isinstance(payload, dict) else {}


def load_kanban_tasks(db_path: Path = KANBAN_DB) -> List[Dict[str, Any]]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(
            "SELECT id,title,body,assignee,status,workspace_path,result,session_id FROM tasks "
            "WHERE status != 'archived'"
        )]
    except Exception:
        return []


def _frontmatter_status(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if line.startswith("status:"):
                    return line.split(":", 1)[1].strip().strip('"')
    return ""


def _markdown_title(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text or "", re.MULTILINE)
    return m.group(1).strip() if m else ""


def load_brain_notes(tasks_dir: Path = TASKS_DIR) -> List[Dict[str, str]]:
    notes: List[Dict[str, str]] = []
    if not tasks_dir.exists():
        return notes
    for path in tasks_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        notes.append({
            "path": str(path),
            "status": _frontmatter_status(text),
            "title": _markdown_title(text),
            "text": text,
        })
    return notes


def _spawned_count(dispatch_dry_run: Mapping[str, Any]) -> int:
    spawned = dispatch_dry_run.get("spawned") or []
    return len(spawned) if isinstance(spawned, list) else 0


def _skipped_nonspawnable_ids(dispatch_dry_run: Mapping[str, Any]) -> List[str]:
    skipped = dispatch_dry_run.get("skipped_nonspawnable") or []
    if not isinstance(skipped, list):
        return []
    return [str(x) for x in skipped]


def _brain_mirror_active_count(kanban_stats: Mapping[str, Any]) -> int:
    by_assignee = kanban_stats.get("by_assignee") or {}
    if not isinstance(by_assignee, Mapping):
        return 0
    mirror_data = by_assignee.get("brain-mirror") or {}
    if isinstance(mirror_data, Mapping):
        return sum(_as_int(mirror_data.get(status)) for status in ("ready", "running", "in_progress", "blocked"))
    return _as_int(mirror_data)


def _note_has_kanban_ref(note: Mapping[str, str]) -> bool:
    text = note.get("text", "") or ""
    return bool(KANBAN_ID_RE.search(text) or KANBAN_WORKSPACE_RE.search(text))


def _note_has_projection_coverage(note: Mapping[str, str]) -> bool:
    text = note.get("text", "") or ""
    return _note_has_kanban_ref(note) or bool(EXEMPT_RE.search(text))


def _note_index(notes: Sequence[Mapping[str, str]]) -> Dict[str, Mapping[str, str]]:
    index: Dict[str, Mapping[str, str]] = {}
    for note in notes:
        title = _norm_title(note.get("title", ""))
        if title:
            index.setdefault(title, note)
    return index


def _best_note_for_task(task: Mapping[str, Any], notes: Sequence[Mapping[str, str]]) -> Optional[Mapping[str, str]]:
    task_title = _norm_title(str(task.get("title") or ""))
    if not task_title:
        return None
    best: Mapping[str, str] | None = None
    best_score = 0
    for note in notes:
        note_title = _norm_title(note.get("title", ""))
        if not note_title:
            continue
        score = 0
        if task_title == note_title:
            score = 100
        elif task_title[:42] and task_title[:42] in note_title:
            score = 80
        elif note_title[:42] and note_title[:42] in task_title:
            score = 75
        elif task_title[:28] and task_title[:28] in note_title:
            score = 50
        if score > best_score:
            best = note
            best_score = score
    return best if best_score >= 50 else None


def _classify_projection(task: Mapping[str, Any], note: Optional[Mapping[str, str]]) -> Dict[str, Any]:
    task_status = str(task.get("status") or "")
    source_status = _source_status(str(task.get("body") or ""))
    note_status = str(note.get("status") or "") if note else ""
    workspace_path = str(task.get("workspace_path") or "")
    workspace_exists = bool(workspace_path and Path(workspace_path).exists())
    stale = False
    reason = "ok"

    source_current = note_status or source_status
    if task_status == "blocked" and source_current == "done":
        stale = True
        reason = "blocked_projection_for_done_source"
    elif task_status == "done" and source_current in {"pending", "ready", "running", "review", "blocked", "retry"}:
        # Done kanban can be a historical attempt. Keep as warning-level, not hard stale,
        # because old task mirrors may have been intentionally closed with proof.
        reason = "done_projection_for_active_source"
    elif task_status == "blocked" and source_current in {"pending", "ready", "running", "review", "retry"}:
        reason = "blocked_projection_for_non_done_source"
    elif task_status == "blocked" and source_current == "blocked":
        reason = "blocked_source_aligned"

    structured = bool(source_status and workspace_path)
    return {
        "task_id": task.get("id"),
        "kanban_status": task_status,
        "source_status": source_status,
        "note_status": note_status,
        "source_current_status": source_current,
        "workspace_path": workspace_path,
        "workspace_exists": workspace_exists,
        "structured": structured,
        "stale": stale,
        "reason": reason,
    }


def _coverage_v2(
    brain_rows: Sequence[Mapping[str, Any]],
    kanban_stats: Mapping[str, Any],
    assignees: Sequence[Mapping[str, Any]],
    dispatch_dry_run: Mapping[str, Any],
    brain_notes: Sequence[Mapping[str, str]],
    kanban_tasks: Sequence[Mapping[str, Any]],
    v1_coverage: Mapping[str, float],
    counts: Mapping[str, int],
) -> Dict[str, Any]:
    assignee_names = {str(a.get("name")) for a in assignees if a.get("name")}
    referenced_assignees = {str(t.get("assignee")) for t in kanban_tasks if t.get("assignee")}
    missing_assignees = sorted(a for a in referenced_assignees if a not in assignee_names)
    profile_score = _ratio(len(referenced_assignees) - len(missing_assignees), len(referenced_assignees), 1.0)

    blocked_tasks = [t for t in kanban_tasks if str(t.get("status") or "") == "blocked"]
    projection_rows = [_classify_projection(t, _best_note_for_task(t, brain_notes)) for t in kanban_tasks]
    stale_rows = [r for r in projection_rows if r["stale"]]
    drift_rows = [
        r for r in projection_rows
        if r["reason"] not in {"ok", "blocked_source_aligned"}
        and r["kanban_status"] in {"ready", "running", "blocked"}
    ]
    active_projection_rows = [r for r in projection_rows if r["kanban_status"] in {"ready", "running", "blocked"}]
    structured_blocked = [r for r in projection_rows if r["kanban_status"] == "blocked" and r["structured"] and r["workspace_exists"]]

    active_notes = [n for n in brain_notes if n.get("status") in ACTIVE_BRAIN_STATUSES]
    active_notes_with_ref_or_exempt = sum(1 for n in active_notes if _note_has_projection_coverage(n))

    profile_coverage = profile_score
    if counts["kanban_ready"] > 0:
        flow_state = "flow_active" if counts["kanban_ready_spawnable"] > 0 else "flow_profile_blocked"
        flow_coverage = v1_coverage["kanban_ready_spawnability"]
    elif counts["kanban_blocked"] > 0:
        flow_state = "flow_blocked_backlog"
        # A blocked backlog can be healthy only when every blocked item is explicitly classified.
        flow_coverage = _ratio(len(structured_blocked), len(blocked_tasks), empty_value=1.0)
    else:
        flow_state = "flow_idle_clean"
        flow_coverage = 1.0

    projection_coverage = _ratio(len(active_projection_rows) - len(drift_rows), len(active_projection_rows), empty_value=1.0)
    provenance_coverage = _ratio(active_notes_with_ref_or_exempt, len(active_notes), empty_value=1.0)
    blockage_coverage = _ratio(len(structured_blocked), len(blocked_tasks), empty_value=1.0)

    metrics = {
        "profile_coverage": profile_coverage,
        "flow_coverage": flow_coverage,
        "projection_coverage": projection_coverage,
        "provenance_coverage": provenance_coverage,
        "blockage_coverage": blockage_coverage,
    }
    score = round(
        0.20 * profile_coverage
        + 0.25 * flow_coverage
        + 0.25 * projection_coverage
        + 0.20 * provenance_coverage
        + 0.10 * blockage_coverage,
        3,
    )

    caps: List[str] = []
    if stale_rows:
        score = min(score, 0.75)
        caps.append("stale_projection_caps_score_at_0.75")
    if provenance_coverage < 0.5:
        score = min(score, 0.75)
        caps.append("active_provenance_below_0.5_caps_score_at_0.75")
    if counts["kanban_ready"] == 0 and counts["kanban_blocked"] > 0 and blockage_coverage < 0.9:
        score = min(score, 0.75)
        caps.append("unclassified_blocked_backlog_caps_score_at_0.75")

    return {
        "schema_version": "agent_coverage_v2",
        "state": flow_state,
        "score": round(score, 3),
        "metrics": metrics,
        "caps": caps,
        "counts": {
            "referenced_assignees": len(referenced_assignees),
            "missing_assignees": len(missing_assignees),
            "active_projection_tasks": len(active_projection_rows),
            "stale_projection_tasks": len(stale_rows),
            "projection_drift_tasks": len(drift_rows),
            "blocked_tasks_structured": len(structured_blocked),
            "active_notes_with_ref_or_exempt": active_notes_with_ref_or_exempt,
        },
        "missing_assignees": missing_assignees,
        "stale_projection_ids": [str(r["task_id"]) for r in stale_rows],
        "projection_drift": drift_rows,
    }


def compute_coverage(
    brain_rows: Sequence[Mapping[str, Any]],
    kanban_stats: Mapping[str, Any],
    assignees: Sequence[Mapping[str, Any]],
    dispatch_dry_run: Mapping[str, Any],
    brain_notes: Sequence[Mapping[str, str]],
    kanban_tasks: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    by_status = kanban_stats.get("by_status") or {}
    if not isinstance(by_status, Mapping):
        by_status = {}

    dispatchable = sum(1 for row in brain_rows if bool(row.get("dispatchable")))
    mirrored_active = _brain_mirror_active_count(kanban_stats)
    kanban_ready = _as_int(by_status.get("ready"))
    skipped_ids = _skipped_nonspawnable_ids(dispatch_dry_run)
    ready_nonspawnable = len(skipped_ids)
    spawned = _spawned_count(dispatch_dry_run)
    ready_spawnable = max(0, kanban_ready - ready_nonspawnable)

    total_notes = len(brain_notes)
    notes_with_ref = sum(1 for note in brain_notes if _note_has_kanban_ref(note))
    active_notes = [note for note in brain_notes if note.get("status") in ACTIVE_BRAIN_STATUSES]
    active_notes_with_ref = sum(1 for note in active_notes if _note_has_kanban_ref(note))

    missing_ready_assignees = sorted(
        str(a.get("name"))
        for a in assignees
        if not a.get("on_disk") and _as_int((a.get("counts") or {}).get("ready")) > 0
    )

    coverage = {
        "dispatchable_mirror": _ratio(min(mirrored_active, dispatchable), dispatchable, empty_value=1.0),
        "kanban_ready_spawnability": _ratio(ready_spawnable, kanban_ready, empty_value=1.0),
        "brain_note_provenance": _ratio(notes_with_ref, total_notes, empty_value=1.0),
        "active_brain_note_provenance": _ratio(active_notes_with_ref, len(active_notes), empty_value=1.0),
    }

    counts = {
        "local_brain_rows": len(brain_rows),
        "local_brain_dispatchable": dispatchable,
        "brain_mirror_active": mirrored_active,
        "kanban_ready": kanban_ready,
        "kanban_ready_spawnable": ready_spawnable,
        "ready_nonspawnable": ready_nonspawnable,
        "dispatch_dry_run_spawned": spawned,
        "kanban_blocked": _as_int(by_status.get("blocked")),
        "kanban_done": _as_int(by_status.get("done")),
        "kanban_archived": _as_int(by_status.get("archived")),
        "brain_notes_total": total_notes,
        "brain_notes_with_kanban_ref": notes_with_ref,
        "active_brain_notes_total": len(active_notes),
        "active_brain_notes_with_kanban_ref": active_notes_with_ref,
    }

    # Legacy score kept for dashboards that still expect the old field shape.
    legacy_score = round(
        0.45 * coverage["dispatchable_mirror"]
        + 0.45 * coverage["kanban_ready_spawnability"]
        + 0.10 * coverage["active_brain_note_provenance"],
        3,
    )
    v2 = _coverage_v2(
        brain_rows=brain_rows,
        kanban_stats=kanban_stats,
        assignees=assignees,
        dispatch_dry_run=dispatch_dry_run,
        brain_notes=brain_notes,
        kanban_tasks=kanban_tasks or [],
        v1_coverage=coverage,
        counts=counts,
    )
    bottleneck = min(v2["metrics"], key=v2["metrics"].get)

    return {
        "schema_version": "kanban_coverage_v2",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "score": v2["score"],
        "legacy_score_v1": legacy_score,
        "bottleneck": bottleneck,
        "coverage": coverage,
        "agent_coverage_v2": v2,
        "counts": counts,
        "ids": {"skipped_nonspawnable": skipped_ids},
        "missing_ready_assignees": missing_ready_assignees,
        "principles": {
            "toyota_lean_flow": "Expose stopped flow/andon: ready work that cannot be pulled is unhealthy even when another queue is empty.",
            "goldratt_toc": "Surface the current constraint: missing spawnable assignee profiles or unclassified blocked backlog.",
            "anderson_kanban": "Visualize work and flow with ready, blocked, WIP/spawnable, and explicit policies rather than a single green score.",
            "kleppmann_ddia_event_sourcing": "Treat local-brain task notes as the source-of-truth and Kanban as a projection; measure projection consistency separately.",
            "twelve_factor_agents": "Persist run/task provenance so agent executions can be replayed, audited, and tied back to canonical tasks.",
        },
    }


def live_report() -> Dict[str, Any]:
    return compute_coverage(
        brain_rows=load_brain_rows(),
        kanban_stats=load_kanban_stats(),
        assignees=load_kanban_assignees(),
        dispatch_dry_run=load_dispatch_dry_run(),
        brain_notes=load_brain_notes(),
        kanban_tasks=load_kanban_tasks(),
    )


def _print_text(report: Mapping[str, Any]) -> None:
    v2 = report["agent_coverage_v2"]
    print(f"Agent coverage score = {report['score']:.3f} ({v2['state']})")
    print(f"Bottleneck: {report['bottleneck']}")
    for name, value in v2["metrics"].items():
        print(f"  {name:30} {value:.3f}")
    counts = report["counts"]
    print(
        "  ready_nonspawnable="
        f"{counts['ready_nonspawnable']} / kanban_ready={counts['kanban_ready']} "
        f"blocked={counts['kanban_blocked']} stale_projection={v2['counts']['stale_projection_tasks']}"
    )
    if v2.get("caps"):
        print("  caps=" + ",".join(v2["caps"]))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute Hermes Kanban/agent coverage metrics.")
    parser.add_argument("--json", action="store_true", help="Emit stable JSON report")
    args = parser.parse_args(argv)
    report = live_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
