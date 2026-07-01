# Confirmed flight anchors for flight-in self-drive trips

Use when the user shares a flight/order screenshot after an itinerary has already been drafted. The goal is to convert the screenshot into hard schedule anchors and immediately re-run only the affected logistics windows, not to redesign the whole trip.

## Procedure

1. Extract the factual anchors from the screenshot:
   - route, date, departure/arrival time, +1 day markers;
   - airline and flight number;
   - displayed price and whether the screenshot likely shows total order price or per-person price;
   - booking status if visible.
2. Classify arrival against the trip's previously defined execution windows:
   - preserves first self-drive day;
   - preserves it but requires later pickup / conservative first day;
   - pushes self-drive start to the next day and therefore requires scenic-branch cuts.
3. Patch the itinerary rather than restarting it:
   - D0: airport/near-pickup hotel, late check-in, no night pickup/drive;
   - D1: pickup time, sleep buffer, grocery/fuel window, conservative long-transfer gate;
   - final day: hard backward plan from flight time to airport arrival, car return, fuel, luggage, and proof photos;
   - penultimate night: prioritize lodging that protects the final flight/car-return buffer.
4. Update the booking tracker with flight number/time/price, but label price ambiguity if order passenger count is not explicit.
5. Re-state the next booking actions that changed because of the flight anchor.

## Flight-in self-drive heuristics

- A late-night/early-morning arrival can still preserve a full self-drive itinerary if the next day uses a mid-morning rental pickup and a conservative transfer target.
- Do not schedule car pickup immediately after a post-midnight landing unless the user explicitly wants it; sleep and safe driving are more valuable than one or two hours.
- If the return flight is late afternoon/evening, the previous night can stay outside the airport city, but it must be on a reliable return corridor with a hard morning departure gate.
- For road-trip endings after a mountain/highway scenic day, penultimate lodging should be chosen for the final flight buffer, not just scenery.

## Output card

- Confirmed flight facts.
- Whether the original itinerary remains valid.
- Exact changed windows for D0/D1/final day.
- Lodging/rental implications.
- Price calculation with explicit assumption about passenger count.
- Immediate next actions.

## Anti-conditions

- Do not store the user's specific flight numbers, prices, or dates as global skill facts.
- Do not infer checked-bag allowance, refund rules, terminal, or actual passenger count unless visible in the screenshot or confirmed by the user.
- Do not treat a late arrival as permission to night-drive a rental car unless explicitly authorized and safe.
