# Hulunbuir live self-drive gate checks (2026-06)

Applicability: use as a scoped example for mainland China same-day self-drive execution when a user is already en route, sharing pins, and needs immediate decisions around attractions, meals, and hotels.

Anti-conditions:
- Do not reuse the named hotel, coordinates, prices, or attraction status for future trips without rechecking live evidence.
- Do not treat this as a global rule for all countries or all map providers.
- Do not store one session's route progress as durable state.

## Session learning

The user corrected the assistant during a live couples self-drive day:

- The assistant gave process advice when the user wanted direct confirmation and a clickable next destination.
- The assistant routed toward an attraction without foregrounding ticket / reservation / last-entry gates, causing the user to arrive unable to enter.
- The user needed a hotel destination from a previously recommended property and expected exact navigation content, not a generic search instruction.

## Reusable response pattern

When the user is already moving:

1. Lead with the action: “现在去酒店 / 现在别进景区 / 直接点这个导航”。
2. Provide a clickable local-map navigation link plus fallback POI text.
3. State the evidence in 2–4 bullets only: source, POI name, address, coordinates, time/sunset/weather if relevant.
4. If an attraction is involved, verify before routing:
   - opening hours;
   - last entry;
   - ticket/reservation requirement;
   - on-site purchase availability;
   - parking/gate name.
5. If current ticket evidence is unavailable, ask for a screenshot from the user's active booking/map app and give a conservative fallback route.
6. At dusk or after a failed attraction gate, protect comfort: hotel/city first, scenic alternates tomorrow.

## Concrete evidence from the session

Hotel POI rechecked through 360 map API/search evidence during the session:

- Name: 额尔古纳万庭深呼吸酒店 / Wanting Deep Breath Hotel
- User-provided full name: 额尔古纳万庭深呼吸酒店(额尔古纳湿地景区店)
- Address evidence: 呼伦贝尔市额尔古纳市外环路136号
- Phone evidence: +86-470-6923777
- Coordinate evidence from map API: lon 120.171307, lat 50.223245
- Rating/review evidence from 360 map: 4.8 / 882 reviews
- Booking source evidence: Ctrip hotel id 5448293 was surfaced in the map API payload

These are historical evidence only. Recheck live before future use.
