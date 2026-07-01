# Live On-Road Travel Execution Mode

Extracted from `/Users/charles/.hermes/skills/personal-productivity/travel-planning/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Live on-road execution mode

Applicability: same-day, in-trip assistance when the user is already driving/walking, sharing live locations, or asking for the next concrete action. Anti-conditions: do not store one trip's hotel names, prices, route incidents, or booking IDs here; those belong in scoped references or project profiles.

1. **Confirm the decision first, then explain only what is needed.** If the user needs to act now, lead with a direct yes/no or a single recommended destination/link. Avoid teaching the process or giving a long generic checklist before the actionable answer.
2. Treat live travel as a chain of gates, not just route ideas:
   - food/water/fatigue: has the user eaten, are they safe to continue driving;
   - lodging: exact hotel name, address, parking/check-in cutoff, route arrival time;
   - attraction entry: ticket, reservation, opening hours, last entry, parking gate, whether tickets can be bought on-site;
   - road safety: sunset, weather, unpaved/private-road avoidance, fuel and phone signal.
3. For attractions, **surface ticket/entry/last-admission evidence before routing the user to the gate**. If current ticket evidence is blocked or app-only, say so and ask for the user's booking/map/review-app screenshots; do not let the user discover a closed/no-ticket gate only after arrival.
4. When the user asks for a precise next location, provide a clickable map-deep-link and a text fallback in the same message: navigation link, POI name, full address, coordinates/evidence source, and fallback search phrase if the link does not open.
5. For couples self-drive, default to comfort-protecting decisions at dusk: if the current attraction gate fails or time is tight, route to hotel/city first instead of trying alternate scenic gates.
6. Evidence hierarchy for live POIs: local/native map and booking evidence first, user screenshots when web is blocked, broad/global maps only as orientation fallback. If sources disagree, label uncertainty and prefer the user-visible app/official booking evidence.
