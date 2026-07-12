#!/usr/bin/env python3
"""Proof debt migration planner for Hermes taskpool warnings.

Default mode is read-only. With --apply, this script only normalizes already
present evidence references into the structured evidence vocabulary; it does not
fabricate missing ratification artifacts, delete invalid hashes, or change task
lifecycle status.
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
INVALID_HASH_RE = re.compile(r"terminal invalid autorun proof hash debt in (?P<task>.+?): proof:sha256:(?P<sha>.+)$")

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
        return "candidate_reclassify_invalid_autorun_proof" if inspection.get("proof_hash_present") else "reviewed_legacy_hash_debt"
    if inspection.get("evidence_markers"):
        return "candidate_migratable_existing_evidence"
    return "reviewed_legacy_missing_structured_evidence"


def evidence_is_structured(value: Any) -> bool:
    text = str(value or "").strip()
    return text.startswith((
        "command:", "file:", "search:", "brainctl:", "url:", "artifact:", "proof:",
        "live_lark_snapshot:", "classification:", "child-task:", "child-axis:",
    ))


def normalize_ref(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text or evidence_is_structured(text):
        return value
    if text.startswith(("http://", "https://")):
        return f"url:{text}"
    expanded = Path(text).expanduser()
    if expanded.is_absolute():
        return f"artifact:{expanded}"
    return f"proof:{text}"


FRONTMATTER_REF_FIELDS = ("evidence", "evidence_refs", "handoff_artifacts", "proof_artifacts", "ratification_artifact")
QUOTED_REF_RE = re.compile(r"(?P<quote>[\"'])(?P<ref>(?:~|/|https?://)[^\"']+)(?P=quote)")
SCALAR_REF_RE = re.compile(r"^(?P<prefix>\s*(?:ratification_artifact):\s*)(?P<ref>(?!artifact:|proof:|url:|command:|file:|search:|brainctl:)[^\n#][^\n]*?)\s*$")
DASH_REF_RE = re.compile(r"^(?P<prefix>\s*-\s*)(?P<ref>(?:~|/|https?://)[^\n#]*?)\s*$")


def frontmatter_bounds(text: str) -> tuple[int, int] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    return 4, end


def normalize_ref_line_preserving(line: str, *, in_ref_list: bool = False) -> tuple[str, bool]:
    stripped = line.lstrip()
    field_line = any(stripped.startswith(f"{field}:") for field in FRONTMATTER_REF_FIELDS)
    if not field_line and not in_ref_list:
        return line, False
    changed = False

    def quoted_repl(match: re.Match[str]) -> str:
        nonlocal changed
        ref = match.group("ref")
        normalized = normalize_ref(ref)
        if normalized != ref:
            changed = True
        return f"{match.group('quote')}{normalized}{match.group('quote')}"

    new_line = QUOTED_REF_RE.sub(quoted_repl, line)
    scalar = SCALAR_REF_RE.match(new_line) if field_line else None
    if scalar:
        ref = scalar.group("ref").strip().strip('"\'')
        normalized = normalize_ref(ref)
        if normalized != ref:
            new_line = f"{scalar.group('prefix')}{normalized}"
            changed = True
    dash = DASH_REF_RE.match(new_line) if in_ref_list else None
    if dash:
        ref = dash.group("ref").strip().strip('"\'')
        normalized = normalize_ref(ref)
        if normalized != ref:
            new_line = f"{dash.group('prefix')}{normalized}"
            changed = True
    return new_line, changed


def normalize_task_frontmatter(path: Path, *, dry_run: bool = True) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    bounds = frontmatter_bounds(original)
    if bounds is None:
        return {"changed": False, "reason": "missing_or_invalid_frontmatter"}
    start, end = bounds
    frontmatter = original[start:end]
    lines = frontmatter.splitlines()
    changed_fields: set[str] = set()
    normalized_lines: list[str] = []
    current_ref_field = ""
    for line in lines:
        stripped = line.lstrip()
        if stripped and not line.startswith((" ", "\t", "-")):
            current_ref_field = ""
        if any(stripped.startswith(f"{field}:") for field in FRONTMATTER_REF_FIELDS):
            current_ref_field = stripped.split(":", 1)[0]
        in_ref_list = bool(current_ref_field and stripped.startswith("-"))
        new_line, changed = normalize_ref_line_preserving(line, in_ref_list=in_ref_list)
        if changed:
            field = current_ref_field or line.lstrip().split(":", 1)[0]
            changed_fields.add(field)
        normalized_lines.append(new_line)
    if not changed_fields:
        return {"changed": False, "reason": "no_normalizable_existing_refs"}
    rewritten = original[:start] + "\n".join(normalized_lines) + original[end:]
    if not dry_run:
        path.write_text(rewritten, encoding="utf-8")
    return {"changed": True, "changed_fields": sorted(changed_fields)}


def reclassify_invalid_autorun_proof(path: Path, proof_sha: str, *, dry_run: bool = True) -> dict[str, Any]:
    original = path.read_text(encoding="utf-8")
    bounds = frontmatter_bounds(original)
    if bounds is None:
        return {"changed": False, "reason": "missing_or_invalid_frontmatter"}
    start, end = bounds
    frontmatter = original[start:end]
    old = f"proof:sha256:{proof_sha}"
    new = f"classification:legacy_invalid_autorun_proof_hash={proof_sha}"
    lines = frontmatter.splitlines()
    replaced = 0
    rewritten_lines = []
    for line in lines:
        if line.strip() == f"- {old}":
            indent = line[: len(line) - len(line.lstrip())]
            rewritten_lines.append(f"{indent}- {new}")
            replaced += 1
        else:
            rewritten_lines.append(line)
    if replaced < 1:
        return {"changed": False, "reason": "exact_frontmatter_ref_not_found"}
    rewritten = original[:start] + "\n".join(rewritten_lines) + original[end:]
    if not dry_run:
        path.write_text(rewritten, encoding="utf-8")
    return {"changed": True, "changed_fields": ["evidence"], "reclassified_count": replaced}


def apply_plan(plan: dict[str, Any], *, dry_run: bool = True) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    seen_reclassifications: set[tuple[str, str]] = set()
    for item in plan.get("items", []):
        action = item.get("recommended_action")
        if action not in {"candidate_migratable_existing_evidence", "candidate_reclassify_invalid_autorun_proof"}:
            continue
        task_file = item.get("task_file")
        if not task_file:
            continue
        path = Path(str(task_file))
        if action == "candidate_reclassify_invalid_autorun_proof":
            key = (str(path), str(item.get("proof_sha") or ""))
            if key in seen_reclassifications:
                continue
            seen_reclassifications.add(key)
            result = reclassify_invalid_autorun_proof(path, key[1], dry_run=dry_run)
        else:
            result = normalize_task_frontmatter(path, dry_run=dry_run)
        results.append({
            "task": item.get("task"),
            "task_file": str(path),
            "dry_run": dry_run,
            **result,
        })
    counts = Counter("changed" if r.get("changed") else str(r.get("reason") or "unchanged") for r in results)
    return {
        "schema": "proof_debt_migration_apply_v1",
        "dry_run": dry_run,
        "attempted_count": len(results),
        "result_counts": dict(sorted(counts.items())),
        "results": results,
    }


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
    parser.add_argument("--apply", action="store_true", help="normalize existing refs in candidate task files")
    parser.add_argument("--apply-dry-run", action="store_true", help="show what --apply would change without writing")
    args = parser.parse_args()

    proof = run_proof_check()
    warnings = proof.get("warnings", []) if isinstance(proof, dict) else []
    plan = build_plan([str(w) for w in warnings], limit=max(0, args.limit))
    plan["proof_check_status"] = proof.get("status") if isinstance(proof, dict) else None
    plan["proof_checked_count"] = proof.get("checked_count") if isinstance(proof, dict) else None
    if args.apply or args.apply_dry_run:
        apply_report = apply_plan(plan, dry_run=not args.apply)
        plan["apply_report"] = apply_report
        plan["safety"] = (
            "apply mode only normalizes existing evidence refs; it does not fabricate artifacts, "
            "remove invalid hashes, or change lifecycle status"
        )
    print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
