#!/usr/bin/env python3
"""China local eating/travel evidence probe.

Read-only, bounded probes for China-local POI/review sources.

Safety boundary:
- Does not bypass CAPTCHA, sliders, login gates, paywalls, or platform anti-bot systems.
- Does not collect private/authenticated data.
- Uses official map APIs only when keys are provided via environment.
- Falls back to public/open POI sources and platform reachability classification.

Example:
  python3 ~/.hermes/scripts/china_local_evidence_probe.py \
    --query '品伊阁烧麦' --city '呼和浩特' --lat 40.811341 --lon 111.654969
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

UA_DESKTOP = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
)
UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0 Safari/604.1"
)
TIMEOUT = 18
MAX_BODY = 80_000


@dataclass
class SourceProbe:
    source: str
    status: str
    url: str
    final_url: str = ""
    http_status: Optional[int] = None
    content_type: str = ""
    evidence: str = ""
    action: str = ""


@dataclass
class PoiCandidate:
    source: str
    name: str
    kind: str = ""
    distance_m: Optional[float] = None
    address: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    tags: Dict[str, Any] | None = None


def fetch(url: str, *, mobile: bool = False, data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None) -> tuple[int, str, str, str]:
    h = {
        "User-Agent": UA_MOBILE if mobile else UA_DESKTOP,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = resp.read(MAX_BODY).decode("utf-8", "ignore")
        return resp.status, resp.url, resp.headers.get("content-type", ""), body


def classify_platform_body(source: str, final_url: str, body: str) -> tuple[str, str, str]:
    text = re.sub(r"\s+", " ", body)[:2000]
    lower = (final_url + " " + text).lower()
    if any(k in lower for k in ["captcha", "verify", "验证码", "滑块", "安全验证", "spiderindefence"]):
        return "blocked_verification", text[:220], "Use user app screenshot/OCR or explicit browser login; do not bypass verification."
    if any(k in lower for k in ["login", "登录", "smslogin", "pclogin", "扫码"]):
        return "needs_login", text[:220], "Use user app screenshot/OCR or explicit temporary login if user authorizes."
    if len(body.strip()) < 500 and source in {"douyin", "douyin_web"}:
        return "blocked_or_js_shell", text[:220], "Web shell returned no readable results; use app screenshot/OCR."
    if any(k in body for k in ["品伊阁", "宽巷子", "烧麦", "羊肉", "评价", "推荐菜"]):
        return "readable_partial", text[:300], "Parse visible text manually or with browser/OCR; verify freshness in app."
    return "reachable_no_result_text", text[:220], "Reachable but no useful result text in bounded probe."


def probe_platforms(query: str, city: str) -> List[SourceProbe]:
    q = urllib.parse.quote(query)
    qc = urllib.parse.quote(f"{query} {city}")
    urls = {
        "dianping_pc": f"https://www.dianping.com/search/keyword/5/0_{q}",
        "dianping_mobile": f"https://m.dianping.com/search/keyword/5/0_{q}",
        "meituan_mobile": f"https://i.meituan.com/s/{q}/",
        "xiaohongshu_web": f"https://www.xiaohongshu.com/search_result?keyword={qc}",
        "douyin_web": f"https://www.douyin.com/search/{qc}",
        "amap_web": f"https://ditu.amap.com/search?query={q}&city=150100",
        "baidu_map_web": f"https://map.baidu.com/search/{q}",
    }
    results: List[SourceProbe] = []
    for source, url in urls.items():
        try:
            status, final, ctype, body = fetch(url, mobile=("mobile" in source or source in {"douyin_web", "xiaohongshu_web"}))
            cls, evidence, action = classify_platform_body(source, final, body)
            results.append(SourceProbe(source, cls, url, final, status, ctype, evidence, action))
        except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
            body = ""
            try:
                body = e.read(MAX_BODY).decode("utf-8", "ignore")
            except Exception:
                pass
            cls, evidence, action = classify_platform_body(source, getattr(e, "url", url), body)
            results.append(SourceProbe(source, cls, url, getattr(e, "url", url), e.code, e.headers.get("content-type", ""), evidence, action))
        except Exception as e:
            results.append(SourceProbe(source, "error", url, evidence=f"{type(e).__name__}: {str(e)[:180]}", action="Use alternate channel or app screenshot."))
    return results


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nominatim_search(query: str, city: str, lat: Optional[float], lon: Optional[float]) -> List[PoiCandidate]:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"format": "jsonv2", "limit": "8", "countrycodes": "cn", "q": f"{query} {city}"}
    )
    out: List[PoiCandidate] = []
    try:
        status, final, ctype, body = fetch(url, headers={"User-Agent": "HermesChinaLocalEvidence/1.0"})
        data = json.loads(body)
        for item in data:
            la, lo = float(item["lat"]), float(item["lon"])
            dist = distance_m(lat, lon, la, lo) if lat is not None and lon is not None else None
            out.append(PoiCandidate("nominatim", item.get("name") or item.get("display_name", "")[:80], item.get("type", ""), dist, item.get("display_name", ""), la, lo, {"importance": item.get("importance")}))
    except Exception:
        pass
    return out


def overpass_nearby(query: str, lat: Optional[float], lon: Optional[float], radius: int = 1200) -> List[PoiCandidate]:
    if lat is None or lon is None:
        return []
    terms = [t for t in re.split(r"\s+", query) if t]
    name_regex = ".*" + ".*".join(map(re.escape, terms[:2])) + ".*" if terms else ".*"
    overpass = f"""
