"""Tests for social_distribution_adapter.py — safety behavior and dry-run correctness."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Make the adapter importable
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
from social_distribution_adapter import (
    Evidence,
    PlatformPreview,
    AdapterStatus,
    build_command_preview,
    check_adapter,
    load_package,
    map_payload,
    run,
    MATRIXMEDIA_REPO,
    POSTIZ_AGENT_REPO,
)

EVIDENCE_DIR = Path(
    os.path.expanduser(
        "~/.hermes/runs/social-distribution-dry-run-2026-06-11"
    )
)


def _make_pkg(title="Test", media_type="image", media_path=None):
    """Create a minimal valid package."""
    if media_path is None:
        media_path = str(EVIDENCE_DIR / "test-dummy.png")
        Path(media_path).touch()
    return {
        "title": title,
        "body": "Test body",
        "tags": ["test", "hermes"],
        "media": [{"type": media_type, "path": media_path}],
    }


def _write_pkg(pkg, dir):
    p = Path(dir) / "publish-package.json"
    p.write_text(json.dumps(pkg, ensure_ascii=False))
    return str(p)


# ── RED LINE TESTS ─────────────────────────────────────────────────────

def test_publish_mode_rejected_without_approval_token():
    """mode=publish must return error when no human_approval_token."""
    with tempfile.TemporaryDirectory() as td:
        pp = _write_pkg(_make_pkg(), td)
        ev = run(pp, mode="publish", human_approval_token=None)
        assert any(
            "RED_LINE" in e and "publish" in e.lower() for e in ev.errors
        ), f"Expected publish rejection, got: {ev.errors}"
        assert "publish_without_approval_token" in ev.red_lines_held


def test_publish_mode_allowed_with_approval_token():
    """mode=publish with token should not reject on the gate."""
    with tempfile.TemporaryDirectory() as td:
        pp = _write_pkg(_make_pkg(), td)
        ev = run(pp, mode="publish", human_approval_token="test-abc123")
        assert not any(
            "publish_without_approval_token" in r for r in ev.red_lines_held
        )
        assert ev.human_approval_token_provided is True


def test_all_previews_have_will_publish_false_in_dry_run():
    """In dry-run mode, every PlatformPreview.will_publish must be False."""
    with tempfile.TemporaryDirectory() as td:
        pp = _write_pkg(_make_pkg(), td)
        ev = run(pp, mode="dry-run")
        for pv in ev.platform_previews:
            assert pv.will_publish is False, (
                f"platform {pv.platform} has will_publish={pv.will_publish}"
            )


def test_load_package_rejects_invalid():
    """load_package must return errors for bad input."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "bad.json"
        p.write_text("not json")
        _, errors = load_package(str(p))
        assert errors

        p.write_text('{"wrong": "schema"}')
        _, errors = load_package(str(p))
        assert any("title" in e for e in errors)


def test_load_package_validates_media_paths():
    """Missing media paths must be reported."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "pkg.json"
        p.write_text(json.dumps({
            "title": "Test",
            "media": [{"type": "image", "path": "/nonexistent/img.png"}]
        }))
        _, errors = load_package(str(p))
        assert any("path_not_found" in e for e in errors)


# ── PLATFORM MAPPING TESTS ─────────────────────────────────────────────

def test_map_payload_applies_overrides():
    """Platform overrides should take precedence."""
    pkg = {
        "title": "Default title",
        "body": "Default body",
        "tags": ["general"],
        "media": [{"type": "image", "path": "/tmp/dummy.png"}],
        "platformOverrides": {
            "dy": {"title": "抖音专用标题", "tags": ["抖音", "AI"]}
        },
    }
    mapped, warnings = map_payload(pkg, "dy", "matrixmedia")
    assert mapped["title"] == "抖音专用标题"
    assert mapped["tags"] == ["抖音", "AI"]


def test_map_payload_truncates_long_titles():
    """Titles exceeding platform limits should be truncated with warning."""
    pkg = {
        "title": "A" * 30,
        "media": [{"type": "image", "path": "/tmp/dummy.png"}],
    }
    mapped, warnings = map_payload(pkg, "xhs", "matrixmedia")
    assert len(mapped["title"]) <= 20
    assert any("truncated" in w.lower() for w in warnings)


def test_command_preview_matrixmedia():
    """MatrixMedia command preview includes dry-run marker."""
    payload = {
        "title": "Hello",
        "body": "Body text",
        "tags": ["AI", "测试"],
        "media": [{"type": "image", "path": "/tmp/v.mp4"}],
    }
    cmd = build_command_preview(payload, "dy", "matrixmedia", {})
    assert "matrixmedia cli publish" in cmd
    assert "DRY-RUN ONLY" in cmd
    assert "will_publish=false" in cmd


def test_command_preview_postiz():
    """Postiz command preview for international platforms."""
    payload = {
        "title": "Hello World",
        "body": "Test",
        "tags": [],
        "media": [{"type": "image", "path": "/tmp/i.png"}],
    }
    cmd = build_command_preview(payload, "x", "postiz", {})
    assert "postiz posts:create" in cmd
    assert "DRY-RUN ONLY" in cmd


def test_command_preview_unsupported_platform():
    """Unsupported platform returns a note."""
    cmd = build_command_preview({}, "xhs", "postiz", {})
    assert "not supported" in cmd.lower()


# ── ADAPTER DETECTION TESTS ────────────────────────────────────────────

def test_check_adapter_reports_missing_binary():
    """check_adapter for non-existent binary returns login_status=unknown_binary_missing."""
    status = check_adapter("nonexistent-cli-tool", "no_such_binary_xyz")
    assert not status.available
    assert status.login_status == "unknown_binary_missing"


def test_matrixmedia_repo_exists():
    """The MatrixMedia repo checkout should be discoverable."""
    assert MATRIXMEDIA_REPO.exists(), (
        "MatrixMedia repo not found — run social-distribution-oss-verify first"
    )


def test_postiz_agent_repo_exists():
    """The postiz-agent repo checkout should be discoverable."""
    assert POSTIZ_AGENT_REPO.exists(), (
        "Postiz agent repo not found"
    )


# ── EVIDENCE STRUCTURE ─────────────────────────────────────────────────

def test_evidence_structure():
    """Evidence output has expected top-level keys."""
    with tempfile.TemporaryDirectory() as td:
        pp = _write_pkg(_make_pkg(), td)
        out = Path(td) / "evidence.json"
        ev = run(pp, mode="dry-run", out=str(out))
        assert out.exists()
        data = json.loads(out.read_text())
        for key in [
            "generated_at", "package_valid", "mode",
            "matrixmedia", "postiz", "platform_previews",
            "red_lines_held",
        ]:
            assert key in data, f"Missing key: {key}"


# ── SAMPLE PACKAGE ─────────────────────────────────────────────────────

def test_sample_package_is_valid():
    """The sample package must pass validation."""
    sp = EVIDENCE_DIR / "publish-package.sample.json"
    assert sp.exists(), "Sample package not found"
    _, errors = load_package(str(sp))
    # media paths in sample may not exist — that's expected
    path_errors = [e for e in errors if "path_not_found" not in e]
    assert not path_errors, f"Unexpected validation errors: {path_errors}"
