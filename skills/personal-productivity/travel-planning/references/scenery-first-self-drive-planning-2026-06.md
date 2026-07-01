# Scenery-first domestic self-drive planning lesson (2026-06)

Applicability: domestic China self-drive planning where the user says the trip is mainly for natural scenery, accepts 5–6h driving days, does not want night driving, and wants local food included without sacrificing daytime scenery. Anti-conditions: do not apply when the user explicitly wants city culture, shopping, nightlife, museums, or food as the primary objective.

## Lessons

1. Do not convert user-specified “must-go” attractions into automatic full-day allocations. Treat them as mandatory waypoints, then assign time by scenery value, route fit, season/weather, ticket/queue risk, and opportunity cost.
2. Separate region labels from scenic points. If a route is an “Ili route”, show the area modules (e.g. Sayram/Bortala, Yining as food/lodging node, Zhaosu/Xiata, Tekes/Qiongkushitai/Kalajun, Xinyuan/Nalati, Duku/Bayinbuluk) so the user understands which part of Xinjiang/China the plan covers.
3. When the user says city scenery is not needed, downgrade cities to lodging/meal/refuel/supply anchors. Do not reserve daytime for city streets or old towns. City walks are only optional if adjacent to dinner/lodging.
4. If night driving is disallowed, use evenings in the lodging city for nearby dinner/night-snack only. Do not create a separate urban tourism branch, and do not drive across town for food.
5. Food should be embedded at natural meal points: list local categories by lodging city first, then choose specific restaurants only after hotels are fixed and native app/map evidence can be checked.
6. Keep safety anchors: the day before a hard return should not depend on a long mountain road. For Duku-like roads, define opening/weather/control/time gates and a stable lodging anchor outside the risky section.
7. For transport-to-destination screening, split “preserve itinerary days” from “rail/soft-sleeper comfort”. A long soft-sleeper route can be acceptable in abstract but still bad if it consumes one or two scenic days. Present its itinerary impact explicitly.

## Output pattern

- Name the route by region and scope, not vague labels: e.g. “Ili depth + Sayram Lake + Duku Highway”, not “North Xinjiang big loop” if Kanas/Hemu are excluded.
- Give a final default route plus controlled branches:
  - scenic/lodging upgrade branch (e.g. Qiongkushitai if reliable lodging exists),
  - stable branch (e.g. Kalajun + push toward Nalati),
  - weather/road-control fallback (e.g. skip Duku or shorten Nalati).
- For each day include: main natural target, drive/load band, lodging anchor, dinner/night-snack category, and gate/fallback.
- For public transport: show direct rail, high-speed + sleeper/EMU transfer, flight/direct or one-stop, and state whether each preserves or breaks the scenic itinerary.
