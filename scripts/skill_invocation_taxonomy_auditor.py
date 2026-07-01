#!/usr/bin/env python3
"""Read-only Hermes skill invocation/lifecycle taxonomy auditor.

This script scans SKILL.md files and emits JSON/Markdown reports. It is
intentionally read-only: it never mutates skills, config, taskpool, or runtime
state. It classifies skills into advisory lifecycle/invocation buckets to find
routing drift before any semantic rewrite.
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path.home() / ".hermes" / "skills"
DEFAULT_REPORT_DIR = Path.home() / ".hermes" / "docs" / "private" / "skill-invocation-taxonomy"
MAX_SKILL_MD_CHARS = 100_000
TARGET_CORE_WARN_CHARS = 20_000


@dataclass
class SkillFinding:
    severity: str
    code: str
    message: str


@dataclass
class SkillRecord:
    name: str
    path: str
    relpath: str
    category: str
    description: str = ""
    size_chars: int = 0
    lifecycle: str = "active"
    invocation: str = "model-invoked"
    has_when_to_use: bool = False
    has_dont_use_for: bool = False
    has_common_pitfalls: bool = False
    has_verification_checklist: bool = False
    has_linked_dirs: dict[str, int] = field(default_factory=dict)
    findings: list[SkillFinding] = field(default_factory=list)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str, list[SkillFinding]]:
    findings: list[SkillFinding] = []
    if not text.startswith("---\n"):
        return {}, text, [SkillFinding("error", "missing_frontmatter", "SKILL.md does not start with YAML frontmatter")]
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text, [SkillFinding("error", "unterminated_frontmatter", "YAML frontmatter closing marker not found")]
    raw = text[4:end]
    body = text[end + 5 :]
    # Minimal YAML-ish parser for common scalar/list fields. Avoids PyYAML dependency.
    fm: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and ":" in line:
            k, v = line.split(":", 1)
            key = k.strip()
            val = v.strip()
            current_key = key
            if val == "":
                fm[key] = []
            elif val in {"true", "false"}:
                fm[key] = val == "true"
            elif val.startswith("[") and val.endswith("]"):
                inside = val[1:-1].strip()
                fm[key] = [p.strip().strip("'\"") for p in inside.split(",") if p.strip()] if inside else []
            else:
                fm[key] = val.strip("'\"")
        elif current_key and line.strip().startswith("-"):
            fm.setdefault(current_key, [])
            if isinstance(fm[current_key], list):
                fm[current_key].append(line.strip()[1:].strip().strip("'\""))
    return fm, body, findings


def classify(path: Path, root: Path) -> SkillRecord:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body, findings = parse_frontmatter(text)
    rel = path.relative_to(root)
    parts = rel.parts
    category = parts[0] if len(parts) > 1 else "uncategorized"
    name = str(fm.get("name") or path.parent.name)
    desc = str(fm.get("description") or "")
    lower_path = "/".join(p.lower() for p in parts)
    lower_text = text.lower()

    lifecycle = "active"
    if "deprecated" in lower_path or "deprecated" in lower_text[:3000]:
        lifecycle = "deprecated"
    elif "in-progress" in lower_path or "draft" in lower_path or "draft" in lower_text[:3000]:
        lifecycle = "draft"
    elif "personal" in lower_path:
        lifecycle = "personal"
    elif path.name != "SKILL.md":
        lifecycle = "reference-only"

    invocation = "model-invoked"
    if fm.get("disable-model-invocation") is True or fm.get("user_invoked") is True:
        invocation = "user-invoked"
    if lifecycle in {"deprecated", "draft", "personal"}:
        invocation = "not-default"

    record = SkillRecord(
        name=name,
        path=str(path),
        relpath=str(rel),
        category=category,
        description=desc,
        size_chars=len(text),
        lifecycle=lifecycle,
        invocation=invocation,
        has_when_to_use="## When to Use" in text,
        has_dont_use_for=bool(re.search(r"don.?t use for|anti-conditions?|anti-condition", text, re.I)),
        has_common_pitfalls="## Common Pitfalls" in text,
        has_verification_checklist="## Verification Checklist" in text,
    )
    for d in ("references", "templates", "scripts", "assets"):
        p = path.parent / d
        record.has_linked_dirs[d] = len([x for x in p.rglob("*") if x.is_file()]) if p.exists() else 0

    record.findings.extend(findings)
    if not name:
        record.findings.append(SkillFinding("error", "missing_name", "frontmatter missing name"))
    if not desc:
        record.findings.append(SkillFinding("error", "missing_description", "frontmatter missing description"))
    if desc and not desc.lower().startswith("use when"):
        record.findings.append(SkillFinding("warn", "description_not_trigger_shaped", "description should start with 'Use when' and express trigger class"))
    if len(desc) > 1024:
        record.findings.append(SkillFinding("error", "description_too_long", "description exceeds 1024 chars"))
    if len(text) > MAX_SKILL_MD_CHARS:
        record.findings.append(SkillFinding("error", "skill_too_large", "SKILL.md exceeds manager hard limit"))
    elif len(text) > TARGET_CORE_WARN_CHARS:
        record.findings.append(SkillFinding("warn", "core_body_large", "SKILL.md is large; consider moving conditional detail to references/"))
    if not record.has_when_to_use:
        record.findings.append(SkillFinding("warn", "missing_when_to_use", "missing ## When to Use section"))
    if not record.has_dont_use_for:
        record.findings.append(SkillFinding("warn", "missing_anti_conditions", "missing Don't use for / anti-conditions"))
    if not record.has_common_pitfalls:
        record.findings.append(SkillFinding("warn", "missing_common_pitfalls", "missing ## Common Pitfalls section"))
    if not record.has_verification_checklist:
        record.findings.append(SkillFinding("warn", "missing_verification_checklist", "missing ## Verification Checklist section"))
    if lifecycle in {"deprecated", "draft", "personal"} and invocation == "model-invoked":
        record.findings.append(SkillFinding("error", "unsafe_default_invocation", "draft/deprecated/personal skill appears model-invoked"))
    return record


def scan(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    records = [classify(p, root) for p in sorted(root.rglob("SKILL.md"))]
    counts: dict[str, Any] = {
        "total": len(records),
        "by_lifecycle": {},
        "by_invocation": {},
        "findings_by_severity": {},
        "findings_by_code": {},
    }
    for r in records:
        counts["by_lifecycle"][r.lifecycle] = counts["by_lifecycle"].get(r.lifecycle, 0) + 1
        counts["by_invocation"][r.invocation] = counts["by_invocation"].get(r.invocation, 0) + 1
        for f in r.findings:
            counts["findings_by_severity"][f.severity] = counts["findings_by_severity"].get(f.severity, 0) + 1
            counts["findings_by_code"][f.code] = counts["findings_by_code"].get(f.code, 0) + 1
    return {
        "ok": counts["findings_by_severity"].get("error", 0) == 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "counts": counts,
        "skills": [asdict(r) for r in records],
    }


def to_markdown(result: dict[str, Any]) -> str:
    c = result["counts"]
    lines = [
        "# Hermes Skill Invocation Taxonomy Audit",
        "",
        f"Generated: {result['generated_at']}",
        f"Root: `{result['root']}`",
        f"Status: {'OK' if result['ok'] else 'NEEDS_REVIEW'}",
        "",
        "## Summary",
        "",
        f"- Total skills: {c['total']}",
        f"- Lifecycle: `{json.dumps(c['by_lifecycle'], ensure_ascii=False, sort_keys=True)}`",
        f"- Invocation: `{json.dumps(c['by_invocation'], ensure_ascii=False, sort_keys=True)}`",
        f"- Finding severities: `{json.dumps(c['findings_by_severity'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Top Findings",
        "",
    ]
    findings = []
    for s in result["skills"]:
        for f in s["findings"]:
            findings.append((f["severity"], f["code"], s["relpath"], f["message"]))
    order = {"error": 0, "warn": 1, "info": 2}
    for sev, code, rel, msg in sorted(findings, key=lambda x: (order.get(x[0], 9), x[1], x[2]))[:200]:
        lines.append(f"- **{sev}** `{code}` — `{rel}` — {msg}")
    lines += ["", "## Skills", ""]
    for s in sorted(result["skills"], key=lambda x: x["relpath"]):
        lines.append(
            f"- `{s['relpath']}` — lifecycle={s['lifecycle']} invocation={s['invocation']} findings={len(s['findings'])} size={s['size_chars']}"
        )
    return "\n".join(lines) + "\n"


def write_reports(result: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"skill-taxonomy-audit-{stamp}.json"
    md_path = out_dir / f"skill-taxonomy-audit-{stamp}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(to_markdown(result), encoding="utf-8")
    latest_json = out_dir / "latest.json"
    latest_md = out_dir / "latest.md"
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "latest_json": str(latest_json), "latest_markdown": str(latest_md)}


def selftest() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "skills"
        good = root / "software-development" / "good-skill"
        good.mkdir(parents=True)
        (good / "SKILL.md").write_text(
            "---\nname: good-skill\ndescription: Use when testing a good skill.\n---\n"
            "# Good\n\n## Overview\nOk.\n\n## When to Use\n- Tests.\n- Don't use for: prod.\n\n## Common Pitfalls\n1. None.\n\n## Verification Checklist\n- [ ] pass\n",
            encoding="utf-8",
        )
        bad = root / "deprecated" / "bad-skill"
        bad.mkdir(parents=True)
        (bad / "SKILL.md").write_text("---\nname: bad-skill\ndescription: Bad.\n---\n# Bad\n", encoding="utf-8")
        result = scan(root)
        assert result["counts"]["total"] == 2
        assert result["counts"]["by_lifecycle"].get("deprecated") == 1
        assert result["counts"]["findings_by_code"].get("description_not_trigger_shaped", 0) >= 1
        return {"ok": True, "skills": result["counts"]["total"], "findings": result["counts"]["findings_by_code"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--out-dir", default=str(DEFAULT_REPORT_DIR))
    ap.add_argument("--write-report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        result = selftest()
    else:
        result = scan(Path(args.root))
        if args.write_report:
            result["reports"] = write_reports(result, Path(args.out_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
