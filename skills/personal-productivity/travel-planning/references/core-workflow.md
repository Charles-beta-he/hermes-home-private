# Travel Planning Core Workflow

Extracted from `/Users/charles/.hermes/skills/personal-productivity/travel-planning/SKILL.md` on 2026-07-01T08:54:33.968451+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Core workflow

1. **Clarify only path-changing assumptions.**
   - If the user gives a clear origin/dates/mode, proceed.
   - Ask only when missing context materially changes feasibility, safety, budget, side effects, or booking decisions.
   - Do not assume “depart from home by vehicle” for motorcycle trips: explicitly distinguish:
     - ride from origin;
     - fly/train to destination then rent locally;
     - self-drive car;
     - guided/chartered route.

2. **Ground current facts with tools and outside best practice.**
   - Before giving a concrete plan or recommendation, check market/public practice first: official sources, maps/reviews, open web/social evidence, competitor/operator patterns, or local community signals depending on the travel decision.
   - Verify current date/holiday window, weather, road/season risks, and transport feasibility with tools.
   - Treat forecasts as provisional; call out when a plan depends on rechecking T-7/T-2 days.
   - For flights/rentals/food/nightlife, prefer current search/official/vendor/map/social evidence over generic memory; if blocked by CAPTCHA/login, state the evidence boundary and switch to executable heuristics rather than inventing rankings.
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
   - Treat user-declared “must-go” POIs as route constraints, not automatic full-day allocations. Before assigning a full day, rank each POI against alternatives by evidence, route fit, crowd/booking risk, time cost, and “不白来” payoff. A must-go site may deserve a quick scenic stop, half day, or full day depending on current evidence.
   - When the user asks to verify “宝藏景点/可游玩点/排行”, switch from itinerary drafting to evidence collection first: search native/social sources, capture note titles/claims, cluster candidates, then produce a ranked POI shortlist with recommended dwell time and routing implications.

5. **Produce an executable plan, not a generic list.**
   - Give a final recommendation first.
   - Include date-by-date route, distance bands, lodging zones, contingency branches, and decision gates.
   - Keep output focused on choices that affect booking/routing/safety.
