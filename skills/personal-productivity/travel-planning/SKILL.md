---
name: travel-planning
description: Use when planning personal trips, road trips, motorcycle trips, flight-to-local-rental itineraries, weather-aware routes, destination shortlists, or travel logistics that should account for the user's prior visited places/photos and safety constraints.
---

# Travel Planning

Use this skill when the user asks for trip recommendations, itinerary design, route planning, motorcycle/road-trip planning, destination comparison, or travel logistics, including mobile connectivity/SIM decisions for travel.

## Connectivity / UK mobile porting

Reference: `references/uk-mobile-porting-and-travel-sims.md` covers UK travel SIM selection and number porting patterns, including giffgaff → CTExcel. Use it when the user asks whether an existing SIM can use another operator's plan, or whether porting enables CTExcel UK/China benefits.

## Core workflow

1. **Clarify only path-changing assumptions.**
   - If the user gives a clear origin/dates/mode, proceed.
   - Ask only when missing context materially changes feasibility, safety, budget, side effects, or booking decisions.
   - Do not assume “depart from home by vehicle” for motorcycle trips: explicitly distinguish:
     - ride from origin;
     - fly/train to destination then rent locally;
     - self-drive car;
     - guided/chartered route.

2. **Ground current facts with tools.**
   - Verify current date/holiday window, weather, road/season risks, and transport feasibility with tools.
   - Treat forecasts as provisional; call out when a plan depends on rechecking T-7/T-2 days.
   - For flights/rentals, prefer current search/official/vendor/map evidence over generic memory.
   - When travel execution depends on dynamic booking platforms, first verify the available query paths before comparing options: public endpoint, official API, mobile app on desktop, authenticated browser, or user-provided screenshot. Stop at login, CAPTCHA, identity, or payment gates.
   - For complex trips with route fallbacks, keep a compact local planning source of truth: objective, route branches, booking chains, deterministic probes, evidence output, open gaps, and manual intervention boundaries.

3. **Use the user's prior travel history when available.**
   - If the user asks to avoid repeats or references图库/photos, inspect photo/location metadata when accessible.
   - Use it only to reduce repetition and improve recommendations; do not expose unnecessary personal-location details.
   - Summarize as broad regions already visited, not raw coordinates or exhaustive private logs.

4. **Optimize for the stated trip objective.**
   - Identify whether the trip is romance, scenery, riding intensity, novelty, safety, budget, food, photography, or family comfort.
   - Rank destinations by the objective, not by generic popularity.
   - For couples trips, protect experience quality: avoid night riding, excessive daily mileage, and weather-driven “拉练”.

5. **Produce an executable plan, not a generic list.**
   - Give a final recommendation first.
   - Include date-by-date route, distance bands, lodging zones, contingency branches, and decision gates.
   - Keep output focused on choices that affect booking/routing/safety.

## Motorcycle / local-rental trip planning

When the user will fly/train to a destination and rent a motorcycle locally:

1. Plan around **rental pickup/return windows**, not only scenic routes.
2. Keep the first rental day conservative if pickup, contract, inspection, and local acclimation happen that morning.
3. Prefer ending the penultimate day near the rental return city/airport when weather risk exists.
4. Identify local rental candidates by evidence tier:
   - explicit rental inventory and model availability;
   - motorcycle clubs with route/rental signals;
   - brand dealers that may know local ADV/rental resources;
   - general motor shops only as fallback.
5. Never assume a specific high-demand/new model is available unless confirmed by vendor evidence.
6. For desired models, define fallbacks by functional requirement: displacement, ADV/comfort, luggage, wind protection, tire/road suitability, insurance, rescue coverage.
7. Provide a vendor inquiry template that asks for:
   - exact model/year/version;
   - real vehicle video/photos;
   - contract, insurance, deposit, mileage limits;
   - rescue/towing range;
   - allowed route/regions;
   - luggage/helmet/rain gear/phone mount/USB;
   - damage, tire, breakdown, late-return liability.

## Weather-aware route shaping

