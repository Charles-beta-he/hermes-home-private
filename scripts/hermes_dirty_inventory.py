#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class DirtyEntry:
    status: str
    path: str
    bucket: str
    risk: str
    action: str
    size: int | None = None


def git_status(repo: Path) -> list[tuple[str, str]]:
    raw = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain=v1", "-z"])
    entries: list[tuple[str, str]] = []
    for part in raw.split(b"\0"):
        if not part:
            continue
        text = part.decode("utf-8", "surrogateescape")
        entries.append((text[:2], text[3:]))
    return entries


def classify(path: str, status: str) -> tuple[str, str, str]:
    p = path
    if "__pycache__/" in p or p.endswith((".pyc", ".pyo", ".pyd")):
        return "cache/pycache", "low", "clean_or_ignore"
    if p.startswith("cron/output/"):
        return "runtime/cron-output", "low", "ignore_generated"
    if p.startswith("logs/") or p.endswith(".log") or ".log." in p:
        return "runtime/logs", "low", "ignore_or_rotate"
    if p.startswith("state-snapshots/") or p.startswith("state/") or p.startswith("taskpool/"):
        return "runtime/state", "medium", "archive_or_ignore_after_owner_review"
    if p.endswith((".db", ".db-wal", ".db-shm", ".lock")) or p in {"gateway_state.json", "gateway.lock", "route_outcomes.db", "state.db"}:
        return "runtime/db-lock", "high", "manual_gate_do_not_reset"
    if p.startswith("memories/"):
        return "profile/memory", "critical", "manual_gate_do_not_commit_bulk"
    if p.startswith("config") or p in {"config.yaml", "context_length_cache.yaml", "models_dev_cache.json", "ollama_cloud_models_cache.json"}:
        return "profile/config-cache", "high", "manual_gate_diff_each"
    if p.startswith("profiles/"):
        return "profiles/cross-profile", "high", "manual_gate_cross_profile"
    if p.startswith("skills-archived/") or p.startswith("skills/.archive/"):
        return "skills/archive", "medium", "inventory_then_possible_ignore"
    if p.startswith("skills/"):
        return "skills/active", "high", "manual_gate_skill_semantics"
    if p.startswith("scripts/"):
        return "scripts/local-control-plane", "high", "cluster_and_review"
    if p.startswith("notes/brain/"):
        return "brain/workpad", "high", "manual_gate_ssot"
    if p.startswith("notes/engineering-cybernetics/") or p.startswith("notes/reports/"):
        return "notes/generated-reports", "medium", "archive_or_ignore_after_review"
    if p.startswith("docs/private/"):
        return "docs/private", "medium", "review_and_commit_if_durable"
    if p.startswith("images/") or p.startswith("image_cache/") or p.startswith("pastes/"):
        return "media/generated", "low", "ignore_generated"
    if p.startswith("backups/"):
        return "backups", "medium", "archive_external_or_ignore"
    if p.startswith("hermes-agent"):
        return "submodule/hermes-agent", "high", "handle_inner_repo_separately"
    return "other", "medium", "review"


def file_size(repo: Path, path: str) -> int | None:
    fp = repo / path
    try:
        if fp.is_file():
            return fp.stat().st_size
        if fp.is_dir():
            total = 0
            for child in fp.rglob("*"):
                if child.is_file():
                    try:
                        total += child.stat().st_size
                    except OSError:
                        pass
            return total
    except OSError:
        return None
    return None


def build_inventory(repo: Path) -> list[DirtyEntry]:
    out: list[DirtyEntry] = []
    for status, path in git_status(repo):
        bucket, risk, action = classify(path, status)
        out.append(DirtyEntry(status=status, path=path, bucket=bucket, risk=risk, action=action, size=file_size(repo, path)))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify Hermes root dirty/untracked state without mutating it.")
    parser.add_argument("--repo", default=str(Path.home() / ".hermes"))
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    inventory = build_inventory(repo)
    counts_by_bucket = collections.Counter(e.bucket for e in inventory)
    counts_by_risk = collections.Counter(e.risk for e in inventory)
    counts_by_status = collections.Counter(e.status for e in inventory)
    summary = {
        "schema": "hermes_dirty_inventory_v1",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": str(repo),
        "total": len(inventory),
        "counts_by_bucket": dict(counts_by_bucket.most_common()),
        "counts_by_risk": dict(counts_by_risk.most_common()),
        "counts_by_status": dict(counts_by_status.most_common()),
        "manual_gate_count": sum(1 for e in inventory if e.risk in {"high", "critical"}),
        "low_risk_count": sum(1 for e in inventory if e.risk == "low"),
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.out_dir:
        out_dir = Path(args.out_dir).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with (out_dir / "inventory.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["status", "path", "bucket", "risk", "action", "size"],
                lineterminator="\n",
            )
            writer.writeheader()
            for entry in inventory:
                writer.writerow(asdict(entry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
