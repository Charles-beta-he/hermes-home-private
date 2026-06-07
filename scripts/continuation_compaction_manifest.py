#!/usr/bin/env python3
"""Read-only continuation compaction manifest for Hermes long-running work.

Classifies continuation packets before any archive/delete mutation. This is the
required dry-run gate for memory-cache / recurrent-task-state work: reduce prompt
and state debt only after proving which packets are live, recoverable, terminal
for audit, or disposable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path.home() / ".hermes" / "state" / "continuations"
TASKS_DIR = Path.home() / "Documents" / "brain" / "05-实践与项目" / "tasks"
TASK_ID_RE = re.compile(r"20\d{2}-\d{2}-\d{2}-[^\s\\\"'，。:：]+")
LIVE_STATUSES = {"claimed", "running"}
RECOVERABLE_STATUSES = {"pending", "retry", "review", "blocked", "proposed"}
TERMINAL_STATUSES = {"done", "archived", "expired"}


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def safe_load(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"json_load_error:{type(exc).__name__}"
    if not isinstance(data, dict):
        return None, "json_not_object"
    return data, None


def compact_text(data: Any, limit: int = 16000) -> str:
    try:
        text = json.dumps(data, ensure_ascii=False, sort_keys=True)
    except Exception:
        text = str(data)
    return text[:limit]


def extract_task_id(data: dict[str, Any]) -> str | None:
    # Prefer explicit nested context if present.
    candidates: list[Any] = []
    for key in ("task_id", "id"):
        if data.get(key):
            candidates.append(data.get(key))
    meta_obj = data.get("metadata")
    meta: dict[str, Any] = meta_obj if isinstance(meta_obj, dict) else {}
    for key in ("task_id", "id"):
        if meta.get(key):
            candidates.append(meta.get(key))
    snapshots = meta.get("messages_snapshot", [])
    for msg in snapshots if isinstance(snapshots, list) else []:
        if isinstance(msg, dict):
            candidates.append(msg.get("content"))

    # Inspect JSON-ish body for context.task_id and fallback regex.
    for item in candidates:
        text = str(item or "")
        if not text:
            continue
        direct = re.search(r'"task_id"\s*:\s*"([^"]+)"', text)
        if direct:
            return direct.group(1)
        m = TASK_ID_RE.search(text)
        if m:
            return m.group(0).rstrip(".,;)")
    m = TASK_ID_RE.search(compact_text(data))
    return m.group(0).rstrip(".,;)") if m else None


def task_index(tasks_dir: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not tasks_dir.exists():
        return out
    for path in tasks_dir.glob("*.md"):
        tid = path.stem
        status = ""
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:120]:
                if line.startswith("status:"):
                    status = line.split(":", 1)[1].strip().strip('"\'')
                    break
        except OSError:
            continue
        out[tid] = {"path": str(path), "status": status or "unknown"}
    return out


def classify_packet(path: Path, data: dict[str, Any] | None, error: str | None, *, now: datetime, tasks: dict[str, dict[str, str]], source_dir: str) -> dict[str, Any]:
    stat = path.stat()
    created = parse_dt(data.get("created_at") if data else None) if data else None
    age_days = round((now - created).total_seconds() / 86400, 3) if created else None
    task_id = extract_task_id(data) if data else None
    task = tasks.get(task_id or "") if task_id else None
    task_status = task.get("status") if task else None
    reasons: list[str] = []

    if error:
        bucket = "terminal-audit"
        reasons.append(error)
    elif task_status in LIVE_STATUSES:
        bucket = "live"
        reasons.append(f"task_status:{task_status}")
    elif source_dir == "active" and age_days is not None and age_days < 1:
        bucket = "live"
        reasons.append("active_recent_under_1d")
        if task_status:
            reasons.append(f"task_status:{task_status}")
    elif task_status in RECOVERABLE_STATUSES:
        bucket = "stale-recoverable"
        reasons.append(f"task_status:{task_status}")
    elif task_status in TERMINAL_STATUSES:
        bucket = "disposable"
        reasons.append(f"task_status:{task_status}")
    elif not task_id:
        bucket = "terminal-audit"
        reasons.append("missing_task_id")
    elif not task:
        bucket = "terminal-audit"
        reasons.append("task_note_not_found")
    else:
        bucket = "terminal-audit"
        reasons.append(f"unclassified_task_status:{task_status or 'unknown'}")

    # Archived packets are never live; if they still point to active work, require audit.
    if source_dir == "archived" and bucket == "live":
        bucket = "terminal-audit"
        reasons.append("archived_points_to_live_task")

    return {
        "path": str(path),
        "source_dir": source_dir,
        "bucket": bucket,
        "reasons": reasons,
        "created_at": created.isoformat().replace("+00:00", "Z") if created else None,
        "age_days": age_days,
        "size_bytes": stat.st_size,
        "task_id": task_id,
        "task_status": task_status,
        "task_path": task.get("path") if task else None,
        "sha_hint": path.stem,
    }


def build_manifest(root: Path, tasks_dir: Path, *, include_archived_sample: int, now: datetime) -> dict[str, Any]:
    tasks = task_index(tasks_dir)
    packets: list[dict[str, Any]] = []
    for source_dir in ("active", "archived"):
        files = sorted((root / source_dir).glob("*.json")) if (root / source_dir).exists() else []
        if source_dir == "archived" and include_archived_sample >= 0:
            files = files[:include_archived_sample]
        for path in files:
            data, error = safe_load(path)
            packets.append(classify_packet(path, data, error, now=now, tasks=tasks, source_dir=source_dir))

    buckets = {"live": [], "stale-recoverable": [], "terminal-audit": [], "disposable": []}
    for pkt in packets:
        buckets[pkt["bucket"]].append(pkt)
    counts = {k: len(v) for k, v in buckets.items()}
    total_active = len(list((root / "active").glob("*.json"))) if (root / "active").exists() else 0
    total_archived = len(list((root / "archived").glob("*.json"))) if (root / "archived").exists() else 0
    return {
        "schema": "hermes_continuation_compaction_manifest_v1",
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "root": str(root),
        "tasks_dir": str(tasks_dir),
        "mode": "dry_run_read_only",
        "mutation_performed": False,
        "policy": {
            "live": "do not mutate; active/recent or task currently claimed/running",
            "stale-recoverable": "candidate for recurrent_task_state compaction or targeted resume review",
            "terminal-audit": "requires human/reviewer audit before any archive/delete",
            "disposable": "candidate only after reference-safety review; no automatic deletion in this script",
        },
        "source_totals": {"active_total": total_active, "archived_total": total_archived, "archived_sample_scanned": include_archived_sample},
        "counts": counts,
        "packets": buckets,
        "human_intervention_required": bool(buckets["terminal-audit"]),
        "next_safe_step": "Review terminal-audit and stale-recoverable buckets; only then run a separate explicit mutation tool if approved.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.environ.get("HERMES_CONTINUATION_DIR", str(DEFAULT_ROOT)))
    parser.add_argument("--tasks-dir", default=str(TASKS_DIR))
    parser.add_argument("--include-archived-sample", type=int, default=0, help="scan first N archived packets; 0 means none, -1 scans all")
    parser.add_argument("--out", default=None)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    manifest = build_manifest(Path(args.root).expanduser(), Path(args.tasks_dir).expanduser(), include_archived_sample=args.include_archived_sample, now=datetime.now(timezone.utc))
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest["report_path"] = str(out)
    if args.summary:
        print(json.dumps({
            "schema": manifest["schema"],
            "mode": manifest["mode"],
            "mutation_performed": manifest["mutation_performed"],
            "source_totals": manifest["source_totals"],
            "counts": manifest["counts"],
            "human_intervention_required": manifest["human_intervention_required"],
            "report_path": manifest.get("report_path"),
        }, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