[out:json][timeout:25];
(
  node(around:{radius},{lat},{lon})[name~"{name_regex}"];
  way(around:{radius},{lat},{lon})[name~"{name_regex}"];
  relation(around:{radius},{lat},{lon})[name~"{name_regex}"];
  node(around:{radius},{lat},{lon})[amenity~"restaurant|cafe|fast_food|food_court"];
  way(around:{radius},{lat},{lon})[amenity~"restaurant|cafe|fast_food|food_court"];
);
out center tags 80;
"""
    data = urllib.parse.urlencode({"data": overpass}).encode()
    out: List[PoiCandidate] = []
    try:
        status, final, ctype, body = fetch("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": "HermesChinaLocalEvidence/1.0"})
        obj = json.loads(body)
        for el in obj.get("elements", []):
            tags = el.get("tags", {})
            name = tags.get("name")
            if not name:
                continue
            la = el.get("lat") or el.get("center", {}).get("lat")
            lo = el.get("lon") or el.get("center", {}).get("lon")
            if la is None or lo is None:
                continue
            dist = distance_m(lat, lon, float(la), float(lo))
            out.append(PoiCandidate("overpass", name, tags.get("amenity") or tags.get("shop") or tags.get("tourism") or "poi", dist, tags.get("addr:full") or tags.get("addr:street") or "", float(la), float(lo), tags))
    except Exception:
        pass
    return sorted(out, key=lambda x: x.distance_m if x.distance_m is not None else 10**9)[:20]


def amap_official(query: str, city: str, lat: Optional[float], lon: Optional[float]) -> List[PoiCandidate]:
    key = os.getenv("AMAP_WEB_SERVICE_KEY") or os.getenv("GAODE_MAP_KEY")
    if not key:
        return []
    params = {"key": key, "keywords": query, "city": city, "offset": 10, "page": 1, "extensions": "base"}
    url = "https://restapi.amap.com/v3/place/text?" + urllib.parse.urlencode(params)
    out: List[PoiCandidate] = []
    try:
        status, final, ctype, body = fetch(url)
        data = json.loads(body)
        for p in data.get("pois", []):
            loc = p.get("location") or ""
            la = lo = None
            if "," in loc:
                lo_s, la_s = loc.split(",", 1)
                lo, la = float(lo_s), float(la_s)
            dist = distance_m(lat, lon, la, lo) if lat is not None and lon is not None and la is not None and lo is not None else None
            out.append(PoiCandidate("amap_official", p.get("name", ""), p.get("type", ""), dist, p.get("address", ""), la, lo, {"tel": p.get("tel"), "biz_ext": p.get("biz_ext")}))
    except Exception:
        pass
    return out


def baidu_official(query: str, city: str, lat: Optional[float], lon: Optional[float]) -> List[PoiCandidate]:
    ak = os.getenv("BAIDU_MAP_AK")
    if not ak:
        return []
    params = {"query": query, "region": city, "output": "json", "ak": ak}
    url = "https://api.map.baidu.com/place/v2/search?" + urllib.parse.urlencode(params)
    out: List[PoiCandidate] = []
    try:
        status, final, ctype, body = fetch(url)
        data = json.loads(body)
        for p in data.get("results", []):
            loc = p.get("location") or {}
            la, lo = loc.get("lat"), loc.get("lng")
            dist = distance_m(lat, lon, la, lo) if lat is not None and lon is not None and la is not None and lo is not None else None
            out.append(PoiCandidate("baidu_official", p.get("name", ""), p.get("tag", ""), dist, p.get("address", ""), la, lo, {"telephone": p.get("telephone"), "detail": p.get("detail")}))
    except Exception:
        pass
    return out


def github_support() -> List[Dict[str, Any]]:
    # Static shortlist from verified GitHub searches; avoids burning rate limit every travel query.
    return [
        {"repo": "NanmiCoder/MediaCrawler", "stars": 51295, "fit": "multi-platform xhs/douyin keyword search via Playwright login-state; high capability, high governance risk"},
        {"repo": "Sniper970119/dianping_spider", "stars": 1234, "fit": "Dianping search/detail/comment crawler; requires cookies/proxies/font handling; spike only"},
        {"repo": "Mocha-Pudding/DPspider", "stars": 37, "fit": "Dianping API-like city/keyword/shop search; low stars, useful design reference"},
        {"repo": "yangsijie666/xiaohongshu-crawler", "stars": 8, "fit": "Playwright + MCP Xiaohongshu search/detail/comments; Hermes-shaped experiment candidate"},
        {"repo": "Civitasv/AMapPoi", "stars": 551, "fit": "AMap POI/geocoding reference; prefer official AMap Web Service API"},
        {"repo": "soaringsoul/easypoi", "stars": 122, "fit": "Baidu map POI collection reference; prefer official Baidu Place API"},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--city", default="")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--radius", type=int, default=1200)
    args = ap.parse_args()

    started = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    platform = probe_platforms(args.query, args.city)
    pois: List[PoiCandidate] = []
    pois.extend(amap_official(args.query, args.city, args.lat, args.lon))
    pois.extend(baidu_official(args.query, args.city, args.lat, args.lon))
    pois.extend(nominatim_search(args.query, args.city, args.lat, args.lon))
    pois.extend(overpass_nearby(args.query, args.lat, args.lon, args.radius))

    # Deduplicate POIs by source/name/address-ish.
    seen = set()
    deduped: List[PoiCandidate] = []
    for p in sorted(pois, key=lambda x: (x.distance_m if x.distance_m is not None else 10**9, x.name)):
        key = (p.source, p.name, round(p.lat or 0, 5), round(p.lon or 0, 5))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)

    result = {
        "schema": "china_local_evidence_probe_v1",
        "generated_at": started,
        "query": args.query,
        "city": args.city,
        "location": {"lat": args.lat, "lon": args.lon},
        "safety_boundary": "read-only bounded probe; no CAPTCHA/login bypass; no private account data; official map APIs only if user-provided environment keys exist",
        "platform_reachability": [asdict(x) for x in platform],
        "poi_candidates": [asdict(x) for x in deduped[:25]],
        "github_support_candidates": github_support(),
        "recommended_next_channel": "For Dianping/Meituan/XHS/Douyin, use user app screenshots + OCR unless explicit temporary login is authorized.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
