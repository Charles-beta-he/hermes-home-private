#!/usr/bin/env python3
"""Tests for upstream-ratchet-watch.py."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "upstream-ratchet-watch.py"


def load_module():
    spec = importlib.util.spec_from_file_location("upstream_ratchet_watch", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return (proc.stdout or "").strip()


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_repo(path: Path) -> None:
    git(path, "init", "-b", "private/main")
    git(path, "config", "user.email", "test@example.com")
    git(path, "config", "user.name", "Ratchet Test")
    write(path, "README.md", "base\n")
    git(path, "add", ".")
    git(path, "commit", "-m", "base")
    git(path, "remote", "add", "origin", "https://github.com/Charles-beta-he/hermes-agent-private.git")
    git(path, "remote", "add", "upstream", "https://github.com/NousResearch/hermes-agent.git")


def test_parse_overlay_touchpoints_and_path_matching():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        registry = Path(td) / "overlay-registry.md"
        registry.write_text(
            "| ID | Purpose | Main touchpoints | Tests / evidence | Replay / retire rule |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| prompt-cache-layering | cache | `agent/prompt_builder.py`, `agent/prompt_caching.py` | tests | keep |\n",
            encoding="utf-8",
        )
        overlays = m.parse_overlay_touchpoints(registry)
        assert overlays == [{"id": "prompt-cache-layering", "touchpoints": ["agent/prompt_builder.py", "agent/prompt_caching.py"]}]
        assert m.path_matches_touchpoint("agent/prompt_builder.py", "agent/prompt_builder.py")
        assert m.path_matches_touchpoint("agent/prompt_caching.py", "agent/")
        assert not m.path_matches_touchpoint("tools/memory_tool.py", "agent/")


def test_first_run_detects_upstream_and_writes_state():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        base = git(repo, "rev-parse", "HEAD")
        git(repo, "checkout", "-b", "upstream_work")
        write(repo, "agent/prompt_builder.py", "upstream change\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "upstream change")
        upstream = git(repo, "rev-parse", "HEAD")
        git(repo, "branch", "-f", "upstream/main", upstream)
        git(repo, "checkout", "private/main")

        registry = repo / "docs/private/overlay-registry.md"
        registry.parent.mkdir(parents=True, exist_ok=True)
        registry.write_text(
            "| ID | Purpose | Main touchpoints | Tests / evidence | Replay / retire rule |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| prompt-cache-layering | cache | `agent/prompt_builder.py` | tests | keep |\n",
            encoding="utf-8",
        )
        state = Path(td) / "state.json"
        report, should_print = m.collect(repo, state, registry, no_fetch=True)
        assert should_print is True
        assert report["status"] == "new_upstream_detected"
        assert report["ratchet_confirmed"] is True
        assert report["upstream_sha"] == upstream
        assert report["impact_map"]["impacted_overlay_count"] == 1
        saved = json.loads(state.read_text(encoding="utf-8"))
        assert saved["last_seen_upstream_sha"] == upstream
        assert saved["events"]


def test_second_run_is_silent_when_no_change_and_clean():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        head = git(repo, "rev-parse", "HEAD")
        git(repo, "branch", "upstream/main", head)
        state = Path(td) / "state.json"
        registry = Path(td) / "missing.md"
        report, should_print = m.collect(repo, state, registry, no_fetch=True)
        assert report["status"] == "new_upstream_detected"
        report2, should_print2 = m.collect(repo, state, registry, no_fetch=True)
        assert report2["status"] == "no_change"
        assert should_print2 is False


def test_dirty_tree_blocks_integration_but_still_reports():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        head = git(repo, "rev-parse", "HEAD")
        git(repo, "branch", "upstream/main", head)
        write(repo, "dirty.txt", "dirty\n")
        state = Path(td) / "state.json"
        report, should_print = m.collect(repo, state, Path(td) / "missing.md", no_fetch=True)
        assert should_print is True
        assert report["dirty_worktree"] is True
        assert "dirty_worktree_blocks_integration_branch_creation" in report["safety_blockers"]


if __name__ == "__main__":
    test_parse_overlay_touchpoints_and_path_matching()
    test_first_run_detects_upstream_and_writes_state()
    test_second_run_is_silent_when_no_change_and_clean()
    test_dirty_tree_blocks_integration_but_still_reports()
    print("OK: upstream ratchet watcher tests passed")
