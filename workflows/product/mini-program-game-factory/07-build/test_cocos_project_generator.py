import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cocos_project_generator import (
    ProjectGenerationError,
    compress_uuid,
    generate_cocos_project,
    verify_generated_project,
)


BUILD_DIR = Path(__file__).resolve().parent
ROOT = BUILD_DIR.parent
CANDIDATE = ROOT / "evidence" / "cocos-sample-candidate"
RUNTIME_CORE = ROOT / "runtime" / "cocos" / "runtime-core"


class CocosProjectGeneratorTests(unittest.TestCase):
    def test_compress_uuid_matches_official_creator_3_8_fixture(self):
        self.assertEqual(
            compress_uuid("7df5dc69-673e-4d38-806f-c6a22bf59143"),
            "7df5dxpZz5NOIBvxqIr9ZFD",
        )

    def test_generates_deterministic_creator_3_8_project(self):
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = Path(first_tmp) / "project"
            second = Path(second_tmp) / "project"
            first_manifest = generate_cocos_project(CANDIDATE, RUNTIME_CORE, first)
            second_manifest = generate_cocos_project(CANDIDATE, RUNTIME_CORE, second)
            self.assertEqual(first_manifest, second_manifest)
            self.assertEqual(first_manifest["closure_state"], "creator_import_pending")
            self.assertFalse(first_manifest["authority"]["creator_runtime_verified"])
            self.assertFalse(first_manifest["authority"]["may_build_platform"])
            self.assertEqual(verify_generated_project(first), first_manifest)
            package = json.loads((first / "package.json").read_text())
            self.assertEqual(package["creator"]["version"], "3.8.0")
            self.assertEqual(package["type"], "2d")
            self.assertTrue(
                (first / "assets" / "game-factory" / "core" / "official-platform-adapters.ts").is_file()
            )
            scene = json.loads((first / "assets" / "scenes" / "main.scene").read_text())
            script_meta = json.loads((first / "assets" / "game-factory" / "GameBootstrap.ts.meta").read_text())
            component_types = {item.get("__type__") for item in scene if isinstance(item, dict)}
            self.assertIn(compress_uuid(script_meta["uuid"]), component_types)
            for relative in first_manifest["files"]:
                self.assertTrue((first / relative["path"]).is_file())
            compiler = RUNTIME_CORE / "node_modules" / ".bin" / "tsc"
            subprocess.run(
                [str(compiler), "-p", str(first / "tsconfig.json")],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_rejects_existing_output_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            root.mkdir()
            with self.assertRaisesRegex(ProjectGenerationError, "already exists"):
                generate_cocos_project(CANDIDATE, RUNTIME_CORE, root)

    def test_rejects_tampered_candidate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            import shutil
            shutil.copytree(CANDIDATE, candidate)
            (candidate / "generated" / "content-pack.json").write_text("{}\n")
            with self.assertRaisesRegex(ProjectGenerationError, "candidate manifest"):
                generate_cocos_project(candidate, RUNTIME_CORE, Path(tmp) / "project")

    def test_verifier_rejects_generated_file_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            generate_cocos_project(CANDIDATE, RUNTIME_CORE, root)
            bootstrap = root / "assets" / "game-factory" / "GameBootstrap.ts"
            bootstrap.write_text(bootstrap.read_text() + "// tampered\n")
            with self.assertRaisesRegex(ProjectGenerationError, "digest mismatch"):
                verify_generated_project(root)

    def test_verifier_rejects_generated_file_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            generate_cocos_project(CANDIDATE, RUNTIME_CORE, root)
            bootstrap = root / "assets" / "game-factory" / "GameBootstrap.ts"
            external = Path(tmp) / "external.ts"
            external.write_bytes(bootstrap.read_bytes())
            bootstrap.unlink()
            bootstrap.symlink_to(external)
            with self.assertRaisesRegex(ProjectGenerationError, "digest mismatch"):
                verify_generated_project(root)

    def test_cli_verify_requires_no_generation_arguments(self):
        completed = subprocess.run(
            ["python3", str(BUILD_DIR / "cocos_project_generator.py"), "--verify", str(ROOT / "evidence" / "cocos-creator-project-candidate")],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(completed.stdout)["closure_state"], "creator_import_pending")


if __name__ == "__main__":
    unittest.main()
