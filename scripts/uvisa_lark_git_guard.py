#!/usr/bin/env python3
"""Pre-commit guard for Hermes local runtime/secrets boundary.

Blocks staged runtime paths and obvious secret-like values before they enter the
private Hermes repository. This is intentionally conservative and redacted.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / ".hermes"
BLOCKED_PREFIXES = (
    "sessions/",
    "cache/",
    "tmp/",
    "state/",
    "checkpoints/",
    "snapshots/",
    "tick-",
    "shared/",
)
BLOCKED_EXACT = {".env", "auth.json", "task_ledger.db", ".hermes_history"}
ALLOWED_STATE_PREFIXES = (
    "state/governance_ratchet.json",
)
SECRET_NAME_RE = re.compile(r"(?i)(APP_SECRET|API[_-]?KEY|TOKEN|BEARER|PASSWORD|PASSWD|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET|CREDENTIAL|AUTHORIZATION)")
SECRET_VALUE_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._~+/=-]{16,}|[a-z0-9_-]{20,}\.[a-z0-9_-]{20,}\.[a-z0-9_-]{10,}|\b(sk|ak|rk|pk|xox)[-_][a-z0-9_-]{16,}|secret\s*[:=]\s*['\"]?[^'\"\s]{12,})"
)
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".toml", ".py", ".sh", ".txt", ".env"}


def run(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL)


def staged_files() -> list[str]:
    try:
        out = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_blocked_path(path: str) -> bool:
    if path in BLOCKED_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in ALLOWED_STATE_PREFIXES):
        return False
    return any(path.startswith(prefix) for prefix in BLOCKED_PREFIXES)


def blob_text(path: str) -> str | None:
    if Path(path).suffix.lower() not in TEXT_SUFFIXES and not Path(path).name.startswith(".env"):
        return None
    try:
        return run(["git", "show", f":{path}"])
    except Exception:
        return None


def main() -> int:
    files = staged_files()
    blocked: list[str] = []
    secret_hits: list[str] = []
    for f in files:
        if is_blocked_path(f):
            blocked.append(f)
            continue
        text = blob_text(f)
        if not text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if SECRET_VALUE_RE.search(line):
                secret_hits.append(f"{f}:{i}: secret-like value [REDACTED]")
                break
            # Allow governance docs/scripts to mention variable names, but never values.
            if f.startswith(("docs/", "scripts/", "skills/", "profiles/", "project-profiles/", "eval/")):
                continue
            if SECRET_NAME_RE.search(line):
                secret_hits.append(f"{f}:{i}: sensitive variable name [REDACTED]")
                break
    if blocked or secret_hits:
        print("Hermes UVISA/Lark governance guard blocked this commit.", file=sys.stderr)
        if blocked:
            print("Blocked runtime/secret/cache paths:", file=sys.stderr)
            for item in blocked[:50]:
                print(f"  - {item}", file=sys.stderr)
        if secret_hits:
            print("Secret-like staged content:", file=sys.stderr)
            for item in secret_hits[:50]:
                print(f"  - {item}", file=sys.stderr)
        print("Use git reset <path> or move durable facts into redacted docs/profiles/skills.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
