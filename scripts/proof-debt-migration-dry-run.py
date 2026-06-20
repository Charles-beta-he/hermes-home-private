#!/usr/bin/env python3
"""Read-only proof debt migration planner for Hermes taskpool warnings.

This script does not rewrite task notes or proof hashes. It converts proof-check
warnings into a small migration plan so historical proof debt can be reviewed in
batches without fabricating evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

TASKS_DIR = Path.home() / "Documents" / "brain" / "05-实践与项目" / "tasks"
ORCHESTRATOR = Path.home() / ".hermes" / "scripts" / "brain_task_orchestrator.py"

MISSION_RE = re.compile(r"terminal mission envelope debt: mission envelope missing (?P<fields>\[[^\]]*\]): (?P<task>.+)$")
INVALID_HASH_RE = re.compile(r"terminal invalid autorun proof hash debt in (?P<task>.+?): proof:sha256:(?P<sha>[A-Za-z0-9_.-]+)$")

EVIDENCE_MARKERS = (
    "## Proof Log",
    "## Final Handoff",
    "evidence_refs:",
    "artifact:",
    "command:",
    "brainctl:",
    "file:",
    "url:",
    "proof:sha256:",
)


def run_proof_check() -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(ORCHESTRATOR), "proof-check", "--json"],
        text=True,
        capture_output=True,
        timeout=180,
    )
    if proc.returncode != 0:
        return {"status": "ERROR", "returncode": proc.returncode, "stderr_tail": proc.stderr[-1000:], "stdout_tail": proc.stdout[-1000:]}
    return json.loads(proc.stdout or "{}")


def parse_warning(text: str) -> dict[str, Any]:
    mission = MISSION_RE.match(text)
    if mission:
        return {
            "category": "terminal_mission_envelope_debt",
            "task": mission.group("task").strip(),
            "missing_fields": mission.group("fields"),
            "raw": text,
        }
    invalid = INVALID_HASH_RE.match(text)
    if invalid:
        return {
            "category": "terminal_invalid_autorun_proof_hash_debt",
            "task": invalid.group("task").strip(),
            "proof_sha": invalid.group("sha"),
            "raw": text,
        }
    return {"category": "other", "raw": text}


def task_file_for(task: str, tasks_dir: Path = TASKS_DIR) -> Path | None:
    direct = tasks_dir / f"{task}.md"
    if direct.exists():
        return direct
    matches = sorted(tasks_dir.glob(f"{task[:80]}*.md")) if task else []
    return matches[0] if matches else None


def inspect_task_file(path: Path | None, proof_sha: str = "") -> dict[str, Any]:
    if path is None:
        return {"task_file_exists": False, "evidence_markers": [], "proof_hash_present": False}
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return {"task_file_exists": True, "task_file": str(path), "read_error": True, "evidence_markers": [], "proof_hash_present": False}
    markers = [m for m in EVIDENCE_MARKERS if m in body]
    return {
        "task_file_exists": True,
        "task_file": str(path),
        "evidence_markers": markers,
        "proof_hash_present": bool(proof_sha and proof_sha in body),
    }


def classify_plan_item(parsed: dict[str, Any], inspection: dict[str, Any]) -> str:
    if parsed.get("category") == "other":
        return "unclassified_warning"
    if not inspection.get("task_file_exists"):
        return "task_file_missing"
    if parsed.get("category") == "terminal_invalid_autorun_proof_hash_debt":
        return "needs_source_artifact" if inspection.get("proof_hash_present") else "reviewed_legacy_hash_debt"
    if inspection.get("evidence_markers"):
        return "candidate_migratable_existing_evidence"
    return "reviewed_legacy_missing_structured_evidence"


def build_plan(warnings: list[str], *, limit: int = 50, tasks_dir: Path = TASKS_DIR) -> dict[str, Any]:
    items = []
    for warning in warnings[:limit]:
        parsed = parse_warning(str(warning))
        task = str(parsed.get("task") or "")
        path = task_file_for(task, tasks_dir=tasks_dir) if task else None
        inspection = inspect_task_file(path, str(parsed.get("proof_sha") or ""))
        action = classify_plan_item(parsed, inspection)
        items.append({**parsed, **inspection, "recommended_action": action})
    counts = Counter(item["recommended_action"] for item in items)
    categories = Counter(item["category"] for item in items)
    return {
        "schema": "proof_debt_migration_dry_run_v1",
        "safety": "read-only; no task files, proof hashes, evidence artifacts, or lifecycle state are modified",
        "input_warning_count": len(warnings),
        "planned_count": len(items),
        "action_counts": dict(sorted(counts.items())),
        "category_counts": dict(sorted(categories.items())),
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50, help="max warnings to include in detailed plan")
    args = parser.parse_args()

    proof = run_proof_check()
    warnings = proof.get("warnings", []) if isinstance(proof, dict) else []
    plan = build_plan([str(w) for w in warnings], limit=max(0, args.limit))
    plan["proof_check_status"] = proof.get("status") if isinstance(proof, dict) else None
    plan["proof_checked_count"] = proof.get("checked_count") if isinstance(proof, dict) else None
    print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
