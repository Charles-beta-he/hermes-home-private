#!/usr/bin/env python3
"""Create a durable Hermes product-workflow workspace.

This script is intentionally local-only: it writes starter artifacts and never
contacts external services or enqueues taskpool items.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
DEFAULT_ROOT = HOME / ".hermes" / "workflows" / "product"
SKILL_DIR = HOME / ".hermes" / "skills" / "software-development" / "product-workflow-operating-system"
TEMPLATE_DIR = SKILL_DIR / "templates"
VALID_CHAINS = {"opportunity-analysis", "prd-to-engineering", "ai-code-shipping", "full-lifecycle"}


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-._")
    if not value:
        raise SystemExit("slug is empty after normalization")
    return value[:96]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_template(name: str) -> str:
    path = TEMPLATE_DIR / name
    if not path.exists():
        raise SystemExit(f"missing template: {path}")
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SystemExit(f"refusing to overwrite existing file: {path} (use --overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, obj: object, overwrite: bool) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n", overwrite)


def render(template: str, slug: str, title: str, chain: str, now: str) -> str:
    return (
        template.replace("<slug>", slug)
        .replace("<title>", title)
        .replace("opportunity-analysis|prd-to-engineering|ai-code-shipping|full-lifecycle", chain)
        .replace("YYYY-MM-DDTHH:MM:SSZ", now)
    )


def build_workspace(args: argparse.Namespace) -> Path:
    slug = slugify(args.slug or args.title)
    chain = args.chain
    if chain not in VALID_CHAINS:
        raise SystemExit(f"invalid chain {chain!r}; expected one of {sorted(VALID_CHAINS)}")
    root = Path(args.root).expanduser() if args.root else DEFAULT_ROOT
    workdir = root / slug
    now = utc_now()

    if args.dry_run:
        print(json.dumps({"status": "dry_run", "workdir": str(workdir), "chain": chain}, ensure_ascii=False, indent=2))
        return workdir

    workdir.mkdir(parents=True, exist_ok=True)
    for dirname in [
        "00-intake",
        "01-discovery",
        "02-strategy",
        "03-metrics",
        "04-prd",
        "05-risk",
        "06-planning",
        "07-build",
        "08-shipping",
        "09-launch",
        "10-measure",
        "evidence",
        "tasks",
    ]:
        (workdir / dirname).mkdir(exist_ok=True)

    write_text(workdir / "00-intake" / "intent-card.md", render(read_template("intent-card.md"), slug, args.title, chain, now), args.overwrite)
    write_text(workdir / "workflow-state.yaml.md", render(read_template("workflow-state.yaml.md"), slug, args.title, chain, now), args.overwrite)
    write_text(workdir / "decisions.md", render(read_template("decision-log.md"), slug, args.title, chain, now), args.overwrite)

    evidence = json.loads(read_template("evidence-bundle.json"))
    evidence["generated_at"] = now
    evidence["workflow_slug"] = slug
    write_json(workdir / "evidence" / "evidence-bundle.json", evidence, args.overwrite)

    candidates = json.loads(read_template("task-candidates.json"))
    candidates["workflow_slug"] = slug
    # Workspaces start with no taskpool side effects.  Users/agents must fill
    # candidates deliberately before running product_workflow_taskpool_ingest.py.
    candidates["candidates"] = []
    write_json(workdir / "tasks" / "task-candidates.json", candidates, args.overwrite)

    readme = f"""# {args.title}\n\nProduct workflow workspace created by `product-workflow-operating-system`.\n\n- Slug: `{slug}`\n- Chain: `{chain}`\n- Created: `{now}`\n- Authority boundary: local artifacts only; no taskpool enqueue, no external side effects.\n\nStart with `00-intake/intent-card.md`, then update `workflow-state.yaml.md` as stages pass gates.\n"""
    write_text(workdir / "README.md", readme, args.overwrite)

    print(json.dumps({"status": "ok", "workdir": str(workdir), "chain": chain, "created_at": now}, ensure_ascii=False, indent=2))
    return workdir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Hermes product-workflow workspace")
    parser.add_argument("--title", required=True, help="Human-readable workflow title")
    parser.add_argument("--slug", help="Stable workspace slug; defaults to slugified title")
    parser.add_argument("--chain", default="opportunity-analysis", choices=sorted(VALID_CHAINS))
    parser.add_argument("--root", help=f"Output root; default {DEFAULT_ROOT}")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite starter files if they already exist")
    parser.add_argument("--dry-run", action="store_true", help="Print planned workspace path without writing")
    args = parser.parse_args()
    build_workspace(args)


if __name__ == "__main__":
    main()
