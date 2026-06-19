#!/usr/bin/env python3
"""Sanitize a Hermes experience pack before distribution.

The scanner is intentionally deterministic and conservative: an experience pack
may contain capability shapes, templates, example configs, and selfchecks, but
must not contain the owner's lived state (private paths, credentials, DBs, logs,
locks, backups, profiles, memories, or private evidence).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {
    ".bash",
    ".cfg",
    ".conf",
    ".css",
    ".csv",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

FORBIDDEN_BASENAMES = {
    ".env",
    "state.db",
    "auth.json",
    "credentials.json",
    "shell-hooks-allowlist.json",
}

FORBIDDEN_PATH_PARTS = {
    "auth",
    "backups",
    "docs/private",
    "locks",
    "logs",
    "memories",
    "project-profiles",
    "profiles",
    "runtime",
    "sessions",
    "state",
}

FORBIDDEN_GLOBS = (
    "contextcards*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.db-wal",
    "*.db-shm",
    "*.pem",
    "*.key",
)

CONTENT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("owner_absolute_path", re.compile(r"/Users/charles\b")),
    ("absolute_user_home_path", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/(?!\.hermes/templates\b)")),
    ("private_docs_reference", re.compile(r"docs/private")),
    ("env_file_reference", re.compile(r"(?<![A-Za-z0-9_])\.env(?![A-Za-z0-9_])")),
    ("state_db_reference", re.compile(r"(?<![A-Za-z0-9_])state\.db(?![A-Za-z0-9_])")),
    ("contextcards_db_reference", re.compile(r"contextcards[^\s`'\"]*\.db")),
    ("bearer_token", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("secret_assignment", re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|refresh[_-]?token|bot[_-]?token|password|client[_-]?secret)\b\s*[:=]\s*['\"]?[^'\"\s<>{}]{8,}")),
)

ALLOWED_PLACEHOLDER_RE = re.compile(r"(<[^>]+>|\$\{?[A-Z0-9_]+\}?|REPLACE_ME|YOUR_[A-Z0-9_]+|example\.com)")


@dataclass
class Finding:
    severity: str
    rule: str
    path: str
    line: int | None = None
    detail: str = ""


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Do not follow nested VCS/dependency directories; experience packs should
        # not vendor them, and scanning them produces noisy implementation details.
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}
        ]
        for name in filenames:
            yield Path(dirpath) / name


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\0" not in chunk


def path_findings(path: Path, root: Path) -> list[Finding]:
    rel = _rel(path, root)
    lowered = rel.lower()
    findings: list[Finding] = []
    if path.name in FORBIDDEN_BASENAMES:
        findings.append(Finding("error", "forbidden_basename", rel, detail=path.name))
    for pattern in FORBIDDEN_GLOBS:
        if path.match(pattern) or path.name.lower().endswith(pattern.replace("*", "")):
            findings.append(Finding("error", "forbidden_file_pattern", rel, detail=pattern))
    parts = rel.split("/")
    for part in FORBIDDEN_PATH_PARTS:
        if "/" in part:
            if part in lowered:
                findings.append(Finding("error", "forbidden_path_part", rel, detail=part))
        elif part in parts:
            findings.append(Finding("error", "forbidden_path_part", rel, detail=part))
    return findings


def content_findings(path: Path, root: Path) -> list[Finding]:
    rel = _rel(path, root)
    if not is_text_file(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [Finding("error", "unreadable_file", rel, detail=str(exc))]
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule, regex in CONTENT_RULES:
            match = regex.search(line)
            if not match:
                continue
            # Placeholder examples are allowed for secret-like assignments.
            if rule == "secret_assignment" and ALLOWED_PLACEHOLDER_RE.search(line):
                continue
            # Policy documents and manifests must be able to name forbidden
            # payload classes. Runtime DB examples are also allowed when they are
            # explicitly parameterized through $HERMES_HOME instead of embedding a
            # real owner-local path. Actual DB/log/auth payloads are caught by
            # path rules above.
            if rule in {"env_file_reference", "private_docs_reference", "state_db_reference", "contextcards_db_reference"}:
                if rel in {"README.md", "manifest.yaml"}:
                    continue
                if "$HERMES_HOME" in line or "<HERMES_HOME>" in line:
                    continue
            snippet = line.strip()[:220]
            findings.append(Finding("error", rule, rel, line_no, snippet))
    return findings


def scan(root: Path) -> dict:
    root = root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"experience pack root is not a directory: {root}")
    files = list(iter_files(root))
    findings: list[Finding] = []
    for path in files:
        findings.extend(path_findings(path, root))
        findings.extend(content_findings(path, root))
    return {
        "schema": "hermes_experience_pack_sanitize_v1",
        "root": str(root),
        "file_count": len(files),
        "finding_count": len(findings),
        "ok": not findings,
        "findings": [asdict(f) for f in findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sanitize a Hermes experience pack directory")
    parser.add_argument("root", help="Experience pack directory to scan")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args(argv)
    result = scan(Path(args.root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status}: scanned {result['file_count']} files, findings={result['finding_count']}")
        for finding in result["findings"][:50]:
            loc = finding["path"]
            if finding.get("line"):
                loc += f":{finding['line']}"
            print(f"- {finding['severity']} {finding['rule']} {loc} {finding.get('detail','')}")
        if result["finding_count"] > 50:
            print(f"... {result['finding_count'] - 50} more findings")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
