#!/usr/bin/env python3
"""Tests for local_brain_precommit_hook.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "local_brain_precommit_hook.py"
spec = importlib.util.spec_from_file_location("local_brain_precommit_hook", SCRIPT)
hook = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(hook)


class LocalBrainPrecommitHookTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init"], cwd=self.repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_writes_enabled_pre_commit_hook(self):
        result = hook.install(self.repo)
        self.assertTrue(result["ok"])
        self.assertTrue(result["enabled"])
        hook_path = Path(result["hook"])
        self.assertTrue(hook_path.exists())
        self.assertIn("local_brain_precommit_hook.py", hook_path.read_text(encoding="utf-8"))
        status = hook.status(self.repo)
        self.assertTrue(status["enabled"])

    def test_cli_status_json_is_parseable(self):
        hook.install(self.repo)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--status", "--repo", str(self.repo), "--json"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["enabled"])


if __name__ == "__main__":
    unittest.main()
