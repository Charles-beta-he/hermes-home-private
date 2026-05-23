#!/usr/bin/env python3
"""Hermes private fork upstream ratchet watcher.

Detects official upstream movement for the private Hermes line without merging,
rebasing, checking out branches, or promoting private/main.

Default behaviour is cron/no-agent friendly:
- no stdout when upstream/main has not changed since the last recorded check;
- actionable JSON when new upstream commits are detected or a safety blocker exists;
- non-zero only for broken prerequisites / command failures.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOME = Path.home()
DEFAULT_REPO = HOME / ".hermes" / "hermes-agent"
DEFAULT_STATE = HOME / ".hermes" / "state" / "upstream-ratchet.json"
DEFAULT_OVERLAY_REGISTRY = DEFAULT_REPO / "docs" / "private" / "overlay-registry.md"
OFFICIAL_REMOTE_NEEDLE = "NousResearch/hermes-agent"
PRIVATE_REMOTE_NEEDLE = "Charles-beta-he/hermes-agent-private"
WATCH_SCHEMA = "hermes_private_upstream_ratchet_watch_v1"


class WatchError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_git(repo: Path, args: list[str], *, timeout: int = 60, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if check and proc.returncode != 0:
        raise WatchError(f"git {' '.join(args)} failed ({proc.returncode}): {err or out}")
    return out


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise WatchError(f"bad state JSON at {path}: {exc}") from exc


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def lockfile(path: Path, stale_seconds: int = 1800):
    path.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            age = now - path.stat().st_mtime
        except FileNotFoundError:
            age = 0
        if age > stale_seconds:
            try:
                path.unlink()
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                raise WatchError(f"ratchet watcher lock is active: {path}") from exc
        else:
            raise WatchError(f"ratchet watcher lock is active: {path}")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"pid": os.getpid(), "created_at": utc_now()}) + "\n")
    try:
        yield
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def parse_overlay_touchpoints(registry_path: Path) -> list[dict[str, Any]]:
    if not registry_path.exists():
        return []
    overlays: list[dict[str, Any]] = []
    for line in registry_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "| ID |" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        overlay_id = cells[0].strip("`")
        touchpoint_cell = cells[2]
        touchpoints = [m.strip() for m in re.findall(r"`([^`]+)`", touchpoint_cell)]
        if overlay_id:
            overlays.append({"id": overlay_id, "touchpoints": touchpoints})
    return overlays


def normalize_path(p: str) -> str:
    return p.strip().lstrip("./")


def path_matches_touchpoint(path: str, touchpoint: str) -> bool:
    path = normalize_path(path)
    touchpoint = normalize_path(touchpoint)
    if not path or not touchpoint:
        return False
    if touchpoint.endswith("/"):
        return path.startswith(touchpoint)
    return path == touchpoint or path.startswith(touchpoint.rstrip("/") + "/")


def build_impact_map(repo: Path, old_rev: str, new_rev: str, overlays: list[dict[str, Any]]) -> dict[str, Any]:
    changed_raw = run_git(repo, ["diff", "--name-only", f"{old_rev}..{new_rev}"], timeout=120)
    changed_paths = [p for p in changed_raw.splitlines() if p.strip()]
    impacted: list[dict[str, Any]] = []
    for overlay in overlays:
        hits: list[str] = []
        for path in changed_paths:
            if any(path_matches_touchpoint(path, tp) for tp in overlay.get("touchpoints", [])):
                hits.append(path)
        if hits:
            impacted.append({
                "id": overlay.get("id"),
                "matched_paths": sorted(set(hits))[:25],
                "matched_path_count": len(set(hits)),
            })
    return {
        "changed_path_count": len(changed_paths),
        "changed_paths_sample": changed_paths[:80],
        "overlay_count": len(overlays),
        "impacted_overlay_count": len(impacted),
        "impacted_overlays": impacted,
    }


def collect(repo: Path, state_path: Path, registry_path: Path, *, no_fetch: bool) -> tuple[dict[str, Any], bool]:
    if not (repo / ".git").exists():
        raise WatchError(f"not a git checkout: {repo}")

    branch = run_git(repo, ["branch", "--show-current"])
    origin = run_git(repo, ["remote", "get-url", "origin"])
    upstream = run_git(repo, ["remote", "get-url", "upstream"])
    if PRIVATE_REMOTE_NEEDLE not in origin:
        raise WatchError(f"origin is not private Hermes repo: {origin}")
    if OFFICIAL_REMOTE_NEEDLE not in upstream:
        raise WatchError(f"upstream is not official Hermes repo: {upstream}")
    if branch not in {"private/main"} and not branch.startswith("integrate/"):
        raise WatchError(f"unexpected branch {branch!r}; expected private/main or integrate/*")

    if not no_fetch:
        run_git(repo, ["fetch", "upstream", "main", "--quiet"], timeout=180)
        run_git(repo, ["fetch", "origin", "private/main", "--quiet"], timeout=180, check=False)

    private_ref = "private/main"
    upstream_ref = "upstream/main"
    private_sha = run_git(repo, ["rev-parse", private_ref])
    upstream_sha = run_git(repo, ["rev-parse", upstream_ref])
    merge_base = run_git(repo, ["merge-base", private_ref, upstream_ref])
    counts = run_git(repo, ["rev-list", "--left-right", "--count", f"{upstream_ref}...{private_ref}"])
    upstream_ahead, private_ahead = [int(x) for x in counts.split()[:2]]
    dirty_lines = run_git(repo, ["status", "--porcelain"], check=False).splitlines()

    state = read_json(state_path)
    previous = state.get("last_seen_upstream_sha") or state.get("upstream_sha")
    first_run = not bool(previous)
    changed = first_run or previous != upstream_sha
    old_for_diff = previous if previous else merge_base
    overlays = parse_overlay_touchpoints(registry_path)
    impact = build_impact_map(repo, old_for_diff, upstream_sha, overlays) if changed else state.get("last_impact_map", {})

    status = "new_upstream_detected" if changed else "no_change"
    blockers: list[str] = []
    if dirty_lines:
        blockers.append("dirty_worktree_blocks_integration_branch_creation")
    if upstream_ahead > 200:
        blockers.append("large_divergence_requires_review_batching")

    integrate_branch = f"integrate/upstream-{upstream_sha[:9]}"
    report = {
        "schema": WATCH_SCHEMA,
        "generated_at": utc_now(),
        "status": status,
        "ratchet_confirmed": True,
        "ratchet_stage": "detect_and_impact_map_only",
        "repo": str(repo),
        "branch": branch,
        "origin_private": PRIVATE_REMOTE_NEEDLE in origin,
        "upstream_official": OFFICIAL_REMOTE_NEEDLE in upstream,
        "private_ref": private_ref,
        "private_sha": private_sha,
        "upstream_ref": upstream_ref,
        "upstream_sha": upstream_sha,
        "previous_upstream_sha": previous,
        "merge_base": merge_base,
        "upstream_ahead_private": upstream_ahead,
        "private_ahead_upstream": private_ahead,
        "dirty_worktree": bool(dirty_lines),
        "dirty_sample": dirty_lines[:30],
        "safety_blockers": blockers,
        "proposed_integration_branch": integrate_branch,
        "impact_map": impact,
        "next_steps": [
            "Do not auto-promote private/main.",
            f"Create or reuse {integrate_branch} only after current worktree is clean or intentionally committed/stashed.",
            "Run docs/private/upgrade-sop.md ratchet flow: replay/retire overlays, post-update-check.py --fix, targeted tests, doctor/smoke.",
            "Advance private/main only after evidence is recorded in docs/private/stable-points.md.",
        ],
    }

    new_state = dict(state)
    new_state.update({
        "schema": WATCH_SCHEMA,
        "last_checked_at": report["generated_at"],
        "last_seen_upstream_sha": upstream_sha,
        "last_private_sha": private_sha,
        "last_merge_base": merge_base,
        "last_counts": {
            "upstream_ahead_private": upstream_ahead,
            "private_ahead_upstream": private_ahead,
        },
        "last_status": status,
        "last_safety_blockers": blockers,
        "last_proposed_integration_branch": integrate_branch,
        "last_impact_map": impact,
    })
    history = list(new_state.get("events") or [])
    if changed:
        history.append({
            "detected_at": report["generated_at"],
            "previous_upstream_sha": previous,
            "upstream_sha": upstream_sha,
            "private_sha": private_sha,
            "merge_base": merge_base,
            "counts": new_state["last_counts"],
            "safety_blockers": blockers,
            "proposed_integration_branch": integrate_branch,
        })
    new_state["events"] = history[-50:]
    write_json_atomic(state_path, new_state)
    return report, changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Watch official Hermes upstream as a private fork ratchet gate")
    parser.add_argument("--repo", default=str(DEFAULT_REPO))
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--overlay-registry", default=str(DEFAULT_OVERLAY_REGISTRY))
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--quiet-no-change", action="store_true", help="Print nothing when no upstream change and no blockers")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    state_path = Path(args.state).expanduser()
    registry_path = Path(args.overlay_registry).expanduser()
    lock_path = state_path.with_suffix(state_path.suffix + ".lock")
    try:
        with lockfile(lock_path):
            report, should_print = collect(repo, state_path, registry_path, no_fetch=args.no_fetch)
    except WatchError as exc:
        err = {"schema": WATCH_SCHEMA, "generated_at": utc_now(), "status": "error", "error": str(exc)}
        print(json.dumps(err, ensure_ascii=False, indent=2 if args.pretty else None))
        return 2

    if should_print or not args.quiet_no_change:
        print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
