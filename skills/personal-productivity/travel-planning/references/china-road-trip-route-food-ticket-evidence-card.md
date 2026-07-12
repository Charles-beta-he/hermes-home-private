# China road-trip route, food, ticket, and navigation evidence card

Applicability: same-day mainland China self-drive briefs where the user expects an executable route, a concrete meal stop, advance ticket reminders, and native-map links. Especially useful when a scheduled brief combines a transfer day with attractions in the next 1–3 days.

Anti-conditions: do not use weak public snippets as proof of current opening, inventory, queue, road closure, or mobile-app traffic. Do not log in, solve CAPTCHAs, purchase, reserve, or pay without separate authorization. Do not request a user screenshot for information already obtained from a current web/map readback.

## Required sequence

1. Read the scoped itinerary/TripState and preserve booked hotels, pickup/return times, flights, and route gates.
2. Open the native-map route and read back origin/destination identity, distance, planned drive time, and major roads. Separate map travel time from added meal/rest/fuel buffers.
3. Build meal timing from the verified route rather than from a generic long-drive estimate.
4. Offer a concrete off-highway meal plan when time permits:
   - one primary named restaurant and one fallback;
   - exact map-search name, address/coordinates when available, published hours, cuisine/signature dishes, and evidence freshness;
   - estimated detour/time gate derived from the route, not guessed;
   - explicit fallback if closed, queued, or too far from the route.
5. Cross-check restaurant identity using at least two accessible evidence classes where possible: native map for POI/location and a public restaurant/OTA/official page for address, coordinates, published hours, menu, or reviews. Treat old/small-sample reviews as weak; state positive and negative signals rather than calling the venue definitively “best.”
6. Generate native-map links, not only search terms:
   - place marker: `https://uri.amap.com/marker?position=<lng>,<lat>&name=<encoded-name>&coordinate=gaode&callnative=0`
   - segment navigation: `https://uri.amap.com/navigation?from=<lng>,<lat>,<name>&to=<lng>,<lat>,<name>&mode=car&policy=1&coordinate=gaode&callnative=0`
   - verify that each URL resolves to a map/route page before sending it.
7. Add a rolling 1–3 day ticket/booking horizon. Classify each attraction as:
   - **today must act** — inventory/entry mode can block the route;
   - **today verify** — rules/hours/opening need confirmation;
   - **not yet needed** — no immediate action, but state the next check time.
   Include ticket vs vehicle/self-drive admission, shuttle/route choice, entry window/last admission, parking, weather/road dependency, and official app/mini-program/phone fallback.
8. Ask for exactly one screenshot only when the unresolved field is genuinely app-only or mobile-live (current congestion, temporary closure notice, logged-in inventory/order state). Name the missing field. Never ask for a route screenshot after web readback already supplied the same distance/time/road data.

## Evidence labels

- **Verified now:** opened/read back in the current run.
- **Published listing:** address/hours/menu shown by an accessible public page; current operation still needs same-day confirmation.
- **Weak reputation evidence:** old, sparse, or non-native reviews.
- **App-only unknown:** current inventory, queue, promotion, or logged-in order state unavailable without user app evidence.

## Compact output order

1. Route/time readback.
2. Exact meal recommendation with clickable map links.
3. Today’s ticket/booking actions plus 1–3 day horizon.
4. Safety/fuel/fatigue gate.
5. Only the single remaining app-only evidence request, if any.

## Pitfalls

- “Eat at a service area” is a fallback, not a completed food recommendation when a safe local stop fits the route.
- A candidate restaurant name without a verified location/link is not executable.
- Published opening hours do not prove the restaurant is open now.
- Do not shift research work to the user merely because native review sites require login; first exhaust accessible map and public listing evidence, then clearly isolate the remaining app-only reputation/queue gap.
- Transfer days can still require advance ticket action for tomorrow’s attraction.