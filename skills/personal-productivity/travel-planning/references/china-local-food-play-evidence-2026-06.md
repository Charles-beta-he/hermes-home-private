# China local food/play evidence pattern — 2026-06

Applicability: mainland China restaurant/nightlife/local-play recommendations, especially small local stores where Google/Bing/OSM coverage is weak. Use for live travel decisions such as "附近好吃的", "这家店怎么样", "夜宵推荐", "小红书/大众点评/美团/抖音上怎么看".

Anti-conditions:

- Do not bypass CAPTCHAs, slider verification, login gates, app anti-bot, or platform protections.
- Do not ask for or enter user passwords, SMS codes, payment credentials, or private tokens.
- Do not treat Google Maps/Bing/OSM absence as evidence that a mainland China local store is bad or nonexistent.
- Do not build broad crawlers, proxy pools, or mass review scraping for live travel advice.

## Evidence hierarchy

1. User-provided app screenshots from 大众点评 / 美团 / 小红书 / 抖音 / 高德 / 百度地图, then OCR and compare.
2. Official map APIs when configured: 高德 Web Service (`AMAP_WEB_SERVICE_KEY` or `GAODE_MAP_KEY`) and 百度地图 Place API (`BAIDU_MAP_AK`).
3. Explicitly authorized temporary browser/app login for public read-only evidence, with a scoped profile and cleanup.
4. Open POI fallback: OSM/Nominatim/Overpass/Google Maps/Bing, labeled as weak for China-local small shops.
5. On-site heuristics:明码标价、翻台、热气、当地人比例、是否强推大套餐、卫生/排队/服务 signals.

## Current local probe scripts

These scripts are support tooling, not permission to bypass platform gates:

```bash
python3 ~/.hermes/scripts/china_local_evidence_probe.py \
  --query '品伊阁烧麦' --city '呼和浩特' --lat 40.811341 --lon 111.654969

python3 ~/.hermes/scripts/china_local_screenshot_ocr.py <app-screenshot.png>

python3 ~/.hermes/scripts/china_local_evidence_pipeline.py \
  --query '品伊阁烧麦' --city '呼和浩特' \
  --lat 40.811341 --lon 111.654969 \
  --screenshot <大众点评或美团截图.png> --markdown
```

`china_local_evidence_probe.py` outputs `china_local_evidence_probe_v1` with:

- `platform_reachability`: Dianping / Meituan / XHS / Douyin / Amap Web / Baidu Map Web boundary classification.
- `poi_candidates`: official-map API results when keys exist, plus open POI fallback.
- `github_support_candidates`: candidate projects for future adapters.

`china_local_screenshot_ocr.py` outputs `china_local_screenshot_ocr_v1` and extracts visible ratings, price/person candidates, recommended dish lines, and risk lines such as 排队/踩雷/服务差/贵/卫生.

`china_local_evidence_pipeline.py` outputs `china_local_evidence_pipeline_v1` or Markdown and combines live probe + optional app screenshot OCR into a practical verdict:

- `worth_trying`: evidence is strong enough to continue/order normally;
- `try_small_order`: evidence is mixed/partial, order small and avoid big套餐;
- `insufficient_evidence`: ask for app截图 or use现场 heuristics.

It is the default executable path for live same-day店铺判断.

## Observed platform boundaries from the Hohhot 宽巷子 run

For `品伊阁烧麦` / `宽巷子烧麦`:

- 大众点评 PC/mobile: `needs_login`.
- 美团 mobile: `blocked_verification`.
- 小红书 web: reachable shell but no stable result text.
- 抖音 web: reachable shell / verification-like empty result, not reliable.
- 高德/百度 web: reachable but DOM/verification can prevent reliable POI extraction.
- OSM/Overpass can find larger nearby POIs like 额尔敦传统涮 but missed small local store 品伊阁烧麦.

Lesson: for mainland China food/play, ask for app screenshots early. Do not over-trust foreign/open-web sources.

## GitHub support candidates reviewed

- `NanmiCoder/MediaCrawler`: multi-platform 小红书/抖音 keyword search via Playwright login-state; high capability and high governance risk.
- `Sniper970119/dianping_spider`: 大众点评 search/detail/comment crawler; requires cookies/proxies/font handling; spike only.
- `Mocha-Pudding/DPspider`: 大众点评 API-like city/keyword/shop search; useful design reference, lower confidence.
- `yangsijie666/xiaohongshu-crawler`: Playwright + MCP 小红书 search/detail/comments; most Hermes-shaped experiment candidate.
- `Civitasv/AMapPoi`: 高德 POI/geocoding reference; prefer official AMap Web Service API.
- `soaringsoul/easypoi`: 百度地图 POI collection reference; prefer official Baidu Place API.

## Live-response workflow

1. Identify city, position, time, and whether the user is already inside a store.
2. If the decision depends on mainland local reputation, ask for 大众点评/美团/小红书/抖音 screenshot instead of pretending web search is enough.
3. Run OCR if a screenshot is supplied; extract score, people/price, recommended dishes, latest negative review/risk, and open hours.
4. Use official/open POI only for distance/route/cross-check, labeling source confidence.
5. Give an immediate practical recommendation: eat/skip/only small-order, what to order, what to avoid, and next nearby fallback.
6. If evidence is blocked, state the boundary and use on-site heuristics rather than fabricating review data.

## Rural/border-town weak-evidence fallback

Use this when the user is in a small mainland town, grassland route, border area, scenic-town stop, or roadside location where domestic app screenshots are not yet available and open POI coverage is sparse:

1. Reverse-geocode first to name the nearest town/road, then search the town name plus 美食/餐厅/local specialty keywords.
2. Treat Google Maps/Bing/OSM as weak candidate discovery only. A restricted Google Maps result can still provide useful candidate names, coarse distance, and weak ratings, but it is not review-quality evidence for China-local restaurants.
3. Separate restaurant POIs from scenic/play POIs. Do not rank 景区/骑马场/营地 as food-first choices unless the user explicitly wants a scenic stop; prefer family-style 饭店/家常菜/百姓人家-like names for dinner.
4. In grassland/Inner Mongolia border towns, give order guidance by category rather than inventing house specialties: 手把肉/羊排/烤羊腿, 铁锅炖牛羊肉/小鸡炖蘑菇, 奶茶/奶皮子/酸奶, and local bread/jam when culturally appropriate.
5. Add an on-site decision gate: local cars/tables, visible heat/active kitchen, clear per-jin/per-portion pricing for beef/lamb, and no aggressive big-package upsell. If price is vague or only tourist set meals are pushed, downgrade or move to the next candidate.
6. If the user says “不急/要好吃/本地特色”, avoid a single rushed nearest-place answer: provide a ranked shortlist with evidence class and ask for app screenshots to make the final call.

## Validation checklist

- Run `china_local_evidence_pipeline.py --markdown` when location/query inputs are enough, or explain why a screenshot is required.
- Label evidence class explicitly: native-app screenshot OCR, official map API, authorized temporary login, or weak open-web fallback.
- For China-local small shops, "not found on Google/OSM" is not a negative quality signal; treat it only as weak indexing evidence.
- Stop at password, SMS, CAPTCHA, slider, payment, identity, or biometric gates. The next action is screenshot/OCR or explicit temporary-login authorization, not bypassing.
- For GitHub crawler projects, record them as adapter/spike references with governance risk; do not make them live-trip dependencies unless separately authorized and verified.
