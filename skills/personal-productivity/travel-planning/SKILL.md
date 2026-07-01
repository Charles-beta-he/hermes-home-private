---
name: travel-planning
description: Use when planning personal trips, road trips, motorcycle trips, flight-to-local-rental itineraries, weather-aware routes, destination shortlists, or travel logistics that should account for the user's prior visited places/photos and safety constraints.
---

# Travel Planning

## Overview

Plan personal trips, routes, day-by-day itineraries, live on-road execution, local food/nightlife choices, booking evidence, and travel-assistant reminders with evidence-first routing.

## When to Use

- Planning personal trips, motorcycle/road trips, routes, hotels, scenic stops, food, parking, tickets, reservations, or live travel execution.
- Recalling an existing travel plan, booked hotel, or scheduled travel assistant state.
- Evaluating local recommendations with public evidence, social evidence, opening hours, route fit, and risk.

Don't use for:
- generic geography facts or visa/legal/medical advice that require a specialist source;
- booking, payment, cancellation, or credential entry without explicit authority and human confirmation;
- recommending already-booked hotels as alternatives unless the user asks to compare.

Use this skill when the user asks for trip recommendations, itinerary design, route planning, motorcycle/road-trip planning, destination comparison, or travel logistics, including mobile connectivity/SIM decisions for travel.

## Connectivity / UK mobile porting

Reference: `references/uk-mobile-porting-and-travel-sims.md` covers UK travel SIM selection and number porting patterns, including giffgaff → CTExcel. Use it when the user asks whether an existing SIM can use another operator's plan, or whether porting enables CTExcel UK/China benefits.

## Core workflow

Detailed travel planning core workflow moved to `references/core-workflow.md`.

Load it when building a full trip plan from destination, dates, route constraints, bookings, evidence, and day-by-day itinerary.

Minimum in-root rule: preserve booked hotels and front-load ticket/reservation/opening-hour/parking checks.

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

Detailed weather-aware route shaping moved to `references/weather-aware-route-shaping.md`.

Load it when weather, seasonal scenery, closures, road safety, or alternative routes affect the itinerary.

Minimum in-root rule: adjust route and timing for weather/safety before optimizing attractions.

## Mobile offline travel copilot / TripState productization

Detailed mobile offline travel copilot and TripState productization guidance moved to `references/mobile-offline-travel-copilot-tripstate.md`.

Load it when turning travel planning into a product/workflow artifact with state, reminders, offline support, or execution checkpoints.

Minimum in-root rule: keep travel plan evidence separate from productization ideas and do not imply live assistant behavior without runtime proof.

## Must-go anchors vs time allocation

When a user says a place is “必须去 / must visit,” treat that as a **route inclusion constraint**, not as an automatic full-day allocation. Decide duration by evidence and opportunity cost: scenery intensity, route fit, ticket/traffic friction, crowd risk, weather dependency, and what higher-value candidates would be displaced. For social-media-shaped domestic trips, first build and rank the candidate pool (required anchors + treasure spots + food/city windows + road-experience segments), then assign time bands such as quick stop / half-day / big half-day / full day.

If Xiaohongshu or another domestic social platform is login-gated, blocked, or returns empty after the user helps with login, do not claim the notes were read and do not keep burning time on the same blocked UI. State the boundary, ask for mobile app screenshots for OCR when useful, and continue with accessible official/OTA/map evidence as provisional. See `references/xinjiang-ili-social-evidence-route-shaping-2026-06.md` for the session-derived Ili/Xinjiang pattern.

## Output shape

Detailed travel output shape moved to `references/output-shape.md`.

Load it when producing a full itinerary, must-go ranking, route table, booking checklist, or risk/evidence appendix.

Minimum in-root rule: include route/time/booking/opening-hour/parking evidence for must-go items and avoid recommending already-booked hotels.

## Scheduled travel assistant drift / evidence audits

When auditing or operating a scheduled travel-assistant cron/job, treat it as a stateful travel co-pilot, not a static itinerary generator. Before judging quality or sending the next briefing, verify the job config, actual run evidence, latest foreground user updates, TripState/state-file freshness, data-source coverage, and delivery evidence. Weather-only freshness is insufficient: compare outputs against confirmed seen POIs, purchased tickets, cancelled preferences, car-return/flight anchors, route/ticket/opening gates, and local food evidence boundaries. If the latest chat state is not available to the job, create/read a scoped TripState SSOT and downgrade stale/unknown cases to confirmation/checklist mode instead of guessing. See `references/scheduled-travel-assistant-drift-evidence-governance.md`.

