import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).parent / "experience_pack_install.py"
SANITIZER = Path(__file__).parent / "experience_pack_sanitize.py"
spec = importlib.util.spec_from_file_location("experience_pack_install", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules["experience_pack_install"] = mod
spec.loader.exec_module(mod)
setattr(mod, "SANITIZER", SANITIZER)


class ExperiencePackInstallTests(unittest.TestCase):
    def make_pack(self, root: Path) -> Path:
        pack = root / "pack"
        (pack / "templates" / "hooks").mkdir(parents=True)
        (pack / "manifest.yaml").write_text("schema: hermes_experience_pack_v1\n", encoding="utf-8")
        (pack / "README.md").write_text("clean pack\n", encoding="utf-8")
        (pack / "templates" / "hooks" / "registry.example.yaml").write_text("enabled: false\n", encoding="utf-8")
        return pack

    def test_dry_run_plans_copy_without_writing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = self.make_pack(root)
            target = root / "home"
            result = mod.install(str(pack), target, dry_run=True)
            self.assertTrue(result.ok, result.blocked)
            self.assertTrue(any(op.action == "copy" for op in result.operations))
            self.assertFalse((target / "experience-packs" / "pack" / "manifest.yaml").exists())

    def test_install_copies_missing_and_writes_disabled_activation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = self.make_pack(root)
            target = root / "home"
            result = mod.install(str(pack), target, dry_run=False)
            self.assertTrue(result.ok, result.blocked)
            installed = target / "experience-packs" / "pack" / "templates" / "hooks" / "registry.example.yaml"
            self.assertTrue(installed.exists())
            activation = json.loads((target / "state" / "experience-pack-activation.json").read_text())
            self.assertFalse(activation["cron_enabled"])
            self.assertFalse(activation["hooks_enabled"])
            self.assertFalse(activation["gateway_delivery_enabled"])
            self.assertFalse(activation["taskpool_mutation_enabled"])

    def test_no_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = self.make_pack(root)
            target = root / "home"
            first = mod.install(str(pack), target, dry_run=False)
            self.assertTrue(first.ok)
            dest = target / "experience-packs" / "pack" / "README.md"
            dest.write_text("user edit\n", encoding="utf-8")
            second = mod.install(str(pack), target, dry_run=False)
            self.assertTrue(second.ok)
            self.assertEqual(dest.read_text(encoding="utf-8"), "user edit\n")
            self.assertTrue(any(op.action == "skip" and op.destination == str(dest.resolve()) for op in second.operations))

    def test_sanitizer_fail_closes_install(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = self.make_pack(root)
            (pack / "contextcards.db").write_bytes(b"bad")
            target = root / "home"
            result = mod.install(str(pack), target, dry_run=False)
            self.assertFalse(result.ok)
            self.assertTrue(any("sanitizer failed" in b for b in result.blocked))
            self.assertFalse((target / "experience-packs").exists())

    def test_cli_install_dry_run_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack = self.make_pack(root)
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "install", str(pack), "--target-home", str(root / "home"), "--dry-run", "--json"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["dry_run"])


if __name__ == "__main__":
    unittest.main()
