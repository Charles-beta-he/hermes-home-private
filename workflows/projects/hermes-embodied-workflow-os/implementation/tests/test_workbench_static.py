import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.workbench_static import render_workbench_html, write_workbench_html_fixture


class StaticWorkbenchTest(unittest.TestCase):
    def test_renders_static_html_without_execution_paths(self):
        html = render_workbench_html()
        self.assertIn("HEWOS Workbench", html)
        self.assertIn("Dashboard", html)
        self.assertIn("ActionIntent Review", html)
        self.assertIn("EvidenceLedger", html)
        self.assertIn("Simulation-only", html)
        forbidden = ["/execute", "taskpool", "deploy", "publish", "gateway", "credential"]
        lowered = html.lower()
        for item in forbidden:
            self.assertNotIn(item, lowered)

    def test_writes_fixture_html(self):
        out = ROOT / "artifacts" / "workbench-static-fixture.test.html"
        result = write_workbench_html_fixture(out)
        self.assertEqual(result, out)
        html = out.read_text()
        self.assertIn("HEWOS Workbench", html)
        self.assertIn("simulated", html.lower())
        out.unlink()


if __name__ == "__main__":
    unittest.main()
