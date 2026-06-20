import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import file_arch_adapter


class FileArchAdapterTests(unittest.TestCase):
    def make_sample(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="file-arch-adapter-"))
        (root / "agent" / "tools").mkdir(parents=True)
        (root / "agent" / "skills").mkdir(parents=True)
        (root / "agent" / "channels").mkdir(parents=True)
        (root / "agent" / "schedules").mkdir(parents=True)
        (root / "agent" / "instructions.md").write_text("You are a demo agent.\n", encoding="utf-8")
        (root / "agent" / "agent.ts").write_text("export default {};\n", encoding="utf-8")
        (root / "agent" / "tools" / "weather.ts").write_text("export {};\n", encoding="utf-8")
        (root / "agent" / "skills" / "plan.md").write_text("# Plan\n", encoding="utf-8")
        return root

    def test_inspect_project_passes_with_required_instructions(self):
        result = file_arch_adapter.inspect_project(self.make_sample())
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["required"]["instructions"])
        self.assertEqual(result["optional_counts"]["tools"], 1)
        self.assertTrue(result["red_lines"]["does_not_replace_hermes_skills"])
        self.assertTrue(result["read_only"])

    def test_inspect_project_fails_without_required_instructions(self):
        root = Path(tempfile.mkdtemp(prefix="file-arch-adapter-missing-"))
        (root / "agent").mkdir()
        result = file_arch_adapter.inspect_project(root)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["required"]["instructions"])

    def test_cli_json_readback(self):
        root = self.make_sample()
        proc = subprocess.run(
            [sys.executable, str(Path(file_arch_adapter.__file__)), str(root), "--json"],
            check=True,
            text=True,
            capture_output=True,
        )
        result = json.loads(proc.stdout)
        self.assertEqual(result["schema"], "file_arch_adapter_v1")
        self.assertEqual(result["status"], "pass")


if __name__ == "__main__":
    unittest.main()