## Stateful scheduled briefs and drift prevention

When supporting a multi-day live trip through scheduled briefs or repeated check-ins, treat the trip as a stateful workflow, not a fresh itinerary each time. Maintain or recover a compact TripState before giving concrete daily guidance: current phase, current/tonight location, booked hotels, pickup/return windows, flights, completed/seen POIs, booked tickets, cancelled preferences, open unknowns, and hard safety constraints.

For every scheduled travel brief:

1. Start with a **30-second decision card**: today’s main line, route, latest time gate, explicit do-not-do list, fallback, and the single most valuable missing screenshot/location.
2. Separate **confirmed facts / inferred from original plan / unknowns**. Do not present placeholders such as “hotel” or previously recommended candidates as confirmed anchors.
3. Check for drift: already-seen POIs, changed hotels/current location, route phase shift from sightseeing to return logistics, outdated ticket/food assumptions, and whether weather was updated but TripState was not.
4. If the next hard constraint is flight/car return, switch from attraction advice to an execution checklist: fuel, car video, luggage, return point, airport buffer, and only nearby/low-risk food.
5. For live in-trip messages, switch to short copilot mode rather than long daily-brief mode.

See `references/stateful-live-travel-pa-drift-review-2026-06.md` for the session-derived TripState pattern, drift checklist, and daily-brief vs live-copilot output cards.

## TripState-gated travel copilot

When a trip has confirmed booking anchors or the user wants a travel-agent/copilot experience, operate from a scoped TripState and gate engine rather than chat memory alone. See `references/tripstate-gated-travel-copilot.md` for the full pattern: classify booking screenshots as confirmed anchors, keep trip-specific facts out of long-term memory, default live decisions to current conversation time + TripState unless explicitly overridden by user-provided live facts, and answer with a 30-second copilot card plus fallback.

Key pitfall: if the user corrects a live-travel workflow rule, first ask whether it is a class-level gate, scoped TripState rule, or stable personal preference. Do not reflexively write it to durable memory; for most trip execution rules, land it as a TripState gate or skill procedure.

## Live trip execution checkpoints

Use this when the user is already moving, shares live location pins, or asks for the next place/route during a trip.

### Recalling an original plan / booked hotels mid-trip

When the user asks to "回顾原有计划", "我订的酒店", or similar during an active trip:

1. First recover evidence from prior conversation/session context, scheduled trip brief prompts, and scoped travel references before asking the user to repeat details.
2. Separate facts by confidence:
   - **confirmed anchors**: flights, rental window, dates, current live location, explicit order screenshots or user-confirmed bookings;
   - **planned route**: intended city/attraction sequence and safety constraints;
   - **hotel candidates / decision logic**: hotels previously compared or recommended but not proven booked.
3. Never upgrade a previously recommended/candidate hotel into "已订" unless the evidence includes an order screenshot, explicit user confirmation, or booking artifact.
4. Return the answer in an operational shape: trip topology by date, hotel evidence by city/night, what is confirmed vs uncertain, and the immediate implication for today's route.
5. If booking proof is missing, ask for the hotel/order screenshot only after giving the best recovered summary and marking uncertainty.

1. **Confirm first, don't lecture.** Start by acknowledging the live state the user is in (already picked up car, already ate, nearing a scenic spot, blocked at gate), then give the next executable action. Avoid generic "how to search" instructions unless evidence is blocked and the user needs a field tactic.
2. For every next attraction / scenic area / tribe / park / paid viewpoint recommendation, verify or explicitly flag the operational gate before routing: ticket/预约 channel, opening status, last entry, parking/drop-off point, route permission, and failure branch. Do not send a user to a gate with only a navigation pin.
3. For domestic China road-trip execution, return copyable native-map links when possible: 高德 marker/navigation links with precise coordinates and name, plus a fallback keyword search if the URI fails.
4. For couples on the road, protect continuity and mood: avoid long detours to uncertain venues, preserve sunset/return windows, and give a graceful fallback if a ticket/entry/parking check fails.
5. Use a compact live-response shape: **current confirmation → precise next navigation/action → key gate check → fallback**. Keep it short enough to read while parked.

## Live on-road travel execution

Use this when the user is already moving, has shared live pins, is near a gate/parking lot, or needs the next stop. The priority is not education; it is operational confirmation.

