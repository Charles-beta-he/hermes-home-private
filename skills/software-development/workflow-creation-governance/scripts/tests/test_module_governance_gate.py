import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "module_governance_gate.py"
spec = importlib.util.spec_from_file_location("module_governance_gate", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load module_governance_gate")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ModuleLifecycleGateTests(unittest.TestCase):
    def make_fixture(self, root: Path) -> Path:
        for rel in (
            "scripts/example_adapter.py",
            "scripts/tests/test_example_adapter.py",
            "modules/example/package.json",
        ):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("placeholder\n", encoding="utf-8")
        skill = root / "skills/example/SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(
            "---\nname: example\ndescription: Use when testing an example module.\n---\n# Example\n\nBody.\n",
            encoding="utf-8",
        )
        evals = root / "skills/example/evals/prompts.csv"
        evals.parent.mkdir(parents=True, exist_ok=True)
        evals.write_text(
            "id,bucket,prompt\n"
            "p1,positive,a\np2,positive,b\np3,positive,c\n"
            "n1,neighbor,d\nn2,neighbor,e\n"
            "f1,forbidden,f\nf2,forbidden,g\n"
            "z1,no-load,h\n",
            encoding="utf-8",
        )
        manifest = {
            "schema": "hermes_module_governance_v1",
            "module": {
                "id": "example",
                "kind": "runtime_skill_module",
                "scope": "user_local",
                "maturity": "validated",
                "version": "1.0.0",
            },
            "artifacts": {
                "skill": "skills/example/SKILL.md",
                "adapter": "scripts/example_adapter.py",
                "runtime_manifest": "modules/example/package.json",
                "tests": ["scripts/tests/test_example_adapter.py"],
                "route_evals": "skills/example/evals/prompts.csv",
            },
            "credentials": {
                "mode": "keychain",
                "plaintext_forbidden": True,
            },
            "runtime": {
                "daemon": False,
                "pinned_dependencies": {"example-package": "1.2.3"},
                "side_effects": ["external_read"],
            },
            "verification": {
                "commands": ["python3 -m unittest scripts.tests.test_example_adapter"],
                "fresh_smoke_required": True,
                "secret_scan_required": True,
            },
            "lifecycle": {
                "owner": "user-local",
                "rollback": "git revert the scoped module commit",
                "upgrade": "pin, test, smoke, and commit a new exact version",
                "deprecate": "disable routes, retain redirect, then archive",
            },
            "git": {
                "scoped_commit_required": True,
                "push_requires_separate_authority": True,
                "exclude": ["node_modules/", "credentials", "runtime-output"],
            },
        }
        path = root / "modules/example/module-governance.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_valid_manifest_passes_all_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_fixture(root)
            result = gate.validate_manifest(manifest, root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["failed_gates"], [])

    def test_missing_lifecycle_section_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_fixture(root)
            data = json.loads(manifest.read_text())
            del data["lifecycle"]
            manifest.write_text(json.dumps(data), encoding="utf-8")
            result = gate.validate_manifest(manifest, root)
            self.assertFalse(result["ok"])
            self.assertIn("lifecycle", result["failed_gates"])

    def test_floating_dependency_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_fixture(root)
            data = json.loads(manifest.read_text())
            data["runtime"]["pinned_dependencies"]["example-package"] = "latest"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            result = gate.validate_manifest(manifest, root)
            self.assertFalse(result["ok"])
            self.assertIn("runtime", result["failed_gates"])

    def test_route_eval_minimums_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_fixture(root)
            evals = root / "skills/example/evals/prompts.csv"
            evals.write_text("id,bucket,prompt\np1,positive,a\n", encoding="utf-8")
            result = gate.validate_manifest(manifest, root)
            self.assertFalse(result["ok"])
            self.assertIn("artifacts", result["failed_gates"])

    def test_skill_frontmatter_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_fixture(root)
            skill = root / "skills/example/SKILL.md"
            skill.write_text("# Missing frontmatter\n", encoding="utf-8")
            result = gate.validate_manifest(manifest, root)
            self.assertFalse(result["ok"])
            self.assertIn("artifacts", result["failed_gates"])

    def test_plaintext_secret_field_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.make_fixture(root)
            data = json.loads(manifest.read_text())
            data["credentials"]["token"] = "actual-value-must-not-be-here"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            result = gate.validate_manifest(manifest, root)
            self.assertFalse(result["ok"])
            self.assertIn("credentials", result["failed_gates"])


if __name__ == "__main__":
    unittest.main()
