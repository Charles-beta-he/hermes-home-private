#!/usr/bin/env python3
"""Inventory local Hermes changes for sanitized experience-pack extraction.

This is broader than package sanitization: it scans a Hermes home/repo working
copy, classifies changed/untracked files into landing buckets, and emits a
machine-readable review packet for deciding what can become a new-user install
artifact.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".jsonl", ".txt", ".sql", ".toml"}
RUNTIME_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".log", ".lock"}

OWNER_PATH_RE = re.compile(r"/Users/charles\b|/(?:Users|home)/[A-Za-z0-9._-]+/")
SECRET_RE = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._~+/=-]{20,}|\b(api[_-]?key|access[_-]?token|refresh[_-]?token|bot[_-]?token|password|client[_-]?secret)\b\s*[:=]\s*['\"]?[^'\"\s<>{}]{8,})")
PRIVATE_REF_RE = re.compile(r"docs/private|\.env|auth/|state\.db|contextcards[^\s`'\"]*\.db")


@dataclass
class Item:
    status: str
    path: str
    kind: str
    landing: str
    portable: bool
    reasons: list[str]
    size_bytes: int = 0
    file_count: int = 1


def git_status(root: Path) -> list[tuple[str, str]]:
    try:
        out = subprocess.check_output(["git", "-C", str(root), "status", "--short"], text=True)
    except Exception:
        return []
    rows: list[tuple[str, str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip() or "M"
        rel = line[3:]
        # Git collapses untracked directories as "?? dir/". Expand them so the
        # inventory can classify individual templates, DBs, notes, and scripts.
        if status == "??" and rel.endswith("/"):
            base = root / rel.rstrip("/")
            expanded = False
            for child in iter_leaf_files(base):
                rows.append((status, child.relative_to(root).as_posix()))
                expanded = True
            if expanded:
                continue
        rows.append((status, rel))
    return rows


def iter_leaf_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}]
        for name in filenames:
            yield Path(dirpath) / name


def read_sample(path: Path, limit: int = 120_000) -> str:
    if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except Exception:
        return ""


def classify_path(rel: str, full: Path) -> tuple[str, str, list[str]]:
    lowered = rel.lower()
    reasons: list[str] = []

    if rel == "hermes-agent":
        return "submodule", "manual_review", ["nested repo/submodule state must be reviewed separately"]

    if any(part in lowered for part in ["docs/private", "/logs/", "logs/", "/locks/", "locks/", "/backups/", "backups/"]):
        return "private_or_runtime_state", "exclude", ["private docs/logs/locks/backups are lived state"]
    if any(part in lowered for part in ["memory", "memories", "project-profiles", "profiles/"]):
        return "profile_or_memory_state", "exclude", ["memory/profile state is user-specific"]
    if full.suffix.lower() in RUNTIME_SUFFIXES or full.name.startswith("contextcards") and full.suffix == ".db":
        return "runtime_database_or_lock", "exclude", ["runtime database/log/lock must be generated per user"]
    if rel == "shell-hooks-allowlist.json":
        return "local_approval_state", "template_only", ["approval records are local; extract schema only"]
    if rel.startswith("templates/experience-pack/"):
        return "experience_pack_template", "copy_template", ["already under template pack"]
    if rel.startswith("skills/"):
        return "skill_or_reference", "sanitize_then_bundle_or_optional", ["skill content may be portable after scope/path sanitization"]
    if rel.startswith("scripts/test_"):
        return "test", "bundle_with_feature_if_feature_portable", ["test can ship with its feature if fixture-only"]
    if rel.startswith("scripts/"):
        return "script", "candidate_code_or_template", ["script requires path/secret/runtime review before shipping"]
    if rel.startswith("hooks/"):
        return "hook_config", "template_only", ["hook commands require user re-approval"]
    if rel.startswith("notes/"):
        return "local_observation", "extract_pattern_only", ["notes/history are local observations, not install payload"]
    return "unknown", "manual_review", ["unclassified path requires human review"]


def classify_content(text: str, rel: str) -> list[str]:
    reasons: list[str] = []
    if OWNER_PATH_RE.search(text):
        reasons.append("contains owner/local absolute path")
    if SECRET_RE.search(text):
        reasons.append("contains secret-like assignment/token pattern")
    if PRIVATE_REF_RE.search(text) and not rel.startswith("templates/experience-pack/"):
        reasons.append("mentions private/runtime state path")
    return reasons


def build_item(root: Path, status: str, rel: str) -> Item:
    full = root / rel
    files = list(iter_leaf_files(full))
    size = sum(f.stat().st_size for f in files if f.exists()) if files else (full.stat().st_size if full.exists() else 0)
    kind, landing, reasons = classify_path(rel, full)
    content_reasons: list[str] = []
    for f in files[:50]:
        sample = read_sample(f)
        if sample:
            content_reasons.extend(classify_content(sample, rel))
    # de-dupe preserving order
    all_reasons: list[str] = []
    for reason in reasons + content_reasons:
        if reason not in all_reasons:
            all_reasons.append(reason)
    portable = landing in {"copy_template", "sanitize_then_bundle_or_optional"} and not any(
        r for r in all_reasons if "owner/local" in r or "secret-like" in r
    )
    if landing in {"exclude", "extract_pattern_only", "template_only", "manual_review"}:
        portable = False
    return Item(status=status, path=rel, kind=kind, landing=landing, portable=portable, reasons=all_reasons, size_bytes=size, file_count=max(1, len(files)))


def inventory(root: Path) -> dict:
    root = root.expanduser().resolve()
    items = [build_item(root, status, rel.rstrip("/")) for status, rel in git_status(root)]
    by_landing: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for item in items:
        by_landing[item.landing] = by_landing.get(item.landing, 0) + 1
        by_kind[item.kind] = by_kind.get(item.kind, 0) + 1
    return {
        "schema": "hermes_experience_pack_inventory_v1",
        "root": str(root),
        "item_count": len(items),
        "by_landing": dict(sorted(by_landing.items())),
        "by_kind": dict(sorted(by_kind.items())),
        "portable_candidate_count": sum(1 for i in items if i.portable),
        "items": [asdict(i) for i in items],
        "rules": {
            "copy_template": "safe template payload after sanitizer",
            "sanitize_then_bundle_or_optional": "candidate skill/reference, requires scope and path cleanup",
            "candidate_code_or_template": "code must be promoted through tests and installer boundaries",
            "template_only": "extract schema/template; never copy live approval/config",
            "extract_pattern_only": "abstract lesson only; do not install raw file",
            "exclude": "lived state/private/runtime; never distribute",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inventory Hermes local changes for experience-pack extraction")
    parser.add_argument("root", nargs="?", default=str(Path.home() / ".hermes"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args(argv)
    result = inventory(Path(args.root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"items={result['item_count']} portable_candidates={result['portable_candidate_count']}")
        print("by_landing", json.dumps(result["by_landing"], ensure_ascii=False, sort_keys=True))
        for item in result["items"][: args.limit]:
            print(f"- {item['status']:>2} {item['landing']:<32} {item['kind']:<28} {item['path']}")
            for reason in item["reasons"][:3]:
                print(f"    reason: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
