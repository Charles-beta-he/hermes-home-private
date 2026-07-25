#!/usr/bin/env python3
"""Regression tests for nullable health metrics introduced by evidence gating."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NullableHealthMetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan = load_script("self_scan_4h", "self-scan-4h.py")
        cls.dashboard = load_script("refresh_dashboard", "refresh-dashboard.py")

    def test_nullable_vdot_is_unknown_not_zero(self):
        record = {"V": None, "V_dot": None, "measurement_status": "insufficient_evidence"}
        self.assertIsNone(self.scan.get_vdot(record))
        self.assertIsNone(self.dashboard.get_vdot(record))
        self.assertIsNone(self.dashboard.finite_number(record["V"]))

    def test_scan_reports_nullable_latest_vdot_without_crashing(self):
        records = [
            {"V": 0.86, "V_dot": 0.0, "measurement_status": "observed"},
            {"V": None, "V_dot": None, "measurement_status": "insufficient_evidence"},
            {"V": None, "V_dot": None, "measurement_status": "insufficient_evidence"},
        ]
        old_path = self.scan.HEALTH_PATH
        try:
            with tempfile.TemporaryDirectory() as tmp:
                health_path = Path(tmp) / "health-history.jsonl"
                health_path.write_text("".join(json.dumps(row) + "\n" for row in records))
                setattr(self.scan, "HEALTH_PATH", str(health_path))
                issues = self.scan.check_health()
        finally:
            setattr(self.scan, "HEALTH_PATH", old_path)

        self.assertTrue(any("V̇ 最新不可用 (insufficient_evidence)" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()