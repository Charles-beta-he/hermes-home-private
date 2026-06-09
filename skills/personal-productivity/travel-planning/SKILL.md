---
name: travel-planning
description: Use when planning personal trips, road trips, motorcycle trips, flight-to-local-rental itineraries, weather-aware routes, destination shortlists, or travel logistics that should account for the user's prior visited places/photos and safety constraints.
---

# Travel Planning

Use this skill when the user asks for trip recommendations, itinerary design, route planning, motorcycle/road-trip planning, destination comparison, or travel logistics.

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

## References

- `references/hulunbuir-motorcycle-rental-planning-2026-06.md` — session-derived pattern for Hangzhou→Hulunbuir flight + local motorcycle rental, weather-window route shaping, and rental-vendor screening for a desired ADV model.