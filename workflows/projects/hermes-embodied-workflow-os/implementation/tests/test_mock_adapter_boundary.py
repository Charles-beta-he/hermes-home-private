import ast
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.mock_adapters import mock_adapter_manifests
from hewos_core.registry import CapabilityRegistry

FORBIDDEN_CORE_IMPORT_ROOTS = {"flask", "fastapi", "django", "react", "websocket", "rospy", "rclpy", "paho"}


class MockAdapterBoundaryTest(unittest.TestCase):
    def test_all_mock_adapters_register_without_core_changes(self):
        registry = CapabilityRegistry()
        manifests = mock_adapter_manifests()

        adapter_ids = {registry.register(item)["adapter_id"] for item in manifests}

        self.assertEqual(
            adapter_ids,
            {
                "adapter.cli.mock",
                "adapter.web.mock",
                "adapter.glasses.mock",
                "adapter.embedded.mock",
                "adapter.robot.mock",
            },
        )
        self.assertTrue(registry.find_by_type("observe.image.single"))
        self.assertTrue(registry.find_by_type("act.robot.grip"))

    def test_core_has_no_platform_or_hardware_imports(self):
        core_dir = ROOT / "hewos_core"
        imported_roots = set()
        for path in core_dir.glob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])

        self.assertFalse(imported_roots & FORBIDDEN_CORE_IMPORT_ROOTS)


if __name__ == "__main__":
    unittest.main()
