# Travel planning with personal history

Use this reference when the user asks for travel, route, road-trip, motorbike-trip, or couple-trip recommendations and expects non-generic options.

## Goal

Produce an executable shortlist, not a destination catalog. Rank routes by fit for the user's departure point, time budget, season, transportation mode, companion style, and previously visited places.

## Evidence sequence

1. Establish route constraints
   - departure city and return city;
   - number of days and whether leave can be extended;
   - vehicle/mode, pillion/passenger, daily distance tolerance;
   - desired mood: mountain roads, sea, old towns, grassland, food, quiet stay, photography, romance;
   - hard constraints: no night riding, no off-road, no high altitude, no crowded scenic spots.

2. Check current facts with tools when available
   - holiday date/window and likely traffic pressure;
   - seasonal weather risks for candidate regions;
   - route distance/time and whether it fits the trip length;
   - road-class hazards for the chosen mode: mountain rain/fog, sea-crosswind, ferry dependency, closures, high altitude, tourist congestion.

3. Use personal history as a de-duplication signal when the user asks for it or it is available
   - Query local photo/location metadata only as needed; city/moment metadata is usually enough.
   - Treat photo-library locations as probabilistic “visited / familiar” signals, not a complete travel history.
   - Downrank places with strong prior-photo evidence unless the user explicitly wants to revisit.
   - Do not inspect private image contents unless the user asks for visual analysis; location metadata is less invasive and usually sufficient.

4. Compare, then recommend
   - Start with 2–4 ranked route options.
   - State why each fits and why lower-ranked options were not chosen.
   - Include day-by-day route skeleton, stay points, highlights, and risk controls.
   - Flag weather-dependent alternatives and fallback routes.

## Output shape

Prefer:

- “Conclusion first”: top route + why.
- “Shortlist”: 2–4 options with fit/risk.
- “Recommended itinerary”: day-by-day route.
- “Avoid / downrank”: places likely already visited, too crowded, too long, or weather-risky.
- “Pre-departure checks”: weather, lodging, gear, road safety.

For couple motorbike trips, optimize for:

- daily distance <= roughly 250–350 km unless the user accepts harder riding;
- no night riding;
- lodging comfort and parking;
- half-day slack for photos, food, and rest;
- rain plan and route-shortening plan.

## Pitfalls

- Recommending generic famous spots without checking departure city or time budget.
- Ignoring repeated destinations already visible in the user's photo/location history.
- Over-optimizing for scenic roads while ignoring passenger comfort.
- Treating forecast APIs as long-range certainty; clearly label short-term forecast vs seasonal risk.
- For motorcycle trips, suggesting long coastal or mountain routes in rainy season without fallback.
