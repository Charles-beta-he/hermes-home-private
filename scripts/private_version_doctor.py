#!/usr/bin/env python3
"""Private Hermes home version readiness scanner.

This doctor is intentionally repository-focused. It checks whether the private
home tree is suitable as a reproducible capability pack. It does not validate a
live user's ~/.hermes runtime config or credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REQUIRED_PATHS = [
    "AGENTS.md",
    ".gitignore",
    "PRIVATE_VERSIONING.md",
    "docs/private/version-ops/private-repo-versioning.md",
    "docs/private/version-ops/install-same-experience.md",
    "docs/private/version-ops/installed-system-issue-flow.md",
    "docs/private/version-ops/private-version-manifest.json",
    "scripts/private_version_doctor.py",
    "scripts/private_home_update_check.py",
    "scripts/test_private_version_doctor.py",
    "scripts/test_private_home_update_check.py",
    ".github/ISSUE_TEMPLATE/installed-system-report.yml",
    "scripts/dynamic_selfcheck_coverage.py",
    "scripts/tests/test_dynamic_selfcheck_coverage.py",
    "skills/autonomous-ai-agents/hermes-agent/SKILL.md",
    "project-profiles/hermes.json",
]

RUNTIME_PREFIXES = (
    "cron/output/",
    "logs/",
    "sessions/",
    "state/",
    "memories/",
)

RUNTIME_EXACT = {
    "config.yaml",
    "config/quorum.yaml",
    "cron/jobs.json",
    "gateway_state.json",
    "route_outcomes.db",
    "state.db",
    "contextcards.db",
    "verification_evidence.db",
    "auth.json",
}

RUNTIME_SUFFIXES = (
    ".db",
    ".db-wal",
    ".db-shm",
    ".lock",
    ".pid",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
)

SECRET_MARKERS = (
    "BEGIN PRIVATE KEY",
    "OPENAI_API_KEY=",
    "ANTHROPIC_API_KEY=",
    "TELEGRAM_BOT_TOKEN=",
    "SLACK_BOT_TOKEN=",
    "xoxb-",
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"\b(?:sk|sk-proj)-[A-Za-z0-9_\-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]{40,}?-----END [A-Z ]*PRIVATE KEY-----"),
)

@dataclass
class Finding:
    severity: str
    code: str
    path: str
    message: str


def git_files(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(["git", "-C", str(root), "ls-files"], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            if ".git" in dirnames:
                dirnames.remove(".git")
            for name in filenames:
                files.append(str((Path(dirpath) / name).relative_to(root)))
        return sorted(files)
    return [line for line in out.splitlines() if line]


def is_runtime_artifact(path: str) -> bool:
    if path in RUNTIME_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in RUNTIME_PREFIXES):
        return True
    name = Path(path).name
    if name.startswith(".") and name.endswith(".lock"):
        return True
    return path.endswith(RUNTIME_SUFFIXES)


def is_placeholder_secret(match_text: str, rel: str) -> bool:
    name = Path(rel).name
    if name.startswith("test_") or "/test_" in rel or "/tests/" in rel:
        return True
    compact = "".join(ch.lower() for ch in match_text if ch.isalnum())
    for prefix in ("skproj", "sk", "ghp", "gho", "ghu", "ghs", "ghr", "xoxb", "xoxa", "xoxp", "xoxr", "xoxs"):
        if compact.startswith(prefix):
            compact = compact[len(prefix):]
            break
    return bool(compact) and (set(compact) <= {"x"} or compact in {"abc", "abc3456", "ab7890"})


def scan_secret_markers(root: Path, files: list[str], limit_bytes: int = 512_000) -> list[Finding]:
    findings: list[Finding] = []
    for rel in files:
        path = root / rel
        try:
            if path.stat().st_size > limit_bytes:
                continue
            data = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_VALUE_PATTERNS:
            match = pattern.search(data)
            if match and "..." not in match.group(0) and not is_placeholder_secret(match.group(0), rel):
                findings.append(Finding("blocker", "secret_value", rel, "contains token/private-key shaped secret value"))
                break
        else:
            for marker in SECRET_MARKERS:
                if marker in data:
                    findings.append(Finding("warning", "secret_marker_string", rel, f"contains secret marker string {marker!r}; verify it is example/test text"))
                    break
    return findings


def run(root: Path) -> dict:
    root = root.resolve()
    files = git_files(root)
    file_set = set(files)
    findings: list[Finding] = []

    for rel in REQUIRED_PATHS:
        if rel not in file_set and not (root / rel).exists():
            findings.append(Finding("blocker", "missing_required_path", rel, "required release path is missing"))

    manifest_path = root / "docs/private/version-ops/private-version-manifest.json"
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            if payload.get("schema") != "hermes_private_home_release_manifest_v1":
                findings.append(Finding("blocker", "manifest_schema", str(manifest_path.relative_to(root)), "unexpected version manifest schema"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("blocker", "manifest_json", str(manifest_path.relative_to(root)), f"invalid JSON: {exc}"))

    runtime = [rel for rel in files if is_runtime_artifact(rel)]
    for rel in runtime[:200]:
        findings.append(Finding("warning", "tracked_runtime_artifact", rel, "tracked runtime artifact; do not add more, remove in separate cleanup release"))
    if len(runtime) > 200:
        findings.append(Finding("warning", "tracked_runtime_artifact_truncated", "", f"{len(runtime)-200} additional runtime artifacts omitted"))

    findings.extend(scan_secret_markers(root, files))

    counts = {
        "tracked_files": len(files),
        "skills": sum(1 for f in files if f.startswith("skills/")),
        "scripts": sum(1 for f in files if f.startswith("scripts/")),
        "workflows": sum(1 for f in files if f.startswith("workflows/")),
        "project_profiles": sum(1 for f in files if f.startswith("project-profiles/")),
        "docs_private": sum(1 for f in files if f.startswith("docs/private/")),
        "runtime_artifacts_tracked": len(runtime),
    }
    blockers = [f for f in findings if f.severity == "blocker"]
    warnings = [f for f in findings if f.severity == "warning"]
    readiness = "blocked" if blockers else ("candidate_with_debt" if warnings else "stable_candidate")
    return {
        "ok": not blockers,
        "readiness": readiness,
        "root": str(root),
        "counts": counts,
        "blockers": [asdict(f) for f in blockers],
        "warnings": [asdict(f) for f in warnings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private Hermes home version doctor")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="return non-zero when warnings exist")
    args = parser.parse_args(argv)
    payload = run(Path(args.root))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"{payload['readiness']}: blockers={len(payload['blockers'])} warnings={len(payload['warnings'])}")
        for f in payload["blockers"][:20]:
            print(f"BLOCKER {f['code']} {f['path']} {f['message']}")
        for f in payload["warnings"][:20]:
            print(f"WARNING {f['code']} {f['path']} {f['message']}")
    if not payload["ok"]:
        return 2
    if args.strict and payload["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
