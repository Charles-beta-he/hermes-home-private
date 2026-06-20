#!/usr/bin/env python3
"""Read-only Vercel/eve-style file-as-architecture convention inspector.

This does not replace Hermes skills/project-profiles/AGENTS.md. It provides a
low-coupling adapter/harness for evaluating projects that expose an `agent/`
directory with `instructions.md`, tools, skills, channels, and schedules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CONVENTION_PATHS = {
    "instructions": "agent/instructions.md",
    "agent_config": "agent/agent.ts",
    "tools": "agent/tools",
    "skills": "agent/skills",
    "channels": "agent/channels",
    "schedules": "agent/schedules",
}


def inspect_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings: dict[str, Any] = {
        "schema": "file_arch_adapter_v1",
        "root": str(root),
        "convention": "vercel-eve-file-as-architecture",
        "read_only": True,
        "paths": {},
        "required": {"instructions": False},
        "optional_counts": {},
        "status": "unknown",
        "red_lines": {
            "does_not_replace_hermes_skills": True,
            "does_not_replace_project_profiles": True,
            "does_not_require_global_filename_gate": True,
        },
    }
    for key, rel in CONVENTION_PATHS.items():
        p = root / rel
        entry = {"relative": rel, "exists": p.exists(), "type": "dir" if p.is_dir() else "file" if p.is_file() else "missing"}
        if p.is_dir():
            entry["children"] = sorted(child.name for child in p.iterdir() if not child.name.startswith("."))
        findings["paths"][key] = entry
    findings["required"]["instructions"] = bool(findings["paths"]["instructions"]["exists"])
    for key in ("tools", "skills", "channels", "schedules"):
        entry = findings["paths"][key]
        findings["optional_counts"][key] = len(entry.get("children") or []) if entry.get("exists") else 0
    findings["status"] = "pass" if findings["required"]["instructions"] else "fail"
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = inspect_project(args.root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{result['status'].upper()} {result['convention']} root={result['root']}")
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
