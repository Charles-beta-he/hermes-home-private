# Xinjiang flight + hotel + car anchor triage pattern (session-derived, 2026-06)

Applicability: Mainland China flight-in self-drive trips where the user provides screenshots of confirmed hotels, flights, and rental-car orders after an itinerary draft. Especially useful for Xinjiang / Ili routes with long distances, scenic-road risk, and airport pickup/return.

Anti-conditions:
- Do not reuse the exact dates, hotels, flight numbers, prices, or order IDs for other trips.
- Do not treat rental order return time as the safe airport arrival time; score it against flight time and local return workflow.
- Do not infer booking facts from recommended candidates; only screenshots or explicit user confirmation are confirmed anchors.

## Workflow

1. **Parse anchors by evidence tier**
   - Confirmed: hotel/order screenshots, flight screenshots, rental-car order screenshots, explicit user correction.
   - Inferred: route topology implied by consecutive confirmed hotels.
   - Unknown: insurance, route restrictions, rescue coverage, road gates, current weather, ticket rules.

2. **Update the TripState immediately**
   - Create or patch a scoped trip file rather than keeping facts only in chat.
   - Separate sections for: objective/constraints, flight anchors, rental-car anchors, hotel anchors, day-by-day execution, weather/road evidence, open gates.
   - Remove resolved unknowns when the user corrects them (e.g. a single hotel room is a 4-person villa).

3. **Re-score the first and final driving days**
   - Late inbound flight: if arrival is after midnight, do not plan night pickup, city exploration, or long driving. Sleep near the airport; move pickup and supplies to the next day.
   - Midday pickup after a red-eye/late arrival: first driving day becomes recovery + vehicle inspection + conservative transfer. If pickup/inspection slips, drop optional stops.
   - Rental return close to flight: compare order return time to departure. If the gap is tight (e.g. <=2h), treat the order time as the platform latest commitment, not the plan. Set an earlier execution target for fuel, cleaning, vehicle video, queueing, luggage, check-in, and security.

4. **Vehicle fit and upgrade triage**
   - For 4-person long scenic Xinjiang self-drive with luggage, roomy mid/large SUVs are usually better than small crossovers and often better than hard-core off-roaders on mature paved routes.
   - Four-wheel drive increases stability margin but does not permit wild roads, muddy牧道, grassland shortcuts, or routes disallowed by the rental contract.
   - Do not blindly upgrade to MPV when the route includes mountain/grassland/scenic-road uncertainty; preserve ground clearance and tire/road confidence unless comfort needs dominate.

5. **Rental order follow-up checklist**
   Ask for or inspect order detail pages for:
   - insurance scope and deductibles;
   - rescue/towing range and phone number;
   - deposit and violation deposit;
   - fuel/cleaning/late-return rules;
   - route/region restrictions, including Duku, Nalati, Bayinbuluk, village roads, and unpaved roads;
   - pickup证件, driver eligibility, and whether airport station is truly in-terminal / shuttle / offsite.

## Output pattern

Give a short operational patch, not a full re-plan every time:

- What was newly confirmed.
- What changed in D0/D1/final day.
- The new hard time gates.
- Whether the vehicle is fit for the route.
- The one next screenshot or detail still needed.

## Pitfalls

- A flight landing after midnight makes the previous calendar day misleading; write the itinerary as “D0 late flight -> D1 early arrival”.
- A rental order return time 1–2 hours before departure is not safe enough for a real plan even if the shop is airport-adjacent.
- A single room in hotel screenshots may still be sufficient if the user confirms it is a villa/suite for the whole party; remove the uncertainty instead of repeatedly asking.
- Keep order IDs, prices, and hotel facts in scoped trip references/files, not global memory.
