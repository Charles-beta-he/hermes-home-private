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


SAFE_DECISION_OPTION_MAP = {
    "needs_more_evidence": {"decision": "needs_more_evidence", "label": "退回补证据", "resumeMode": "repair"},
    "hold": {"decision": "hold", "label": "暂停", "resumeMode": "hold"},
}


def decision_option(decision: str) -> dict[str, str]:
    return dict(SAFE_DECISION_OPTION_MAP[decision])


def derive_safe_decision_options(boundary_class: str, missing_evidence: list[str], workflow_stage: str) -> list[dict[str, str]]:
    if boundary_class == "none" and not missing_evidence:
        return []
    if boundary_class in {"permission", "external_side_effect", "destructive", "credential", "value_judgement", "safety_legal"}:
        return [decision_option("hold")]
    if boundary_class == "evidence" or missing_evidence:
        return [decision_option("needs_more_evidence")]
    if workflow_stage in {"human_gate", "writeback", "done"}:
        return [decision_option("hold")]
    return [decision_option("hold")]


def derive_auto_decision(options: list[dict[str, str]]) -> dict[str, str] | None:
    if len(options) != 1:
        return None
    return {**options[0], "reason": "single_safe_option"}


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
    safe_decision_options: list[dict[str, str]]
    auto_decision: dict[str, str] | None
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
    hint_fm = {k: v for k, v in fm.items() if k != "evidence"}
    combined = "\n".join([title, body, json.dumps(hint_fm, ensure_ascii=False)])
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

    if has_side_effect and stage in {"writeback", "review", "done", "human_gate"}:
        boundary = "external_side_effect"
        blocked_actions.append("external_writeback_without_authority_gate")
        safe_actions.extend(["prepare writeback intent", "prepare rollback plan", "run read-only verification"])
        reasons.append("side_effect_requires_gate")
    elif status == "blocked":
        boundary = "evidence"
        blocked_actions.append("lifecycle_done_transition")
        safe_actions.extend(["read task evidence", "derive missing proof", "prepare human gate packet"])
        reasons.append("status_blocked")
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
    safe_decision_options = derive_safe_decision_options(boundary, missing, stage)
    auto_decision = derive_auto_decision(safe_decision_options)

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
        safe_decision_options=safe_decision_options,
        auto_decision=auto_decision,
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


def build_enterprise_gate(evaluations: list[FlowEvaluation]) -> dict[str, Any]:
    blocked = [e for e in evaluations if e.boundary_class != "none"]
    missing = sorted({item for e in evaluations for item in e.missing_evidence})
    human_gates = [e for e in evaluations if e.workflow_stage == "human_gate" or e.boundary_class in {"permission", "external_side_effect", "destructive", "credential", "value_judgement", "safety_legal"}]
    reasons = sorted({reason for e in evaluations for reason in e.reasons})
    status = "PASS"
    if blocked or missing:
        status = "BLOCKED"
    return {
        "status": status,
        "policy": "read_only_projection_no_lifecycle_mutation",
        "blocked_count": len(blocked),
        "human_gate_count": len(human_gates),
        "missing_evidence": missing,
        "reasons": reasons,
        "authority_boundary": "no task transition, external writeback, publish, delete, credential, or production mutation is performed by this evaluator",
    }


def build_payload(evaluations: list[FlowEvaluation]) -> dict[str, Any]:
    gate = build_enterprise_gate(evaluations)
    blocked_or_missing = sum(
        1 for e in evaluations if e.boundary_class != "none" or bool(e.missing_evidence)
    )
    return {
        "schema_version": "execution-flow/v1",
        "status": "OK",
        "mode": "read_only",
        "framework": "unified_execution_flow",
        "contract": {
            "truth_owner": "taskpool",
            "order_owner": "workflow",
            "action_owner": "hermes_runner",
            "proof_owner": "harness",
            "closeout_owner": "verifier",
            "permission_owner": "human_gate",
        },
        "summary": {
            "evaluated": len(evaluations),
            "blocked_or_missing_evidence": blocked_or_missing,
            "closeout_ready": sum(1 for e in evaluations if e.closeout_ready),
        },
        "enterprise_gate": gate,
        "evaluations": [asdict(e) for e in evaluations],
    }


