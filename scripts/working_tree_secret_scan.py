#!/usr/bin/env python3
"""Fail-closed working-tree secret scanner for Hermes profile changes.

Scans git diffs and selected runtime config files without printing secret values.
Default scope is intentionally narrow to avoid flagging the expected private
~/.hermes/.env vault unless --include-env is requested.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("telegram_bot_token", re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b")),
    ("openai_like_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "generic_assignment_secret",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"]?([A-Za-z0-9_./+=:@-]{24,})['\"]?"
        ),
    ),
]

ALLOWLIST_SUBSTRINGS = (
    "[REDACTED]",
    "REDACTED_",
    "your_token",
    "example",
    "placeholder",
    "dummy",
    "test-token",
    "fake-token",
)

@dataclass(frozen=True)
class Finding:
    source: str
    line: int
    kind: str
    fingerprint: str
    length: int


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:12]


def _extract_secret(kind: str, match: re.Match[str]) -> str:
    if kind == "generic_assignment_secret" and match.groups():
        return match.group(1)
    return match.group(0)


def scan_line(line: str, source: str, lineno: int) -> list[Finding]:
    if any(marker.lower() in line.lower() for marker in ALLOWLIST_SUBSTRINGS):
        return []
    findings: list[Finding] = []
    for kind, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(line):
            candidate_value = _extract_secret(kind, match)
            if len(candidate_value.strip()) < 20:
                continue
            findings.append(
                Finding(
                    source=source,
                    line=lineno,
                    kind=kind,
                    fingerprint=_fingerprint(candidate_value),
                    length=len(candidate_value),
                )
            )
    return findings


def scan_text(text: str, source: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        findings.extend(scan_line(line, source, lineno))
    return findings


def _git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(["git", *args], cwd=str(cwd), text=True, capture_output=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def _added_lines(diff: str) -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    current_file = "diff"
    new_lineno = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
            continue
        if raw.startswith("@@"):
            m = re.search(r"\+(\d+)(?:,(\d+))?", raw)
            new_lineno = int(m.group(1)) - 1 if m else 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            new_lineno += 1
            out.append((current_file, new_lineno, raw[1:]))
        elif raw.startswith("-") and not raw.startswith("---"):
            continue
        else:
            new_lineno += 1
    return out


def scan_git_diff(repo: Path, staged: bool) -> list[Finding]:
    args = ["diff", "--cached"] if staged else ["diff"]
    diff = _git(args, repo)
    findings: list[Finding] = []
    for source, lineno, line in _added_lines(diff):
        findings.extend(scan_line(line, source, lineno))
    return findings


def scan_files(paths: Iterable[Path], repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            rel = str(path.relative_to(repo))
        except ValueError:
            rel = str(path)
        findings.extend(scan_text(path.read_text(errors="replace"), rel))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan Hermes working tree for committed/diffable secrets")
    parser.add_argument("--repo", default=str(Path.home() / ".hermes"))
    parser.add_argument("--staged", action="store_true", help="scan staged diff plus high-risk tracked config files")
    parser.add_argument("--all-diff", action="store_true", help="scan staged and unstaged diffs")
    parser.add_argument("--include-env", action="store_true", help="also scan .env; expected to fail on real private vaults")
    parser.add_argument("--file", action="append", default=[], help="extra file to scan")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists():
        print(f"ERROR repo not found: {repo}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    findings.extend(scan_git_diff(repo, staged=True))
    if args.all_diff or not args.staged:
        findings.extend(scan_git_diff(repo, staged=False))

    default_files = [repo / "config.yaml", repo / "cron" / "jobs.json", repo / "gateway_state.json"]
    if args.include_env:
        default_files.append(repo / ".env")
    default_files.extend(Path(p).expanduser() for p in args.file)
    findings.extend(scan_files(default_files, repo))

    # Stable de-dupe by redacted secret identity. A tracked config secret may be
    # seen in both diff and current-file scans, and a specific token can also
    # match the generic assignment pattern. One finding is enough to block;
    # prefer the more specific classifier for clearer remediation.
    kind_rank = {"generic_assignment_secret": 10}
    by_secret: dict[str, Finding] = {}
    for finding in findings:
        existing = by_secret.get(finding.fingerprint)
        if existing is None or kind_rank.get(finding.kind, 0) < kind_rank.get(existing.kind, 0):
            by_secret[finding.fingerprint] = finding
    unique = sorted(by_secret.values(), key=lambda f: (f.source, f.line, f.kind, f.fingerprint))
    if unique:
        print(f"SECRET_SCAN_FAIL findings={len(unique)}")
        for f in unique:
            print(f"{f.source}:{f.line}:{f.kind}:{f.fingerprint}:{f.length}")
        return 1
    print("SECRET_SCAN_PASS findings=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
