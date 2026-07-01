#!/usr/bin/env python3
"""Hermes project setup/profile bootstrap dry-run planner.

Creates a no-overwrite bootstrap plan for a Hermes-managed project: project
profile, domain glossary, taskpool conventions, docs/SSOT layout, validation
commands, and red lines. Default mode is dry-run and only writes a receipt under
~/.hermes/docs/private/project-bootstrap/. Use --apply only for explicit local
file creation in a chosen output root; it still refuses to overwrite files.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_RECEIPT_DIR = Path.home() / ".hermes" / "docs" / "private" / "project-bootstrap"
DEFAULT_PROFILE_DIR = Path.home() / ".hermes" / "project-profiles"


@dataclass
class PlannedFile:
    path: str
    action: str
    exists: bool
    kind: str
    content: str


def slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80] or "project"


def profile_content(project_id: str, title: str, docs_root: str, validation_commands: list[str], red_lines: list[str]) -> str:
    data = {
        "schema_version": "hermes_project_profile_v1",
        "project_id": project_id,
        "title": title,
        "status": "bootstrap-dry-run-ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "docs_root": docs_root,
        "taskpool": {
            "default_lane": "evolution",
            "priority_policy": "P1 for governance/control-plane; P2 for evaluators/adapters; P3 for speculative research",
            "required_fields": ["objective", "acceptance_evidence", "red_lines", "non_goals", "source_refs"],
        },
        "domain_language": {
            "canonical_terms": [],
            "avoided_terms": [],
            "relationships": [],
            "flagged_ambiguities": [],
        },
        "validation_commands": validation_commands,
        "red_lines": red_lines,
        "authority_boundaries": [
            "no credential entry by agent",
            "no external dispatch/publish/deploy/destructive action without exact target + rollback + readback",
            "no taskpool done/certified claim without lifecycle/certification evidence",
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def glossary_content(title: str) -> str:
    return f"""# {title} Domain Glossary

Status: bootstrap template

## Canonical Terms

| Term | Definition | Avoid |
|---|---|---|
| TODO | Fill from project source docs and user language. | vague synonyms |

## Relationships

- TODO: object A owns object B / adapter X projects to surface Y.

## Flagged Ambiguities

- TODO: terms that were used inconsistently and the chosen resolution.

## Update Rule

Update this file when a durable project term, red line, or ambiguity is resolved. Do not store transient task progress here.
"""


def task_template_content(title: str) -> str:
    return f"""---
type: task
lane: evolution
status: pending
priority: P2
project: {slugify(title)}
source_refs: []
acceptance_evidence: ""
red_lines: []
non_goals: []
vertical_slice_boundary: ""
first_tracer_bullet: ""
blocked_by: []
afkhitl_boundary: ""
---

# Task — <title>

## Objective

## Acceptance Criteria

- [ ] Evidence-backed acceptance item.

## Verification

| Check | Command / Evidence | Result |
|---|---|---|
| deterministic gate | TODO | pending |

## Handoff

