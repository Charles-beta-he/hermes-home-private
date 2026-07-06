#!/usr/bin/env python3
"""Private Hermes Home update checker and installed-system issue reporter.

This script is designed for trusted installers of `hermes-home-private`.
It can check private-home version tags and, when explicitly enabled, submit a
sanitized GitHub issue describing a local system problem.

Default behavior is local-only: it writes issue packets and receipts but does
not submit to GitHub unless `report --submit --github-repo OWNER/REPO` is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

TAG_RE = re.compile(r"^private-home-(\d{4})\.(\d{2})\.(\d{2})\.(\d+)(?:-([A-Za-z0-9_.-]+))?$")
DEFAULT_MANIFEST = Path("docs/private/version-ops/private-version-manifest.json")
DEFAULT_GITHUB_REPO = "Charles-beta-he/hermes-home-private"
SECRET_PATTERNS = [
    re.compile(r"\b(?:sk|sk-proj)-[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{12,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s]+"),
]


@dataclass(order=True, frozen=True)
class PrivateHomeVersion:
    year: int
    month: int
    day: int
    seq: int
    suffix: str = ""

    @classmethod
    def parse(cls, tag: str) -> "PrivateHomeVersion | None":
        m = TAG_RE.match(tag.strip())
        if not m:
            return None
        year, month, day, seq, suffix = m.groups()
        return cls(int(year), int(month), int(day), int(seq), suffix or "")

    def tag(self) -> str:
        base = f"private-home-{self.year:04d}.{self.month:02d}.{self.day:02d}.{self.seq}"
        return base + (f"-{self.suffix}" if self.suffix else "")


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 45) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
        return {"cmd": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    except Exception as exc:
        return {"cmd": cmd, "returncode": 127, "stdout": "", "stderr": f"{type(exc).__name__}: {exc}"}


def redact(text: str, max_len: int = 6000) -> str:
    out = text[:max_len]
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def load_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / DEFAULT_MANIFEST
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def current_tag_from_manifest(repo_root: Path) -> str | None:
    manifest = load_manifest(repo_root)
    for key in ("current_version", "candidate_version", "version"):
        val = manifest.get(key)
        if isinstance(val, str) and PrivateHomeVersion.parse(val):
            return val
    return None


def git_head(repo_root: Path) -> str | None:
    res = run(["git", "rev-parse", "HEAD"], cwd=repo_root)
    return res["stdout"].strip() if res["returncode"] == 0 else None


def list_remote_tags(repo_root: Path, remote: str) -> list[str]:
    res = run(["git", "ls-remote", "--tags", remote, "private-home-*"], cwd=repo_root, timeout=60)
    if res["returncode"] != 0:
        raise RuntimeError(res["stderr"] or res["stdout"] or "git ls-remote failed")
    tags: list[str] = []
    for line in res["stdout"].splitlines():
        if "refs/tags/" not in line:
            continue
        ref = line.rsplit("refs/tags/", 1)[-1]
        if ref.endswith("^{}"):
            ref = ref[:-3]
        if PrivateHomeVersion.parse(ref):
            tags.append(ref)
    return sorted(set(tags), key=lambda t: PrivateHomeVersion.parse(t) or PrivateHomeVersion(0, 0, 0, 0))


def latest_stable_tag(tags: list[str]) -> str | None:
    stable: list[str] = []
    for tag in tags:
        parsed = PrivateHomeVersion.parse(tag)
        if parsed and not parsed.suffix:
            stable.append(tag)
    if not stable:
        return None
    return sorted(stable, key=lambda t: PrivateHomeVersion.parse(t) or PrivateHomeVersion(0, 0, 0, 0))[-1]


def check_update(repo_root: Path, remote: str = "origin") -> dict[str, Any]:
    current = current_tag_from_manifest(repo_root)
    tags = list_remote_tags(repo_root, remote)
    latest = latest_stable_tag(tags) or (tags[-1] if tags else None)
    cur_v = PrivateHomeVersion.parse(current) if current else None
    latest_v = PrivateHomeVersion.parse(latest) if latest else None
    update_available = bool(cur_v and latest_v and latest_v > cur_v)
    return {
        "schema": "private_home_update_check_v1",
        "repo_root": str(repo_root),
        "remote": remote,
        "current_version": current,
        "latest_version": latest,
        "all_versions": tags,
        "update_available": update_available,
        "head": git_head(repo_root),
    }


def collect_diagnostics(repo_root: Path, hermes_home: Path, reason: str) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "schema": "private_home_installed_system_diagnostics_v1",
        "reason": reason,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "repo_head": git_head(repo_root),
        "manifest_version": current_tag_from_manifest(repo_root),
        "commands": {},
    }
    command_map = {
        "hermes_version": ["hermes", "--version"],
        "hermes_doctor": ["hermes", "doctor"],
        "private_version_doctor": [sys.executable, str(repo_root / "scripts" / "private_version_doctor.py"), str(repo_root), "--json"],
        "dynamic_selfcheck_compile": [sys.executable, "-m", "py_compile", str(repo_root / "scripts" / "dynamic_selfcheck_coverage.py")],
    }
    for name, cmd in command_map.items():
        if shutil.which(cmd[0]) or Path(cmd[0]).exists() or cmd[0] == sys.executable:
            res = run(cmd, cwd=repo_root, timeout=90)
        else:
            res = {"cmd": cmd, "returncode": 127, "stdout": "", "stderr": f"command not found: {cmd[0]}"}
        diagnostics["commands"][name] = {
            "cmd": cmd,
            "returncode": res["returncode"],
            "stdout": redact(res.get("stdout", ""), 2000),
            "stderr": redact(res.get("stderr", ""), 2000),
        }
    state_dir = hermes_home / "state" / "private-home-issue-reports"
    diagnostics["state_dir"] = str(state_dir)
    return diagnostics


def fingerprint(payload: dict[str, Any]) -> str:
    stable = {
        "reason": payload.get("reason"),
        "platform": payload.get("platform"),
        "manifest_version": payload.get("manifest_version"),
        "commands": {k: v.get("returncode") for k, v in sorted(payload.get("commands", {}).items())},
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def issue_body(diagnostics: dict[str, Any]) -> str:
    fp = diagnostics.get("fingerprint") or fingerprint(diagnostics)
    lines = [
        "## Installed Hermes private-home system report",
        "",
        f"Fingerprint: `{fp}`",
        f"Reason: {diagnostics.get('reason','')}",
        f"Platform: `{diagnostics.get('platform','')}`",
        f"Python: `{diagnostics.get('python','')}`",
        f"Private-home version: `{diagnostics.get('manifest_version')}`",
        f"Repo head: `{diagnostics.get('repo_head')}`",
        "",
        "### Command diagnostics",
    ]
    for name, res in diagnostics.get("commands", {}).items():
        lines.extend([
            f"\n#### {name}",
            f"returncode: `{res.get('returncode')}`",
            "stdout:",
            "```text",
            redact(str(res.get("stdout", "")), 3000),
            "```",
            "stderr:",
            "```text",
            redact(str(res.get("stderr", "")), 3000),
            "```",
        ])
    lines.extend([
        "",
        "### Maintainer flow",
        "1. Reproduce from private-home version and repo head.",
        "2. Decide target repo: home pack vs hermes-agent runtime fork vs upstream.",
        "3. Patch in clean worktree, run targeted checks, tag private-home version if needed.",
        "4. Comment issue with fix commit/tag and close only after update readback.",
    ])
    return "\n".join(lines) + "\n"


def write_packet(diagnostics: dict[str, Any], hermes_home: Path) -> dict[str, Any]:
    fp = fingerprint(diagnostics)
    diagnostics["fingerprint"] = fp
    state_dir = hermes_home / "state" / "private-home-issue-reports"
    state_dir.mkdir(parents=True, exist_ok=True)
    json_path = state_dir / f"{fp}.json"
    md_path = state_dir / f"{fp}.md"
    existed = json_path.exists()
    json_path.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(issue_body(diagnostics), encoding="utf-8")
    return {"fingerprint": fp, "json_path": str(json_path), "body_path": str(md_path), "duplicate": existed}


def submit_issue(github_repo: str, title: str, body_path: Path, labels: list[str]) -> dict[str, Any]:
    if not shutil.which("gh"):
        return {"ok": False, "submitted": False, "error": "gh CLI not found"}
    auth = run(["gh", "auth", "status"], timeout=30)
    if auth["returncode"] != 0:
        return {"ok": False, "submitted": False, "error": redact(auth.get("stderr") or auth.get("stdout") or "gh auth failed")}
    cmd = ["gh", "issue", "create", "--repo", github_repo, "--title", title, "--body-file", str(body_path)]
    for label in labels:
        cmd.extend(["--label", label])
    res = run(cmd, timeout=60)
    return {
        "ok": res["returncode"] == 0,
        "submitted": res["returncode"] == 0,
        "returncode": res["returncode"],
        "stdout": redact(res.get("stdout", ""), 2000),
        "stderr": redact(res.get("stderr", ""), 2000),
    }


def report_problem(repo_root: Path, hermes_home: Path, reason: str, submit: bool, github_repo: str, force: bool) -> dict[str, Any]:
    diag = collect_diagnostics(repo_root, hermes_home, reason)
    receipt = write_packet(diag, hermes_home)
    result = {"schema": "private_home_issue_report_v1", **receipt, "submitted": False, "submit_result": None}
    if submit:
        if receipt["duplicate"] and not force:
            result["submit_result"] = {"ok": True, "submitted": False, "reason": "duplicate packet; use --force to resubmit"}
        else:
            title = f"[private-home install] system report {receipt['fingerprint']}: {reason[:80]}"
            result["submit_result"] = submit_issue(github_repo, title, Path(receipt["body_path"]), ["installed-system", "automated-report"])
            result["submitted"] = bool(result["submit_result"].get("submitted"))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private Hermes home update checker and issue reporter")
    sub = parser.add_subparsers(dest="cmd", required=True)

    check = sub.add_parser("check")
    check.add_argument("--repo-root", default=".")
    check.add_argument("--remote", default="origin")
    check.add_argument("--json", action="store_true")

    report = sub.add_parser("report")
    report.add_argument("--repo-root", default=".")
    report.add_argument("--hermes-home", default=str(Path.home() / ".hermes"))
    report.add_argument("--reason", required=True)
    report.add_argument("--github-repo", default=DEFAULT_GITHUB_REPO)
    report.add_argument("--submit", action="store_true")
    report.add_argument("--force", action="store_true")
    report.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "check":
        payload = check_update(Path(args.repo_root).resolve(), args.remote)
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload)
        return 0
    if args.cmd == "report":
        payload = report_problem(Path(args.repo_root).resolve(), Path(args.hermes_home).expanduser().resolve(), args.reason, args.submit, args.github_repo, args.force)
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload)
        return 0 if not args.submit or (payload.get("submit_result") or {}).get("ok") else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
