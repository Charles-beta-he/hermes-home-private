import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).parent / "private_version_doctor.py"
spec = importlib.util.spec_from_file_location("private_version_doctor", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules["private_version_doctor"] = mod
spec.loader.exec_module(mod)


class PrivateVersionDoctorTests(unittest.TestCase):
    def make_min_repo(self, root: Path) -> None:
        for rel in mod.REQUIRED_PATHS:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if rel.endswith(".json"):
                path.write_text('{"schema":"hermes_private_home_release_manifest_v1"}\n', encoding="utf-8")
            elif rel.endswith(".py"):
                path.write_text("print('ok')\n", encoding="utf-8")
            else:
                path.write_text("ok\n", encoding="utf-8")

    def test_minimal_release_tree_is_stable_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            payload = mod.run(root)
            self.assertTrue(payload["ok"], payload)
            self.assertEqual(payload["readiness"], "stable_candidate")
            self.assertEqual(payload["blockers"], [])

    def test_missing_required_path_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            (root / "PRIVATE_VERSIONING.md").unlink()
            payload = mod.run(root)
            self.assertFalse(payload["ok"])
            self.assertTrue(any(f["code"] == "missing_required_path" for f in payload["blockers"]))

    def test_runtime_artifact_is_warning_not_blocker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            p = root / "cron" / "output" / "job" / "old.md"
            p.parent.mkdir(parents=True)
            p.write_text("old runtime\n", encoding="utf-8")
            payload = mod.run(root)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["readiness"], "candidate_with_debt")
            self.assertTrue(any(f["code"] == "tracked_runtime_artifact" for f in payload["warnings"]))

    def test_secret_marker_warns_but_token_value_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            (root / "docs" / "private" / "example.md").write_text("OPENAI_API_KEY=placeholder\n", encoding="utf-8")
            marker_payload = mod.run(root)
            self.assertTrue(marker_payload["ok"])
            self.assertTrue(any(f["code"] == "secret_marker_string" for f in marker_payload["warnings"]))
            (root / "docs" / "private" / "bad.md").write_text("OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
            payload = mod.run(root)
            self.assertFalse(payload["ok"])
            self.assertTrue(any(f["code"] == "secret_value" for f in payload["blockers"]))

    def test_personal_project_profile_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            p = root / "project-profiles" / "uvisa-app-2.0.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('{"project":"uvisa-app-2.0","paths":{"repo":"/Users/charles/work/uvisa"}}\n', encoding="utf-8")
            payload = mod.run(root)
            self.assertFalse(payload["ok"])
            codes = {f["code"] for f in payload["blockers"]}
            self.assertIn("personal_project_profile_published", codes)

    def test_unallowlisted_profile_with_personal_token_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            p = root / "project-profiles" / "client.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('{"project":"client","note":"Lark task flow"}\n', encoding="utf-8")
            payload = mod.run(root)
            self.assertFalse(payload["ok"])
            self.assertTrue(any(f["code"] == "personal_profile_token" for f in payload["blockers"]))

    def test_cli_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_min_repo(root)
            proc = subprocess.run([sys.executable, str(SCRIPT), str(root), "--json"], text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
