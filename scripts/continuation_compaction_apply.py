#!/usr/bin/env python3
"""Apply approved continuation compaction actions from a manifest.

This is deliberately separate from continuation_compaction_manifest.py. It only
consumes a previously generated dry-run manifest and performs explicitly allowed
low-risk mutations. By default the only supported mutation is archiving active
packets that the manifest classified as disposable.

Red lines:
- never mutate live packets
- never mutate stale-recoverable packets
- never delete packets
- never rescan and invent a new decision set; consume the manifest/audit supplied by
  the reviewer/operator
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "hermes_continuation_compaction_manifest_v1"
AUDIT_SCHEMA = "hermes_continuation_terminal_audit_v1"
APPLY_SCHEMA = "hermes_continuation_compaction_apply_report_v1"


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest is not a JSON object")
    if data.get("schema") != EXPECTED_SCHEMA:
        raise ValueError(f"unexpected manifest schema: {data.get('schema')!r}")
    if data.get("mutation_performed") is not False:
        raise ValueError("manifest must be a dry-run/no-mutation manifest")
    return data


def active_disposable_packets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    packets = manifest.get("packets", {}).get("disposable", [])
    if not isinstance(packets, list):
        return []
    return [p for p in packets if isinstance(p, dict) and p.get("source_dir") == "active" and p.get("bucket") == "disposable"]


def safe_archive_destination(src: Path, root: Path) -> Path:
    archive_dir = root / "archived"
    dest = archive_dir / src.name
    if not dest.exists():
        return dest
    stem = src.stem
    suffix = src.suffix
    for i in range(1, 1000):
        candidate = archive_dir / f"{stem}.compacted-{i}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not find non-conflicting archive path for {src}")


def apply_archive_disposable(manifest: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    root = Path(str(manifest.get("root") or "")).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"manifest root not found: {root}")
    archived: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for pkt in active_disposable_packets(manifest):
        src = Path(str(pkt.get("path") or "")).expanduser()
        raw_reasons = pkt.get("reasons")
        reasons: list[Any] = raw_reasons if isinstance(raw_reasons, list) else []
        if not src.exists():
            skipped.append({"path": str(src), "reason": "source_missing"})
            continue
        if src.parent.name != "active":
            skipped.append({"path": str(src), "reason": "not_in_active_dir"})
            continue
        if "task_status:done" not in reasons:
            skipped.append({"path": str(src), "reason": "not_done_disposable"})
            continue
        dest = safe_archive_destination(src, root)
        record = {
            "source": str(src),
            "destination": str(dest),
            "task_id": pkt.get("task_id"),
            "task_status": pkt.get("task_status"),
            "reasons": reasons,
        }
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
        archived.append(record)
    return {
        "schema": APPLY_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "dry_run" if dry_run else "apply_archive_disposable_only",
        "manifest_path": str(Path(str(manifest.get("report_path") or "")).expanduser()) if manifest.get("report_path") else None,
        "manifest_generated_at": manifest.get("generated_at"),
        "root": str(root),
        "mutation_performed": not dry_run,
        "allowed_bucket": "disposable",
        "allowed_source_dir": "active",
        "archived_count": len(archived),
        "skipped_count": len(skipped),
        "archived": archived,
        "skipped": skipped,
        "blocked_buckets_not_mutated": {
            "live": len(manifest.get("packets", {}).get("live", [])),
            "stale_recoverable": len(manifest.get("packets", {}).get("stale-recoverable", [])),
            "terminal_audit": len(manifest.get("packets", {}).get("terminal-audit", [])),
        },
        "delete_performed": False,
    }


def load_audit(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("audit is not a JSON object")
    if data.get("schema") != AUDIT_SCHEMA:
        raise ValueError(f"unexpected audit schema: {data.get('schema')!r}")
    if data.get("mutation_performed") is not False:
        raise ValueError("audit must be read-only/no-mutation")
    return data


def apply_archive_audit_candidates(audit: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    archived: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    blocked = {"keep_active_linked": 0, "needs_human_review": 0, "other_not_mutated": 0}
    for item in audit.get("audited", []):
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or "")
        if action == "keep-active-linked":
            blocked["keep_active_linked"] += 1
            continue
        if action == "needs-human-review":
            blocked["needs_human_review"] += 1
            continue
        if not action.startswith("archive-candidate"):
            blocked["other_not_mutated"] += 1
            continue
        src = Path(str(item.get("path") or "")).expanduser()
        if not src.exists():
            skipped.append({"path": str(src), "reason": "source_missing", "action": action})
            continue
        if src.parent.name != "active":
            skipped.append({"path": str(src), "reason": "not_in_active_dir", "action": action})
            continue
        root = src.parent.parent
        dest = safe_archive_destination(src, root)
        record = {
            "source": str(src),
            "destination": str(dest),
            "action": action,
            "confidence": item.get("confidence"),
            "audit_reasons": item.get("audit_reasons"),
            "linked_statuses": item.get("linked_statuses"),
        }
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
        archived.append(record)
    return {
        "schema": APPLY_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "dry_run_terminal_audit" if dry_run else "apply_archive_terminal_audit_candidates_only",
        "audit_path": audit.get("report_path"),
        "audit_generated_at": audit.get("generated_at"),
        "mutation_performed": not dry_run,
        "allowed_actions": ["archive-candidate-terminal-linked", "archive-candidate-orphaned-multimodel-delta"],
        "archived_count": len(archived),
        "skipped_count": len(skipped),
        "archived": archived,
        "skipped": skipped,
        "blocked_buckets_not_mutated": blocked,
        "delete_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", help="path to dry-run manifest JSON")
    parser.add_argument("--audit", help="path to terminal-audit JSON")
    parser.add_argument("--archive-disposable", action="store_true", help="archive active disposable packets from the supplied manifest")
    parser.add_argument("--archive-audit-candidates", action="store_true", help="archive active terminal-audit archive candidates from the supplied audit report")
    parser.add_argument("--dry-run", action="store_true", help="show actions without moving files")
    parser.add_argument("--out", default=None, help="write apply report JSON")
    parser.add_argument("--summary", action="store_true", help="print compact summary")
    args = parser.parse_args()
    if args.archive_disposable:
        if not args.manifest:
            raise SystemExit("--manifest is required with --archive-disposable")
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest = load_manifest(manifest_path)
        manifest["report_path"] = str(manifest_path)
        report = apply_archive_disposable(manifest, dry_run=args.dry_run)
    elif args.archive_audit_candidates:
        if not args.audit:
            raise SystemExit("--audit is required with --archive-audit-candidates")
        audit_path = Path(args.audit).expanduser().resolve()
        audit = load_audit(audit_path)
        audit["report_path"] = str(audit_path)
        report = apply_archive_audit_candidates(audit, dry_run=args.dry_run)
    else:
        raise SystemExit("No action selected. Use --archive-disposable or --archive-audit-candidates.")
    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["report_path"] = str(out)
    if args.summary:
        print(json.dumps({
            "schema": report["schema"],
            "mode": report["mode"],
            "mutation_performed": report["mutation_performed"],
            "archived_count": report["archived_count"],
            "skipped_count": report["skipped_count"],
            "blocked_buckets_not_mutated": report["blocked_buckets_not_mutated"],
            "delete_performed": report["delete_performed"],
            "report_path": report.get("report_path"),
        }, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
