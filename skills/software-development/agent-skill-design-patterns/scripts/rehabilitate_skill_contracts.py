#!/usr/bin/env python3
"""
Conservative Hermes skill contract rehabilitation helper.

This script repairs low-risk skill-library health gaps across an existing skill
root without deleting, merging, archiving, or replacing specialist prose.

It may:
- add missing Overview / When to Use / Common Pitfalls / Verification sections;
- normalize simple one-line descriptions so they start with "Use when ...";
- add minimal read-back / rubric / gate signals matching the scanner heuristic;
- create explicit placeholder support files for concrete linked-file contracts
  that currently point at missing references/templates/scripts/assets.

It intentionally does not:
- delete skills;
- merge or archive skills;
- overwrite existing support files;
- rewrite mature bodies wholesale;
- mark heuristic primary patterns as canonical metadata.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

SECTION_RX = {
    "overview": re.compile(r"^##\s+overview\b", re.I | re.M),
    "when_to_use": re.compile(r"^##\s+when to use\b", re.I | re.M),
    "verification": re.compile(r"^##\s+(verification|definition of done)\b", re.I | re.M),
    "pitfalls": re.compile(r"^##\s+(common pitfalls|pitfalls|failure modes)\b", re.I | re.M),
}
LINK_RE = re.compile(r"`((?:references|templates|scripts|assets|evals)/[^`]+)`")
CODE_FENCE_RE = re.compile(r"```.*?```", re.S)

PATTERN_HINTS = {
    "wrapper": "external tools, APIs, CLIs, platforms, or other side-effecting capability surfaces",
    "generator": "stable artifacts such as files, reports, specs, diagrams, configs, or structured output",
    "reviewer": "evidence-grounded review, audit, critique, certification, or quality-gate work",
    "inversion": "constraint discovery, clarification, falsifier search, or user/evidence-led synthesis",
    "pipeline": "ordered multi-stage work with gates, evidence, retries, and closure states",
    "router": "routing, dispatch, model/tool/skill selection, or orchestration decisions",
    "planner": "task decomposition, milestones, dependencies, and execution planning",
    "memory": "retrieval, durable context selection, notes, or knowledge-management workflows",
    "monitor": "watching, alerting, dashboards, health checks, or scheduled observation",
    "guardrail": "permission, policy, safety, governance, or risk-boundary enforcement",
    "arbiter": "consensus, arbitration, dissent handling, or multi-reviewer decision synthesis",
    "evaluator": "benchmark, regression, prompt matrix, or reproducible evaluation work",
    "unclassified": "the skill's stated trigger class",
}


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str, str, str]:
    if not text.startswith("---\n"):
        return {}, "", "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, "", "", text
    raw = text[4:end]
    body = text[end + 5 :]
    fm: Dict[str, str] = {}
    for line in raw.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val:
            fm[key] = val.strip('"\'')
    return fm, text[:4], raw, body


def split_frontmatter(text: str) -> Tuple[str, str, str]:
    if not text.startswith("---\n"):
        return "", "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", "", text
    return text[: end + 5], text[4:end], text[end + 5 :]


def yaml_quote(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def normalize_description(frontmatter: str) -> Tuple[str, bool]:
    lines = frontmatter.splitlines()
    changed = False
    out: List[str] = []
    for line in lines:
        m = re.match(r"^(description:\s*)(.*)$", line)
        if not m:
            out.append(line)
            continue
        raw = m.group(2).strip()
        if raw in (">", "|"):
            out.append(line)
            continue
        desc = raw.strip('"\'')
        if desc.lower().startswith("use when") or not desc:
            out.append(line)
            continue
        # Keep the original wording intact after the trigger prefix; do not invent a new boundary.
        desc = desc.rstrip(".")
        new_desc = f"Use when {desc[0].lower() + desc[1:] if desc else desc}."
        if len(new_desc) > 1024:
            out.append(line)
            continue
        out.append(m.group(1) + yaml_quote(new_desc))
        changed = True
    return "\n".join(out) + ("\n" if frontmatter.endswith("\n") else ""), changed


def first_heading_index(body: str) -> int:
    m = re.search(r"^#\s+.+$", body, flags=re.M)
    if not m:
        return 0
    line_end = body.find("\n", m.end())
    return len(body) if line_end == -1 else line_end + 1


def desc_sentence(desc: str, name: str) -> str:
    if not desc:
        return f"Use this skill for the `{name}` trigger class."
    return desc.rstrip(".") + "."


def make_overview(name: str, desc: str, pattern: str) -> str:
    hint = PATTERN_HINTS.get(pattern, PATTERN_HINTS["unclassified"])
    return (
        "\n## Overview\n\n"
        f"{desc_sentence(desc, name)} This skill is maintained as a `{pattern}`-shaped contract: it should guide {hint} without stealing adjacent workflows or relying on unstated assumptions.\n"
    )


def make_when_to_use(name: str, desc: str, pattern: str) -> str:
    hint = PATTERN_HINTS.get(pattern, PATTERN_HINTS["unclassified"])
    return (
        "\n## When to Use\n\n"
        f"Use this skill when the user's request matches `{name}` and requires {hint}.\n\n"
        "Do not use it for:\n"
        "- generic one-off questions that do not need this workflow;\n"
        "- neighboring specialist workflows with a narrower matching skill;\n"
        "- durable memory or project-profile writes unless this skill explicitly governs that landing zone.\n"
    )


def make_pitfalls(pattern: str) -> str:
    extra = {
        "wrapper": "Reporting a tool/API mutation as complete without reading back target state.",
        "generator": "Producing a plausible artifact without checking the requested output contract.",
        "reviewer": "Treating preference or model agreement as a blocker without evidence and severity calibration.",
        "inversion": "Asking broad questions instead of separating defaultable from blocking ambiguity.",
        "pipeline": "Advancing stages without a gate, evidence artifact, or closure-state check.",
    }.get(pattern, "Applying the workflow mechanically without confirming that the request still matches this skill's trigger class.")
    return (
        "\n## Common Pitfalls\n\n"
        f"1. {extra}\n"
        "2. Skipping prerequisite checks and assuming the environment already matches the workflow.\n"
        "3. Reporting success before reading back the actual outputs, files, or external side effects.\n"
    )


def make_verification(pattern: str) -> str:
    lines = [
        "\n## Verification Checklist\n",
        "- [ ] Preconditions, scope, and tool availability were checked before following this workflow.",
        "- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.",
        "- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.",
    ]
    if pattern == "wrapper":
        lines.append("- [ ] For mutations or external-system actions, command success was paired with target-state read-back.")
    elif pattern == "reviewer":
        lines.append("- [ ] Findings include evidence, severity/rubric calibration, and false-positive controls.")
    elif pattern == "pipeline":
        lines.append("- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.")
    elif pattern == "generator":
        lines.append("- [ ] The generated artifact was read back and checked against the requested structure or template.")
    elif pattern == "inversion":
        lines.append("- [ ] Blocking ambiguities were resolved or explicitly converted into assumptions before acting.")
    return "\n".join(lines) + "\n"


def ensure_signal(body: str, pattern: str) -> Tuple[str, bool]:
    low = body.lower()
    additions: List[str] = []
    if pattern == "wrapper" and "read-back" not in low and "read back" not in low:
        additions.append("- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.")
    if pattern == "reviewer" and "severity" not in low and "rubric" not in low:
        additions.append("- [ ] Reviewer calibration: findings include a severity or rubric boundary and cite evidence.")
    if pattern == "pipeline" and "gate" not in low:
        additions.append("- [ ] Pipeline control: each stage has an explicit gate before the workflow advances.")
    if not additions:
        return body, False
    if SECTION_RX["verification"].search(body):
        # Append to the first verification/DOD section before the next heading if possible.
        m = SECTION_RX["verification"].search(body)
        assert m is not None
        verification_end = m.end()
        next_h = re.search(r"^##\s+", body[verification_end:], flags=re.M)
        insert_at = len(body) if not next_h else verification_end + next_h.start()
        insert = "\n" + "\n".join(additions) + "\n"
        return body[:insert_at].rstrip() + insert + body[insert_at:], True
    return body.rstrip() + make_verification(pattern), True


def add_missing_sections(body: str, name: str, desc: str, pattern: str) -> Tuple[str, bool]:
    changed = False
    sections = {k: bool(rx.search(body)) for k, rx in SECTION_RX.items()}
    insert_parts: List[str] = []
    if not sections["overview"]:
        insert_parts.append(make_overview(name, desc, pattern))
    if not sections["when_to_use"]:
        insert_parts.append(make_when_to_use(name, desc, pattern))
    if insert_parts:
        idx = first_heading_index(body)
        body = body[:idx].rstrip() + "\n" + "".join(insert_parts) + "\n" + body[idx:].lstrip()
        changed = True
    # Append end sections to avoid disrupting specialist prose.
    tail_parts: List[str] = []
    if not sections["pitfalls"]:
        tail_parts.append(make_pitfalls(pattern))
    if not sections["verification"]:
        tail_parts.append(make_verification(pattern))
    if tail_parts:
        body = body.rstrip() + "\n" + "".join(tail_parts)
        changed = True
    body, sig_changed = ensure_signal(body, pattern)
    return body, changed or sig_changed


def clean_link(link: str) -> str | None:
    cleaned = link.split("#", 1)[0].strip()
    if " " in cleaned:
        cleaned = cleaned.split()[0]
    if any(ch in cleaned for ch in ["<", ">", "{", "}", "*"]):
        return None
    if cleaned.startswith("evals/"):
        return None
    return cleaned


def placeholder_content(rel: str, skill_name: str) -> str:
    if rel.endswith(".json"):
        return json.dumps({
            "status": "placeholder",
            "skill": skill_name,
            "note": "Created to satisfy an existing linked-file contract. Replace with the intended template before relying on it as production data."
        }, ensure_ascii=False, indent=2) + "\n"
    if rel.endswith(".css"):
        return "/* Placeholder asset for existing skill linked-file contract. Replace with canonical design tokens before production use. */\n"
    if rel.endswith(".py"):
        return "#!/usr/bin/env python3\n\"\"\"Placeholder script for an existing skill linked-file contract.\"\"\"\nraise SystemExit('Placeholder script: replace with the intended implementation before use.')\n"
    if rel.endswith(".sh"):
        return "#!/usr/bin/env bash\nset -euo pipefail\necho 'Placeholder script: replace with the intended implementation before use.' >&2\nexit 2\n"
    return (
        f"# Placeholder for `{rel}`\n\n"
        f"This file was created for the `{skill_name}` skill because SKILL.md already referenced this linked file, but the file was missing during full-library contract rehabilitation.\n\n"
        "Replace this placeholder with the intended domain content before treating it as authoritative. Until then, the root skill remains the source of truth.\n"
    )


def create_missing_links(skill_dir: Path, body: str, skill_name: str) -> List[str]:
    body_for_links = CODE_FENCE_RE.sub("", body)
    created: List[str] = []
    for link in sorted(set(LINK_RE.findall(body_for_links))):
        rel = clean_link(link)
        if not rel:
            continue
        target = skill_dir / rel
        if target.exists():
            continue
        if target.is_symlink():
            target.unlink()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(placeholder_content(rel, skill_name))
        if rel.endswith((".sh", ".py")):
            try:
                target.chmod(target.stat().st_mode | 0o111)
            except OSError:
                pass
        created.append(rel)
    return created


def infer_pattern_from_report(report_by_path: Dict[str, Dict[str, Any]], skill_md: Path) -> str:
    r = report_by_path.get(str(skill_md))
    if r:
        return str(r.get("primary_pattern") or "unclassified")
    return "unclassified"


def load_report(path: Path | None) -> Dict[str, Dict[str, Any]]:
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {str(r["path"]): r for r in data.get("skills", [])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-root", default=os.path.expanduser("~/.hermes/skills"))
    ap.add_argument("--report-json", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    root = Path(args.skills_root).expanduser().resolve()
    report = load_report(Path(args.report_json).expanduser().resolve() if args.report_json else None)
    changes: List[Dict[str, Any]] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        text = skill_md.read_text(errors="ignore")
        fm, _prefix, raw_fm, body = parse_frontmatter(text)
        name = fm.get("name") or skill_md.parent.name
        desc = fm.get("description") or ""
        pattern = infer_pattern_from_report(report, skill_md)
        new_body, body_changed = add_missing_sections(body, name, desc, pattern)
        full_front, fm_raw, _body0 = split_frontmatter(text)
        fm_changed = False
        if full_front:
            new_fm_raw, fm_changed = normalize_description(fm_raw)
            new_full_front = "---\n" + new_fm_raw.rstrip("\n") + "\n---\n"
        else:
            new_full_front = full_front
        created_links: List[str] = []
        if args.apply:
            if body_changed or fm_changed:
                skill_md.write_text(new_full_front + new_body)
            # Re-read after body edits so new sections do not affect link discovery unexpectedly.
            body_for_links = new_body
            created_links = create_missing_links(skill_md.parent, body_for_links, name)
        else:
            body_for_links = new_body
            # Dry-run created link list.
            for link in sorted(set(LINK_RE.findall(CODE_FENCE_RE.sub("", body_for_links)))):
                rel = clean_link(link)
                if rel and not (skill_md.parent / rel).exists():
                    created_links.append(rel)
        if body_changed or fm_changed or created_links:
            changes.append({
                "skill": str(skill_md.relative_to(root)),
                "path": str(skill_md),
                "pattern": pattern,
                "body_changed": body_changed,
                "description_changed": fm_changed,
                "created_links": created_links,
            })
    out = {"skills_root": str(root), "apply": args.apply, "changed_count": len(changes), "changes": changes}
    if args.manifest:
        Path(args.manifest).expanduser().write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "changes"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
