# China Local Evidence Probe — 2026-06-16

## Goal

Build a safe first-stage crawler/probe for China-local eating/travel evidence sources after the Hohhot / 宽巷子 live-use case showed that Google/Bing/OSM are weak for mainland POI/review evidence.

## Safety boundary

This probe is intentionally read-only and fail-closed:

- no CAPTCHA / slider bypass;
- no credential or password entry;
- no private account scraping;
- no commercial-scale crawling;
- no hidden proxy pool;
- official map APIs are used only when environment keys exist;
- blocked Dianping/Meituan/XHS/Douyin paths return a structured boundary rather than attempting evasion.

## Landed artifact

Script:

```text
/Users/charles/.hermes/scripts/china_local_evidence_probe.py
```

Run example:

```bash
python3 ~/.hermes/scripts/china_local_evidence_probe.py \
  --query '品伊阁烧麦' \
  --city '呼和浩特' \
  --lat 40.811341 \
  --lon 111.654969
```

Output schema:

```text
china_local_evidence_probe_v1
```

Main sections:

- `platform_reachability`: Dianping / Meituan / XHS / Douyin / Amap Web / Baidu Map Web reachability classification.
- `poi_candidates`: official-map API results when keys exist, plus Nominatim/Overpass fallback POI candidates.
- `github_support_candidates`: verified GitHub repo shortlist for future adapters.
- `recommended_next_channel`: screenshot/OCR guidance for blocked domestic apps.

## Verification run

Commands executed:

```bash
chmod +x ~/.hermes/scripts/china_local_evidence_probe.py
python3 -m py_compile ~/.hermes/scripts/china_local_evidence_probe.py
python3 ~/.hermes/scripts/china_local_evidence_probe.py --query '品伊阁烧麦' --city '呼和浩特' --lat 40.811341 --lon 111.654969
python3 ~/.hermes/scripts/china_local_evidence_probe.py --query '宽巷子烧麦' --city '呼和浩特' --lat 40.811341 --lon 111.654969
```

Evidence outputs:

```text
/Users/charles/.hermes/docs/private/china-local-evidence-probe-pinyige-20260616.json
/Users/charles/.hermes/docs/private/china-local-evidence-probe-kuanxiangzi-shaomai-20260616.json
```

Observed statuses for both probes:

- `dianping_pc`: `needs_login`
- `dianping_mobile`: `needs_login`
- `meituan_mobile`: `blocked_verification`
- `xiaohongshu_web`: `reachable_no_result_text`
- `douyin_web`: `reachable_no_result_text`
- `amap_web`: `reachable_no_result_text`
- `baidu_map_web`: `reachable_no_result_text`

Nearby fallback POI evidence from Overpass included:

- 麦当劳 ~284m
- 肯德基 ~375m
- 额尔敦传统涮 ~416m
- 星巴克 ~511m

`品伊阁烧麦` was not found in the open fallback POI layer, matching the live observation that it is likely a small local store with weak public-web indexing.

## GitHub support shortlist

Verified with GitHub search / repo readme checks:

- `NanmiCoder/MediaCrawler` — multi-platform XHS/Douyin keyword search via Playwright login-state; high capability, high governance risk.
- `Sniper970119/dianping_spider` — Dianping search/detail/comment crawler; requires cookies/proxies/font handling; spike only.
- `Mocha-Pudding/DPspider` — Dianping API-like city/keyword/shop search; lower stars, useful design reference.
- `yangsijie666/xiaohongshu-crawler` — Playwright + MCP Xiaohongshu search/detail/comments; Hermes-shaped experiment candidate.
- `Civitasv/AMapPoi` — AMap POI/geocoding reference; prefer official AMap Web Service API.
- `soaringsoul/easypoi` — Baidu map POI collection reference; prefer official Baidu Place API.

## Recommended next landing path

Completed in the next slice:

- `china_local_evidence_pipeline.py` now composes bounded platform/POI probes plus optional app screenshot OCR into a practical verdict (`worth_trying`, `try_small_order`, `insufficient_evidence`).
- `scripts/test_china_local_evidence.py` covers OCR extraction, platform boundary classification, recommendation scoring, and CLI JSON composition.

Remaining forward path:

1. Add official map API keys if available:
   - `AMAP_WEB_SERVICE_KEY` or `GAODE_MAP_KEY`
   - `BAIDU_MAP_AK`
2. Use screenshot OCR path for Dianping/Meituan/XHS/Douyin app pages by default.
3. Only after explicit authorization, run a temporary-login XHS experiment using a scoped Playwright profile; default cleanup after run.
4. Treat Dianping/Meituan crawlers as research spikes, not default travel-path dependencies.

## Operational rule

For live mainland China food/travel decisions, prefer:

1. user app screenshot/OCR;
2. official map API / POI;
3. explicitly authorized temporary login for social review sources;
4. open-web/OSM as fallback only.
