#!/usr/bin/env python3
"""Self-check for the Hermes goal-calibration control plane landing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOME = Path.home() / ".hermes"
SKILL = HOME / "skills/software-development/goal-calibration/SKILL.md"
EVALS = HOME / "skills/software-development/goal-calibration/references/eval-cases.md"
SSOT = HOME / "docs/private/goal-calibration-control-plane-20260528.md"
ATOM = HOME / "experience-ratchet/atoms/hermes-agent-1f92f1efa412.json"

REQUIRED_SKILL_MARKERS = [
    "## Position in the Agent Flow",
    "## Task Contract",
    "## Prompt-Writing Tasks",
    "## Prototype and Reference Handling",
    "## Regression Evals",
    "Verify against the calibrated target",
]

REQUIRED_EVAL_MARKERS = [
    "下拉框对齐一下",
    "按原型把通知态补齐",
    "优化这个 prompt",
    "Negative / light-path cases",
    "Neighbor-skill boundaries",
]

REQUIRED_SSOT_MARKERS = [
    "Goal calibration is a fixed high-priority internal gate",
    "TaskContract",
    "Risk Policy",
    "Prototype Rule",
    "Prompt Rule",
    "Landing Zones",
]


def fail(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    raise SystemExit(1)


def require_file(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def require_markers(name: str, text: str, markers: list[str]) -> None:
    missing = [m for m in markers if m not in text]
    if missing:
        fail(f"{name} missing markers: {missing}")


def norm_snapshot_contains_key() -> tuple[bool, str | None]:
    proc = subprocess.run(
        ["hermes", "norms", "snapshot", "--scope", "runtime"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        fail(f"hermes norms snapshot failed: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    norms = data.get("norms", {})
    record = norms.get("goal-calibration-gate")
    return record is not None, (record or {}).get("content_hash")


def main() -> None:
    skill = require_file(SKILL)
    evals = require_file(EVALS)
    ssot = require_file(SSOT)
    require_markers("skill", skill, REQUIRED_SKILL_MARKERS)
    require_markers("evals", evals, REQUIRED_EVAL_MARKERS)
    require_markers("ssot", ssot, REQUIRED_SSOT_MARKERS)

    norm_ok, norm_hash = norm_snapshot_contains_key()
    if not norm_ok:
        fail("runtime norm goal-calibration-gate missing")

    atom_ok = ATOM.exists()
    atom_status = None
    if atom_ok:
        atom_data = json.loads(ATOM.read_text(encoding="utf-8"))
        atom_status = atom_data.get("status") or atom_data.get("state")

    print(json.dumps({
        "ok": True,
        "skill": str(SKILL),
        "evals": str(EVALS),
        "ssot": str(SSOT),
        "norm": {"key": "goal-calibration-gate", "content_hash": norm_hash},
        "experience_atom": {"path": str(ATOM), "exists": atom_ok, "status": atom_status},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
