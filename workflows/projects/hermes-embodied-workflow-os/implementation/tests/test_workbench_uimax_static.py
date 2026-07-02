import re
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.workbench_static import render_workbench_html


class WorkbenchUIMaxStaticTest(unittest.TestCase):
    def setUp(self):
        self.html = render_workbench_html()
        self.lowered = self.html.lower()

    def test_has_accessible_landmarks_and_skip_link(self):
        self.assertIn('href="#main-content"', self.html)
        self.assertIn('id="main-content"', self.html)
        self.assertRegex(self.html, r'<header\b[^>]*role="banner"')
        self.assertRegex(self.html, r'<main\b[^>]*role="main"')
        self.assertRegex(self.html, r'<nav\b[^>]*aria-label="Workbench sections"')
        self.assertRegex(self.html, r'<footer\b[^>]*role="contentinfo"')

    def test_sections_are_semantically_labelled(self):
        for section_id in ["dashboard", "action-review", "evidence-ledger", "gate-ladder"]:
            self.assertIn(f'id="{section_id}"', self.html)
            self.assertRegex(self.html, rf'<section\b[^>]*aria-labelledby="{section_id}-title"')
            self.assertIn(f'id="{section_id}-title"', self.html)

    def test_status_and_safety_copy_are_visible_without_execution_paths(self):
        self.assertIn('role="status"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('Projection only', self.html)
        self.assertIn('Blocked', self.html)
        forbidden = ["/execute", "taskpool", "deploy", "publish", "gateway", "credential"]
        for item in forbidden:
            self.assertNotIn(item, self.lowered)

    def test_responsive_and_reduced_motion_css_exists(self):
        self.assertIn('@media (max-width: 760px)', self.html)
        self.assertIn('@media (prefers-reduced-motion: reduce)', self.html)
        self.assertIn(':focus-visible', self.html)
        self.assertIn('grid-template-columns', self.html)

    def test_visual_system_uses_tokens_not_inline_debug_styles(self):
        self.assertGreaterEqual(len(re.findall(r'--[a-z0-9-]+:', self.html)), 12)
        self.assertNotIn('style="', self.lowered)
        self.assertNotIn('debug', self.lowered)


if __name__ == "__main__":
    unittest.main()
