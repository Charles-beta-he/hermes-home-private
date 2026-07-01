# Stateful live travel PA drift review (2026-06)

Applicability: domestic China self-drive or road-trip support where the assistant sends scheduled daily briefs and also handles live in-trip messages. Especially useful for couples trips with hard constraints such as flights, car return windows, weather risk, and booked hotels.

Anti-conditions: do not store one trip's private hotel names, booking IDs, exact locations, or stale route facts as global memory. Use this reference as a workflow pattern, not as a reusable Hulunbuir itinerary.

## Session-derived lesson

A scheduled "daily travel brief" can be directionally correct while still drifting from the real trip. In the reviewed Hulunbuir self-drive case, the 6/20 brief correctly prioritized safe return to Hailar before the next-day flight, avoided grassland deep detours under rain/wind risk, and maintained evidence honesty for Dianping/Meituan/Xiaohongshu. The weakness was architectural: the cron was mostly a static-plan brief plus weather lookup, not a stateful live copilot.

Core finding: weather may be real-time while the trip itself is not. A travel PA must track TripState, otherwise it risks repeating already-seen POIs, missing changed hotels, treating candidates as booked facts, or continuing to recommend attractions when the current phase has become car-return/airport execution.

## TripState requirement

For multi-day live trips, maintain a compact state object or equivalent structured note before scheduled briefs:

- trip_id / date range / mode (self-drive, motorcycle, walking, etc.)
- current_phase: planning, arrival, scenic day, transfer, return-eve, return-day
- confirmed anchors: flights, hotel(s), pickup/return windows, current city/location, booked tickets
- completed/seen POIs and cancelled preferences
- unknowns that affect routing: exact hotel, car return point, fuel rule, current location
- hard constraints: no night driving, no grass/牧道/small roads, border/drone limits, couple comfort
- last_updated_at and source of each key fact when possible

Scheduled briefs must read this state first. If key fields are missing or stale, label the plan as "按原计划推断" and downgrade to conservative routing or ask for the one highest-value screenshot/location.

## Daily brief vs live copilot split

Use two output modes:

1. Daily brief: morning planning skeleton.
   - 30-second decision card first.
   - Today’s main line, explicit do-not-do list, normal/conservative/weather-degraded routes.
   - Latest arrival/departure gates.
   - Weather/clothing and one most useful missing screenshot/location request.

2. Live copilot: in-trip response when user sends location, map screenshot, food/shop screenshot, or asks "now where?".
   - Current judgement.
   - Exact next action/navigation target.
   - Key gate: ticket/opening/parking/route safety/latest time.
   - Fallback if blocked.
   - Keep short enough for a parked driver/passenger to read.

## Drift checks for scheduled travel jobs

Before every scheduled travel output, check:

- Is today still a sightseeing day, or has it become return-day logistics?
- Did the user already visit or cancel any POI being recommended?
- Are hotel/current-location/car-return facts confirmed or placeholders?
- Does the plan rely only on weather but lack route/POI/booking evidence?
- Does the output need a pre-flight/pre-return checklist instead of an attraction list?
- Are unverified assumptions explicitly marked?

## Evidence hierarchy

For China road-trip execution:

- Weather: live forecast is necessary but insufficient.
- Route: prefer Gaode/Baidu navigable strings/deep links and map screenshots; reject no-name roads, grassland tracks, village shortcuts, and 牧道 when comfort/safety matters.
- POI gates: official/map/OTA evidence for opening, last entry, ticket/reservation, parking, and correct entrance.
- Food/play: Dianping/Meituan/Xiaohongshu/Douyin/Gaode screenshots plus OCR; do not invent rankings when blocked.
- Return day: flight status, car return rules, fuel, luggage, airport timing outrank sightseeing.

## Output patterns

### 30-second decision card

- 今日结论: one sentence.
- 路线: one copyable route or link.
- 最晚门槛: latest departure/arrival.
- 不做: explicit abandon list.
- 降级: weather/time/fatigue fallback.
- 需要你补: exactly one highest-value missing screenshot/location.

### Live copilot card

- 当前判断: go / don’t go / downgrade.
- 下一步: exact navigation/action.
- 关键 gate: ticket/opening/parking/route/time.
- fallback: what to do if blocked.

## Pitfalls

- Do not let a daily cron continue recommending scenic POIs when the next hard constraint is a morning flight or car return.
- Do not treat "weather updated" as "trip updated"; user state and completed POIs must be updated too.
- Do not bury the action in a long essay during live travel; lead with the executable decision.
- Do not ask for many screenshots at once; request the one screenshot that removes the biggest uncertainty.
