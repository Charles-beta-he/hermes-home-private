# Local Food / Nightlife Recommendations

Extracted from `/Users/charles/.hermes/skills/personal-productivity/travel-planning/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Local food / nightlife recommendations

Use this when the user is already on the road and asks for places to eat, drink, or wander tonight.
## Local food / nightlife recommendations

Use this when the user is already on the road and asks for places to eat, drink, or wander tonight.

1. Start from live context: location pin, current local time, weather, walking/taxi radius, couple/family/solo fit, fatigue, and tomorrow's travel constraints. If the user is actively traveling, first make the operational call directly ("go now", "do not detour", "eat here first") instead of teaching generic decision rules.
2. Check public evidence before recommending: map POIs/ratings/opening hours, official/open web snippets, social/UGC evidence when accessible, and known local food categories. If search is blocked or map data is sparse, state the boundary and downgrade to a field-executable scouting plan.
3. For late arrivals, prioritize **can still eat** over generic quality: current time, likely kitchen close, distance from hotel, phone availability, category closing pattern (烧烤/烤肉 > 火锅 > 铁锅炖/蒙餐正餐), and whether the meal still leaves rest time. Call the shop when possible; otherwise give a shortest-first fallback chain.
4. Always provide a click-ready navigation target for travel execution, preferably 高德 URI with coordinates and POI name, plus a plain search string fallback. For China travel, do not leave the user to retype vague place names when they are driving.
5. Do not fabricate Dianping/Xiaohongshu rankings or real-time open status. Separate:
   - verified POI/rating/opening/phone evidence;
   - uncertain or unavailable opening-hour evidence;
   - local specialty/category knowledge;
   - on-site heuristics such as hot food, visible turnover, local crowd, clear pricing, and short queue.
6. For late-night street-food areas, recommend an ordered crawl instead of a long restaurant list: walk the street once, pick 1 hot/light starter, 1 grill/main, 1 local sweet/dairy/drink, then stop before overloading digestion.
7. For couples, protect comfort and mood: avoid long detours, heavy/greasy overload, uncertain long queues, unsafe dark streets, or equipment-heavy plans; offer a fallback to a nearby mall/hotel-area cafe/bar if the street closes.
8. Include practical ordering quantities for two people and quick avoid-pitfalls: ask price before weighed/sliced foods, avoid cold/low-turnover items, keep tomorrow's travel/drive in mind, and avoid drone use in dense religious/old-street areas.
