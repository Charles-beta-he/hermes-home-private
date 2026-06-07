#!/usr/bin/env python3
"""
Generate canonical routing eval prompt sets for every Hermes skill.

This is a contract-layer bulk rehabilitation helper: it adds or refreshes
`evals/prompts.csv` so every skill has at least:

- 3 positive prompts
- 2 neighbor prompts
- 2 forbidden prompts
- 1 no-load prompt

It intentionally does NOT rewrite `description` or SKILL.md semantics.
Existing full matrices are preserved unless --overwrite is passed.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

REQUIRED = {"positive": 3, "neighbor": 2, "forbidden": 2, "no-load": 1}


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    out: Dict[str, Any] = {}
    current = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            current = k
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            if v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            out[k] = v
        elif current:
            # Nested metadata is not needed for prompt generation.
            pass
    return out, body


def rel_skill(skill_md: Path, root: Path) -> str:
    rel = skill_md.relative_to(root)
    return "/".join(rel.parts[:-1]) if rel.name == "SKILL.md" else str(rel)


def clean_description(desc: str, fallback: str) -> str:
    desc = " ".join((desc or "").split())
    if not desc:
        return f"Use when working with the {fallback} skill's documented workflow."
    # Keep enough context for a routing prompt while avoiding gigantic CSV rows.
    if len(desc) > 260:
        desc = desc[:257].rstrip() + "..."
    return desc


def display_name(rel: str, fm_name: str) -> str:
    return fm_name or rel.split("/")[-1]


def read_existing_counts(path: Path) -> Dict[str, int]:
    counts = {k: 0 for k in REQUIRED}
    if not path.exists():
        return counts
    try:
        with path.open(newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return counts
    for r in rows:
        bucket = (r.get("bucket") or "").strip().lower()
        should = (r.get("should_trigger") or "").strip().lower()
        if bucket in counts:
            counts[bucket] += 1
        elif should in ("true", "1", "yes"):
            counts["positive"] += 1
        elif should in ("false", "0", "no"):
            # Old files lack bucket; count as forbidden so they do not look positive.
            counts["forbidden"] += 1
    return counts


def is_full(counts: Dict[str, int]) -> bool:
    return all(counts.get(k, 0) >= v for k, v in REQUIRED.items())


def choose_neighbors(skills: List[Dict[str, str]], current: Dict[str, str]) -> List[Dict[str, str]]:
    cur_rel = current["rel"]
    cur_cat = current["category"]
    same_cat = [s for s in skills if s["rel"] != cur_rel and s["category"] == cur_cat]
    if len(same_cat) >= 2:
        return same_cat[:2]
    others = [s for s in skills if s["rel"] != cur_rel]
    return (same_cat + others)[:2]


def q(s: str) -> str:
    return " ".join(s.replace('"', "'").split())


def generate_rows(current: Dict[str, str], neighbors: List[Dict[str, str]]) -> List[Dict[str, str]]:
    name = current["name"]
    rel = current["rel"]
    desc = current["description"]
    n1 = neighbors[0] if neighbors else {"name": "a neighboring skill", "rel": "neighbor", "description": "another workflow"}
    n2 = neighbors[1] if len(neighbors) > 1 else n1
    rows = [
        {
            "id": "pos-01",
            "bucket": "positive",
            "should_trigger": "true",
            "prompt": q(f"Use the {name} skill for this task."),
            "notes": "Explicit skill invocation should load this skill.",
        },
        {
            "id": "pos-02",
            "bucket": "positive",
            "should_trigger": "true",
            "prompt": q(desc),
            "notes": "Natural-language trigger derived from the skill description.",
        },
        {
            "id": "pos-03",
            "bucket": "positive",
            "should_trigger": "true",
            "prompt": q(f"I need help with the workflow documented by {rel}: {desc}"),
            "notes": "Contextual positive prompt with skill path and trigger language.",
        },
        {
            "id": "neighbor-01",
            "bucket": "neighbor",
            "should_trigger": "false",
            "prompt": q(f"Use the {n1['name']} skill instead: {n1['description']}"),
            "notes": q(f"Should route to neighboring skill {n1['rel']}, not this skill."),
        },
        {
            "id": "neighbor-02",
            "bucket": "neighbor",
            "should_trigger": "false",
            "prompt": q(f"This request belongs to {n2['rel']}: {n2['description']}"),
            "notes": q(f"Second neighbor-control case for {n2['rel']}.")
        },
        {
            "id": "forbidden-01",
            "bucket": "forbidden",
            "should_trigger": "false",
            "prompt": "What time is it right now?",
            "notes": "Current-time requests must use a time/system tool path, not this skill.",
        },
        {
            "id": "forbidden-02",
            "bucket": "forbidden",
            "should_trigger": "false",
            "prompt": "Calculate 17 times 23 and show only the number.",
            "notes": "Arithmetic requests must use calculation tooling, not this skill.",
        },
        {
            "id": "no-load-01",
            "bucket": "no-load",
            "should_trigger": "false",
            "prompt": "Say hello in one short sentence.",
            "notes": "Generic conversational prompt should not load any specialist skill.",
        },
    ]
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "bucket", "should_trigger", "prompt", "notes"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-root", default="~/.hermes/skills")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--overwrite", action="store_true", help="Rewrite even existing full eval matrices")
    args = ap.parse_args()

    root = Path(args.skills_root).expanduser().resolve()
    skill_mds = sorted(root.rglob("SKILL.md"))
    skills: List[Dict[str, str]] = []
    for p in skill_mds:
        text = p.read_text(errors="ignore")
        fm, _body = parse_frontmatter(text)
        rel = rel_skill(p, root)
        category = rel.split("/", 1)[0] if "/" in rel else rel
        name = display_name(rel, str(fm.get("name") or ""))
        desc = clean_description(str(fm.get("description") or ""), name)
        skills.append({"rel": rel, "category": category, "name": name, "description": desc, "path": str(p), "eval_path": str(p.parent / "evals" / "prompts.csv")})

    changed: List[Dict[str, Any]] = []
    preserved: List[Dict[str, Any]] = []
    for s in skills:
        eval_path = Path(s["eval_path"])
        before = read_existing_counts(eval_path)
        if is_full(before) and not args.overwrite:
            preserved.append({"rel": s["rel"], "eval_path": s["eval_path"], "before": before})
            continue
        neighbors = choose_neighbors(skills, s)
        rows = generate_rows(s, neighbors)
        write_csv(eval_path, rows)
        after = read_existing_counts(eval_path)
        changed.append({"rel": s["rel"], "eval_path": s["eval_path"], "before": before, "after": after, "neighbors": [n["rel"] for n in neighbors]})

    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else root.parent / "docs" / "private" / f"skill-routing-eval-coverage-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "skills_root": str(root),
        "skill_count": len(skills),
        "changed_count": len(changed),
        "preserved_count": len(preserved),
        "required_buckets": REQUIRED,
        "changed": changed,
        "preserved": preserved,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({k: manifest[k] for k in ["skills_root", "skill_count", "changed_count", "preserved_count"]} | {"manifest": str(manifest_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
