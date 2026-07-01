# T-7 Official Entry Precheck Pack for Gated Travel Plans

Use when a confirmed self-drive/booking-heavy trip has future T-7/T-2/day-of gates for road reservations, scenic-area tickets, rental-car constraints, or dynamic opening/weather facts.

## Applicability

- The trip already has a scoped TripState/SSOT with confirmed anchors such as flights, hotels, rental car, or must-go road segments.
- The next safe action is not to book/pay/login, but to prepare the user to capture official readback evidence at the correct window.
- Public web/search/social results reveal likely official channels, applets, reservation terms, or route constraints, but are not execution proof.

## Anti-conditions

- Do not use this to claim tickets, reservations, road openings, or weather gates have passed.
- Do not enter passwords, SMS codes, identity data, vehicle plates, payment details, or submit bookings.
- Do not promote search snippets, news articles, social videos, or webpage-cleaning output to pass/fail authority.

## Procedure

1. Recover the scoped TripState/SSOT and current date.
2. Extract all T-7/T-2/day-of gates: road reservation, scenic tickets, self-drive permits, shuttle/last-entry, rental insurance/rescue/route restrictions, weather/road status, car return/flight buffers.
3. Probe public sources only enough to identify likely official channels and terms. Record source level as advisory.
4. Create a precheck pack with:
   - target gate;
   - observed public/advisory clues;
   - official app/mini-program/public-account/platform names to open;
   - exact screenshots required;
   - screenshot naming convention;
   - pass/warn/fail decision mapping;
   - what remains uncertified until user/platform readback.
5. Patch the TripState with a `prepared_not_certified` event and evidence-ledger item.
6. Link the pack from the trip README/T-minus checklist.
7. Verify JSON and grep key terms before reporting.

## Evidence levels

- `public_search_snippet`: advisory only; useful for locating official channels.
- `media/article/webcleaned`: advisory only; useful for rule discovery.
- `official_platform_entry_screenshot`: can prove the entry exists, not that the booking succeeded.
- `official_success_screenshot`: certified candidate only if it includes date, person/vehicle where relevant, entrance, timeslot, and status.
- `day_of_road_weather_map_readback`: TTL-bound dynamic evidence; becomes stale after the stated window.

## Output shape

Keep the user-facing summary short:

- file created/updated;
- gates covered;
- what the user must screenshot at T-7;
- what remains not certified;
- verification commands/results.

## Pitfalls

- Do not turn a T-7 preparation pack into a booking attempt.
- Do not bury the user in generic travel advice; produce a concrete screenshot checklist.
- Do not let a road reservation success override day-of road/weather/driver/fuel gates.
- If the actual vehicle plate is not known until pickup, mark reservation-dependent fields as pending rather than guessing.
