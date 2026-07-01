# Travel Planning Output Shape

Extracted from `/Users/charles/.hermes/skills/personal-productivity/travel-planning/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Output shape

Prefer:

- **Conclusion / best choice**
- **Why this fits the user**
- **Weather/season decision**
- **Date-by-date itinerary**
- **Fallback branches**
- **Booking checklist**
- **Safety/risk gates**

For scenery-first self-drive plans, also:

- Name the route by exact regional scope, not vague marketing labels. If the plan is "Ili depth + Sayram Lake + Duku Highway", do not call it a full North Xinjiang loop unless Kanas/Hemu/Altay are actually included.
- Show region modules as well as point-by-point days so the user can see which part of the destination is covered.
- Do not turn user-specified must-go attractions into automatic full-day allocations. Treat them as mandatory waypoints, then assign time by scenery value, season/weather, route fit, ticket/queue risk, and opportunity cost.
- When the objective is natural scenery, downgrade cities to lodging/meal/refuel/supply anchors unless the user explicitly asks for city culture. Use city evenings only for nearby dinner/night-snack when night driving is disallowed.
- Embed food at meal points; choose specific restaurants only after lodging is fixed and native app/map evidence can be checked.
- For rail/soft-sleeper/public-transport alternatives, state not only comfort and seat class but also how many scenic days the option consumes or preserves.
- For flight-in rental-car trips, score flight arrival by whether it preserves the first self-drive day. If a transport option pushes the start from D1 to D2, state the exact scenic branch that must be cut before recommending it.
- When the user shares a confirmed flight/order screenshot, parse it as a hard schedule anchor and patch only the affected D0/D1/final-day windows: late check-in, safe rental pickup time, conservative first transfer, car-return buffer, and penultimate-night lodging priority. Use `references/confirmed-flight-anchors-self-drive.md`.
- For 4-person long scenic self-drive with luggage, do not default to hard-core off-road vehicles just because the route includes Duku/grassland. When main roads are paved/mature, rank roomy mid/large SUVs (e.g. 揽境/途昂/揽巡 equivalents) above hard-core off-roaders (e.g. 坦克300/BJ40) unless route conditions truly require off-road capability. Confirm exact model, fuel type, luggage fit, route permission, rescue, and tire/glass/undercarriage insurance. See `references/xinjiang-ili-rental-hotel-low-touch-2026-06.md`.
- When airport-adjacent hotel pickup/return makes the final flight day easier, do **not** automatically spend that buffer on city attractions. Treat it as resilience for refuel, luggage, vehicle handoff, traffic, and airport procedures; if expanding, usually improve the previous scenic road day instead. For the Xinjiang/Ili pattern, shift margin to Duku viewpoints / Qorma rest / Dushanzi-Kuitun dinner while keeping D9 as airport-return only. See `references/domestic-self-drive-final-day-hotel-return-buffer-2026-06.md`.
- When the user provides confirmed hotel + flight + rental-car order screenshots after a draft, switch to **anchor triage**: patch a scoped TripState, mark screenshots as confirmed anchors, rescore D0/D1/final-day time gates, and treat a tight rental return time before flight as a latest platform commitment rather than the safe plan. See `references/xinjiang-flight-hotel-car-anchor-triage-2026-06.md`. If the user clarifies a suspicious booking detail (e.g. one room is a 4-person villa), remove that unknown immediately instead of asking again.
- In peak-season scenic self-drive, push the plan into a booking matrix early: lock cancellable bottleneck lodgings first, use double-insurance reservations for weather/body-state branch nights, and define cancellation rules.
- When the user wants reduced manual intervention, switch from screenshot-by-screenshot hotel screening to a low-touch booking target list: per-night preferred zone, acceptable hotel types/brands, hard filters, fallback, and cancel/double-insurance rule. Use OTA sources (Ctrip/Meituan/Qunar/Tongcheng/Fliggy) for room/price/reviews and maps only for route/location verification. Ask for screenshots only for bottleneck/unclear properties. See `references/xinjiang-ili-rental-hotel-low-touch-2026-06.md`.
- Add altitude/wind-chill/body-state gates for mountain, high-lake, grassland, and Duku-style road trips: symptoms or driver fatigue should reduce scenic depth, avoid high-altitude overnights, or trigger fallback.
- Provide a packing/clothing checklist by route segment, not just generic "bring warm clothes"; keep warm layers in the car cabin for high-road stops.
- When choosing rental SUVs for 4-person long scenic self-drive, prioritize usable cabin/luggage space, long-distance comfort, confirmed route permission, insurance/rescue coverage, tire condition, and fuel practicality over hard-offroad styling. If budget is not the constraint, large family SUVs usually beat small crossovers and often beat Tank/BJ40-style off-roaders for this class of trip; see `references/domestic-self-drive-rental-vehicle-selection-2026-06.md`.
- When recommending hotels for domestic self-drive trips, especially scenic/high-altitude lodging such as 琼库什台、那拉提、巴音布鲁克、独山子/奎屯, separate **evidence-confirmed candidates**, **brand/search targets**, and **filter keywords**. Do not present OTA search keywords or plausible chain names as confirmed hotel recommendations. If public web evidence is weak or app-only, ask for 携程/美团/去哪儿 screenshots and label unverified names as search targets. See `references/xinjiang-hotel-evidence-tiering-2026-06.md`.

Avoid:

- long generic destination lists after the user has chosen a destination;
- pretending booking inventory is confirmed when only general search evidence exists;
- dumping private photo metadata;
- overfitting a one-day forecast as final truth.

See `references/scenery-first-self-drive-planning-2026-06.md` for the session-derived pattern covering scenery-first itinerary allocation, city-as-night-meal-anchor handling, Duku-style road gates, and rail/soft-sleeper impact screening.
