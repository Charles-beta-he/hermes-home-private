#!/usr/bin/env python3
"""Theory-to-impact propagation ratchet for Hermes architecture evolution.

This verifier makes the architecture rule machine-checkable:
when one slice is optimized under a theory/principle, the same-theory targets and
all impacted architecture layers must be discovered, planned, smoothed, and
verified. Local-first: no network, no model calls, no writes unless explicitly
requested.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TZ = timezone(timedelta(hours=8))
HOME = Path.home()
VAULT = Path(os.environ.get("HERMES_BRAIN_VAULT", str(HOME / "Documents" / "brain"))).expanduser()

MATRIX_REL = Path("05-实践与项目/实践方案/08-理论到影响全架构传播矩阵.md")
ATOM_REL = Path("04-知识原子/atoms/theory-impact-propagation.md")

REQUIRED_THEORY_IDS = [
    "evidence-first",
    "ashby-variety",
    "feedback-stability",
    "double-loop-learning",
    "near-decomposability",
    "uncertainty-propagation",
    "communication-budget",
    "fail-closed-ratification",
]

REQUIRED_SURFACES = [
    "L0-trace",
    "L1-router",
    "L2-protocol",
    "L3-ensemble",
    "L4-taskpool-brain",
    "L5-consult-models",
    "LX-health-quota",
    "skills",
    "cron-gateway",
]

REQUIRED_COLUMNS = [
    "Theory ID",
    "Theory lever",
    "Optimized slice",
    "Same-theory propagation targets",
    "Impact surfaces",
    "Smoothing gate",
    "Verification",
]

FORBID_MARKERS = ["todo", "tbd", "missing", "uncovered", "待补", "未覆盖", "缺失"]
SMOOTHING_KEYWORDS = ["rollback", "regression", "evidence", "selfcheck", "health", "variance", "compat", "ratification", "diff", "stability"]
VERIFICATION_KEYWORDS = ["test", "pytest", "unittest", "py_compile", "selfcheck", "evidence-spine", "lifecycle", "proof", "ratchet", "dispatch", "autonomy"]
ATOM_REQUIRED_PHRASES = [
    "Theory Point ID",
    "Layer Impact Map",
    "Same-theory propagation",
    "Impact Smoothing",
    "two-phase",
    "fail-closed",
    "L0",
    "L5",
    "LX",
]


def iso() -> str:
    return datetime.now(TZ).replace(microsecond=0).isoformat()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_cell(cell: str) -> list[str]:
    parts = re.split(r"[,，;；、\n]+", cell)
    return [p.strip() for p in parts if p.strip()]


def normalize_header(cell: str) -> str:
    return re.sub(r"\s+", " ", cell.strip())


def parse_markdown_tables(text: str) -> list[list[dict[str, str]]]:
    """Parse simple GitHub-style markdown tables into row dictionaries."""
    tables: list[list[dict[str, str]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not (line.startswith("|") and line.endswith("|")):
            i += 1
            continue
        headers = [normalize_header(c) for c in line.strip("|").split("|")]
        if i + 1 >= len(lines) or not re.match(r"^\s*\|?\s*:?-{3,}:?", lines[i + 1]):
            i += 1
            continue
        rows: list[dict[str, str]] = []
        i += 2
        while i < len(lines):
            row_line = lines[i].strip()
            if not (row_line.startswith("|") and row_line.endswith("|")):
                break
            cells = [c.strip() for c in row_line.strip("|").split("|")]
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            i += 1
        tables.append(rows)
    return tables


def find_matrix_rows(text: str) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    for table in parse_markdown_tables(text):
        if not table:
            continue
        headers = set(table[0].keys())
        if all(col in headers for col in REQUIRED_COLUMNS):
            return table, errors
    errors.append("matrix_table_with_required_columns_missing")
    return [], errors


def bad_text(value: str) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in FORBID_MARKERS)


def check_row(row: dict[str, str]) -> list[dict[str, Any]]:
    theory = row.get("Theory ID", "").strip()
    checks: list[dict[str, Any]] = []
    for col in REQUIRED_COLUMNS:
        value = row.get(col, "").strip()
        checks.append({
            "name": f"row:{theory or 'unknown'}:column:{col}",
            "ok": bool(value) and not bad_text(value),
            "value": value,
        })

    targets = split_cell(row.get("Same-theory propagation targets", ""))
    checks.append({
        "name": f"row:{theory}:same_theory_targets_at_least_2",
        "ok": len(targets) >= 2,
        "value": targets,
    })

    surfaces = split_cell(row.get("Impact surfaces", ""))
    checks.append({
        "name": f"row:{theory}:impact_surfaces_at_least_3",
        "ok": len(surfaces) >= 3,
        "value": surfaces,
    })

    smoothing = row.get("Smoothing gate", "")
    smoothing_hits = [kw for kw in SMOOTHING_KEYWORDS if kw.lower() in smoothing.lower()]
    checks.append({
        "name": f"row:{theory}:smoothing_gate_has_operational_keywords",
        "ok": len(smoothing_hits) >= 2,
        "value": smoothing_hits,
    })

    verification = row.get("Verification", "")
    verification_hits = [kw for kw in VERIFICATION_KEYWORDS if kw.lower() in verification.lower()]
    checks.append({
        "name": f"row:{theory}:verification_has_tool_gate",
        "ok": len(verification_hits) >= 1,
        "value": verification_hits,
    })
    return checks


def evaluate(vault: Path = VAULT) -> dict[str, Any]:
    matrix_path = vault / MATRIX_REL
    atom_path = vault / ATOM_REL
    checks: list[dict[str, Any]] = []

    files = {"matrix": matrix_path, "atom": atom_path}
    texts: dict[str, str] = {}
    for name, path in files.items():
        exists = path.exists()
        checks.append({"name": f"file:{name}", "ok": exists, "path": str(path)})
        texts[name] = read(path) if exists else ""

    rows, parse_errors = find_matrix_rows(texts.get("matrix", ""))
    checks.append({"name": "matrix:required_table_parseable", "ok": not parse_errors and bool(rows), "value": parse_errors})
    theory_ids = [r.get("Theory ID", "").strip() for r in rows]
    checks.append({"name": "matrix:theory_ids_unique", "ok": len(theory_ids) == len(set(theory_ids)), "value": theory_ids})

    for theory in REQUIRED_THEORY_IDS:
        checks.append({"name": f"matrix:theory:{theory}", "ok": theory in theory_ids, "value": theory_ids})

    all_surfaces: set[str] = set()
    for row in rows:
        all_surfaces.update(split_cell(row.get("Impact surfaces", "")))
        checks.extend(check_row(row))

    for surface in REQUIRED_SURFACES:
        checks.append({"name": f"matrix:surface:{surface}", "ok": surface in all_surfaces, "value": sorted(all_surfaces)})

    atom = texts.get("atom", "")
    for phrase in ATOM_REQUIRED_PHRASES:
        checks.append({"name": f"atom:phrase:{phrase}", "ok": phrase in atom, "path": str(atom_path)})
    checks.append({
        "name": "atom:does_not_allow_local_patch_as_global_rule",
        "ok": "局部优化不能直接升级为全局规则" in atom or "local patch" in atom.lower(),
        "path": str(atom_path),
    })

    passed = [c for c in checks if c.get("ok")]
    failed = [c for c in checks if not c.get("ok")]
    report = {
        "schema": "architecture_theory_impact_ratchet_v1",
        "generated_at": iso(),
        "status": "PASS" if not failed else "FAIL",
        "vault": str(vault),
        "matrix_path": str(matrix_path),
        "atom_path": str(atom_path),
        "coverage": {
            "theories": {"covered": sum(1 for t in REQUIRED_THEORY_IDS if t in theory_ids), "total": len(REQUIRED_THEORY_IDS)},
            "surfaces": {"covered": sum(1 for s in REQUIRED_SURFACES if s in all_surfaces), "total": len(REQUIRED_SURFACES)},
            "gate_checks": {"passed": len(passed), "total": len(checks), "percent": round(len(passed) / max(1, len(checks)) * 100, 2)},
        },
        "theory_ids": theory_ids,
        "surfaces": sorted(all_surfaces),
        "checks": checks,
        "failed_checks": failed,
        "evidence_boundary": "deterministic ratchet only; not a substitute for target-bound T3 ratification of a concrete code change",
    }
    return report


def markdown_report(report: dict[str, Any]) -> str:
    cov = report["coverage"]
    failed = report.get("failed_checks") or []
    lines = [
        "---",
        "type: review",
        "status: active",
        f"created: {report['generated_at']}",
        "review_subject: theory-impact-propagation-ratchet",
        f"coverage: theories {cov['theories']['covered']}/{cov['theories']['total']}; surfaces {cov['surfaces']['covered']}/{cov['surfaces']['total']}",
        "concepts: [theory-impact-propagation, architecture-ratchet, same-theory-scan, impact-smoothing]",
        "---",
        "",
        "# 理论到影响全架构传播棘轮复审",
        "",
        f"- Gate status: `{report['status']}`",
        f"- 理论覆盖: `{cov['theories']['covered']}/{cov['theories']['total']}`",
        f"- 架构面覆盖: `{cov['surfaces']['covered']}/{cov['surfaces']['total']}`",
        f"- 棘轮检查: `{cov['gate_checks']['passed']}/{cov['gate_checks']['total']}` (`{cov['gate_checks']['percent']}%`)",
        "",
        "## 未通过检查",
        "",
    ]
    if failed:
        for c in failed:
            lines.append(f"- `{c.get('name')}`: `{c.get('value', c.get('path', ''))}`")
    else:
        lines.append("- 无。当前 theory→impact→architecture propagation matrix 覆盖所需理论点、同理论传播目标、影响面、平滑 gate 与验证命令。")
    lines.extend([
        "",
        "## Evidence Boundary",
        "",
        report.get("evidence_boundary", ""),
        "",
        "## 中文检索别名",
        "",
        "理论到影响 全架构传播 同理论优化 同步优化 影响平滑 差异抚平 theory impact propagation ratchet",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write-json", type=Path)
    ap.add_argument("--write-report", type=Path)
    args = ap.parse_args()

    report = evaluate(VAULT)
    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(markdown_report(report), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(report["status"])
        cov = report["coverage"]
        print(f"theories={cov['theories']['covered']}/{cov['theories']['total']} surfaces={cov['surfaces']['covered']}/{cov['surfaces']['total']} checks={cov['gate_checks']['passed']}/{cov['gate_checks']['total']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
