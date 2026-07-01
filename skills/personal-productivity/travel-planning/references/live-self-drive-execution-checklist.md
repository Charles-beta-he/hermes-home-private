# Live self-drive execution checklist

Applicability: use during an active self-drive trip when the user sends location pins, asks whether to go/eat/continue, or needs immediate navigation decisions. This is class-level guidance derived from a live travel failure mode, not a record of one itinerary.

Anti-conditions: do not treat named places, prices, opening hours, or coordinates from any prior trip as reusable facts. Recheck live sources or ask for app screenshots when making a concrete recommendation.

## Principle

In live travel, the assistant is a co-pilot, not a brochure. Start with the direct operational call, then give evidence and fallback.

Bad: “You can search for restaurants and check whether they are open.”
Good: “Go to this shop first; it is closest and most likely still serving. If closed, use this second link.”

## Pre-leg gates

Before sending the user to the next point, actively check or flag:

1. Human state: hungry, tired, restroom, cold/wet, relationship mood.
2. Timing: current local time, sunset/darkness, latest safe arrival, whether the plan leaves dinner/rest time.
3. Route: precise navigation point, parking/entrance, avoid unpaved/grass/shortcut roads.
4. Operated attraction: admission/ticket/appointment, current open status, latest entry, whether on-site purchase is possible.
5. Food: current time vs kitchen-close risk, phone number, distance from lodging, late-night category fit.
6. Weather: rain, wind/gusts, visibility, temperature drop.
7. Recovery: hotel/lodging return link and downgrade route.

## Output shape for live decisions

1. **Decision:** go / do not go / eat here / return now.
2. **Clickable action:** 高德 URI or exact map-search string.
3. **Evidence:** time, distance, weather, map/source evidence, and what could not be verified.
4. **Fallback:** one nearby alternative or abort route.
5. **Hard stop:** latest depart/return time or condition that cancels the plan.

## Late-night food heuristic

When exact opening hours cannot be verified, say so and rank by probability of still serving:

1. 烧烤 / 烤肉 / 夜宵店
2. 火锅
3. 便利店 / 酒店附近简餐
4. 铁锅炖 / 蒙餐正餐 / 景区餐饮

Prefer shops with phone numbers and short drives. Encourage a quick call only as a verification step, not as a replacement for giving a recommendation.
