import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent / "private_home_update_check.py"
spec = importlib.util.spec_from_file_location("private_home_update_check", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules["private_home_update_check"] = mod
spec.loader.exec_module(mod)


class PrivateHomeUpdateCheckTests(unittest.TestCase):
    def test_version_parse_and_sort(self):
        versions = [
            "private-home-2026.07.06.1-candidate",
            "private-home-2026.07.06.1",
            "private-home-2026.07.07.1",
        ]
        self.assertEqual(mod.latest_stable_tag(versions), "private-home-2026.07.07.1")
        self.assertIsNone(mod.PrivateHomeVersion.parse("v1.0.0"))

    def test_manifest_current_version(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "docs" / "private" / "version-ops"
            path.mkdir(parents=True)
            (path / "private-version-manifest.json").write_text(json.dumps({"current_version": "private-home-2026.07.06.1"}), encoding="utf-8")
            self.assertEqual(mod.current_tag_from_manifest(root), "private-home-2026.07.06.1")

    def test_redact_secrets(self):
        text = "OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz token=ghp_abcdefghijklmnopqrstuvwxyz"
        redacted = mod.redact(text)
        self.assertNotIn("sk-proj-", redacted)
        self.assertNotIn("ghp_", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_write_packet_dedupes(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td) / "home"
            diag = {"reason": "doctor failed", "platform": "x", "manifest_version": "private-home-2026.07.06.1", "commands": {"doctor": {"returncode": 1, "stdout": "", "stderr": "bad"}}}
            first = mod.write_packet(dict(diag), home)
            second = mod.write_packet(dict(diag), home)
            self.assertFalse(first["duplicate"])
            self.assertTrue(second["duplicate"])
            self.assertTrue(Path(first["body_path"]).exists())

    def test_report_problem_local_only_does_not_submit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            home = Path(td) / "home"
            (root / "scripts").mkdir(parents=True)
            (root / "docs" / "private" / "version-ops").mkdir(parents=True)
            (root / "docs" / "private" / "version-ops" / "private-version-manifest.json").write_text(json.dumps({"current_version":"private-home-2026.07.06.1"}), encoding="utf-8")
            (root / "scripts" / "private_version_doctor.py").write_text("print('{}')\n", encoding="utf-8")
            (root / "scripts" / "dynamic_selfcheck_coverage.py").write_text("print('ok')\n", encoding="utf-8")
            with mock.patch.object(mod, "submit_issue") as submit:
                payload = mod.report_problem(root, home, "doctor failed", submit=False, github_repo="owner/repo", force=False)
            submit.assert_not_called()
            self.assertFalse(payload["submitted"])
            self.assertTrue(Path(payload["json_path"]).exists())

    def test_submit_duplicate_requires_force(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            home = Path(td) / "home"
            (root / "scripts").mkdir(parents=True)
            (root / "docs" / "private" / "version-ops").mkdir(parents=True)
            (root / "docs" / "private" / "version-ops" / "private-version-manifest.json").write_text(json.dumps({"current_version":"private-home-2026.07.06.1"}), encoding="utf-8")
            (root / "scripts" / "private_version_doctor.py").write_text("print('{}')\n", encoding="utf-8")
            (root / "scripts" / "dynamic_selfcheck_coverage.py").write_text("print('ok')\n", encoding="utf-8")
            mod.report_problem(root, home, "doctor failed", submit=False, github_repo="owner/repo", force=False)
            with mock.patch.object(mod, "submit_issue") as submit:
                payload = mod.report_problem(root, home, "doctor failed", submit=True, github_repo="owner/repo", force=False)
            submit.assert_not_called()
            self.assertFalse(payload["submitted"])
            self.assertIn("duplicate", payload["submit_result"]["reason"])


if __name__ == "__main__":
    unittest.main()
