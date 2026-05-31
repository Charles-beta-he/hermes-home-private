#!/usr/bin/env python3
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("working_tree_secret_scan.py")
spec = importlib.util.spec_from_file_location("working_tree_secret_scan", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


FAKE_TELEGRAM_VALUE = "123456789:" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "abcdefghi"


class WorkingTreeSecretScanTest(unittest.TestCase):
    def _init_repo(self, repo: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.local"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    def _run_cli(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo), *args],
            cwd=repo,
            text=True,
            capture_output=True,
        )

    def test_redacted_finding_for_telegram_token(self):
        text = f"bot_token: {FAKE_TELEGRAM_VALUE}"
        findings = mod.scan_text(text, "config.yaml")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].kind, "telegram_bot_token")
        self.assertEqual(findings[0].source, "config.yaml")
        self.assertEqual(findings[0].line, 1)
        self.assertNotIn("123456789", findings[0].fingerprint)

    def test_redacted_placeholders_are_ignored(self):
        text = "bot_token: [REDACTED_TELEGRAM_TOKEN]\napi_key: your_token"
        self.assertEqual(mod.scan_text(text, "config.yaml"), [])

    def test_git_diff_uses_real_added_line_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "config.yaml").write_text('first: true\nbot_token: ""\n')
            subprocess.run(["git", "add", "config.yaml"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
            (repo / "config.yaml").write_text(f"first: true\nbot_token: {FAKE_TELEGRAM_VALUE}\n")
            findings = mod.scan_git_diff(repo, staged=False)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0].kind, "telegram_bot_token")
            self.assertEqual(findings[0].source, "config.yaml")
            self.assertEqual(findings[0].line, 2)

    def test_cli_output_never_prints_secret_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "config.yaml").write_text(f"bot_token: {FAKE_TELEGRAM_VALUE}\n")
            result = self._run_cli(repo, "--staged")
            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SECRET_SCAN_FAIL findings=1", combined)
            self.assertIn("config.yaml:1:telegram_bot_token:", combined)
            self.assertNotIn(FAKE_TELEGRAM_VALUE, combined)
            self.assertNotIn("ABCDEFGHIJKLMNOPQRSTUVWXYZ", combined)

    def test_default_file_scan_catches_config_without_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "config.yaml").write_text(f"token: {FAKE_TELEGRAM_VALUE}\n")
            result = self._run_cli(repo, "--staged")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SECRET_SCAN_FAIL findings=1", result.stdout)

    def test_env_is_excluded_by_default_and_included_on_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "config.yaml").write_text('bot_token: ""\n')
            (repo / ".env").write_text(f"TELEGRAM_BOT_TOKEN={FAKE_TELEGRAM_VALUE}\n")
            default_result = self._run_cli(repo, "--staged")
            self.assertEqual(default_result.returncode, 0, default_result.stdout + default_result.stderr)
            include_result = self._run_cli(repo, "--staged", "--include-env")
            self.assertNotEqual(include_result.returncode, 0)
            self.assertIn(".env:1:telegram_bot_token:", include_result.stdout)
            self.assertNotIn(FAKE_TELEGRAM_VALUE, include_result.stdout + include_result.stderr)

    def test_duplicate_diff_and_file_scan_reports_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "config.yaml").write_text('bot_token: ""\n')
            subprocess.run(["git", "add", "config.yaml"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
            (repo / "config.yaml").write_text(f"bot_token: {FAKE_TELEGRAM_VALUE}\n")
            result = self._run_cli(repo, "--all-diff")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SECRET_SCAN_FAIL findings=1", result.stdout)


if __name__ == "__main__":
    unittest.main()
