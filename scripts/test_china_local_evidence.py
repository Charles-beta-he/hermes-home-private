#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ocr = load_module("china_local_screenshot_ocr", SCRIPT_DIR / "china_local_screenshot_ocr.py")
pipeline = load_module("china_local_evidence_pipeline", SCRIPT_DIR / "china_local_evidence_pipeline.py")
probe = load_module("china_local_evidence_probe", SCRIPT_DIR / "china_local_evidence_probe.py")


class ChinaLocalEvidenceTests(unittest.TestCase):
    def test_ocr_field_extraction_detects_rating_price_dishes_and_risks(self):
        text = """
        品伊阁烧麦
        评分 4.6分 人均 ¥38
        推荐菜：羊肉烧麦 羊杂汤 焙子 奶茶
        最新差评：排队久 服务一般
        """
        fields = ocr.extract_fields(text)
        self.assertEqual(fields["ratings"], ["4.6"])
        self.assertIn("38", fields["prices_or_per_capita_candidates"])
        self.assertTrue(any("羊肉烧麦" in line for line in fields["dish_signal_lines"]))
        self.assertTrue(any("排队" in line for line in fields["risk_signal_lines"]))

    def test_platform_body_classifies_boundaries(self):
        self.assertEqual(probe.classify_platform_body("dianping_pc", "https://account.dianping.com/pclogin", "APP扫码 登录")[0], "needs_login")
        self.assertEqual(probe.classify_platform_body("meituan_mobile", "https://verify.meituan.com", "spiderindefence 滑块")[0], "blocked_verification")
        self.assertEqual(probe.classify_platform_body("douyin_web", "https://www.douyin.com/search/foo", "<html></html>")[0], "blocked_or_js_shell")

    def test_pipeline_scores_screenshot_evidence_without_exact_poi(self):
        probe_json = {
            "platform_reachability": [{"source": "dianping_pc", "status": "needs_login"}],
            "poi_candidates": [{"source": "overpass", "name": "额尔敦传统涮", "distance_m": 416}],
        }
        ocr_json = {
            "results": [{
                "extracted": {
                    "ratings": ["4.6"],
                    "prices_or_per_capita_candidates": ["38"],
                    "dish_signal_lines": ["推荐菜：羊肉烧麦 羊杂汤"],
                    "risk_signal_lines": [],
                    "lines": [],
                }
            }]
        }
        rec = pipeline.score_recommendation("品伊阁烧麦", probe_json, ocr_json)
        self.assertEqual(rec["verdict"], "try_small_order")
        self.assertGreaterEqual(rec["score"], 55)
        self.assertTrue(any("截图" in reason for reason in rec["reasons"]))
        self.assertTrue(any("开放 POI" in risk for risk in rec["risks"]))

    def test_pipeline_cli_can_use_existing_json(self):
        probe_json = {"platform_reachability": [], "poi_candidates": []}
        ocr_json = {"results": []}
        with tempfile.TemporaryDirectory() as td:
            probe_path = Path(td) / "probe.json"
            ocr_path = Path(td) / "ocr.json"
            probe_path.write_text(json.dumps(probe_json), encoding="utf-8")
            ocr_path.write_text(json.dumps(ocr_json), encoding="utf-8")
            proc = subprocess.run([
                sys.executable,
                str(SCRIPT_DIR / "china_local_evidence_pipeline.py"),
                "--query",
                "品伊阁烧麦",
                "--city",
                "呼和浩特",
                "--probe-json",
                str(probe_path),
                "--ocr-json",
                str(ocr_path),
            ], text=True, capture_output=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(proc.stdout)
            self.assertEqual(data["schema"], "china_local_evidence_pipeline_v1")
            self.assertEqual(data["recommendation"]["verdict"], "insufficient_evidence")


if __name__ == "__main__":
    unittest.main()
