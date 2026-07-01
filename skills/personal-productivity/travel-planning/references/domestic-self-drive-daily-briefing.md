# Domestic self-drive daily briefing pattern

Applicability: mainland China self-drive travel briefings, especially same-day morning plans, airport pickup/return days, scenic-road loops, and couple-focused trips where comfort and arrival time matter.

Anti-conditions:

- Do not treat scenic-area display names as sufficient navigation targets when local guides warn they misroute.
- Do not plan from generic itinerary slots after a user provides flight/train/rental screenshots; the screenshot timing becomes the schedule anchor.
- Do not assume motorcycle routing when the user says self-drive/car rental.
- Do not invent platform rankings or exact POI coordinates without source evidence.

## Required output shape

1. **Anchor facts first**: parse screenshots for flight number, date, planned arrival, airport/terminal, check-in/seat/gate if visible, luggage/transfer status, pickup constraints.
2. **Navigation route, not just itinerary**: provide copyable 高德/百度 waypoint strings with start, intermediate points, destination, and hotel/return-car endpoint when known.
3. **Normal + downgrade routes**:
   - normal route for good weather and on-time pickup;
   - late-arrival route if pickup is delayed;
   - weather/visibility downgrade route;
   - hard stop time when the driver must skip the next point.
4. **Local navigation pitfalls**: when scenic names may misroute (e.g. river/grassland attractions), tell the user to use a verified nearby service point/visitor center/known gate/roadside viewing area rather than the broad scenic name. If uncertain, state uncertainty and ask for an app screenshot/pin instead of making up a coordinate.
5. **Self-drive safety gate**: no night driving on grassland roads; avoid dirt/牧道/草地 shortcuts; prefer main roads; check fuel, tire pressure, insurance/rescue, speed cameras, livestock, wind/rain thresholds.
6. **Couple comfort**: keep first day light after flight/airport pickup; protect food, bathroom, photo, and hotel arrival windows.

## Verification checklist

Before sending a self-drive daily plan, verify it contains:

- [ ] exact date and current-day context;
- [ ] arrival/pickup time derived from screenshots or stated data;
- [ ] copyable 高德/百度 route string;
- [ ] normal and downgrade versions;
- [ ] latest safe departure/arrival threshold;
- [ ] warning against ambiguous scenic-spot navigation when applicable;
- [ ] what screenshot/pin the user should send if a navigation point is uncertain.
