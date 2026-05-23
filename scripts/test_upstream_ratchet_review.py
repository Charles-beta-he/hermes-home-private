#!/usr/bin/env python3
"""Tests for upstream-ratchet-review.py."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path.home() / ".hermes" / "scripts" / "upstream-ratchet-review.py"


def load_module():
    spec = importlib.util.spec_from_file_location("upstream_ratchet_review", SCRIPT)
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
    write(path, "agent/prompt_builder.py", "base\n")
    write(path, "docs/private/overlay-registry.md", "| ID | Purpose | Main touchpoints | Tests / evidence | Replay / retire rule |\n| --- | --- | --- | --- | --- |\n| prompt-cache-layering | cache | `agent/prompt_builder.py` | tests | keep |\n")
    git(path, "add", ".")
    git(path, "commit", "-m", "base")
    git(path, "remote", "add", "origin", "https://github.com/Charles-beta-he/hermes-agent-private.git")
    git(path, "remote", "add", "upstream", "https://github.com/NousResearch/hermes-agent.git")


def make_upstream_change(repo: Path) -> str:
    git(repo, "checkout", "-b", "upstream_work")
    write(repo, "agent/prompt_builder.py", "base\nupstream semantic change\n")
    write(repo, "agent/new_feature.py", "feature\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "upstream semantic change")
    upstream = git(repo, "rev-parse", "HEAD")
    git(repo, "branch", "-f", "upstream/main", upstream)
    git(repo, "checkout", "private/main")
    return upstream


def test_build_review_state_contains_focus_diff_and_constraints():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        upstream = make_upstream_change(repo)
        watch = m.collect_watch_report(repo, no_fetch=True, watch_state=Path(td) / "watch-state.json")
        out_dir = Path(td) / "report"
        state, state_path = m.build_review_state(repo, watch, out_dir)
        assert state_path.exists()
        assert state["schema"] == "hermes_multimodel_task_v1"
        assert state["context"]["upstream_sha"] == upstream
        assert state["context"]["focus_paths"] == ["agent/prompt_builder.py"]
        assert "No auto-merge" in "\n".join(state["constraints"])
        assert "upstream semantic change" in state["context"]["focus_diffs"][0]["diff_excerpt"]


def test_dry_run_review_records_state_and_packet():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        upstream = make_upstream_change(repo)
        args = SimpleNamespace(
            repo=str(repo),
            review_state=str(Path(td) / "review-state.json"),
            watch_state=str(Path(td) / "watch-state.json"),
            report_dir=str(Path(td) / "reports"),
            tier="T0",
            timeout=30,
            discussion=False,
            no_fetch=True,
            only_if_needed=False,
            force=False,
            dry_run=True,
        )
        summary, should_print = m.run_review(args)
        assert should_print is True
        assert summary["status"] == "dry_run_review_packet_built"
        assert summary["upstream_sha"] == upstream
        packet = Path(summary["packet_path"])
        assert packet.exists()
        assert not Path(args.review_state).exists()


def test_only_if_needed_suppresses_already_reviewed():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        upstream = make_upstream_change(repo)
        review_state = Path(td) / "review-state.json"
        review_state.write_text(json.dumps({"reviewed_upstream": {upstream: {"status": "reviewed"}}}), encoding="utf-8")
        args = SimpleNamespace(
            repo=str(repo),
            review_state=str(review_state),
            watch_state=str(Path(td) / "watch-state.json"),
            report_dir=str(Path(td) / "reports"),
            tier="T0",
            timeout=30,
            discussion=False,
            no_fetch=True,
            only_if_needed=True,
            force=False,
            dry_run=True,
        )
        summary, should_print = m.run_review(args)
        assert should_print is False
        assert summary["status"] == "no_review_needed"


def test_not_certified_review_does_not_suppress_future_runs():
    m = load_module()
    original_run_multimodel = getattr(m, "run_multimodel")
    try:
        setattr(m, "run_multimodel", lambda *a, **k: {
            "merged_plan": {
                "status": "degraded_not_certified",
                "summary": "below truth gate",
                "fanout_certification": {"certified": False},
                "truth_assessment": {"can_certify_truth": False},
                "discussion": {},
            },
            "stdout_excerpt": "",
            "stderr_excerpt": "",
        })
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            init_repo(repo)
            upstream = make_upstream_change(repo)
            args = SimpleNamespace(
                repo=str(repo),
                review_state=str(Path(td) / "review-state.json"),
                watch_state=str(Path(td) / "watch-state.json"),
                report_dir=str(Path(td) / "reports"),
                tier="T0",
                timeout=30,
                discussion=False,
                no_fetch=True,
                only_if_needed=True,
                force=False,
                dry_run=False,
            )
            summary, should_print = m.run_review(args)
            assert should_print is True
            assert summary["status"] == "review_not_certified"
            assert summary["review_certified"] is False
            saved = json.loads(Path(args.review_state).read_text(encoding="utf-8"))
            assert saved["reviewed_upstream"][upstream]["status"] == "not_certified"
            assert m.review_needed(saved, upstream, force=False) is True
    finally:
        setattr(m, "run_multimodel", original_run_multimodel)


def test_review_state_redacts_secret_shaped_diff_content():
    m = load_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        init_repo(repo)
        git(repo, "checkout", "-b", "upstream_secret")
        write(repo, "agent/prompt_builder.py", "base\napi_key=sk-abcdefghijklmnopqrstuvwxyz123456\nAuthorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890\ntoken=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n")
        git(repo, "add", ".")
        git(repo, "commit", "-m", "upstream secret-shaped fixture")
        upstream = git(repo, "rev-parse", "HEAD")
        git(repo, "branch", "-f", "upstream/main", upstream)
        git(repo, "checkout", "private/main")
        watch = m.collect_watch_report(repo, no_fetch=True, watch_state=Path(td) / "watch-state.json")
        state, state_path = m.build_review_state(repo, watch, Path(td) / "report")
        blob = json.dumps(state, ensure_ascii=False) + state_path.read_text(encoding="utf-8")
        assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in blob
        assert "Bearer abcdefghijklmnopqrstuvwxyz1234567890" not in blob
        assert "ghp_abcdefghijklmnopqrstuvwxyz1234567890" not in blob
        assert "[REDACTED]" in blob


def test_model_review_certification_gates():
    m = load_module()
    ok_plan = {
        "fanout_certification": {"certified": True},
        "truth_assessment": {"can_certify_truth": True},
        "discussion": {"can_claim_complete_certification": True},
    }
    certified, reasons = m.model_review_certified(ok_plan, discussion_required=True)
    assert certified is True
    assert reasons == []

    certified, reasons = m.model_review_certified({"fanout_certification": {"certified": False}}, discussion_required=False)
    assert certified is False
    assert "fanout_not_certified" in reasons

    certified, reasons = m.model_review_certified({"fanout_certification": {"certified": True}, "truth_assessment": {"can_certify_truth": False}}, discussion_required=False)
    assert certified is False
    assert "truth_gate_rejected" in reasons

    certified, reasons = m.model_review_certified({"fanout_certification": {"certified": True}, "truth_assessment": {"can_certify_truth": True}, "discussion": {}}, discussion_required=True)
    assert certified is False
    assert "discussion_not_certified" in reasons


if __name__ == "__main__":
    test_build_review_state_contains_focus_diff_and_constraints()
    test_dry_run_review_records_state_and_packet()
    test_only_if_needed_suppresses_already_reviewed()
    test_not_certified_review_does_not_suppress_future_runs()
    test_review_state_redacts_secret_shaped_diff_content()
    test_model_review_certification_gates()
    print("OK: upstream ratchet review tests passed")
