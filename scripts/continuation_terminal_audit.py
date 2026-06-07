#!/usr/bin/env python3
"""Second-pass audit for terminal-audit continuation packets.

Consumes a post-compaction manifest and classifies terminal-audit packets with
additional evidence extraction (target_file, task_path, embedded task_id,
manifest_delta/fanout certification hints). It remains read-only and is intended
to find narrowly safe archive candidates after the first disposable pass.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "hermes_continuation_compaction_manifest_v1"
AUDIT_SCHEMA = "hermes_continuation_terminal_audit_v1"
TASK_PATH_RE = re.compile(r"(/(?:Users/charles|var/folders|tmp)/[^\"'\n\\]{1,500}/tasks/([^/\"'\n\\]{1,260}\.md))")
TASK_ID_JSON_RE = re.compile(r'"task_id"\s*:\s*"([^"]{1,260})"')
TARGET_FILE_RE = re.compile(r'"target_file"\s*:\s*"([^"\\]*(?:\\/[^"\\]*)*)"')


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path, limit: int = 80000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def task_status(path: Path) -> str | None:
    text = load_text(path, limit=10000)
    for line in text.splitlines()[:160]:
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip().strip('"\'') or "unknown"
    return None


def resolve_candidate_paths(text: str) -> list[Path]:
    out: list[Path] = []
    for rx in (TARGET_FILE_RE,):
        for m in rx.finditer(text):
            p = Path(m.group(1).replace("\\/", "/"))
            if p.suffix == ".md":
                out.append(p)
    for m in TASK_PATH_RE.finditer(text):
        raw = m.group(1).replace("\\/", "/")
        out.append(Path(raw))
    # Preserve order, de-dupe.
    seen = set()
    deduped = []
    for p in out:
        s = str(p)
        if s not in seen:
            seen.add(s)
            deduped.append(p)
    return deduped[:8]


def classify_packet(pkt: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(pkt.get("path") or ""))
    data = load_json(path) if path.exists() else {}
    text = json.dumps(data, ensure_ascii=False, sort_keys=True) if isinstance(data, dict) else ""
    packet_schema = None
    mode = None
    # message content often contains an escaped JSON comm packet; inspect text regex-first.
    if "multi_model_comm_packet_v1" in text:
        packet_schema = "multi_model_comm_packet_v1"
    if "manifest_delta" in text:
        mode = "manifest_delta"
    task_ids = TASK_ID_JSON_RE.findall(text)
    paths = resolve_candidate_paths(text)
    existing_paths = [p for p in paths if p.exists()]
    statuses = [task_status(p) for p in existing_paths]
    done_count = sum(1 for s in statuses if s in {"done", "archived", "expired"})
    active_count = sum(1 for s in statuses if s in {"pending", "claimed", "running", "retry", "review", "blocked", "proposed"})

    reasons = list(pkt.get("reasons") or [])
    audit_reasons: list[str] = []
    action = "needs-human-review"
    confidence = "low"

    if active_count:
        action = "keep-active-linked"
        confidence = "high"
        audit_reasons.append("linked_task_not_terminal")
    elif existing_paths and done_count == len(existing_paths):
        action = "archive-candidate-terminal-linked"
        confidence = "high"
        audit_reasons.append("all_linked_task_paths_terminal")
    elif packet_schema == "multi_model_comm_packet_v1" and mode == "manifest_delta" and not existing_paths and not task_ids:
        action = "archive-candidate-orphaned-multimodel-delta"
        confidence = "medium"
        audit_reasons.append("orphaned_manifest_delta_no_task_binding")
    elif task_ids and not existing_paths:
        action = "needs-human-review"
        confidence = "medium"
        audit_reasons.append("task_ids_found_but_paths_missing")
    elif not path.exists():
        action = "needs-human-review"
        audit_reasons.append("packet_missing")
    else:
        audit_reasons.append("insufficient_binding_evidence")

    return {
        "path": str(path),
        "packet_exists": path.exists(),
        "created_at": pkt.get("created_at"),
        "age_days": pkt.get("age_days"),
        "original_reasons": reasons,
        "action": action,
        "confidence": confidence,
        "audit_reasons": audit_reasons,
        "packet_schema_hint": packet_schema,
        "mode_hint": mode,
        "task_ids_found": sorted(set(task_ids))[:8],
        "linked_paths": [str(p) for p in paths],
        "existing_linked_paths": [str(p) for p in existing_paths],
        "linked_statuses": statuses,
    }


def build_audit(manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if manifest.get("schema") != EXPECTED_SCHEMA:
        raise ValueError(f"unexpected manifest schema: {manifest.get('schema')!r}")
    packets = manifest.get("packets", {}).get("terminal-audit", [])
    audited = [classify_packet(p) for p in packets if isinstance(p, dict)]
    by_action = Counter(a["action"] for a in audited)
    return {
        "schema": AUDIT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_manifest": str(manifest_path),
        "mode": "read_only_audit",
        "mutation_performed": False,
        "counts_by_action": dict(sorted(by_action.items())),
        "total_terminal_audit": len(audited),
        "archive_candidate_count": sum(1 for a in audited if a["action"].startswith("archive-candidate")),
        "keep_active_linked_count": by_action.get("keep-active-linked", 0),
        "needs_human_review_count": by_action.get("needs-human-review", 0),
        "audited": audited,
        "human_intervention_required": bool(by_action.get("needs-human-review", 0) or by_action.get("keep-active-linked", 0)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    audit = build_audit(Path(args.manifest).expanduser().resolve())
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        audit["report_path"] = str(out)
    if args.summary:
        print(json.dumps({k: audit[k] for k in ["schema", "mode", "mutation_performed", "total_terminal_audit", "counts_by_action", "archive_candidate_count", "keep_active_linked_count", "needs_human_review_count", "human_intervention_required"]} | {"report_path": audit.get("report_path")}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