def render_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    gate = payload["enterprise_gate"]
    summary = payload["summary"]
    lines.append("# Unified Execution Flow Report")
    lines.append("")
    lines.append(f"- schema: {payload['schema_version']}")
    lines.append(f"- mode: {payload['mode']}")
    lines.append(f"- enterprise gate: {gate['status']}")
    lines.append(f"- evaluated: {summary['evaluated']}")
    lines.append(f"- closeout ready: {summary['closeout_ready']}")
    lines.append(f"- blocked or missing evidence: {summary['blocked_or_missing_evidence']}")
    lines.append("")
    lines.append("## Contract")
    for key, value in payload["contract"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Evaluations")
    for e in payload["evaluations"]:
        lines.append(f"- {e['task_id']} [{e['status']}/{e['workflow_stage']}] boundary={e['boundary_class']} closeout_ready={e['closeout_ready']}")
        if e["missing_evidence"]:
            lines.append(f"  - missing: {', '.join(e['missing_evidence'])}")
        if e["safe_actions"]:
            lines.append(f"  - safe actions: {'; '.join(e['safe_actions'])}")
        if e["blocked_actions"]:
            lines.append(f"  - blocked actions: {'; '.join(e['blocked_actions'])}")
    lines.append("")
    lines.append("## Human Gate / Intervention Packets")
    gated = [e for e in payload["evaluations"] if e["blocked_actions"] or e["boundary_class"] != "none"]
    if not gated:
        lines.append("- none")
    for e in gated:
        lines.append(f"- task: {e['task_id']}")
        lines.append(f"  - boundary_class: {e['boundary_class']}")
        lines.append(f"  - blocked_actions: {', '.join(e['blocked_actions']) or 'none'}")
        lines.append(f"  - safe_next: {'; '.join(e['safe_actions']) or 'none'}")
        lines.append("  - rollback_escape: preserve taskpool state; no mutation was performed by evaluator")
    lines.append("")
    lines.append("## Authority Boundary")
    lines.append(f"- {gate['authority_boundary']}")
    lines.append("")
    return "\n".join(lines)


def print_text_summary(evaluations: list[FlowEvaluation]) -> None:
    for e in evaluations:
        print(f"{e.task_id} [{e.status}/{e.workflow_stage}] boundary={e.boundary_class} closeout_ready={e.closeout_ready}")
        if e.missing_evidence:
            print("  missing:", ", ".join(e.missing_evidence))
        if e.safe_actions:
            print("  next:", "; ".join(e.safe_actions))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only unified execution-flow evaluator")
    parser.add_argument("--task-file", action="append", default=[], help="Specific task markdown file(s) to evaluate")
    parser.add_argument("--task-dir", default=os.environ.get("HERMES_TASK_DIR", str(DEFAULT_TASK_DIR)))
    parser.add_argument("--limit", type=int, default=5, help="Max recent tasks when --task-file is not provided")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--fail-on-blocked", action="store_true", help="Exit 2 when enterprise gate is BLOCKED")
    parser.add_argument("--report", help="Write a durable markdown report to this path")
    args = parser.parse_args()

    if args.task_file:
        paths = [Path(p).expanduser() for p in args.task_file]
    else:
        task_dir = Path(args.task_dir).expanduser()
        if not task_dir.exists():
            raise SystemExit(f"task dir not found: {task_dir}")
        paths = iter_task_files(task_dir, args.limit)

    evaluations = [evaluate(p) for p in paths if p.exists()]
    payload = build_payload(evaluations)

    if args.report:
        report_path = Path(args.report).expanduser()
        if not report_path.parent.exists():
            raise SystemExit(f"report parent dir not found: {report_path.parent}")
        report_path.write_text(render_report(payload), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text_summary(evaluations)

    if args.fail_on_blocked and payload["enterprise_gate"]["status"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
