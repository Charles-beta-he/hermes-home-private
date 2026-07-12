#!/usr/bin/env python3
"""Reusable helpers for Hermes project-profile verifier drains.

This module is intentionally generic: import/copy functions into one-off SSOT
update scripts rather than hardcoding a project path in the skill.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

REDACT_QUERY_KEYS = {
    "token",
    "session",
    "cookie",
    "password",
    "secret",
    "apiKey",
    "api_key",
    "apiRSAKey",
    "hisDataSign",
    "tradeId",
    "partnerTradeId",
    "partnerId",
    "partnerNo",
    "timestamp",
}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def git(repo: Path, args: Iterable[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def git_readback(repo: Path, target_commit: str | None = None) -> dict[str, Any]:
    readback = {
        "status": git(repo, ["status", "--short", "--branch"]),
        "head": git(repo, ["rev-parse", "--short", "HEAD"]),
        "dirtyEntries": git(repo, ["status", "--porcelain=v1"]),
    }
    if target_commit:
        try:
            git(repo, ["merge-base", "--is-ancestor", target_commit, "HEAD"])
            readback["currentHeadContainsTarget"] = True
        except subprocess.CalledProcessError:
            readback["currentHeadContainsTarget"] = False
    return readback


def redact_url_like(value: str, replacement: str = "[REDACTED]") -> str:
    """Redact credential/quasi-credential query parameters in plain or encoded URLs."""
    keys = "|".join(re.escape(k) for k in sorted(REDACT_QUERY_KEYS, key=len, reverse=True))
    value = re.sub(rf"((?:{keys})=)[^&\s]+", rf"\1{replacement}", value)
    value = re.sub(rf"((?:{keys})%3D)[^&\s]+", rf"\1{replacement}", value, flags=re.IGNORECASE)
    return value


def redact_evidence_file(path: Path) -> bool:
    """Redact URL-like strings in a JSON evidence file in-place. Returns changed."""
    data = json.loads(path.read_text())
    changed = False

    def walk(x: Any) -> Any:
        nonlocal changed
        if isinstance(x, str):
            y = redact_url_like(x)
            changed = changed or y != x
            return y
        if isinstance(x, list):
            return [walk(v) for v in x]
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        return x

    redacted = walk(data)
    if changed:
        path.write_text(json.dumps(redacted, ensure_ascii=False, indent=2))
    return changed


def stale_amend_receipt(
    *,
    source_delegation: str,
    slice_name: str,
    target_commit: str,
    repo: Path,
    evidence_path: Path,
) -> dict[str, Any]:
    rb = git_readback(repo, target_commit)
    return {
        "generatedAt": utc_now(),
        "sourceDelegation": source_delegation,
        "slice": slice_name,
        "targetCommit": target_commit,
        "verifierVerdict": "AMEND",
        "verifierObjectiveBlocker": "working tree was dirty during stale verifier run",
        "currentReadback": rb,
        "classification": "stale-environment-amend-not-product-blocker",
        "action": "fresh verifier redispatch required; do not upgrade to L3 from this AMEND",
        "evidence": str(evidence_path),
    }


def l3_verdict_base(
    *,
    slice_name: str,
    target_commit: str,
    repo: Path,
    verifier_id: str,
    evidence_path: Path,
    loop_report_path: Path,
    resolves_stale_amend: str | None = None,
) -> dict[str, Any]:
    rb = git_readback(repo, target_commit)
    verifier = {"delegationId": verifier_id, "verdict": "APPROVE", "objectiveBlockers": []}
    if resolves_stale_amend:
        verifier["resolvesStaleAmend"] = resolves_stale_amend
    return {
        "generatedAt": utc_now(),
        "level": "L3-local-certified-packet",
        "slice": slice_name,
        "targetCommit": target_commit,
        "currentHead": rb["head"],
        "currentGitStatus": rb["status"],
        "currentHeadContainsTarget": rb.get("currentHeadContainsTarget"),
        "verifier": verifier,
        "evidence": {"smokeJson": str(evidence_path), "loopReport": str(loop_report_path)},
        "openBoundaries": [
            "no push",
            "no deploy",
            "no real device",
            "no authenticated account certification",
            "no PWA certification",
            "no production certification",
        ],
        "ok": True,
    }
