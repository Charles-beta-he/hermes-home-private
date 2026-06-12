#!/usr/bin/env python3
"""Hermes-native skill candidate staging harness.

Safe SkillClaw-inspired loop: local proof + existing skill + proposed patch
-> staged candidate artifacts under evidence/, never direct skill mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_DIR = Path.home() / ".hermes" / "evidence" / "skill-evolution-candidates"
FORMAL_SKILL_RE = re.compile(r"/(?:\.hermes/)?(?:profiles/[^/]+/)?skills/")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def path_is_formal_skill(path: Path) -> bool:
    s = "/" + str(path.expanduser().resolve())
    return bool(FORMAL_SKILL_RE.search(s))


def validate_candidate(skill_path: Path, evidence_paths: list[Path], proposal_path: Path, output_dir: Path) -> list[Check]:
    checks: list[Check] = []
    skill_text = _read(skill_path) if skill_path.exists() else ""
    proposal_text = _read(proposal_path) if proposal_path.exists() else ""
    frontmatter = parse_frontmatter(skill_text)

    checks.append(Check("existing_skill_exists", skill_path.exists() and skill_path.is_file(), str(skill_path)))
    checks.append(Check("skill_has_frontmatter", bool(frontmatter), "frontmatter keys: " + ",".join(sorted(frontmatter.keys()))))
    checks.append(Check("skill_has_name_or_description", bool(frontmatter.get("name") or frontmatter.get("description")), "requires reusable skill identity"))

    missing = [str(p) for p in evidence_paths if not p.exists()]
    checks.append(Check("evidence_paths_exist", not missing and bool(evidence_paths), "missing=" + json.dumps(missing, ensure_ascii=False)))
    proposal_mentions = [str(p) for p in evidence_paths if str(p) in proposal_text or p.name in proposal_text]
    checks.append(Check("proposal_references_evidence", len(proposal_mentions) == len(evidence_paths), "matched=" + json.dumps(proposal_mentions, ensure_ascii=False)))

    lower = proposal_text.lower()
    checks.append(Check("proposal_has_rollback", "rollback" in lower or "回滚" in proposal_text, "proposal must describe rollback/revert path"))
    checks.append(Check("proposal_has_patch_intent", any(tok in lower for tok in ("patch", "diff", "update", "frontmatter", "trigger", "skill")) or "补丁" in proposal_text, "proposal must be an actionable skill patch candidate"))

    broad_terms = [r"\balways\b", r"\beverything\b", r"\bany task\b", "所有任务", "任何任务", "全局触发"]
    broad_hits = [pat for pat in broad_terms if re.search(pat, lower if pat.startswith("\\b") else proposal_text)]
    checks.append(Check("trigger_breadth_limited", not broad_hits, "broad_hits=" + json.dumps(broad_hits, ensure_ascii=False)))

    checks.append(Check("output_not_formal_skill_store", not path_is_formal_skill(output_dir), str(output_dir)))
    return checks


def stage_candidate(skill_path: Path, evidence_paths: list[Path], proposal_path: Path, output_dir: Path, title: str, dry_run: bool = False) -> dict[str, Any]:
    skill_path = skill_path.expanduser().resolve()
    proposal_path = proposal_path.expanduser().resolve()
    evidence_paths = [p.expanduser().resolve() for p in evidence_paths]
    output_dir = output_dir.expanduser().resolve()
    checks = validate_candidate(skill_path, evidence_paths, proposal_path, output_dir)
    ok = all(c.ok for c in checks)
    seed = "|".join([title, str(skill_path), str(proposal_path), *map(str, evidence_paths)])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", title.strip()).strip("-")[:70] or "skill-candidate"
    candidate_id = f"{stamp}-{slug}-{digest}"

    candidate = {
        "schema_version": "skill_candidate_staging.v1",
        "candidate_id": candidate_id,
        "title": title,
        "status": "staged" if ok and not dry_run else ("dry_run_ok" if ok else "blocked"),
        "created_at": stamp,
        "source_skill": {"path": str(skill_path), "sha256": _sha256(skill_path) if skill_path.exists() else None},
        "proposal": {"path": str(proposal_path), "sha256": _sha256(proposal_path) if proposal_path.exists() else None},
        "evidence": [{"path": str(p), "sha256": _sha256(p) if p.exists() else None} for p in evidence_paths],
        "checks": [c.as_dict() for c in checks],
        "governance": {
            "no_direct_skill_write": True,
            "requires_human_or_skill_manage_apply": True,
            "blocked_side_effects": ["config_rewrite", "proxy_start", "cloud_upload", "cross_profile_write", "auto_publish"],
        },
    }
    if ok and not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / f"{candidate_id}.json"
        md_path = output_dir / f"{candidate_id}.md"
        json_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(candidate, proposal_path), encoding="utf-8")
        candidate["artifact_paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return candidate


def render_markdown(candidate: dict[str, Any], proposal_path: Path) -> str:
    proposal_text = _read(proposal_path) if proposal_path.exists() else ""
    checks = "\n".join(f"- [{'x' if c['ok'] else ' '}] {c['name']}: {c['detail']}" for c in candidate["checks"])
    evidence = "\n".join(f"- `{e['path']}` sha256={e['sha256']}" for e in candidate["evidence"])
    return f"""# Skill candidate staging: {candidate['title']}

- candidate_id: `{candidate['candidate_id']}`
- status: `{candidate['status']}`
- source_skill: `{candidate['source_skill']['path']}` sha256={candidate['source_skill']['sha256']}
- proposal: `{candidate['proposal']['path']}` sha256={candidate['proposal']['sha256']}

## Deterministic checks
{checks}

## Evidence
{evidence}

## Governance
No direct skill write was performed. Apply requires human review or `skill_manage`-equivalent controlled executor with read-back/proof-check.
Blocked side effects: config rewrite, proxy start, cloud upload, cross-profile write, auto-publish.

## Proposal body

{proposal_text}
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stage a Hermes skill patch candidate without applying it")
    p.add_argument("stage", nargs="?", default="stage", choices=["stage"])
    p.add_argument("--skill", required=True, type=Path, help="Existing Hermes skill SKILL.md to patch later")
    p.add_argument("--evidence", required=True, action="append", type=Path, help="Local proof/transcript/task evidence path; repeatable")
    p.add_argument("--proposal", required=True, type=Path, help="Markdown proposal containing patch intent, evidence refs, rollback")
    p.add_argument("--title", required=True)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = stage_candidate(args.skill, args.evidence, args.proposal, args.output_dir, args.title, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"staged", "dry_run_ok"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
