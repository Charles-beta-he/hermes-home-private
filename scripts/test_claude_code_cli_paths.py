#!/usr/bin/env python3
"""Regression tests for Claude Code CLI runtime selection.

These tests prevent local health/certification helpers from routing Claude Max /
Claude Code OAuth checks through Hermes' Anthropic-compatible adapter path.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


certify = load_module("multimodel_autonomy_certify", ROOT / "multimodel_autonomy_certify.py")
cross_check = load_module("cross_check", ROOT / "cross-check.py")
classify = load_module("classify_and_route", ROOT / "classify_and_route.py")


class ClaudeCodeCliPathTests(unittest.TestCase):
    def test_autonomy_certificate_uses_claude_cli_not_hermes_provider(self):
        cmd = certify.probe_command("claude-code", "claude-fable-5")
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertIn("--output-format", cmd)
        self.assertNotIn("hermes", cmd)
        self.assertNotIn("--provider", cmd)

    def test_cross_check_uses_claude_cli_for_anthropic_claude_model(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"type": "result", "result": "4"}),
                stderr="",
            )

        with mock.patch.object(shutil, "which", return_value="/usr/local/bin/claude"), \
             mock.patch.object(subprocess, "run", side_effect=fake_run):
            output, _latency, ok = cross_check.query_provider(
                "只回复: 4",
                provider="anthropic",
                model="claude-fable-5",
                timeout=5,
            )

        self.assertTrue(ok)
        self.assertEqual(output, "4")
        self.assertEqual(calls[0][:2], ["claude", "-p"])
        self.assertNotIn("hermes", calls[0])
        self.assertNotIn("--provider", calls[0])

    def test_cross_check_uses_correct_hermes_chat_arg_order_for_non_claude(self):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        with mock.patch.object(shutil, "which", return_value=None), \
             mock.patch.object(subprocess, "run", side_effect=fake_run):
            output, _latency, ok = cross_check.query_provider(
                "ping",
                provider="xiaomi",
                model="mimo-v2.5-pro",
                timeout=5,
            )

        self.assertTrue(ok)
        self.assertEqual(output, "ok")
        self.assertEqual(calls[0][:4], ["hermes", "chat", "-q", "ping"])
        self.assertIn("--provider", calls[0])
        self.assertIn("xiaomi", calls[0])

    def test_cross_check_redacts_secret_bearing_log_snippets(self):
        self.assertEqual(cross_check.redact_text("token='abcdef123456'"), "[REDACTED_SENSITIVE_TEXT]")
        self.assertEqual(cross_check.redact_text("normal text", limit=6), "normal")

    def test_classify_deep_reasoning_routes_to_claude_code(self):
        selected = classify.get_model_for_tier("reasoning")
        self.assertEqual(selected["provider"], "claude-code")
        self.assertIn("claude", selected["model"])


if __name__ == "__main__":
    unittest.main()
