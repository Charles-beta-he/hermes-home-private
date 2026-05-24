#!/usr/bin/env python3
"""Redacted governance audit for Lark + uvisa-app-2.0 Hermes facts.

This script intentionally reports only paths, line numbers, variable names,
counts, hashes, and categories. It never prints secret values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

HOME = Path.home()
HERMES = HOME / ".hermes"
UVISA_APP = HOME / "Desktop/folder/work/uvisa-app-2.0"
UVISA_ADMIN = HOME / "Desktop/folder/work/uvisa-admin"
UVISA_BACKEND = HOME / "Desktop/folder/work/uvisa-backend"

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|app[_-]?secret|secret|token|bearer|jwt|password|passwd|credential|private[_-]?key|client[_-]?secret|authorization)"
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._~+/=-]{16,}|[a-z0-9_-]{20,}\.[a-z0-9_-]{20,}\.[a-z0-9_-]{10,}|(sk|ak|rk|pk|xox)[-_][a-z0-9_-]{16,}|secret\s*[:=]\s*['\"]?[^'\"\s]{12,})"
)
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
TEXT_EXT = {".md", ".json", ".yaml", ".yml", ".toml", ".env", ".txt", ".py", ".sh"}
PRUNE_DIRS = {
    ".git", "node_modules", "dist", "build", "coverage", ".next", "venv", ".venv",
    "__pycache__", "vendor", "profiles", "kanban", "backups"
}

CANONICAL_LARK_SKILL = HERMES / "skills/software-development/lark-task-reading/SKILL.md"
OVERLAY_LARK_SKILLS = [
    HERMES / "profiles/mlops/skills/software-development/lark-task-reading/SKILL.md",
    HERMES / "profiles/workflow/skills/software-development/lark-task-reading/SKILL.md",
    HERMES / "profiles/dev/skills/software-development/lark-task-reading/SKILL.md",
]


def sha12(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except Exception as exc:  # pragma: no cover - defensive reporting
        return f"ERROR:{type(exc).__name__}"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(HOME))
    except ValueError:
        return str(path)


def git_tracked(root: Path) -> set[str]:
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=root, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def git_check_ignore(root: Path, paths: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for p in paths:
        try:
            out = subprocess.check_output(["git", "check-ignore", "-v", p], cwd=root, text=True, stderr=subprocess.DEVNULL)
            result[p] = out.strip()
        except subprocess.CalledProcessError:
            result[p] = "NOT_IGNORED"
        except Exception as exc:
            result[p] = f"ERROR:{type(exc).__name__}"
    return result


def scan_secret_markers(paths: list[Path], max_files: int = 5000) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen = 0
    for root in paths:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
            for name in filenames:
                p = Path(dirpath) / name
                if p.suffix.lower() not in TEXT_EXT and not name.startswith(".env"):
                    continue
                seen += 1
                if seen > max_files:
                    return findings
                try:
                    text = p.read_text(errors="ignore")
                except Exception:
                    continue
                hits = []
                for i, line in enumerate(text.splitlines(), 1):
                    if SECRET_RE.search(line) or SECRET_VALUE_RE.search(line):
                        key_match = re.search(r"([A-Za-z0-9_]*(?:SECRET|TOKEN|PASSWORD|KEY|CREDENTIAL|AUTH)[A-Za-z0-9_]*)", line, re.I)
                        hits.append({
                            "line": i,
                            "kind": "secret_marker_or_value_shape",
                            "name": key_match.group(1) if key_match else "[REDACTED_NAME_UNKNOWN]",
                            "redacted": True,
                        })
                        if len(hits) >= 8:
                            break
                if hits:
                    findings.append({"path": str(p), "hits": hits})
    return findings


def scan_images(paths: list[Path]) -> dict[str, Any]:
    images: list[dict[str, Any]] = []
    by_hash: dict[str, list[str]] = defaultdict(list)
    for root in paths:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
            for name in filenames:
                p = Path(dirpath) / name
                if p.suffix.lower() not in IMAGE_EXT:
                    continue
                s = str(p).lower()
                if not any(k in s for k in ["uvisa", "lark", "admin", "screenshot", "evidence", "playwright", "test-results"]):
                    continue
                h = sha12(p)
                by_hash[h].append(str(p))
                images.append({"path": str(p), "sha12": h, "bytes": p.stat().st_size})
    duplicates = {h: ps for h, ps in by_hash.items() if len(ps) > 1}
    return {"count": len(images), "duplicates": duplicates, "sample": images[:80]}


def skill_drift() -> list[dict[str, Any]]:
    paths = [CANONICAL_LARK_SKILL] + OVERLAY_LARK_SKILLS
    out = []
    for p in paths:
        out.append({"path": str(p), "exists": p.exists(), "sha12": sha12(p) if p.exists() else None})
    return out


def profile_summary() -> dict[str, Any]:
    targets = [HERMES / "project-profiles/lark.json", HERMES / "project-profiles/uvisa-app-2.0.json"]
    out: dict[str, Any] = {}
    for p in targets:
        item: dict[str, Any] = {"exists": p.exists()}
        if p.exists():
            item.update({"bytes": p.stat().st_size, "lines": len(p.read_text(errors="ignore").splitlines()), "sha12": sha12(p)})
            try:
                data = json.loads(p.read_text())
                item["top_level_keys"] = sorted(data.keys())[:80]
            except Exception as exc:
                item["json_error"] = type(exc).__name__
        out[str(p)] = item
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    ap.add_argument("--redact", action="store_true", help="Required; values are always redacted")
    ap.add_argument("--scope", default="uvisa-lark")
    ap.add_argument("--max-secret-files", type=int, default=5000)
    args = ap.parse_args()

    roots = [HERMES, UVISA_APP, UVISA_ADMIN, UVISA_BACKEND]
    tracked = git_tracked(HERMES)
    sensitive_tracked = sorted(p for p in tracked if (
        p == ".env" or p == "auth.json" or p.startswith(("sessions/", "cache/", "state/", "checkpoints/", "tick-"))
    ))
    report = {
        "schema": "uvisa_lark_governance_audit_v1",
        "scope": args.scope,
        "redaction": "values never printed; secret-like values are [REDACTED] by policy",
        "roots": [str(p) for p in roots if p.exists()],
        "git_boundary": {
            "hermes_root": str(HERMES),
            "root_gitignore_exists": (HERMES / ".gitignore").exists(),
            "sensitive_tracked_count": len(sensitive_tracked),
            "sensitive_tracked_sample": sensitive_tracked[:80],
            "ignore_probe": git_check_ignore(HERMES, [".env", "auth.json", "sessions/example.json", "cache/screenshots/example.png", "state/continuations/example.json", "tick-example/state.json"]),
        },
        "profile_summary": profile_summary(),
        "lark_skill_drift": skill_drift(),
        "secret_markers": scan_secret_markers(roots, max_files=args.max_secret_files),
        "image_evidence": scan_images([HERMES / "evidence", HERMES / "cache/screenshots", UVISA_APP / ".playwright-mcp", UVISA_APP / "test-results"]),
        "recommended_next_actions": [
            "Keep .gitignore and this audit script under scoped git commit.",
            "Run git rm --cached only after reviewing sensitive_tracked_sample and backing up active runtime state.",
            "Rotate exposed Lark/Feishu/model/auth secrets outside this script.",
            "Choose canonical lark-task-reading skill/reference source and sync/remove profile overlay copies.",
            "Create a manifest before deleting or promoting screenshots.",
        ],
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"scope: {args.scope}")
        print(f"root_gitignore_exists: {report['git_boundary']['root_gitignore_exists']}")
        print(f"sensitive_tracked_count: {report['git_boundary']['sensitive_tracked_count']}")
        print(f"secret_marker_files: {len(report['secret_markers'])}")
        print(f"image_count: {report['image_evidence']['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
