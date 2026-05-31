#!/usr/bin/env python3
"""Create Feynman-inspired research artifact scaffolds for Hermes runs.

The script is intentionally small and dependency-free.  It does not execute
research, spawn agents, or mutate task lifecycle state; it only creates the
file-based working-memory/provenance skeleton that a Hermes worker can fill
with deterministic evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


FILLER_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def slugify(topic: str, max_words: int = 5) -> str:
    words = re.findall(r"[a-z0-9]+", topic.lower())
    kept = [word for word in words if word not in FILLER_WORDS]
    if not kept:
        kept = words or ["research"]
    return "-".join(kept[:max_words])


def write_if_missing(path: Path, content: str, overwrite: bool) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def plan_template(topic: str, slug: str, now: str) -> str:
    return f"""# Research Plan: {topic}

- Slug: `{slug}`
- Created: {now}
- Status: draft

## Key questions
- [ ] What exact question must the run answer?
- [ ] Which claims require primary-source evidence?
- [ ] Which checks would block delivery if missing?

## Evidence needed
| Claim / question | Required evidence | Owner | Status | Artifact |
|---|---|---|---|---|
| Primary landscape | URLs, docs, papers, repo paths | lead | pending | |
| Critical claims | source line / URL / command output | verifier | pending | |

## Scale decision
- Mode: direct | subagent-assisted
- Rationale:
- Subagent lanes, if any:
  - researcher-web:
  - researcher-papers:
  - verifier:

## Task ledger
| Task | Owner | Status | Output file | Notes |
|---|---|---|---|---|
| Plan created | lead | done | outputs/.plans/{slug}.md | scaffold only |

## Verification log
| Check | Status | Evidence |
|---|---|---|
| Required artifact scaffold | pending | |
| URL/source verification | pending | |
| Unsupported-claim sweep | pending | |

## Decision log
| Time | Decision | Evidence / reason |
|---|---|---|
| {now} | Created artifact scaffold | script-generated skeleton |
"""


def provenance_template(topic: str, slug: str, now: str) -> str:
    return f"""# Provenance: {topic}

- Date: {now}
- Slug: `{slug}`
- Plan: `outputs/.plans/{slug}.md`
- Final output: `outputs/{slug}.md`
- Verification: BLOCKED until evidence is filled and checked

## Source accounting
| Source ID | URL / artifact path | Type | Used for | Verification status |
|---|---|---|---|---|
| S1 |  |  |  | pending |

## Claims requiring support
| Claim | Support | Status |
|---|---|---|
|  |  | pending |

## Verification performed
| Check | Command / method | Result |
|---|---|---|
|  |  | pending |

## Removed or downgraded unsupported claims
- None recorded yet.

## Residual risk
- Scaffold only; do not treat this provenance sidecar as delivery proof until populated with real evidence.
"""


def draft_template(topic: str, slug: str) -> str:
    return f"""# {topic}

Draft placeholder for `{slug}`.

## Summary

## Findings

## Sources

"""


def changelog_entry(topic: str, slug: str, now: str) -> str:
    return f"""\n## {now} — {slug}\n- Objective: {topic}\n- Status: scaffolded; evidence gathering not yet performed.\n- Next: fill the plan ledger, gather evidence, then update provenance before delivery.\n"""


def create_scaffold(root: Path, topic: str, overwrite: bool) -> dict[str, object]:
    slug = slugify(topic)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    files = {
        root / "outputs" / ".plans" / f"{slug}.md": plan_template(topic, slug, now),
        root / "outputs" / ".drafts" / f"{slug}-draft.md": draft_template(topic, slug),
        root / "outputs" / f"{slug}.provenance.md": provenance_template(topic, slug, now),
    }
    written: list[str] = []
    skipped: list[str] = []
    for path, content in files.items():
        if write_if_missing(path, content, overwrite):
            written.append(str(path))
        else:
            skipped.append(str(path))

    changelog = root / "CHANGELOG.md"
    changelog.parent.mkdir(parents=True, exist_ok=True)
    if changelog.exists() and not overwrite:
        with changelog.open("a", encoding="utf-8") as handle:
            handle.write(changelog_entry(topic, slug, now))
        written.append(str(changelog))
    else:
        changelog.write_text(f"# Research Artifact Changelog\n{changelog_entry(topic, slug, now)}", encoding="utf-8")
        written.append(str(changelog))

    return {"slug": slug, "root": str(root), "written": written, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a research plan/provenance scaffold.")
    parser.add_argument("topic", help="Research topic or objective")
    parser.add_argument("--root", default=".", help="Workspace root for outputs/ and CHANGELOG.md")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing scaffold files")
    args = parser.parse_args()

    result = create_scaffold(Path(args.root).resolve(), args.topic, args.overwrite)
    print(f"slug={result['slug']}")
    for key in ("written", "skipped"):
        values = result[key]
        if not isinstance(values, list):
            raise TypeError(f"expected list result for {key}")
        print(f"{key}={len(values)}")
        for value in values:
            print(f"  {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
