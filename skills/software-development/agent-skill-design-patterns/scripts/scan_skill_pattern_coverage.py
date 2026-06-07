#!/usr/bin/env python3
"""
Scan Hermes SKILL.md files for Agent Skill design-pattern coverage.

This is a non-mutating audit helper. It classifies each skill with heuristic
signals and reports coverage gaps for routing, pattern structure, verification,
progressive loading, evals, and linked-file hygiene.

Usage:
  python3 scripts/scan_skill_pattern_coverage.py \
    --skills-root ~/.hermes/skills \
    --out-dir ~/.hermes/docs/private/skill-pattern-coverage-YYYYMMDD
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

PATTERNS = [
    "wrapper",
    "generator",
    "reviewer",
    "inversion",
    "pipeline",
    "router",
    "planner",
    "memory",
    "monitor",
    "guardrail",
    "arbiter",
    "evaluator",
]

PATTERN_KEYWORDS = {
    "wrapper": [
        "api", "cli", "mcp", "sdk", "command", "commands", "auth", "deploy", "github",
        "gh ", "external", "tool", "server", "webhook", "telegram", "email", "cloudflare",
        "vercel", "browser", "homeassistant", "apple", "send", "credentials",
    ],
    "generator": [
        "generate", "create", "write", "draft", "template", "artifact", "report",
        "document", "diagram", "slides", "image", "content", "output format", "schema",
        "prd", "adr", "spec", "presentation", "illustration",
    ],
    "reviewer": [
        "review", "audit", "evaluate", "rubric", "severity", "pass", "fail", "warn",
        "check", "critique", "certification", "quality", "accessibility", "security", "score",
    ],
    "inversion": [
        "clarify", "ask", "question", "interview", "discover", "ambigu", "intake",
        "requirements", "user preference", "default", "anti-condition", "falsifier", "goal calibration",
    ],
    "pipeline": [
        "workflow", "stage", "step", "pipeline", "gate", "evidence", "closure", "rollback",
        "task", "plan", "verify", "verification", "ratchet", "sdd", "tdd", "deploy",
    ],
    "router": ["route", "routing", "dispatch", "orchestr", "select", "delegate", "subagent", "worker"],
    "planner": ["plan", "decompose", "milestone", "roadmap", "tasks", "dependencies"],
    "memory": ["memory", "retrieval", "context", "session_search", "profile", "knowledge"],
    "monitor": ["monitor", "watch", "cron", "alert", "dashboard", "health", "incident", "observability"],
    "guardrail": ["policy", "gate", "safety", "permission", "danger", "confirm", "red line", "governance"],
    "arbiter": ["arbitrat", "consensus", "dissent", "multi-model", "judge", "certification"],
    "evaluator": ["eval", "benchmark", "test cases", "regression", "prompts.csv", "golden"],
}

SECTION_PATTERNS = {
    "overview": re.compile(r"^##\s+overview\b", re.I | re.M),
    "when_to_use": re.compile(r"^##\s+when to use\b", re.I | re.M),
    "verification": re.compile(r"^##\s+(verification|definition of done)\b", re.I | re.M),
    "pitfalls": re.compile(r"^##\s+(common pitfalls|pitfalls|failure modes)\b", re.I | re.M),
    "references": re.compile(r"^##\s+references\b", re.I | re.M),
}

LINK_RE = re.compile(r"`((?:references|templates|scripts|assets|evals)/[^`]+)`")


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str, List[str]]:
    issues: List[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["missing_frontmatter"]
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text, ["unterminated_frontmatter"]
    raw = text[4:end]
    body = text[end + 5 :]
    fm: Dict[str, Any] = {}
    current_key = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_-]+:\s*", line):
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"\'')
            current_key = key
            if val == "":
                fm[key] = {}
            elif val.startswith("[") and val.endswith("]"):
                fm[key] = [x.strip().strip('"\'') for x in val[1:-1].split(",") if x.strip()]
            else:
                fm[key] = val
        elif current_key:
            # Keep parser permissive. Nested metadata is not fully parsed.
            pass
    for k in ["name", "description"]:
        if not fm.get(k):
            issues.append(f"frontmatter_missing_{k}")
    return fm, body, issues


def rel_skill_name(skill_md: Path, root: Path) -> str:
    rel = skill_md.relative_to(root)
    if rel.parts[-1] == "SKILL.md":
        return "/".join(rel.parts[:-1])
    return str(rel)


def score_patterns(text: str, fm: Dict[str, Any]) -> Dict[str, int]:
    hay = (str(fm.get("name", "")) + "\n" + str(fm.get("description", "")) + "\n" + text[:8000]).lower()
    scores = {}
    for p, kws in PATTERN_KEYWORDS.items():
        score = 0
        for kw in kws:
            score += hay.count(kw.lower())
        scores[p] = score
    return scores


def choose_primary(scores: Dict[str, int]) -> Tuple[str, int, List[str]]:
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    primary, score = ranked[0]
    if score <= 0:
        return "unclassified", 0, []
    secondary = [p for p, s in ranked[1:4] if s > 0 and s >= max(2, score * 0.35)]
    return primary, score, secondary


def eval_counts(skill_dir: Path) -> Dict[str, int]:
    out = {"positive": 0, "neighbor": 0, "forbidden": 0, "no-load": 0, "negative": 0, "total": 0}
    candidates = [skill_dir / "evals" / "prompts.csv"]
    candidates.extend((skill_dir / "references").glob("*eval*.csv") if (skill_dir / "references").exists() else [])
    seen = set()
    for p in candidates:
        if not p.exists() or p in seen:
            continue
        seen.add(p)
        try:
            rows = list(csv.DictReader(p.open(newline="")))
        except Exception:
            continue
        for r in rows:
            out["total"] += 1
            bucket = (r.get("bucket") or "").strip().lower()
            should = (r.get("should_trigger") or "").strip().lower()
            if bucket in out:
                out[bucket] += 1
            elif should in ("false", "0", "no"):
                out["negative"] += 1
            elif should in ("true", "1", "yes"):
                out["positive"] += 1
    return out


def analyze_skill(skill_md: Path, root: Path) -> Dict[str, Any]:
    text = skill_md.read_text(errors="ignore")
    fm, body, issues = parse_frontmatter(text)
    skill_dir = skill_md.parent
    name = str(fm.get("name") or skill_dir.name)
    desc = str(fm.get("description") or "")
    sections = {k: bool(rx.search(body)) for k, rx in SECTION_PATTERNS.items()}
    scores = score_patterns(body, fm)
    primary, primary_score, secondary = choose_primary(scores)
    ev = eval_counts(skill_dir)
    # Link hygiene should inspect prose contracts, not examples inside fenced code.
    body_for_links = re.sub(r"```.*?```", "", body, flags=re.S)
    links = sorted(set(LINK_RE.findall(body_for_links)))
    broken = []
    placeholders = []
    for link in links:
        # Trim anchors or human comments after whitespace.
        cleaned = link.split("#", 1)[0].strip()
        if " " in cleaned:
            cleaned = cleaned.split()[0]
        # Pattern placeholders such as references/<topic>.md, references/{subcommand}.md,
        # references/*.md, or scripts/<file> are load-contract examples, not concrete
        # broken files. Track them separately so the report does not overstate damage.
        if any(ch in cleaned for ch in ["<", ">", "{", "}", "*"]):
            placeholders.append(link)
            continue
        if not (skill_dir / cleaned).exists():
            broken.append(link)
    support_counts = {}
    for d in ["references", "templates", "scripts", "assets", "evals"]:
        dd = skill_dir / d
        support_counts[d] = sum(1 for x in dd.rglob("*") if x.is_file()) if dd.exists() else 0
    root_bytes = len(text.encode("utf-8", errors="ignore"))
    desc_quality = {
        "present": bool(desc),
        "starts_use_when": desc.lower().startswith("use when"),
        "len": len(desc),
        "too_short": len(desc) < 40,
        "too_long": len(desc) > 700,
    }
    has_eval_min = ev["positive"] >= 3 and (ev["neighbor"] + ev["negative"] >= 2) and ev["forbidden"] >= 0
    # Stronger Hermes v1 gate when buckets are present.
    has_full_routing_matrix = ev["positive"] >= 3 and ev["neighbor"] >= 2 and ev["forbidden"] >= 2 and ev["no-load"] >= 1
    quality_flags = []
    if not sections["when_to_use"]:
        quality_flags.append("missing_when_to_use")
    if not sections["verification"]:
        quality_flags.append("missing_verification_or_dod")
    if not sections["pitfalls"]:
        quality_flags.append("missing_pitfalls_failure_modes")
    if not desc_quality["starts_use_when"]:
        quality_flags.append("description_not_use_when")
    if not has_eval_min:
        quality_flags.append("missing_min_eval_prompts")
    if not has_full_routing_matrix:
        quality_flags.append("missing_full_routing_matrix")
    if broken:
        quality_flags.append("broken_linked_files")
    if root_bytes > 18000 and support_counts["references"] == 0:
        quality_flags.append("large_root_no_references")
    if primary == "wrapper" and "read-back" not in body.lower() and "read back" not in body.lower():
        quality_flags.append("wrapper_missing_read_back_signal")
    if primary == "reviewer" and "severity" not in body.lower() and "rubric" not in body.lower():
        quality_flags.append("reviewer_missing_rubric_signal")
    if primary == "pipeline" and "gate" not in body.lower():
        quality_flags.append("pipeline_missing_gate_signal")
    risk = "low"
    if broken or "missing_verification_or_dod" in quality_flags or primary == "unclassified":
        risk = "medium"
    if (primary == "wrapper" and "wrapper_missing_read_back_signal" in quality_flags) or len(quality_flags) >= 5:
        risk = "high"
    return {
        "name": name,
        "path": str(skill_md),
        "rel": rel_skill_name(skill_md, root),
        "description": desc,
        "frontmatter_issues": issues,
        "sections": sections,
        "pattern_scores": scores,
        "primary_pattern": primary,
        "primary_score": primary_score,
        "secondary_patterns": secondary,
        "eval_counts": ev,
        "has_min_eval_prompts": has_eval_min,
        "has_full_routing_matrix": has_full_routing_matrix,
        "linked_files": links,
        "placeholder_linked_files": placeholders,
        "broken_linked_files": broken,
        "support_counts": support_counts,
        "root_bytes": root_bytes,
        "description_quality": desc_quality,
        "quality_flags": quality_flags,
        "risk": risk,
    }


def pct(n: int, d: int) -> str:
    return f"{(100*n/d):.1f}%" if d else "0.0%"


def write_markdown(results: List[Dict[str, Any]], out_md: Path, root: Path) -> None:
    total = len(results)
    by_pattern = Counter(r["primary_pattern"] for r in results)
    by_risk = Counter(r["risk"] for r in results)
    flags = Counter(flag for r in results for flag in r["quality_flags"])
    categories = Counter(str(Path(r["rel"]).parts[0]) if Path(r["rel"]).parts else "root" for r in results)
    active_results = [r for r in results if not str(r["rel"]).startswith(".archive/")]
    archived_results = [r for r in results if str(r["rel"]).startswith(".archive/")]
    eval_full = sum(1 for r in results if r["has_full_routing_matrix"])
    eval_min = sum(1 for r in results if r["has_min_eval_prompts"])
    verification = sum(1 for r in results if r["sections"].get("verification"))
    when = sum(1 for r in results if r["sections"].get("when_to_use"))
    broken = [r for r in results if r["broken_linked_files"]]
    placeholder = [r for r in results if r.get("placeholder_linked_files")]
    high = [r for r in results if r["risk"] == "high"]
    no_eval_top = [r for r in results if not r["has_min_eval_prompts"]][:30]
    unclassified = [r for r in results if r["primary_pattern"] == "unclassified"][:30]

    lines: List[str] = []
    lines.append("# Hermes Skill Pattern Coverage Audit")
    lines.append("")
    lines.append(f"Date: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Skills root: `{root}`")
    lines.append("Scope: non-mutating heuristic audit of existing `SKILL.md` files.")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Total skills scanned: {total}")
    lines.append(f"- Active skills scanned: {len(active_results)}; archived skills scanned: {len(archived_results)}")
    if active_results:
        active_total = len(active_results)
        active_verification = sum(1 for r in active_results if r["sections"].get("verification"))
        active_when = sum(1 for r in active_results if r["sections"].get("when_to_use"))
        active_eval_min = sum(1 for r in active_results if r["has_min_eval_prompts"])
        active_eval_full = sum(1 for r in active_results if r["has_full_routing_matrix"])
        active_broken = sum(1 for r in active_results if r["broken_linked_files"])
        active_high = sum(1 for r in active_results if r["risk"] == "high")
        lines.append(f"- Active `## When to Use`: {active_when}/{active_total} ({pct(active_when,active_total)})")
        lines.append(f"- Active verification or Definition of Done: {active_verification}/{active_total} ({pct(active_verification,active_total)})")
        lines.append(f"- Active minimum eval prompts: {active_eval_min}/{active_total} ({pct(active_eval_min,active_total)})")
        lines.append(f"- Active full routing matrix: {active_eval_full}/{active_total} ({pct(active_eval_full,active_total)})")
        lines.append(f"- Active broken concrete linked-file references: {active_broken}/{active_total} ({pct(active_broken,active_total)})")
        lines.append(f"- Active high-risk skills by heuristic: {active_high}/{active_total} ({pct(active_high,active_total)})")
    lines.append(f"- Skills with `## When to Use`: {when}/{total} ({pct(when,total)})")
    lines.append(f"- Skills with verification or Definition of Done: {verification}/{total} ({pct(verification,total)})")
    lines.append(f"- Skills with minimum eval prompts: {eval_min}/{total} ({pct(eval_min,total)})")
    lines.append(f"- Skills with full routing matrix: {eval_full}/{total} ({pct(eval_full,total)})")
    lines.append(f"- Skills with broken concrete linked-file references: {len(broken)}/{total} ({pct(len(broken),total)})")
    lines.append(f"- Skills with placeholder/example linked-file contracts: {len(placeholder)}/{total} ({pct(len(placeholder),total)})")
    lines.append(f"- High-risk skills by heuristic: {len(high)}/{total} ({pct(len(high),total)})")
    lines.append("")
    lines.append("Interpretation: this is coverage telemetry, not an automatic rewrite mandate. Pattern labels are candidates until human/agent review confirms semantics.")
    lines.append("")
    lines.append("## Primary pattern coverage")
    lines.append("")
    lines.append("| Pattern | Count | Share |")
    lines.append("|---|---:|---:|")
    for p, c in by_pattern.most_common():
        lines.append(f"| {p} | {c} | {pct(c,total)} |")
    lines.append("")
    lines.append("## Risk distribution")
    lines.append("")
    lines.append("| Risk | Count | Share |")
    lines.append("|---|---:|---:|")
    for p in ["high", "medium", "low"]:
        c = by_risk[p]
        lines.append(f"| {p} | {c} | {pct(c,total)} |")
    lines.append("")
    lines.append("## Category coverage")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for cat, c in categories.most_common():
        lines.append(f"| {cat} | {c} |")
    lines.append("")
    lines.append("## Most common gaps")
    lines.append("")
    lines.append("| Flag | Count | Share |")
    lines.append("|---|---:|---:|")
    for flag, c in flags.most_common(20):
        lines.append(f"| {flag} | {c} | {pct(c,total)} |")
    lines.append("")
    lines.append("## Broken concrete linked-file references")
    lines.append("")
    if broken:
        lines.append("| Skill | Broken references |")
        lines.append("|---|---|")
        for r in broken[:50]:
            refs = "<br>".join(str(x) for x in r["broken_linked_files"][:10])
            lines.append(f"| `{r['rel']}` | {refs} |")
        if len(broken) > 50:
            lines.append(f"\nTruncated: {len(broken)-50} more skills with broken references in JSON.")
    else:
        lines.append("None detected by backtick-link heuristic.")
    lines.append("")
    lines.append("## High-risk skills to inspect first")
    lines.append("")
    if high:
        lines.append("| Skill | Pattern | Flags |")
        lines.append("|---|---|---|")
        for r in sorted(high, key=lambda x: (-len(x["quality_flags"]), x["rel"]))[:50]:
            lines.append(f"| `{r['rel']}` | {r['primary_pattern']} | {', '.join(r['quality_flags'][:8])} |")
    else:
        lines.append("None by current heuristic.")
    lines.append("")
    lines.append("## Skills missing minimum eval prompts, sample")
    lines.append("")
    if no_eval_top:
        for r in no_eval_top:
            lines.append(f"- `{r['rel']}` ({r['primary_pattern']})")
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Unclassified skills, sample")
    lines.append("")
    if unclassified:
        for r in unclassified:
            lines.append(f"- `{r['rel']}`")
    else:
        lines.append("None.")
    lines.append("")
    lines.append("## Recommended next actions")
    lines.append("")
    lines.append("1. Do not batch-edit all skills. Use this report as a triage queue.")
    lines.append("2. Fix broken linked-file references first; they are silent runtime failures.")
    lines.append("3. Pilot 10 representative skills: 2 each from Wrapper, Generator, Reviewer, Inversion, Pipeline.")
    lines.append("4. For any skill whose `description` changes, add/refresh `evals/prompts.csv` before committing.")
    lines.append("5. Treat high-risk Wrapper skills without read-back signals as safety-priority audits.")
    lines.append("6. Promote recurring scan usage into the `agent-skill-design-patterns` skill script; keep generated reports in docs/private.")
    lines.append("")
    lines.append("## Boundary / human intervention")
    lines.append("")
    lines.append("This audit intentionally stops before bulk mutation. Human/owner review is needed before:")
    lines.append("")
    lines.append("- changing many skill descriptions, because descriptions are routing logic;")
    lines.append("- deleting or merging skills;")
    lines.append("- deciding whether a broken linked reference was intentionally removed;")
    lines.append("- labeling a heuristic pattern as canonical metadata for a skill;")
    lines.append("- enabling automated routing tests across multiple model families.")
    lines.append("")
    lines.append("## Method limits")
    lines.append("")
    lines.append("- Pattern classification is keyword-based and may over-detect broad workflow words.")
    lines.append("- Linked-file detection only catches backtick paths under references/templates/scripts/assets/evals.")
    lines.append("- Eval presence is file-coverage only; it does not prove the evals were executed against the active router.")
    lines.append("- Verification section presence does not prove verification quality.")
    lines.append("")
    out_md.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-root", default=os.path.expanduser("~/.hermes/skills"))
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()
    root = Path(args.skills_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"skills root not found: {root}")
    date = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else Path.home() / ".hermes" / "docs" / "private" / f"skill-pattern-coverage-{date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    skill_mds = sorted(root.rglob("SKILL.md"))
    results = [analyze_skill(p, root) for p in skill_mds]
    json_path = out_dir / "skill-pattern-coverage.json"
    md_path = out_dir / "skill-pattern-coverage.md"
    json_path.write_text(json.dumps({"skills_root": str(root), "generated_at": date, "skills": results}, ensure_ascii=False, indent=2))
    write_markdown(results, md_path, root)
    print(json.dumps({
        "skills_root": str(root),
        "out_dir": str(out_dir),
        "report": str(md_path),
        "json": str(json_path),
        "skill_count": len(results),
        "high_risk": sum(1 for r in results if r["risk"] == "high"),
        "broken_concrete_linked_refs": sum(1 for r in results if r["broken_linked_files"]),
        "placeholder_linked_contracts": sum(1 for r in results if r.get("placeholder_linked_files")),
        "full_routing_matrix": sum(1 for r in results if r["has_full_routing_matrix"]),
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
