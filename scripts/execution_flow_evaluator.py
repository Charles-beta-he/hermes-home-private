#!/usr/bin/env python3
"""Read-only unified execution-flow evaluator for Hermes taskpool notes.

This is the MVP projection for the unified framework:
Taskpool owns truth; workflow owns order; Hermes owns action; harness owns proof;
verifier owns closeout; human gate owns permission.

It never mutates task files. It derives a workflow stage, safe next actions,
boundary class, and missing harness evidence from existing task frontmatter/body.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

DEFAULT_TASK_DIR = Path.home() / "Documents/brain/05-实践与项目/tasks"

STATUS_TO_STAGE = {
    "pending": "evidence",
    "ready": "evidence",
    "claimed": "execute",
    "running": "execute",
    "review": "review",
    "blocked": "human_gate",
    "retry": "evidence",
    "done": "done",
    "archived": "done",
}

STRUCTURED_EVIDENCE_PREFIXES = (
    "command:",
    "artifact:",
    "proof:",
    "file:",
    "classification:",
)

IMPLEMENTATION_HINTS = re.compile(
    r"(implement|fix|修复|实现|落地|UI|browser|frontend|backend|API|接口|页面|按钮|route|tab|modal|build|test|验证)",
    re.IGNORECASE,
)

UI_HINTS = re.compile(r"(UI|页面|浏览器|browser|frontend|H5|mobile|viewport|截图|tab|modal|按钮|表单)", re.IGNORECASE)
API_HINTS = re.compile(r"(API|接口|backend|后端|curl|read-?back|contract|数据库|持久)", re.IGNORECASE)
SIDE_EFFECT_HINTS = re.compile(r"(发布|push|deploy|write[- ]?back|发送|关闭任务|delete|删除|覆盖|生产|payment|付款|credential|secret|token)", re.IGNORECASE)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + len("\n---") :]
    fm: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_\-]+:\s*", line):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value in ("", "[]"):
                fm[key] = [] if value == "[]" else ""
            elif value.lower() in ("true", "false"):
                fm[key] = value.lower() == "true"
            else:
                fm[key] = value.strip('"\'')
        elif current_key and line.strip().startswith("-"):
            existing = fm.get(current_key)
            if not isinstance(existing, list):
                existing = []
            existing.append(line.strip()[1:].strip().strip('"\''))
            fm[current_key] = existing
    return fm, body


def evidence_entries(fm: dict[str, Any], body: str) -> list[str]:
    entries: list[str] = []
    raw = fm.get("evidence")
    if isinstance(raw, list):
        entries.extend(str(x) for x in raw)
    elif isinstance(raw, str) and raw:
        entries.append(raw)
    for line in body.splitlines():
        s = line.strip().lstrip("-*").strip()
        if s.startswith(STRUCTURED_EVIDENCE_PREFIXES):
            entries.append(s)
    return entries


def has_any(entries: list[str], terms: tuple[str, ...]) -> bool:
    lowered = "\n".join(entries).lower()
    return any(term in lowered for term in terms)


@dataclass
class FlowEvaluation:
    task_id: str
    title: str
    status: str
    workflow_stage: str
    lane: str | None
    priority: str | None
    boundary_class: str
    allowed_to_continue: bool
    safe_actions: list[str]
    blocked_actions: list[str]
    missing_evidence: list[str]
    harness_spec: dict[str, Any]
    closeout_ready: bool
    reasons: list[str]
    path: str


def evaluate(path: Path) -> FlowEvaluation:
    text = path.read_text(errors="replace")
    fm, body = parse_frontmatter(text)
    title = str(fm.get("title") or path.stem)
    task_id = str(fm.get("id") or path.stem)
    status = str(fm.get("status") or "unknown")
    lane = str(fm.get("lane")) if fm.get("lane") else None
    priority = str(fm.get("priority") or fm.get("priority_layer") or "") or None
    stage = str(fm.get("workflow_stage") or STATUS_TO_STAGE.get(status, "evidence"))
    combined = "\n".join([title, body, json.dumps(fm, ensure_ascii=False)])
    entries = evidence_entries(fm, body)

    is_impl = bool(IMPLEMENTATION_HINTS.search(combined)) or lane == "work"
    needs_ui = bool(UI_HINTS.search(combined))
    needs_api = bool(API_HINTS.search(combined))
    has_side_effect = bool(SIDE_EFFECT_HINTS.search(combined)) or bool(fm.get("external_side_effects"))

    missing: list[str] = []
    if is_impl and not has_any(entries, ("command:", "artifact:", "proof:")):
        missing.append("feature_specific_structured_evidence")
    if needs_ui and not has_any(entries, ("proof:browser", "screenshot", "playwright", "browser")):
        missing.append("browser_or_ui_surface_proof")
    if needs_api and not has_any(entries, ("proof:api", "curl", "readback", "read-back")):
        missing.append("api_or_backend_readback_proof")
    if status == "review" and is_impl and not has_any(entries, ("command:",)):
        missing.append("command_proof_for_review_closeout")

    boundary = "none"
    blocked_actions: list[str] = []
    safe_actions: list[str] = []
    reasons: list[str] = []

    if status == "blocked":
        boundary = "evidence"
        blocked_actions.append("lifecycle_done_transition")
        safe_actions.extend(["read task evidence", "derive missing proof", "prepare human gate packet"])
        reasons.append("status_blocked")
    elif has_side_effect and stage in {"writeback", "review", "done"}:
        boundary = "external_side_effect"
        blocked_actions.append("external_writeback_without_authority_gate")
        safe_actions.extend(["prepare writeback intent", "prepare rollback plan", "run read-only verification"])
        reasons.append("side_effect_requires_gate")
    elif missing:
        boundary = "evidence"
        blocked_actions.append("done_closeout")
        safe_actions.extend(["run missing harness checks", "collect structured evidence", "update proof log"])
        reasons.append("missing_required_evidence")
    else:
        safe_actions.append("advance to next workflow stage via taskpool lifecycle gate")

    if stage == "done":
        safe_actions = ["audit only; do not mutate unless false-positive evidence is found"]

    harness_spec = {
        "required": bool(is_impl or needs_ui or needs_api),
        "surfaces": [s for s, needed in (("ui", needs_ui), ("api", needs_api), ("command", is_impl)) if needed],
        "required_artifacts": [],
        "disallow": ["mock_acceptance_without_explicit_allowance"],
    }
    if is_impl:
        harness_spec["required_artifacts"].append("command_output")
    if needs_ui:
        harness_spec["required_artifacts"].extend(["screenshot", "console_log", "target_surface_anchor"])
    if needs_api:
        harness_spec["required_artifacts"].append("api_readback")

    closeout_ready = status in {"review", "done"} and not missing and boundary in {"none"}
    allowed = boundary == "none" and status not in {"done", "archived"}

    return FlowEvaluation(
        task_id=task_id,
        title=title,
        status=status,
        workflow_stage=stage,
        lane=lane,
        priority=priority,
        boundary_class=boundary,
        allowed_to_continue=allowed,
        safe_actions=safe_actions,
        blocked_actions=blocked_actions,
        missing_evidence=missing,
        harness_spec=harness_spec,
        closeout_ready=closeout_ready,
        reasons=reasons,
        path=str(path),
    )


def looks_like_task_note(path: Path) -> bool:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return False
    fm, _body = parse_frontmatter(text)
    status = str(fm.get("status") or "")
    return status in STATUS_TO_STAGE


def iter_task_files(task_dir: Path, limit: int | None) -> list[Path]:
    files = [p for p in task_dir.glob("*.md") if looks_like_task_note(p)]
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    if limit is not None:
        files = files[:limit]
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only unified execution-flow evaluator")
    parser.add_argument("--task-file", action="append", default=[], help="Specific task markdown file(s) to evaluate")
    parser.add_argument("--task-dir", default=os.environ.get("HERMES_TASK_DIR", str(DEFAULT_TASK_DIR)))
    parser.add_argument("--limit", type=int, default=5, help="Max recent tasks when --task-file is not provided")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    if args.task_file:
        paths = [Path(p).expanduser() for p in args.task_file]
    else:
        task_dir = Path(args.task_dir).expanduser()
        if not task_dir.exists():
            raise SystemExit(f"task dir not found: {task_dir}")
        paths = iter_task_files(task_dir, args.limit)

    evaluations = [evaluate(p) for p in paths if p.exists()]
    payload = {
        "status": "OK",
        "mode": "read_only",
        "framework": "unified_execution_flow",
        "summary": {
            "evaluated": len(evaluations),
            "blocked_or_missing_evidence": sum(1 for e in evaluations if e.boundary_class != "none"),
            "closeout_ready": sum(1 for e in evaluations if e.closeout_ready),
        },
        "evaluations": [asdict(e) for e in evaluations],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for e in evaluations:
            print(f"{e.task_id} [{e.status}/{e.workflow_stage}] boundary={e.boundary_class} closeout_ready={e.closeout_ready}")
            if e.missing_evidence:
                print("  missing:", ", ".join(e.missing_evidence))
            if e.safe_actions:
                print("  next:", "; ".join(e.safe_actions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
