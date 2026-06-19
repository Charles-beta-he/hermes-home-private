import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

SCRIPT = Path(__file__).parent / "experience_pack_sanitize.py"


class ExperiencePackSanitizeTests(unittest.TestCase):
    def run_scan(self, root: Path):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--json"],
            text=True,
            capture_output=True,
        )
        payload = json.loads(proc.stdout)
        return proc, payload

    def test_clean_template_pack_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "manifest.yaml").write_text(
                """
schema: hermes_experience_pack_v1
copy_policy:
  overwrite_existing: false
example_placeholder: <PLACEHOLDER_VALUE>
paths:
  scripts: $HERMES_HOME/scripts
""".strip(),
                encoding="utf-8",
            )
            (root / "templates" / "hooks").mkdir(parents=True)
            (root / "templates" / "hooks" / "registry.example.yaml").write_text(
                "hook_class: observer\nfail_policy: fail-open\n",
                encoding="utf-8",
            )
            proc, payload = self.run_scan(root)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["finding_count"], 0)

    def test_rejects_owner_path_and_runtime_db(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "README.md").write_text("bad /Users/charles/.hermes/state.db\n", encoding="utf-8")
            (root / "template.md").write_text("runtime source points to state.db without placeholder\n", encoding="utf-8")
            (root / "contextcards.db").write_bytes(b"sqlite payload")
            proc, payload = self.run_scan(root)
            self.assertEqual(proc.returncode, 2)
            rules = {f["rule"] for f in payload["findings"]}
            self.assertIn("owner_absolute_path", rules)
            self.assertIn("state_db_reference", rules)
            self.assertIn("forbidden_file_pattern", rules)

    def test_rejects_secret_assignment_but_allows_placeholder(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config.example.yaml").write_text(
                "api_" "key: <YOUR_API_" "KEY>\n"
                "client_" "secret: real-" "redacted-value\n",
                encoding="utf-8",
            )
            proc, payload = self.run_scan(root)
            self.assertEqual(proc.returncode, 2)
            findings = payload["findings"]
            self.assertEqual(len([f for f in findings if f["rule"] == "secret_assignment"]), 1)
            self.assertIn("client_secret", findings[0]["detail"])

    def test_rejects_forbidden_state_directories(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "logs").mkdir()
            (root / "logs" / "agent.log").write_text("runtime log\n", encoding="utf-8")
            (root / "docs" / "private").mkdir(parents=True)
            (root / "docs" / "private" / "note.md").write_text("private\n", encoding="utf-8")
            proc, payload = self.run_scan(root)
            self.assertEqual(proc.returncode, 2)
            details = {f["detail"] for f in payload["findings"] if f["rule"] == "forbidden_path_part"}
            self.assertIn("logs", details)
            self.assertIn("docs/private", details)


if __name__ == "__main__":
    unittest.main()