1. First confirm the next executable action: exact destination/gate/parking point, clickable navigation, ticket/entry requirement, opening/last-entry time, parking/traffic risk, and fallback if blocked.
2. For scenic spots, treat tickets and admission gates as mandatory checks before sending the user onward: whether tickets are required, where to buy/check in, last entry, correct entrance/parking lot, and whether the user can still enter today.
3. If live platform evidence is blocked, say the boundary and give a field-action fallback: call the scenic spot, ask gate staff/security, buy via official/Meituan/Ctrip/Trip.com if available, or choose a nearby free viewpoint/parking-safe stop.
4. Do not respond with a how-to lecture when the user needs navigation or confirmation. Give the confirmed point first, then one short note about risk/fallback.

## Live on-road execution mode

Detailed live on-road execution mode moved to `references/live-on-road-execution-mode.md`.

Load it during same-day road-trip execution, rerouting, fatigue/weather changes, or time-sensitive checkpoint decisions.

Minimum in-root rule: preserve safety, fuel/charging/rest, weather, and parking constraints before optimizing attractions.

## Local food / nightlife recommendations

Detailed local food/nightlife recommendation guidance moved to `references/local-food-nightlife-recommendations.md`.

Load it when selecting restaurants, cafes, bars, nightlife, or local experience stops.

Minimum in-root rule: align meal timing, route fit, opening hours, booking need, and local evidence.

## App-only booking evidence

Detailed app-only booking evidence guidance moved to `references/app-only-booking-evidence.md`.

Load it when reservations/tickets/availability are visible only through apps or platform-specific evidence.

Minimum in-root rule: label app-only evidence limits and do not imply confirmed booking/payment without user authorization.

## Mainland China local food / nightlife evidence

For mainland China same-day restaurant, cafe, bar, night-market, or local eat/drink/play recommendations, do **not** rely on Google/Bing/OSM as the primary evidence. Prefer, in order: Dianping / Meituan for shop rating, review count, per-capita price, current hours, packages, recommended dishes, and recent bad reviews; Xiaohongshu for recent traveler/local notes and vibe/queue signals; Douyin for current heat and dish visuals; Gaode/Baidu Maps for routing and live opening signals. If web access is blocked, ask for app screenshots and OCR them instead of filling gaps with weak overseas-map evidence. See `references/china-local-food-play-evidence-2026-06.md`.

## China mainland local eat/drink/play evidence

For mainland China restaurants, night markets, cafes, bars, entertainment, and date spots, generic web/map sources are only weak fallback evidence. Prefer native consumer-app evidence before recommending a specific venue:

1. Ask for screenshots or screen recordings from 大众点评 / 美团 / 小红书 / 抖音 / 高德 / 百度地图 when direct web access is blocked or weak.
2. OCR the screenshot for shop name/branch, rating, review count, per-capita price, current open status, recommended dishes, latest negative reviews, queue/wait hints, group-buy/menu prices, and ambience photos.
3. Use 高德/百度/official POI APIs or map pages mainly for distance, route, and location identity; do not treat them as enough proof of food quality.
4. Use Google Maps/Bing/OSM only as rough orientation or fallback for China local shops; label confidence as weak if no native-app evidence is available.
5. Stop at password, SMS, CAPTCHA, payment, identity, or biometric gates. Do not bypass platform defenses for a one-off travel decision.

If evaluating durable project support, treat open-source crawlers/reverse-engineering projects as architecture references or isolated spikes only. For live trip decisions, screenshot/OCR plus map cross-check is usually safer and faster.

## Xiaohongshu / social-media travel evidence

Detailed Xiaohongshu/social-media travel evidence guidance moved to `references/xiaohongshu-social-travel-evidence.md`.

Load it when local food/nightlife/attraction choices depend on recent social evidence or Chinese-language sources.

Minimum in-root rule: distinguish social hype from verified opening hours, location, booking, parking, and route fit.

## References

Detailed travel planning references index moved to `references/references-index.md`.

Load it when locating older travel subtopic references or related project profiles.

Minimum in-root rule: use the smallest relevant reference, not the whole index, for ordinary itinerary planning.

## Common Pitfalls

1. Recommending a hotel after the user already said lodging is booked.
2. Omitting ticket/reservation/opening-hour/parking checks for must-go items.
3. Optimizing for famous spots while ignoring route time, meal timing, weather, or live execution risk.

## Verification Checklist

- [ ] Must-go items include evidence, route fit, time cost, and risk.
- [ ] Food stops align with meal times and local evidence.
- [ ] Tickets/reservations/opening hours/parking are checked or explicitly marked unknown.
- [ ] Existing bookings and user preferences are preserved.
