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


def preview_candidate(skill_path: Path, evidence_paths: list[Path], proposal_path: Path, output_dir: Path, title: str) -> dict[str, Any]:
    """Return a dry-run candidate plus the exact Markdown preview without writing artifacts."""
    candidate = stage_candidate(skill_path, evidence_paths, proposal_path, output_dir, title, dry_run=True)
    candidate["preview_markdown"] = render_markdown(candidate, proposal_path.expanduser().resolve())
    candidate["governance"]["preview_only"] = True
    return candidate


def read_back_candidate(json_path: Path) -> dict[str, Any]:
    """Read a staged candidate and deterministically verify linked artifacts and hashes."""
    json_path = json_path.expanduser().resolve()
    payload = json.loads(_read(json_path))
    checks: list[Check] = [Check("candidate_json_exists", json_path.exists(), str(json_path))]

    for section in ("source_skill", "proposal"):
        item = payload.get(section) or {}
        path = Path(item.get("path") or "")
        exists = path.exists() and path.is_file()
        expected = item.get("sha256")
        actual = _sha256(path) if exists else None
        checks.append(Check(f"{section}_exists", exists, str(path)))
        checks.append(Check(f"{section}_sha256_matches", exists and actual == expected, f"expected={expected} actual={actual}"))

    for idx, item in enumerate(payload.get("evidence") or []):
        path = Path(item.get("path") or "")
        exists = path.exists() and path.is_file()
        expected = item.get("sha256")
        actual = _sha256(path) if exists else None
        checks.append(Check(f"evidence_{idx}_exists", exists, str(path)))
        checks.append(Check(f"evidence_{idx}_sha256_matches", exists and actual == expected, f"expected={expected} actual={actual}"))

    artifact_paths = payload.get("artifact_paths") or {}
    md_path = Path(artifact_paths.get("markdown") or json_path.with_suffix(".md"))
    md_exists = md_path.exists() and md_path.is_file()
    md_text = _read(md_path) if md_exists else ""
    checks.append(Check("markdown_artifact_exists", md_exists, str(md_path)))
    checks.append(Check("markdown_mentions_candidate_id", payload.get("candidate_id", "") in md_text, "candidate id must be visible in read-back"))
    checks.append(Check("governance_requires_controlled_apply", bool((payload.get("governance") or {}).get("requires_human_or_skill_manage_apply")), "apply remains gated"))
    checks.append(Check("staged_checks_all_ok", all(c.get("ok") for c in payload.get("checks") or []), "stored deterministic checks must pass"))
    return {"candidate_id": payload.get("candidate_id"), "status": payload.get("status"), "checks": [c.as_dict() for c in checks], "ok": all(c.ok for c in checks)}


def proof_check_candidate(json_path: Path) -> dict[str, Any]:
    """Fail-closed proof check for a staged candidate before any formal skill mutation."""
    json_path = json_path.expanduser().resolve()
    result = read_back_candidate(json_path)
    payload = json.loads(_read(json_path))
    required = {"config_rewrite", "proxy_start", "cloud_upload", "cross_profile_write", "auto_publish"}
    declared = set((payload.get("governance") or {}).get("blocked_side_effects", []))
    result["checks"].append(Check("blocked_side_effects_declared", required.issubset(declared), "required blocked side effects remain declared").as_dict())
    result["checks"].append(Check("no_formal_skill_output", not path_is_formal_skill(json_path.parent), str(json_path.parent)).as_dict())
    result["ok"] = all(c.get("ok") for c in result["checks"])
    result["status"] = "proof_ok" if result["ok"] else "proof_failed"
    return result


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
    p.add_argument("command", nargs="?", default="stage", choices=["stage", "preview", "read-back", "proof-check"])
    p.add_argument("--skill", type=Path, help="Existing Hermes skill SKILL.md to patch later")
    p.add_argument("--evidence", action="append", type=Path, default=[], help="Local proof/transcript/task evidence path; repeatable")
    p.add_argument("--proposal", type=Path, help="Markdown proposal containing patch intent, evidence refs, rollback")
    p.add_argument("--title")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--candidate", type=Path, help="Staged candidate JSON path for read-back/proof-check")
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"stage", "preview"}:
        missing = [name for name in ("skill", "proposal", "title") if getattr(args, name) is None]
        if missing or not args.evidence:
            raise SystemExit(f"{args.command} requires --skill, --proposal, --title, and at least one --evidence")
        if args.command == "preview":
            result = preview_candidate(args.skill, args.evidence, args.proposal, args.output_dir, args.title)
        else:
            result = stage_candidate(args.skill, args.evidence, args.proposal, args.output_dir, args.title, args.dry_run)
    else:
        if args.candidate is None:
            raise SystemExit(f"{args.command} requires --candidate")
        result = read_back_candidate(args.candidate) if args.command == "read-back" else proof_check_candidate(args.candidate)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok", result.get("status") in {"staged", "dry_run_ok"}) else 2


if __name__ == "__main__":
    raise SystemExit(main())
