#!/usr/bin/env python3
"""Local-first self-check for the Resumable Multi-Model Certification System landing.

This verifies deterministic project/brain artifacts and the explicit deferred status of
TaskCreate -> next-round ralph. It does not certify implementation readiness.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

PROJECT = "resumable-multimodel-certification"
DEFER_MARKER = "TASKCREATE_RALPH_DEFERRED_UNTIL_RESUMABLE_CERT_READY"

REQUIRED_FILES = [
    "05-实践与项目/projects/resumable-multimodel-certification/Project - Resumable Multi-Model Certification.md",
    "05-实践与项目/projects/resumable-multimodel-certification/P10 - Long-term Strategy.md",
    "05-实践与项目/projects/resumable-multimodel-certification/P9 - Implementation Backlog.md",
    "05-实践与项目/实践方案/10-可恢复多模型认证系统Playbook.md",
    "06-治理与评审/reviews/2026-05-07-resumable-multimodel-certification-multimodel-selfcheck.md",
    "05-实践与项目/tasks/2026-05-07-resumable-multimodel-certification-landing-log.md",
    "06-治理与评审/进化日志/2026-05-07-可恢复多模型认证系统长期目标落地.md",
    "99-hermes-notes/evolution/2026-05-07-resumable-multimodel-certification.md",
]

REQUIRED_INDEXES = [
    "05-实践与项目/projects/00-projects索引.md",
    "05-实践与项目/实践方案/00-实践方案索引.md",
    "05-实践与项目/tasks/00-tasks索引.md",
    "06-治理与评审/reviews/00-reviews索引.md",
    "06-治理与评审/进化日志/00-进化日志索引.md",
]

REQUIRED_TERMS = {
    "project": [
        "Resumable Multi-Model Certification",
        "discussion_result.json",
        "certification_manifest.json",
        DEFER_MARKER,
    ],
    "p10": [
        "Discussion is a resumable state machine",
        "audit-certification",
        "resume-discussion",
        "TaskCreate -> ralph",
    ],
    "p9": [
        "RMCS-P0-001",
        "RMCS-P1-003",
        "DEFERRED-TASKCREATE-RALPH",
    ],
    "playbook": [
        "Certification Rule",
        "Fail-closed Rule",
        "TaskCreate -> ralph Policy",
    ],
    "review": [
        "consensus verdict: dissent",
        "not full certification",
        "TaskCreate -> ralph before RMCS",
    ],
}

FILE_BY_KEY = {
    "project": REQUIRED_FILES[0],
    "p10": REQUIRED_FILES[1],
    "p9": REQUIRED_FILES[2],
    "playbook": REQUIRED_FILES[3],
    "review": REQUIRED_FILES[4],
}


def vault_root() -> Path:
    return Path(os.environ.get("HERMES_BRAIN_VAULT") or os.environ.get("OBSIDIAN_VAULT_PATH") or Path.home() / "Documents/brain")


def run_check(root: Path | None = None) -> dict:
    root = root or vault_root()
    missing_files = [f for f in REQUIRED_FILES if not (root / f).exists()]
    missing_indexes = [f for f in REQUIRED_INDEXES if not (root / f).exists()]

    missing_terms: dict[str, list[str]] = {}
    for key, terms in REQUIRED_TERMS.items():
        rel = FILE_BY_KEY[key]
        p = root / rel
        text = p.read_text(encoding="utf-8") if p.exists() else ""
        misses = [t for t in terms if t not in text]
        if misses:
            missing_terms[rel] = misses

    index_missing_links: dict[str, str] = {}
    for rel in REQUIRED_INDEXES:
        p = root / rel
        text = p.read_text(encoding="utf-8") if p.exists() else ""
        if PROJECT not in text and "可恢复多模型认证系统" not in text:
            index_missing_links[rel] = "project link missing"

    secret_patterns = ["api_key", "password", "Authorization: Bearer", "connection string", "BEGIN PRIVATE KEY"]
    allowed_policy_phrases = ["不记录", "不保存", "如出现", "统一写", "Non-goals"]
    secret_hits = []
    for rel in REQUIRED_FILES:
        p = root / rel
        lines = (p.read_text(encoding="utf-8") if p.exists() else "").splitlines()
        for line_no, line in enumerate(lines, start=1):
            if any(policy in line for policy in allowed_policy_phrases):
                continue
            for pat in secret_patterns:
                if pat in line and "[REDACTED]" not in line:
                    secret_hits.append({"file": rel, "line": line_no, "pattern": pat})

    project_text = (root / REQUIRED_FILES[0]).read_text(encoding="utf-8") if (root / REQUIRED_FILES[0]).exists() else ""
    deferred_ok = DEFER_MARKER in project_text and "TaskCreate -> 下一轮 ralph" in project_text

    tick = Path.home() / ".hermes/tick-20260507-031812/merged_plan.json"
    tick_exists = tick.exists()
    tick_summary = {}
    if tick_exists:
        try:
            merged = json.loads(tick.read_text(encoding="utf-8"))
            tick_summary = {
                "consensus_verdict": merged.get("merge_info", {}).get("consensus_verdict"),
                "consensus_score": merged.get("merge_info", {}).get("consensus_score"),
                "source_plans": merged.get("meta", {}).get("source_plans"),
            }
        except Exception as e:  # noqa: BLE001 - selfcheck reports deterministic error text
            tick_summary = {"error": str(e)}

    fail_reasons = []
    if missing_files:
        fail_reasons.append("missing_files")
    if missing_indexes:
        fail_reasons.append("missing_indexes")
    if missing_terms:
        fail_reasons.append("missing_terms")
    if index_missing_links:
        fail_reasons.append("index_missing_links")
    if secret_hits:
        fail_reasons.append("secret_hits")
    if not deferred_ok:
        fail_reasons.append("taskcreate_deferred_marker")

    result = {
        "status": "FAIL" if fail_reasons else "PASS",
        "project": PROJECT,
        "vault": str(root),
        "required_files_count": len(REQUIRED_FILES),
        "missing_files": missing_files,
        "missing_indexes": missing_indexes,
        "missing_terms": missing_terms,
        "index_missing_links": index_missing_links,
        "taskcreate_ralph_deferred": deferred_ok,
        "defer_marker": DEFER_MARKER,
        "source_tick_exists": tick_exists,
        "source_tick_summary": tick_summary,
        "secret_hits": secret_hits,
        "fail_reasons": fail_reasons,
        "certification_note": "This self-check verifies local-brain landing only; no discussion_result means the prior fanout remains not fully certified.",
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = run_check()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"RMCS self-check: {result['status']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
