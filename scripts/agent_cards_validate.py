#!/usr/bin/env python3
"""Validate Hermes Agent Cards against live profiles and active architecture domains.

Read-only validator. It does not mutate profiles, Kanban, brain notes, or runtime
routing. The goal is to ensure the explicit Agent Card layer covers the live
self-architecture surface and the Google-style component checklist.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

HOME = Path.home()
CARDS_PATH = HOME / ".hermes" / "docs" / "private" / "agent-cards-v1.json"
TASKS_DIR = HOME / "Documents" / "brain" / "05-实践与项目" / "tasks"
PROFILES_DIR = HOME / ".hermes" / "profiles"
ACTIVE_STATUSES = {"pending", "ready", "claimed", "running", "review", "blocked", "retry"}
REQUIRED_CARD_FIELDS = [
    "goal",
    "role",
    "observation",
    "memory",
    "planning",
    "tools",
    "actions",
    "policy",
    "evaluation",
    "collaboration",
    "escalation",
]
REQUIRED_TASK_FIELDS = [
    "lane",
    "layer",
    "project",
    "architecture_target",
    "completion_gate",
    "iceberg_tier",
    "iceberg_scope",
    "iceberg_confidence",
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _frontmatter(text: str) -> Dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: Dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def _active_tasks() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not TASKS_DIR.exists():
        return rows
    for path in TASKS_DIR.glob("*.md"):
        data = _frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        if data.get("status") in ACTIVE_STATUSES:
            row = {field: data.get(field, "") for field in REQUIRED_TASK_FIELDS}
            row.update({"file": path.name, "status": data.get("status", "")})
            rows.append(row)
    return rows


def _profile_dirs() -> List[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(path.name for path in PROFILES_DIR.iterdir() if path.is_dir())


def _kanban_assignees() -> List[str]:
    try:
        proc = subprocess.run(
            ["hermes", "kanban", "assignees", "--json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            return []
        payload = json.loads(proc.stdout)
    except Exception:
        return []
    return sorted(item.get("name") for item in payload if item.get("name"))


def _missing_card_fields(cards: Mapping[str, Mapping[str, Any]]) -> Dict[str, List[str]]:
    missing: Dict[str, List[str]] = {}
    for name, card in cards.items():
        gaps = [field for field in REQUIRED_CARD_FIELDS if not card.get(field)]
        if gaps:
            missing[name] = gaps
    return missing


def validate(cards_path: Path = CARDS_PATH) -> Dict[str, Any]:
    cards = _load_json(cards_path)
    runtime_cards = cards.get("runtime_profiles", {})
    domain_cards = cards.get("architecture_domains", {})
    active_tasks = _active_tasks()
    active_scopes = Counter(task.get("iceberg_scope", "") for task in active_tasks)
    active_scope_names = sorted(scope for scope in active_scopes if scope)
    task_missing = [
        {"file": task["file"], "missing": [field for field in REQUIRED_TASK_FIELDS if not task.get(field)]}
        for task in active_tasks
        if any(not task.get(field) for field in REQUIRED_TASK_FIELDS)
    ]

    profile_dirs = _profile_dirs()
    kanban_assignees = _kanban_assignees()
    profile_surface = sorted(set(profile_dirs) | set(kanban_assignees))

    missing_runtime_cards = [name for name in profile_surface if name not in runtime_cards]
    missing_domain_cards = [scope for scope in active_scope_names if scope not in domain_cards]
    unexpected_domain_cards = [name for name in sorted(domain_cards) if name not in active_scope_names]
    runtime_field_gaps = _missing_card_fields(runtime_cards)
    domain_field_gaps = _missing_card_fields(domain_cards)

    status = "PASS"
    failures: List[str] = []
    if task_missing:
        status = "FAIL"
        failures.append("active_tasks_missing_classification")
    if missing_runtime_cards:
        status = "FAIL"
        failures.append("missing_runtime_cards")
    if missing_domain_cards:
        status = "FAIL"
        failures.append("missing_domain_cards")
    if runtime_field_gaps or domain_field_gaps:
        status = "FAIL"
        failures.append("agent_cards_missing_required_google_components")

    return {
        "status": status,
        "failures": failures,
        "cards_path": str(cards_path),
        "active_task_count": len(active_tasks),
        "active_scope_counts": dict(active_scopes),
        "task_missing_classification": task_missing,
        "profile_dirs": profile_dirs,
        "kanban_assignees": kanban_assignees,
        "missing_runtime_cards": missing_runtime_cards,
        "missing_domain_cards": missing_domain_cards,
        "unexpected_domain_cards": unexpected_domain_cards,
        "runtime_field_gaps": runtime_field_gaps,
        "domain_field_gaps": domain_field_gaps,
        "boundary": cards.get("current_runtime_boundary", {}),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Hermes Agent Cards coverage.")
    parser.add_argument("--cards", default=str(CARDS_PATH), help="Path to agent-cards-v1.json")
    parser.add_argument("--json", action="store_true", help="Emit full JSON payload")
    args = parser.parse_args(list(argv) if argv is not None else None)

    result = validate(Path(args.cards))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Agent card validation: {result['status']}")
        print(f"active_task_count={result['active_task_count']}")
        print(f"active_scopes={json.dumps(result['active_scope_counts'], ensure_ascii=False)}")
        if result["failures"]:
            print("failures=" + ",".join(result["failures"]))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
