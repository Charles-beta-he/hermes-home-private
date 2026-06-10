#!/usr/bin/env python3
"""Tests for social_distribution_adapter.py.
Run with: python3 ~/.hermes/scripts/test_social_distribution_adapter.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "social_distribution_adapter.py"


def load_module():
    spec = importlib.util.spec_from_file_location("social_distribution_adapter_under_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_validate_publish_package_rejects_publish_without_explicit_approval():
    mod = load_module()
    package = {
        "title": "测试标题",
        "body": "正文 #标签",
        "media": [{"type": "video", "path": "/tmp/demo.mp4"}],
        "targets": [
            {"platform": "douyin", "adapter": "matrixmedia", "mode": "publish", "account": "13800138000"}
        ],
    }

    result = mod.validate_publish_package(package, media_exists=lambda p: True)

    assert result["ok"] is False
    assert "publish_requires_explicit_approval" in result["errors"]


def test_matrixmedia_dry_run_maps_payload_and_never_builds_publish_command():
    mod = load_module()
    package = {
        "title": "AI 眼镜现场注意力",
        "body": "从共享注意力到内容证据链",
        "tags": ["AI眼镜", "小红书"],
        "cover": "/tmp/cover.jpg",
        "media": [{"type": "video", "path": "/tmp/video.mp4"}],
        "targets": [
            {"platform": "xhs", "adapter": "matrixmedia", "mode": "dry-run", "account": "13800138000"}
        ],
    }

    adapter = mod.MatrixMediaAdapter(binary="matrixmedia")
    result = adapter.plan(package, package["targets"][0], media_exists=lambda p: True, command_exists=lambda c: False)

    assert result["ok"] is True
    assert result["adapter"] == "matrixmedia"
    assert result["platform"] == "xhs"
    assert result["mode"] == "dry-run"
    assert result["will_publish"] is False
    assert result["login_check"]["status"] == "unknown_binary_missing"
    assert result["mapped_payload"]["title"] == "AI 眼镜现场注意力"
    assert result["mapped_payload"]["tags"] == "AI眼镜,小红书"
    assert result["commands"]["publish_preview"][0:3] == ["matrixmedia", "cli", "publish"]
    assert result["commands"]["publish_preview"].count("--dry-run") == 1


def test_postiz_draft_plan_uses_external_cli_boundary():
    mod = load_module()
    package = {
        "title": "国际平台草稿",
        "body": "Content body",
        "media": [{"type": "image", "path": "/tmp/img.jpg"}],
        "targets": [
            {"platform": "linkedin", "adapter": "postiz", "mode": "draft", "integration_id": "linkedin-123"}
        ],
    }

    adapter = mod.PostizAdapter(binary="postiz")
    result = adapter.plan(package, package["targets"][0], media_exists=lambda p: True, command_exists=lambda c: False)

    assert result["ok"] is True
    assert result["adapter"] == "postiz"
    assert result["mode"] == "draft"
    assert result["will_publish"] is False
    assert result["commands"]["create_draft_preview"][:3] == ["postiz", "posts:create", "-c"]
    assert "-t" in result["commands"]["create_draft_preview"]
    assert "draft" in result["commands"]["create_draft_preview"]


def test_cli_dry_run_writes_readable_evidence_bundle():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        video = root / "video.mp4"
        video.write_bytes(b"fake video fixture")
        package = root / "publish-package.json"
        out = root / "dry-run.json"
        package.write_text(json.dumps({
            "title": "CLI dry-run",
            "body": "body",
            "media": [{"type": "video", "path": str(video)}],
            "targets": [
                {"platform": "douyin", "adapter": "matrixmedia", "mode": "dry-run", "account": "13800138000"},
                {"platform": "linkedin", "adapter": "postiz", "mode": "draft", "integration_id": "linkedin-123"},
            ],
        }, ensure_ascii=False), encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "dry-run", "--package", str(package), "--out", str(out)],
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": "/usr/bin:/bin"},
        )

        assert proc.returncode == 0, proc.stderr + proc.stdout
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["ok"] is True
        assert data["safety"]["default_public_publish"] == "blocked_without_explicit_approval"
        assert [r["adapter"] for r in data["results"]] == ["matrixmedia", "postiz"]
        assert all(r["will_publish"] is False for r in data["results"])


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    for name in tests:
        globals()[name]()
    print(f"PASS {len(tests)} tests")
