# Scheduled travel assistant drift & evidence governance

Use this reference when auditing or operating a scheduled travel-assistant cron/job that sends daily or same-day trip guidance.

## Applicability

- A travel assistant is scheduled to send daily briefings during an active trip.
- The user continues to update the trip in foreground chat: seen attractions, purchased tickets, cancelled preferences, changed hotels, live location, car-return details, flight changes, food screenshots, etc.
- The task is to review whether the assistant drifted, whether real-time information is abnormal, or how to repair evidence governance.

## Anti-conditions

- Do not store one trip's hotel names, prices, booking IDs, or exact private route as global skill facts.
- Do not convert a one-off route decision into a durable rule for unrelated trips.
- Do not claim unavailable app/platform evidence was read; mark source boundaries.

## Audit procedure

1. **Identify the scheduled artifact and its authority.**
   - Read the cron/job configuration: schedule, repeat count, enabled state, delivery target, prompt, script, toolsets, last/next run, last error, delivery error.
   - Confirm whether the job has tools needed to meet its own prompt. A prompt that says "use recent messages" but only grants terminal/file without a state file or DB query path is a drift risk.

2. **Recover actual run evidence, not just job status.**
   - Look for stored cron sessions, delivered messages, logs, and evidence files.
   - Compare `repeat.completed` or job counters against actual discoverable run outputs. Missing per-run outputs are an evidence-governance defect even when `last_status=ok`.

3. **Build a compact TripState diff.**
   Separate:
   - `confirmed anchors`: flights, car pickup/return, booked hotels, purchased tickets, user-confirmed seen POIs, cancelled preferences, current live location.
   - `planned route`: original intended topology and fallback branches.
   - `unknowns`: current hotel, exact return point, fuel/return rules, live road status, ticket/last-entry status.
   - `latest user changes`: foreground chat updates after the job was created.

4. **Compare output against latest state.**
   Drift signals include:
   - recommending an attraction the user already saw;
   - recommending a cancelled activity;
   - ignoring a purchased ticket or hotel-bound gate;
   - continuing a static itinerary after the trip phase changed to return-day logistics;
   - giving restaurant/scenic rankings without current local evidence;
   - routing to a gate without ticket/opening/last-entry checks.

5. **Classify real-time information health.**
   - Weather-only freshness is not enough. For live travel, inspect whether the assistant also handled route time, road/traffic, tickets/opening, car return, flight timing, and local food evidence.
   - If only one weather source was queried, label it as single-source weather evidence rather than treating it as complete real-time grounding.

6. **Repair the governance boundary.**
   - Create or update a scoped trip state file, for example `~/.hermes/travel/current_trip_state.json`, and make scheduled prompts read it before generating guidance.
   - Add `last_updated_at`, `confirmed`, `unknown`, `seen_pois`, `purchased_tickets`, `cancelled_preferences`, and `current_phase` fields.
   - If state is stale or required fields are unknown, the scheduled assistant should downgrade to a short confirmation/checklist instead of guessing.
   - For return days, switch from generic travel recommendations to airport/car-return execution: hotel → fuel/inspection → return point → airport buffer → flight.

7. **Archive evidence per run.**
   Save an immutable run note containing:
   - job id, run id, run time, delivery target;
   - TripState version/hash used;
   - user-state anchors used;
   - weather/map/ticket/food/flight sources and timestamps;
   - output body;
   - delivery result;
   - unverified assumptions and source boundaries.

## Minimal TripState sketch

```json
{
  "trip_id": "<scoped-trip-id>",
  "last_updated_at": "<iso8601>",
  "mode": "self_drive",
  "current_phase": "return_day",
  "confirmed": {
    "flight_out": "<flight/time>",
    "car_return": "<return point or unknown>",
    "seen_pois": [],
    "purchased_tickets": [],
    "cancelled_preferences": []
  },
  "unknown": [
    "current hotel",
    "exact car return point",
    "fuel/return rules"
  ]
}
```

## Output pattern for audits

- **已证据化**: job config, actual run records, source outputs, user-state updates.
- **推断/风险**: likely drift, missing tool/data path, stale state risks.
- **修复**: immediate prompt/state fix, TripState SSOT, data-source expansion, evidence archive, lifecycle timing changes.
- **未做/边界**: unavailable logs, missing platform evidence, no file changes unless authorized.
