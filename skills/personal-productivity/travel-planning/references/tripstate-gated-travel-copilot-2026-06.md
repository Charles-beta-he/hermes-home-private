# TripState-gated travel copilot pattern (session-derived, 2026-06)

Applicability: live or soon-to-live trips where the user has shared concrete booking anchors (hotels, flights, rental car, tickets) and expects the agent to act as an execution copilot rather than a generic itinerary generator.

Anti-conditions:
- Do not reuse trip-specific hotels, flight numbers, prices, vehicle orders, or dates for another trip.
- Do not claim realtime road, weather, ticket, map, or opening facts without fresh evidence.
- Do not write trip-local facts or temporary live state into durable memory.

## Core lesson

A travel copilot is complete only when it can run this chain:

```text
orders/screenshots/user confirmations
→ TripState with field provenance
→ evidence ledger
→ gate engine
→ live 30-second card
→ T-7/T-2/day-of verification
→ memory/writeback governance
```

Markdown plans are useful, but they are not the same as a runtime-ready travel agent. If the user asks for “完整落地 / 多模型认为完整 / 旅游 agent”, verify whether the result is only a readable plan or whether it also has executable state, gates, fixtures/tests, and UI/live-card surfaces when a product/runtime is in scope.

## Landing-zone classifier for travel learnings

- Confirmed trip facts (hotel names, flight numbers, car order, ticket screenshots): scoped TripState / trip SSOT.
- Dynamic travel facts (weather, road openings, last entry, map traffic): evidence ledger with freshness and recheck gates.
- Reusable procedure (how to infer live phase, how to decide D9 return day, screenshot OCR flow): skill/reference.
- Stable user preference: memory only if it remains true across trips; also embed the workflow preference in this skill if it changes how travel tasks should be handled.
- Temporary live state (current location, actual departure time, fatigue, “already ate”): do not persist except in the active TripState/session.

## Runtime/live completeness checklist

When a trip becomes a “travel agent” workflow, check for these artifacts:

- TripState schema with labels such as `confirmed`, `inferred`, `user_stated`, `screenshot_derived`, `stale`, `unknown`.
- Evidence ledger: claim → source → freshness → confidence → decision gate.
- Gate engine with outcomes: `pass`, `warn`, `fail`, `blocked`.
- Per-day gate cards including hard time, road/weather, ticket/last-entry, fuel, body-state, lodging, and return/flight constraints.
- Live inference rule: default to current chat time + plan; explicit user live location/departure overrides; if conflict affects safety/flight/lodging, ask the minimum question.
- 30-second live card: current confirmation, one next action/map target, latest hard time, gates, fallback, do-not-do list, and one highest-value missing screenshot/evidence.
- T-7/T-2/day-of checklists for dynamic facts; do not pre-fill them with guesses.
- Memory write gate: trip facts to TripState, reusable procedure to skill, stable preference to memory, temporary state nowhere durable.

## Gate patterns highlighted by the Xinjiang/Ili self-drive case

These are class-level patterns, not destination facts:

1. **Order anchors override recommendations.** Once hotels/flights/car are confirmed, stop recommending replacements unless a safety/evidence gate fails.
2. **Return day is not “no sightseeing”; it is gate-controlled.** Allow nearby, short, reversible stops only if hard return/flight/fuel gates remain safe.
3. **Fuel is a first-class gate.** Before remote, mountain, grassland, or long-return segments, require fuel thresholds and offline maps/supplies.
4. **Village/mountain lodging needs entry gates.** Confirm parking/route/dinner/hot water/check-in cutoff and avoid entering after dark or after rain/road warnings.
5. **Body-state gates must fail closed.** High fatigue, headache, nausea, driver sleepiness, or slowed reaction should downgrade the route.
6. **Ticket/last-entry gates must be executable.** “Check opening hours” is too weak; cards need last-entry, shuttle return, queue threshold, and abandon/depth-reduction rules.

## Multi-model / review handling

If an async or independent review fails the travel-agent completeness claim, do not defend the prior plan. Convert the critique into artifacts or gates:

- If UX says “not live enough”, add a live-card surface or template and test/verify it if a runtime exists.
- If safety says “missing gates”, add explicit per-day gates instead of general advice.
- If product/workflow says “docs vs runtime split”, separate safe local documentation completion from runtime/product completion and downgrade the claim.
- Report true certification separately from degraded multi-role review; model agreement alone is not evidence without objective artifacts.
