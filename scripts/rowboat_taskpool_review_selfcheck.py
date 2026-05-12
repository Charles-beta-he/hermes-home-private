#!/usr/bin/env python3
"""Deterministic selfcheck for the Rowboat → Hermes taskpool review evidence pack.

No network, no model calls, no writes. This validates that the advisory pack is
Rowboat-specific, evidence-linked, and still bounded to selective Hermes-native
extraction rather than wholesale runtime adoption.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_MODELS = {"claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"}
REQUIRED_RECOMMENDATIONS = {"R-P0-1", "R-P0-2", "R-P1-1", "R-REJECT-1"}
REQUIRED_EVIDENCE = {
    "E-README-LOCAL",
    "E-AGENT-SCHEMA",
    "E-SCHEDULE-SCHEMA",
    "E-RUN-REPO",
    "E-RUNTIME-LOCK",
    "E-RUNTIME-PERMISSION",
    "E-AGENT-AS-TOOL",
    "E-LIVE-DOC",
    "E-LIVE-SCHEDULER",
    "E-LIVE-RUNNER",
    "E-LIVE-EVENTS",
    "E-LIVE-ROUTING",
    "E-FILELOCK",
    "E-README-TOOLS",
    "E-COMMAND-EXECUTOR",
    "E-MCP",
    "E-EXEC-TOOL",
    "E-LICENSE",
}
FORBIDDEN_DIRECT_ADOPTION = {
    "adopt_wholesale",
    "import_rowboat_runtime",
    "install_rowboat_runtime",
    "copy_rowboat_code",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("pack root must be object")
    return data


def git_head(repo: Path) -> str | None:
    if not repo.exists():
        return None
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def check_pack(pack: dict[str, Any], repo: Path | None = None) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []

    if pack.get("schema") not in {"rowboat_evidence_pack_v2", "rowboat_evidence_pack_v1"}:
        failures.append("schema_not_rowboat_evidence_pack")

    repo_info = pack.get("repo") or {}
    if repo_info.get("url") != "https://github.com/rowboatlabs/rowboat":
        failures.append("repo_url_not_rowboatlabs_rowboat")
    commit = str(repo_info.get("commit") or "")
    if len(commit) != 40:
        failures.append("repo_commit_not_pinned_sha")
    if repo:
        head = git_head(repo)
        if head and head != commit:
            warnings.append(f"repo_head_differs_from_pack:{head}!={commit}")

    evidence = pack.get("evidence") or []
    evidence_ids = {str(e.get("id")) for e in evidence if isinstance(e, dict)}
    missing_evidence = sorted(REQUIRED_EVIDENCE - evidence_ids)
    if missing_evidence:
        failures.append("missing_evidence_ids:" + ",".join(missing_evidence))

    for e in evidence:
        if not isinstance(e, dict):
            failures.append("evidence_entry_not_object")
            continue
        source = str(e.get("source") or "")
        if ":" not in source or not any(ch.isdigit() for ch in source.split(":")[-1]):
            failures.append(f"evidence_missing_line_ref:{e.get('id')}")
        if not e.get("supports"):
            failures.append(f"evidence_missing_supports:{e.get('id')}")

    claims = pack.get("claims") or []
    claim_ids = {str(c.get("id")) for c in claims if isinstance(c, dict)}
    if len(claim_ids) < 5:
        failures.append("too_few_claims")
    for c in claims:
        if not isinstance(c, dict):
            failures.append("claim_entry_not_object")
            continue
        refs = c.get("evidence") or []
        if not refs:
            failures.append(f"claim_missing_evidence:{c.get('id')}")
        for ref in refs:
            if ref not in evidence_ids:
                failures.append(f"claim_references_unknown_evidence:{c.get('id')}->{ref}")
        if int(c.get("severity") or 0) < 3:
            warnings.append(f"claim_low_severity:{c.get('id')}")

    recs = pack.get("recommendations") or []
    rec_ids = {str(r.get("id")) for r in recs if isinstance(r, dict)}
    missing_recs = sorted(REQUIRED_RECOMMENDATIONS - rec_ids)
    if missing_recs:
        failures.append("missing_recommendation_ids:" + ",".join(missing_recs))
    decisions_blob = json.dumps(recs, ensure_ascii=False).lower()
    for token in FORBIDDEN_DIRECT_ADOPTION:
        if token in decisions_blob:
            failures.append("forbidden_direct_adoption_token:" + token)
    if "reject_wholesale" not in decisions_blob:
        failures.append("missing_reject_wholesale_decision")
    if "spike" not in decisions_blob:
        failures.append("missing_spike_decision")

    verification = pack.get("verification") or {}
    if "multimodel" not in verification:
        failures.append("missing_multimodel_verification_boundary")
    elif "not yet" not in str(verification.get("multimodel", "")).lower() and "not run" not in str(verification.get("multimodel", "")).lower():
        warnings.append("multimodel_boundary_not_explicitly_advisory")

    remaining = "\n".join(map(str, pack.get("remaining_risks") or []))
    if "target-bound" not in remaining and "target_bound" not in remaining:
        failures.append("missing_target_bound_remaining_risk")

    ok = not failures
    return {
        "schema": "rowboat_taskpool_review_selfcheck_v1",
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "failures": failures,
        "warnings": warnings,
        "repo_commit": commit,
        "evidence_count": len(evidence_ids),
        "claim_count": len(claim_ids),
        "recommendation_count": len(rec_ids),
        "boundary": "deterministic advisory gate only; not a replacement for target-bound 4-model ratification",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        pack = load_json(args.pack)
        result = check_pack(pack, args.repo)
    except Exception as exc:
        result = {
            "schema": "rowboat_taskpool_review_selfcheck_v1",
            "ok": False,
            "status": "FAIL",
            "failures": [f"exception:{type(exc).__name__}:{exc}"],
            "warnings": [],
            "boundary": "deterministic advisory gate only",
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result["status"])
        for f in result.get("failures", []):
            print("FAIL", f)
        for w in result.get("warnings", []):
            print("WARN", w)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