1. Put the most scenic/remote/longest segments into the best forecast window.
2. Put rain/wind-prone days near cities, rental bases, or short-loop options.
3. Avoid making the return/rental deadline depend on a long remote ride under rain, wind, or mountain conditions.
4. For grassland/coastal/open roads, treat **crosswind** as a first-class hazard, not secondary to rain.
5. For mountains, account for fog, wet leaves, gravel washout, landslide/rockfall risk, and lower temperatures.
6. For short-holiday motorcycle trips with uncertain weather/rentals, prefer a **fixed-hub A/B contingency topology**:
   - keep arrival city, rental pickup/return, and final pre-flight lodging fixed;
   - design a higher-upside scenic branch and a lower-risk fallback branch from the same hub;
   - book cancellable lodging packages for both branches;
   - choose the branch at T-1 / D0 after checking weather, actual vehicle condition, and lodging constraints;
   - force the penultimate day back to the hub so the final day is only return/short-loop logistics.
7. When the user must depart in the evening but the original destination has no late direct flight, do not force the original airport. Search a larger regional hub with evening origin flights plus early next-morning feeder flights, then re-score against the trip objective, rental certainty, weather, and no-night-riding constraints. Keep “departs late” distinct from merely “arrives late”.
7. When the user asks for concrete execution details, include a riding weather/clothing index, not only a route: min/max temperature, apparent temperature, precipitation probability/amount, wind gusts, UV, sunrise/sunset or latest safe arrival time, and gear layers.

## Output shape

Prefer:

- **Conclusion / best choice**
- **Why this fits the user**
- **Weather/season decision**
- **Date-by-date itinerary**
- **Fallback branches**
- **Booking checklist**
- **Safety/risk gates**

Avoid:

- long generic destination lists after the user has chosen a destination;
- pretending booking inventory is confirmed when only general search evidence exists;
- dumping private photo metadata;
- overfitting a one-day forecast as final truth.

## App-only booking evidence

Scope: use this only when a travel plan reaches concrete booking research and ordinary web pages do not provide current bookable options. Do not use it for high-level itinerary brainstorming.

For domestic social-platform travel evidence (Xiaohongshu/Douyin screenshots, login-gated searches, "马上出发" checklists, or a visual "show me" evidence board), use `references/domestic-social-travel-evidence-board.md`. It covers screenshot OCR, no-proxy temporary browser login, quote→risk→action synthesis, HTML evidence-board output, and cleanup/privacy rules.

1. Prefer current, source-attributed booking evidence over generic search snippets.
2. If a booking web page blocks automation, switch to safer channels: official availability endpoints, official/provider apps, user-provided app screenshots, or semi-automated browsing in the user's real app session.
3. Stop for passwords, SMS/captcha, payment, biometric checks, or other secrets.
4. Summarize booking research as options with source, time, price, fit/risk, and next action.

See `references/china-travel-booking-evidence-2026.md` for a scoped domestic-booking evidence pattern.

## Xiaohongshu / social-media travel evidence

Xiaohongshu web may block with IP-risk/login. Do not claim you read notes if blocked. Prefer, in order: user-provided app screenshots; explicit user consent for a temporary web login/QR scan; broader web snippets as weak evidence; or a provisional checklist clearly labeled as route/weather-derived.

When the user consents to web login, use a no-proxy temporary browser profile to avoid system VPN/proxy ports, read only public search/note DOM, then close the browser and delete the temporary profile. Preserve the evidence chain: note title + short quote/comment → risk judgment → concrete checklist item. See `references/xiaohongshu-travel-evidence-no-proxy-2026-06.md`.

For domestic motorcycle trips where evening flight constraints, air-rail transfers, 12306 timing, and uncertain motorcycle rental leads interact, also consult `references/domestic-motorcycle-trip-transport-rental-evidence-2026-06.md` before recommending the route.

