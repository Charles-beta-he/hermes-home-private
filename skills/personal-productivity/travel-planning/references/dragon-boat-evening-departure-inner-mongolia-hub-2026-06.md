# Dragon Boat evening-departure Inner Mongolia hub pattern (2026-06)

Use when a user wants to preserve a prior Inner Mongolia grassland/forest motorcycle-trip preference but can only depart Hangzhou on the evening of 6/16 or a similar short-holiday eve.

## Problem

Direct late-evening Hangzhou -> Hailar was not available in the checked web inventory. The viable move was to separate the trip into:

1. evening departure to a larger hub with late flights;
2. overnight near the hub airport;
3. early next-morning feeder flight into the scenic/rental region.

## Evidence pattern from the session

Checked on Tongcheng web inventory during the session:

- HGH -> HLD on 2026-06-16: no true 18:00-23:59 departure result; same-day options were concentrated around late morning/noon.
- HGH -> HET on 2026-06-16: viable evening departures existed, including approximately 18:05 -> 20:35 and 18:35 -> 00:25+1.
- HET -> YIE on 2026-06-17: early feeder existed, approximately 06:40 -> 08:30.
- HET -> HLD on 2026-06-17: early feeder existed, approximately 07:30 -> 09:35.
- Return chain example: YIE -> HET late morning, then HET -> HGH evening, leaving a long transfer buffer.

Treat exact times/prices as stale; re-query live inventory before recommending booking.

## Decision logic

When a user says “must depart on the evening of the 16th” and the original destination lacks late direct flights:

1. Do not keep insisting on the original airport as the entry point.
2. Search larger regional hubs that have evening flights from origin and morning feeder flights onward.
3. Compare the hub-chain against the original objective:
   - does it preserve the scenic/riding objective?
   - does it avoid night riding?
   - does it create a safe first day after a late arrival?
   - does it keep rental pickup and return feasible?
4. If the onward destination has uncertain motorcycle rental inventory, separate recommendations:
   - best experience if self-drive or rental confirmed locally;
   - best motorcycle certainty if entering via the stronger rental city.

## Recommended shape from the session

For Hangzhou + Inner Mongolia + grassland/forest/riding preference:

- Experience-first route: Hangzhou evening -> Hohhot overnight -> early flight to Arxan -> Arxan/Chaihe fixed-hub light route.
- Motorcycle-certainty route: Hangzhou evening -> Hohhot overnight -> early flight to Hailar -> rent in Hailar -> shorten toward Arxan/New Barag rather than forcing the full Hailar north loop.

## Pitfalls

- Do not label “arrives late” as satisfying “departs late”; the user cared about leaving after work/evening.
- Do not bind the final return to a long remote ride plus flight chain. Force the penultimate day back near the return airport/rental base.
- Do not assume Arxan has reliable motorcycle rental just because the route is better; verify vehicle source or present self-drive as the cleaner execution mode.
- Do not preserve a full original loop if the hub chain consumes time or weather shifts; compress the route around the highest-value segments.