- Status:
- Evidence:
- Residual risk:
"""


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    project_id = slugify(args.title)
    docs_root = str(Path(args.docs_root).expanduser()) if args.docs_root else str(Path.home() / ".hermes" / "docs" / "private" / project_id)
    profile_path = Path(args.profile_dir).expanduser() / f"{project_id}.json"
    output_root = Path(args.output_root).expanduser() if args.output_root else Path(docs_root)
    validation_commands = args.validation_command or ["git status --short", "git diff --check", "pytest -q"]
    red_lines = args.red_line or [
        "Do not remove existing functionality without explicit approval.",
        "Do not store secrets or credentials in project docs/profile.",
        "Do not claim done without fresh verification evidence.",
    ]
    planned = [
        PlannedFile(str(profile_path), "create_no_overwrite", profile_path.exists(), "project_profile", profile_content(project_id, args.title, docs_root, validation_commands, red_lines)),
        PlannedFile(str(output_root / "README.md"), "create_no_overwrite", (output_root / "README.md").exists(), "project_readme", f"# {args.title}\n\nHermes project SSOT root.\n\n- Profile: `{profile_path}`\n- Domain glossary: `domain-glossary.md`\n- Task template: `task-template.md`\n"),
        PlannedFile(str(output_root / "domain-glossary.md"), "create_no_overwrite", (output_root / "domain-glossary.md").exists(), "domain_glossary", glossary_content(args.title)),
        PlannedFile(str(output_root / "task-template.md"), "create_no_overwrite", (output_root / "task-template.md").exists(), "task_template", task_template_content(args.title)),
        PlannedFile(str(output_root / "validation.md"), "create_no_overwrite", (output_root / "validation.md").exists(), "validation", "# Validation Commands\n\n" + "\n".join(f"- `{c}`" for c in validation_commands) + "\n"),
    ]
    conflicts = [p for p in planned if p.exists]
    return {
        "ok": not conflicts,
        "mode": "apply" if args.apply else "dry-run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "title": args.title,
        "docs_root": docs_root,
        "planned_files": [asdict(p) for p in planned],
        "conflicts": [asdict(p) for p in conflicts],
        "red_lines": red_lines,
        "validation_commands": validation_commands,
    }


def apply_plan(plan: dict[str, Any]) -> None:
    if plan["conflicts"]:
        raise SystemExit("Refusing to apply: target files already exist")
    for p in plan["planned_files"]:
        path = Path(p["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        # x mode enforces no-overwrite even if a race creates the file.
        with path.open("x", encoding="utf-8") as f:
            f.write(p["content"])


def write_receipt(plan: dict[str, Any], receipt_dir: Path) -> dict[str, str]:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = receipt_dir / f"project-bootstrap-{plan['project_id']}-{stamp}.json"
    md_path = receipt_dir / f"project-bootstrap-{plan['project_id']}-{stamp}.md"
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        f"# Project Bootstrap Plan — {plan['title']}",
        "",
        f"Generated: {plan['generated_at']}",
        f"Mode: {plan['mode']}",
        f"Status: {'OK' if plan['ok'] else 'CONFLICTS'}",
        "",
        "## Planned files",
        "",
    ]
    for p in plan["planned_files"]:
        lines.append(f"- `{p['path']}` — {p['kind']} — exists={p['exists']} — action={p['action']}")
    if plan["conflicts"]:
        lines += ["", "## Conflicts", ""]
        for p in plan["conflicts"]:
            lines.append(f"- `{p['path']}`")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def selftest() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        ns = argparse.Namespace(
            title="Temp Bootstrap Project",
            docs_root=str(root / "docs"),
            profile_dir=str(root / "profiles"),
            output_root=str(root / "docs"),
            validation_command=["python -m pytest -q"],
            red_line=["no secrets"],
            apply=False,
        )
        plan = build_plan(ns)
        assert plan["ok"] is True
        assert len(plan["planned_files"]) == 5
        ns.apply = True
        plan_apply = build_plan(ns)
        apply_plan(plan_apply)
        plan_conflict = build_plan(ns)
        assert plan_conflict["ok"] is False
        return {"ok": True, "created": len(plan_apply["planned_files"]), "conflicts_after_apply": len(plan_conflict["conflicts"])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--title", default="Hermes Example Project")
    ap.add_argument("--docs-root", default="")
    ap.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR))
    ap.add_argument("--output-root", default="")
    ap.add_argument("--validation-command", action="append")
    ap.add_argument("--red-line", action="append")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--write-receipt", action="store_true")
    ap.add_argument("--receipt-dir", default=str(DEFAULT_RECEIPT_DIR))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        result = selftest()
    else:
        result = build_plan(args)
        if args.apply:
            apply_plan(result)
            result["applied"] = True
        if args.write_receipt:
            result["receipt"] = write_receipt(result, Path(args.receipt_dir).expanduser())
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
