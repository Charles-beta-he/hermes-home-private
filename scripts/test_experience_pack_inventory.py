import importlib.util
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).parent / "experience_pack_inventory.py"
spec = importlib.util.spec_from_file_location("experience_pack_inventory", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules["experience_pack_inventory"] = mod
spec.loader.exec_module(mod)


class ExperiencePackInventoryTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        (root / "README.md").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=root, check=True, stdout=subprocess.DEVNULL)

    def test_classifies_templates_and_runtime_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.init_repo(root)
            tpl = root / "templates" / "experience-pack" / "pack" / "manifest.yaml"
            tpl.parent.mkdir(parents=True)
            tpl.write_text("schema: example\n", encoding="utf-8")
            (root / "contextcards.db").write_bytes(b"db")
            result = mod.inventory(root)
            by_path = {item["path"]: item for item in result["items"]}
            self.assertEqual(by_path["templates/experience-pack/pack/manifest.yaml"]["landing"], "copy_template")
            self.assertTrue(by_path["templates/experience-pack/pack/manifest.yaml"]["portable"])
            self.assertEqual(by_path["contextcards.db"]["landing"], "exclude")
            self.assertFalse(by_path["contextcards.db"]["portable"])

    def test_skill_with_owner_path_requires_sanitization_not_portable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.init_repo(root)
            skill = root / "skills" / "software-development" / "example" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("Use /Users/charles/.hermes as bad example\n", encoding="utf-8")
            result = mod.inventory(root)
            item = next(i for i in result["items"] if i["path"] == "skills/software-development/example/SKILL.md")
            self.assertEqual(item["landing"], "sanitize_then_bundle_or_optional")
            self.assertFalse(item["portable"])
            self.assertIn("contains owner/local absolute path", item["reasons"])

    def test_notes_are_extract_pattern_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.init_repo(root)
            note = root / "notes" / "health-history.jsonl"
            note.parent.mkdir()
            note.write_text("{}\n", encoding="utf-8")
            result = mod.inventory(root)
            item = next(i for i in result["items"] if i["path"] == "notes/health-history.jsonl")
            self.assertEqual(item["landing"], "extract_pattern_only")
            self.assertFalse(item["portable"])


if __name__ == "__main__":
    unittest.main()
