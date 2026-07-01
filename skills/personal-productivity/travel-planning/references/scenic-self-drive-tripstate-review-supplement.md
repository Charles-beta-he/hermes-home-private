# Scenic self-drive TripState review supplement

Use this reference when a scenic self-drive trip already has confirmed anchors (flights, rental car, hotels) and the user asks to review, refine, or "完善现有计划". The goal is to turn a route/hotel plan into an execution-grade TripState without inventing live facts.

## Applicability

- Multi-day scenic self-drive, especially China domestic routes with app-gated ticketing/traffic evidence.
- Confirmed booking anchors exist and should not be casually replaced.
- The plan has dynamic gates: reservations, tickets, road status, weather, parking, last entry, fuel, fatigue, return flight/car-return windows.
- The user wants reduced manual intervention or proactive reminders.

## Anti-conditions

- Do not store trip-specific hotel names, dates, route incidents, booking IDs, or exact URLs as global rules; keep them in a scoped TripState/project profile/reference.
- Do not claim ticket, road, reservation, or weather gates have passed from static planning, social videos, public articles, or webpage-cleaning output.
- Do not treat a route-pretty plan as execution-ready until each day has gates, latest time, fallback, and evidence status.

## Procedure

1. **Recover the scoped SSOT first.** Read the TripState / daily gate cards / T-minus checklists / evidence ledger before editing. If multiple files exist, patch the canonical JSON plus human-readable cards.
2. **Preserve confirmed anchors.** Flights, rental pickup/return, and booked hotels are hard constraints unless safety/road/weather gates fail. Change route depth, not anchors, first.
3. **Build a P0 gap table.** For each high-risk gap, record risk and the concrete reinforcement: T-7/T-2/Day-of checklist, hard gate, fallback, evidence status, or reminder.
4. **Add daily execution principles.** For every day, ensure there is a main line, latest safe time, hard gates, fallback branch, and a do-not-do list. Scenic days should also say whether the main objective is full-depth, short-line, or low-friction fallback.
5. **Promote one-primary-experience rule.** Peak-season scenic trips should usually pick one main experience per day; extra stops require safe parking, short dwell time, and no impact on the latest gate.
6. **Gate reservation/road-access claims fail-closed.** Social videos and web articles are signals; official readback or user screenshots are execution evidence. Add the gate as advisory/unknown until official readback exists.
7. **Separate evidence-preprocessing from gate authority.** Tools such as Webclaw/browser readability can clean public pages into markdown/JSON, but extraction success should default to warn/advisory. They must not become ticket purchase, reservation execution, or pass/fail authority.
8. **Patch both machine and human artifacts.** Update the structured TripState and the readable daily/T-minus docs so future live-copilot answers and human review match.
9. **Verify the static slice.** Validate JSON syntax and assert the new gate/checklist/evidence IDs exist. State explicitly which dynamic gates remain unverified.

## Recommended artifact shape

- `execution-review-YYYY-MM-DD.md`: hard anchors, P0 gap table, D0-Dn execution principles, evidence-upgrade rules, minimal future user inputs.
- `tripstate.gated.json`: `execution_review_*`, `evidence_promotion_rule`, `daily_execution_rule`, new evidence ledger item, and day-specific gate/fallback updates.
- `daily-gate-cards.md`: concise "review reinforcement" under high-risk days.
- `tminus-checklists.md`: T-7/T-2/Day-of checklist with screenshots/readback and TTL requirements.
- `acceptance-checklist.md`: static slice completed vs dynamic gates still open.

## Verification checklist

- [ ] JSON parses.
- [ ] All days still exist and date/order are unchanged unless explicitly authorized.
- [ ] New review/evidence IDs are present.
- [ ] High-risk road/reservation gates remain unknown/advisory without official readback.
- [ ] Return day protects car-return/flight buffer and does not spend airport margin on optional sightseeing.
- [ ] Final answer distinguishes static plan completion from unverified live facts.
