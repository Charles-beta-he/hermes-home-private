# Domestic Travel Query Chain Notes (Scoped Reference)

Scope: China domestic travel planning where OTA websites/apps, 12306, and Mac iPhone/iPad apps are used as evidence sources. This reference is procedural and source-class specific; examples are illustrative, not persistent trip facts. Anti-condition: do not treat any route, price, date, or platform status here as current truth without re-querying.

## Workflow lesson

When the user asks to “打通链路” or says not to compare prices yet, do not jump straight into fare comparison. Build a query-chain proof first:

1. Define the itinerary SSOT: dates, origin/destination, A/B route branches, fixed return constraints, and manual boundaries.
2. Probe each transport data source for basic usability before relying on it.
3. Record status as: usable / partially usable / blocked / app-only / manual-only.
4. Only after source usability is proven, extract candidate flights/trains/hotels.
5. Keep a local artifact with results, links, timestamps, and next manual handoff steps.

## Web platform patterns

- Ctrip web/mobile pages can return `whaleguard block` in automated browser contexts. If blocked, do not waste time fighting the page; mark as app/manual source and use another web source.
- Tongcheng Web can be a strong browser fallback for China domestic flights. Direct one-way URL pattern observed:
  - `https://www.ly.com/flights/itinerary/oneway/<FROM>-<TO>?date=<YYYY-MM-DD>`
  It can expose route, date, fare calendar, flight count, flight numbers, times, transit points, and prices without login.
- Qunar Web can load route/date forms and price calendars but may show “暂无符合条件的机票信息” for a specific date even when nearby dates have prices. Treat it as cross-check/calendar, not sole source.
- Fliggy Web/H5 may timeout or return 404 for flight pages in automated/browser contexts. Prefer app/manual flow.
- 12306 Web/API is useful for rail reachability and direct-train checks. It is useful as a feasibility/backup check even when rail is not practical for the trip.

## Mac iPhone/iPad App chain

On Apple Silicon Macs, App Store may show iPhone/iPad apps and allow installation, but installed variants may differ:

- Verify installed app path and bundle id after installation (`mdfind`, Finder, or app metadata).
- HD/iPad variants may open but route core functions to login or legacy endpoints. Do not assume they are equivalent to the main phone app.
- Stop at Apple ID, Touch ID, SMS code, login, or payment boundaries; let the user handle secrets and final booking.

## Transport-planning implications

For short trips with a hard return:

- Use candidate flight times to update itinerary constraints. If return departs in the morning, the previous night must be at the return city and the final day should be only return logistics.
- Prefer arrival times that preserve the next morning’s rental/vehicle inspection window.
- Flag overlong overnight connections as itinerary-breaking even when cheap.

## Output shape preferred by this user

- The user often wants final results and selectable options, not long process narration.
- Keep operational detail in a local SSOT/reference file, and report only: source status, usable links, best candidates, blockers, and next required human action.
