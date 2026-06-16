#!/usr/bin/env python3
"""Compose China-local POI probes and app screenshot OCR into a recommendation.

This is the second stage after china_local_evidence_probe.py and
china_local_screenshot_ocr.py. It intentionally stays read-only:

- no login automation;
- no CAPTCHA/slider bypass;
- no platform scraping beyond the bounded probe;
- user-provided screenshots are treated as the highest-confidence review source.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
PROBE_SCRIPT = SCRIPT_DIR / "china_local_evidence_probe.py"
OCR_SCRIPT = SCRIPT_DIR / "china_local_screenshot_ocr.py"


def _run_json(cmd: List[str]) -> Dict[str, Any]:
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=240)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\nSTDOUT:{proc.stdout[:1000]}\nSTDERR:{proc.stderr[:1000]}")
    return json.loads(proc.stdout)


def run_probe(query: str, city: str, lat: Optional[float], lon: Optional[float], radius: int) -> Dict[str, Any]:
    cmd = [sys.executable, str(PROBE_SCRIPT), "--query", query, "--city", city, "--radius", str(radius)]
    if lat is not None:
        cmd += ["--lat", str(lat)]
    if lon is not None:
        cmd += ["--lon", str(lon)]
    return _run_json(cmd)


def run_ocr(images: List[str]) -> Dict[str, Any]:
    if not images:
        return {"schema": "china_local_screenshot_ocr_v1", "results": []}
    return _run_json([sys.executable, str(OCR_SCRIPT), *images])


def exactish_poi_matches(query: str, pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact_query = "".join(query.split()).lower()
    tokens = [tok.lower() for tok in query.split() if tok.strip()]
    out = []
    for poi in pois:
        name = str(poi.get("name") or "")
        compact_name = "".join(name.split()).lower()
        if compact_query and (compact_query in compact_name or compact_name in compact_query):
            out.append(poi)
        elif tokens and all(tok in compact_name for tok in tokens):
            out.append(poi)
    return out


def collect_ocr_signals(ocr: Dict[str, Any]) -> Dict[str, Any]:
    ratings: List[float] = []
    prices: List[str] = []
    dish_lines: List[str] = []
    risk_lines: List[str] = []
    raw_lines: List[str] = []
    for result in ocr.get("results", []):
        extracted = result.get("extracted") or {}
        for rating in extracted.get("ratings", []) or []:
            try:
                ratings.append(float(rating))
            except Exception:
                pass
        prices.extend([str(x) for x in extracted.get("prices_or_per_capita_candidates", []) or []])
        dish_lines.extend([str(x) for x in extracted.get("dish_signal_lines", []) or []])
        risk_lines.extend([str(x) for x in extracted.get("risk_signal_lines", []) or []])
        raw_lines.extend([str(x) for x in extracted.get("lines", []) or []])
    return {
        "ratings": sorted(set(ratings), reverse=True),
        "prices": prices[:20],
        "dish_lines": dish_lines[:30],
        "risk_lines": risk_lines[:30],
        "raw_lines": raw_lines[:80],
    }


def score_recommendation(query: str, probe: Dict[str, Any], ocr: Dict[str, Any]) -> Dict[str, Any]:
    pois = probe.get("poi_candidates") or []
    platform = probe.get("platform_reachability") or []
    ocr_signals = collect_ocr_signals(ocr)
    exact_pois = exactish_poi_matches(query, pois)

    score = 0
    reasons: List[str] = []
    risks: List[str] = []

    if exact_pois:
        score += 25
        reasons.append(f"开放/官方 POI 层命中 {len(exact_pois)} 个近似店名结果")
    else:
        risks.append("开放 POI 层未命中精确店名，可能是小店/新店/弱收录；需依赖 App 截图或现场判断")

    nearby_named = [p for p in pois[:8] if p.get("distance_m") is not None]
    if nearby_named:
        score += 5
        reasons.append("附近 POI 兜底可用，可辅助路线和备选店判断")

    ratings = ocr_signals["ratings"]
    if ratings:
        best = max(ratings)
        if best >= 4.5:
            score += 35
            reasons.append(f"截图 OCR 识别到高评分候选 {best}")
        elif best >= 4.1:
            score += 25
            reasons.append(f"截图 OCR 识别到可接受评分候选 {best}")
        else:
            score += 8
            risks.append(f"截图 OCR 识别到评分候选 {best}，偏谨慎")
    else:
        risks.append("没有截图评分证据")

    if ocr_signals["dish_lines"]:
        score += 15
        reasons.append("截图 OCR 识别到推荐菜/菜品信号")
    if ocr_signals["prices"]:
        score += 8
        reasons.append("截图 OCR 识别到价格/人均候选")
    if ocr_signals["risk_lines"]:
        score -= min(25, 6 * len(ocr_signals["risk_lines"]))
        risks.append("截图 OCR 识别到排队/差评/踩雷等风险信号")

    blocked = [p for p in platform if p.get("status") in {"needs_login", "blocked_verification", "blocked_or_js_shell"}]
    if blocked:
        risks.append("部分主流平台网页触发登录/验证，不能当作已读取评价证据")

    if score >= 65:
        verdict = "worth_trying"
        next_action = "可继续吃/可作为候选；按推荐菜少量多样点，避开 OCR 风险项。"
    elif score >= 35:
        verdict = "try_small_order"
        next_action = "只建议小份试吃；优先点招牌/高频推荐菜，不要直接上大份套餐。"
    else:
        verdict = "insufficient_evidence"
        next_action = "证据不足；需要大众点评/美团/小红书/抖音 App 截图，或现场按人流/明码标价/现做热气判断。"

    return {
        "verdict": verdict,
        "score": max(0, min(100, score)),
        "reasons": reasons,
        "risks": risks,
        "next_action": next_action,
        "exactish_poi_matches": exact_pois[:5],
        "nearby_poi_fallback": nearby_named[:8],
        "ocr_signals": ocr_signals,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--radius", type=int, default=1200)
    ap.add_argument("--screenshot", action="append", default=[], help="Dianping/Meituan/XHS/Douyin/Amap screenshot image path; repeatable")
    ap.add_argument("--probe-json", help="Use existing probe JSON instead of running live probe")
    ap.add_argument("--ocr-json", help="Use existing OCR JSON instead of running OCR")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    if args.probe_json:
        probe = json.loads(Path(args.probe_json).read_text(encoding="utf-8"))
    else:
        probe = run_probe(args.query, args.city, args.lat, args.lon, args.radius)
    if args.ocr_json:
        ocr = json.loads(Path(args.ocr_json).read_text(encoding="utf-8"))
    else:
        ocr = run_ocr(args.screenshot)

    recommendation = score_recommendation(args.query, probe, ocr)
    result = {
        "schema": "china_local_evidence_pipeline_v1",
        "query": args.query,
        "city": args.city,
        "location": {"lat": args.lat, "lon": args.lon},
        "safety_boundary": "read-only composition of bounded probe + user-provided screenshot OCR; no login/CAPTCHA bypass",
        "recommendation": recommendation,
        "probe": probe,
        "ocr": ocr,
    }

    if args.markdown:
        print(f"# {args.query} 本地证据判断")
        print(f"\n- verdict: `{recommendation['verdict']}`")
        print(f"- score: `{recommendation['score']}/100`")
        print(f"- next_action: {recommendation['next_action']}")
        if recommendation["reasons"]:
            print("\n## 支持理由")
            for item in recommendation["reasons"]:
                print(f"- {item}")
        if recommendation["risks"]:
            print("\n## 风险/缺口")
            for item in recommendation["risks"]:
                print(f"- {item}")
        if recommendation["nearby_poi_fallback"]:
            print("\n## 附近 POI 兜底")
            for poi in recommendation["nearby_poi_fallback"][:5]:
                dist = poi.get("distance_m")
                dist_s = f"{dist:.0f}m" if isinstance(dist, (int, float)) else "?"
                print(f"- {poi.get('name')} ({poi.get('source')}, {dist_s})")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