Scoped reference, not a global rule: for a short northern grassland / border-city couples self-drive itinerary where the user asks for scenic, romantic, or internet-famous hotels with date-specific room/price evidence, consult `references/hulunbuir-couples-hotel-booking-evidence-2026-06.md`. Applicability: hotel selection must balance romantic/scenic value against no-night-driving, parking, and pre-flight return logistics. Anti-conditions: do not reuse the named hotels or prices without rechecking live inventory; do not apply it to non-couples, non-driving, or unrelated regions.

For Hailar / Hulunbuir self-drive car rental with airport pickup plus city or hotel return, consult `references/hailar-car-rental-platform-screening-2026-06.md`; verify exact local outlet capability, pickup/return windows, fees, route permission, insurance, rescue, and whether the evidence comes from an app/order page rather than SEO city pages.

## References

- `references/domestic-travel-query-chain.md` — scoped pattern for travel source/query feasibility before price comparison; includes platform-source probing, Mac iPhone/iPad app checks, SSOT artifacts, and anti-conditions for stale route/price data.
- `references/domestic-air-rail-intermodal-screening-2026-06.md` — session-derived pattern for domestic China flight + train transfer screening; includes 12306 station-code/query probing, transfer-buffer feasibility, and when to downgrade theoretical overnight-rail ideas.
- `references/hulunbuir-motorcycle-rental-planning-2026-06.md` — session-derived pattern for Hangzhou→Hulunbuir flight + local motorcycle rental, weather-window route shaping, and rental-vendor screening for a desired ADV model.
- `references/dragon-boat-hailar-arxan-weatherproof-planning-2026-06.md` — session-derived pattern for Hailar-as-hub A/B route planning: Hulunbuir north-loop scenery upside vs Arxan south-loop weather/intensity fallback, cancellable lodging packs, rental-evidence gates, and northern grassland clothing guidance.
- `references/dragon-boat-hulunbuir-arxan-contingency-2026-06.md` — session-derived pattern for fixed-hub A/B contingency planning: Hailar north-line vs Arxan south-line, cancellable hotel packages, rental lead screening, holiday crowding, and riding weather/clothing index.
- `references/hulunbuir-arxan-dual-route-contingency-2026-06.md` — session-derived pattern for Dragon Boat Festival sunny-weather planning where Hailar is the stable in/out + pickup/return hub and Hulunbuir north line vs Arxan/Chaihe south line are treated as switchable branches with holiday-crowd controls.
- `references/dragon-boat-evening-departure-inner-mongolia-hub-2026-06.md` — session-derived pattern for preserving an Inner Mongolia grassland/forest trip when the user can only depart in the evening: use a larger hub such as Hohhot, overnight near the airport, then take an early feeder into Arxan or Hailar while keeping rental certainty and no-night-riding constraints explicit.
- `references/hulunbuir-car-rental-hotel-booking-2026-06.md` — session-derived pattern for Hailar airport pickup/city hotel car return, SUV selection for Hulunbuir roads, Ctrip/Meituan vs Trip.com booking evidence, couple-friendly hotel tradeoffs, and using image URLs to explain why a hotel is worth booking.
- `references/hulunbuir-car-rental-hotel-return-planning-2026-06.md` — session-derived pattern for Hailar afternoon arrival + local car rental: airport pickup, Hailar city/hotel return the evening before an 11:30 departure, north-line lodging topology, platform verification, and no-night-rural-driving cutoffs.
- `references/hulunbuir-couples-self-drive-booking-weather-social-evidence-2026-06.md` — scoped pattern for Hulunbuir couples self-drive decisions that combine domestic hotel booking evidence, Ctrip/Meituan app limitations, GitHub-supported Ctrip scrape options, SUV rental comparison, Open-Meteo clothing/snow checks, and Xiaohongshu screenshot-based避坑 synthesis.
- `references/xiaohongshu-no-proxy-search-evidence-2026-06.md` — scoped pattern for Xiaohongshu travel evidence when the user asks to avoid a VPN/proxy port: bypass system proxy for probes, use isolated no-proxy Chrome if needed, stop at login/CAPTCHA, and report evidence boundaries clearly.