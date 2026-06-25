#!/usr/bin/env python3
"""Dry-run parent evidence aggregation for taskpool auto-subtask trees.

This tool is intentionally read-only: it helps detect the "large parent split into
many child tasks, children done, parent still blocked" condition without changing
lifecycle state. Use the report as input for a governed resolver/ratification step.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

TERMINAL_STATUSES = {"done", "archived", "expired"}
CERTIFICATION_REASON_TOKENS = ("explicit_requires_multimodel", "loop_non_convergence", "truth_gate_contract")
TASK_DIR = Path("/Users/charles/Documents/brain/05-实践与项目/tasks")


class TaskNotFound(FileNotFoundError):
    """Raised when a requested task id is absent from the task directory."""


def _fallback_frontmatter_parse(fm_text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for raw in fm_text.splitlines():
        if not raw.strip() or raw.startswith(" ") or raw.startswith("-") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            try:
                parsed = yaml.safe_load(value)
                data[key.strip()] = parsed if isinstance(parsed, list) else value
            except Exception:
                data[key.strip()] = value
        else:
            data[key.strip()] = value
    return data


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    _, rest = text.split("---\n", 1)
    fm_text, body = rest.split("\n---", 1)
    try:
        data = yaml.safe_load(fm_text) or {}
    except Exception:
        data = _fallback_frontmatter_parse(fm_text)
    return (data if isinstance(data, dict) else {}), body.lstrip("\n")


def list_value(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def load_tasks(tasks_dir: Path) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for path in sorted(tasks_dir.glob("*.md")):
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        task_id = path.stem
        tasks[task_id] = {"id": task_id, "path": str(path), "fm": fm, "body": body}
    return tasks


def _child_ids(parent: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> list[str]:
    declared = list_value(parent["fm"].get("auto_subtask_children"))
    discovered = [task_id for task_id, task in tasks.items() if str(task["fm"].get("auto_subtask_parent") or "") == parent["id"]]
    return sorted(dict.fromkeys(declared + discovered))


def _axis(child: dict[str, Any]) -> str:
    return str(child["fm"].get("auto_subtask_axis") or "unknown")


def _status(task: dict[str, Any]) -> str:
    return str(task["fm"].get("status") or "")


def _stale_child_status_evidence(parent: dict[str, Any], children: list[dict[str, Any]]) -> list[dict[str, str]]:
    current = {child["id"]: _status(child) for child in children}
    stale: list[dict[str, str]] = []
    for evidence in list_value(parent["fm"].get("evidence")):
        match = re.search(r"proof:child-task:([^:]+):status:([^\s]+)", evidence)
        if not match:
            continue
        child_id, evidence_status = match.group(1), match.group(2)
        current_status = current.get(child_id)
        if current_status and evidence_status != current_status:
            stale.append({"child_id": child_id, "evidence_status": evidence_status, "current_status": current_status})
    return stale


def _remaining_gate_reasons(parent: dict[str, Any]) -> list[str]:
    reasons = list_value(parent["fm"].get("blocked_resolve_reasons")) + list_value(parent["fm"].get("multimodel_last_failures"))
    gate = str(parent["fm"].get("multimodel_last_gate_status") or "").upper()
    if gate and gate != "PASS":
        reasons.append(f"multimodel_gate:{gate}")
    return sorted(dict.fromkeys(reasons))


def _action(parent: dict[str, Any], ready: bool, children: list[dict[str, Any]], missing: list[str], reasons: list[str]) -> str:
    if not children and not missing:
        return "no_children_found"
    if not ready:
        return "keep_blocked_children_open"
    if any(token in " ".join(reasons) for token in CERTIFICATION_REASON_TOKENS):
        return "keep_blocked_certification_required"
    if _status(parent) == "blocked":
        return "reopen_for_parent_ratification"
    return "aggregate_only"


def core_bibliography() -> list[dict[str, str]]:
    return [
        {"title": "The Mythical Man-Month", "author": "Frederick P. Brooks Jr.", "argument": "coordination overhead grows nonlinearly with people and interfaces"},
        {"title": "The Goal", "author": "Eliyahu M. Goldratt", "argument": "optimize the system bottleneck, not local activity"},
        {"title": "Critical Chain", "author": "Eliyahu M. Goldratt", "argument": "shared resource contention and hidden buffers delay project flow"},
        {"title": "Managing the Design Factory", "author": "Donald G. Reinertsen", "argument": "limit WIP and expose blocked flow"},
        {"title": "The Principles of Product Development Flow", "author": "Donald G. Reinertsen", "argument": "small batches, queues, and economic WIP limits control latency"},
        {"title": "Design Structure Matrix Methods and Applications", "author": "Steven D. Eppinger and Tyson R. Browning", "argument": "dependency structure predicts iteration, rework, and coordination loops"},
        {"title": "Out of the Tar Pit", "author": "Ben Moseley and Peter Marks", "argument": "separate essential state/complexity from accidental control complexity"},
        {"title": "Team Topologies", "author": "Matthew Skelton and Manuel Pais", "argument": "cognitive load and team/API boundaries constrain sustainable flow"},
        {"title": "Site Reliability Engineering", "author": "Betsy Beyer et al.", "argument": "automation needs explicit SLOs, error budgets, and safe rollback"},
        {"title": "Accelerate", "author": "Nicole Forsgren, Jez Humble, and Gene Kim", "argument": "fast flow requires deployment safety, feedback loops, and low-friction recovery"},
    ]


def build_parent_report(task_id: str, tasks_dir: Path = TASK_DIR) -> dict[str, Any]:
    tasks = load_tasks(tasks_dir)
    if task_id not in tasks:
        raise TaskNotFound(task_id)
    parent = tasks[task_id]
    child_ids = _child_ids(parent, tasks)
    missing = [child_id for child_id in child_ids if child_id not in tasks]
    children = [tasks[child_id] for child_id in child_ids if child_id in tasks]
    open_children = [child["id"] for child in children if _status(child) not in TERMINAL_STATUSES]
    done_children = [child["id"] for child in children if _status(child) == "done"]
    ready = bool(child_ids) and not missing and not open_children and len(done_children) == len(child_ids)
    reasons = _remaining_gate_reasons(parent)
    axis_summary = {_axis(child): _status(child) for child in children}
    return {
        "schema": "taskpool_parent_evidence_aggregation_v1",
        "task_id": task_id,
        "parent_status": _status(parent),
        "ready_for_parent": ready,
        "action": _action(parent, ready, children, missing, reasons),
        "child_count": len(child_ids),
        "done_count": len(done_children),
        "open_children": open_children,
        "missing_children": missing,
        "axis_summary": axis_summary,
        "children": [{"id": child["id"], "status": _status(child), "axis": _axis(child), "path": child["path"]} for child in children],
        "stale_evidence": _stale_child_status_evidence(parent, children),
        "remaining_gate_reasons": reasons,
        "bibliography": core_bibliography(),
        "safety": "read-only aggregation; does not mutate parent lifecycle state",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run taskpool parent evidence aggregation")
    parser.add_argument("--task", required=True)
    parser.add_argument("--tasks-dir", default=str(TASK_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_parent_report(args.task, Path(args.tasks_dir))
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(text if args.json else text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
