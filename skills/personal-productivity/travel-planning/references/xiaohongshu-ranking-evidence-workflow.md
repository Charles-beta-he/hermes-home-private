# Xiaohongshu ranking evidence workflow for domestic travel planning

Use this reference when a user asks to rank “宝藏景点 / 小众景点 / 可游玩点” from Xiaohongshu or similar domestic social sources, especially when the itinerary already has user-stated must-go POIs.

## Applicability

- Mainland China travel planning where social recency and UGC避坑 matter.
- The user wants a ranked candidate pool, not a generic route.
- Web Xiaohongshu search is login-gated, unstable, redirects home, accepts input unreliably, or returns empty results after login.

## Anti-conditions

- Do not treat this as proof that Xiaohongshu is globally unavailable; it is a fallback workflow for the current access path.
- Do not persist one trip’s exact POI ranking as a global rule. Re-rank with fresh screenshots/searches next time.
- Do not bypass CAPTCHA, SMS, password, payment, identity, or app security gates.

## Core lesson

A user-stated “must go” POI means “include it if feasible,” not “allocate a full day.” Rank every POI by evidence and route value, then assign an earned duration:

- quick stop: <2h / passing viewpoint / food-street wander;
- half day: strong but simple attraction;
- big half day: high-value scenic area with weather/queue sensitivity;
- full day: only if evidence and logistics justify it.

## Bounded web attempt

1. Ask for explicit consent before using the user’s logged-in session.
2. Use a temporary browser profile when possible; do not type secrets.
3. Search 2–3 high-signal terms first, e.g.:
   - `<region> 宝藏景点 自驾`
   - `<region> 小众景点 7月`
   - `<known POI> 值不值得 / 避坑`
4. If search input loops, redirects, or returns empty results, stop forcing it after a short bounded attempt and switch to screenshots.
5. State the boundary plainly: “logged-in page opens, but search results did not load reliably; I need phone screenshots to avoid inventing rankings.”

## Screenshot intake request

Ask the user for search-result screenshots, not dozens of opened notes. Provide exact terms, for example:

- `伊犁 小众景点 7月 自驾`
- `伊犁 宝藏景点 自驾`
- `夏塔 值不值得 7月`
- `琼库什台 值不值得 住宿`
- `恰西 库尔德宁 那拉提 对比`
- `那拉提 自驾票 值不值得`
- `独库公路 7月 堵车 避坑`
- `<city> 美食 本地人`

## OCR extraction fields

For each screenshot/note card, extract:

- title and visible snippet;
- posted recency if visible;
- like/save/comment counts if visible;
- POIs mentioned;
- recommended duration and route order;
- explicit avoid-pitfalls: parking, queues, tickets, self-drive restrictions, weather, roads, lodging, crowding;
- food/local-nightlife windows that would be harmed by scenic detours.

## Ranking dimensions

Score candidates qualitatively or 1–5 on:

1. visual uniqueness / “not wasted trip” value;
2. social evidence frequency + recency;
3. route fit with hard anchors;
4. duration efficiency;
5. crowd, ticket, and traffic risk;
6. couple/family comfort and fatigue;
7. weather sensitivity;
8. effect on food/city-experience windows.

## Output shape

Return:

- **Ranked POI list** with evidence strength: strong / medium / weak.
- **Earned duration** for each: quick stop / half day / big half day / full day.
- **Route implication**: keep / shorten / swap / only-if-weather-good / drop.
- **Evidence boundary**: which rankings came from screenshots vs route heuristics.

## Pitfalls

- Do not say “I read Xiaohongshu” if only search pages failed or screenshots were not provided.
- Do not let famous required POIs consume full days by default.
- Do not overfit one viral note; prefer recurring signals across multiple notes plus route feasibility.
- Do not sacrifice final return safety for a social-media detour.
