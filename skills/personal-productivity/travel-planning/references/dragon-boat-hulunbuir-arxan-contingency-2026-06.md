# Dragon Boat Festival Hulunbuir / Arxan contingency planning pattern — 2026-06

## Context

The user accepted a weather-aware Dragon Boat Festival travel plan built around **Hangzhou -> Hailar** with local motorcycle rental. The key refinement was that **Hailar north-line and Arxan south-line can be treated as two switchable branches under one fixed hub**, rather than as unrelated destinations.

This reference is a reusable pattern for short-holiday motorcycle / road trips with weather, holiday crowding, and rental uncertainty.

## Core topology

Use a fixed hub and fixed return deadline:

```text
D0: fly/train to hub, sleep at hub; no night riding.
D1-D3: choose A/B branch after weather + vehicle confirmation.
D4: return to hub, regardless of branch.
D5: local short loop / vehicle return / flight home.
```

For this case:

```text
Hub: Hailar
Fixed hotels: 6/16 Hailar, 6/20 Hailar
A branch: Hailar -> Ergun -> Enhe/Shiwei -> Heishantou -> Manzhouli -> Hailar
B branch: Hailar -> Arxan -> Arxan Forest Park -> Chaihe/Mo'a Highway -> Hailar
```

## Why this works

- Keeps flights and rental return stable.
- Avoids relying on one-way motorcycle return.
- Allows T-1 / D0 branch selection from real weather + actual bike condition.
- Preserves the scenic upside of the north line while giving a credible lower-risk south-line fallback.
- Forces D4 hub return so the final day is not exposed to long-distance weather, vehicle, or flight risk.

## Decision gates

Choose the higher-upside branch only if all are true:

- Forecast does not show continuous rain on the remote/scenic segment.
- Crosswind/gust risk is acceptable on open grassland / lake / border roads.
- A suitable vehicle is confirmed by real photos/video, contract, insurance, and rescue policy.
- Lodging at small-capacity overnight stops is available at acceptable price and cancellation terms.
- The final full day can return to the hub without a remote long ride.

Fallback branch triggers:

- Bike quality is uncertain or only a small/poorly equipped motorcycle is available.
- Rental shop restricts the target route.
- Remote-route weather worsens, especially wind + rain.
- Small-town lodging is overpriced or non-refundable.
- The trip objective shifts toward comfort/romance rather than scenic maximum.

## Lodging pattern

Book cancellable double packages, not one locked itinerary:

```text
Fixed: hub arrival night + hub pre-return night.
A package: remote/scenic north-line overnight stops.
B package: fallback south-line overnight stops.
Cancel one package after T-1 / D0 verification.
```

For Hailar / Arxan:

```text
Fixed: 6/16 Hailar, 6/20 Hailar.
A: 6/17 Enhe or Shiwei, 6/18 Heishantou, 6/19 Manzhouli.
B: 6/17 Arxan, 6/18 Arxan, 6/19 Arxan or Chaihe.
```

Hotel selection for motorcycle travel:

- Cancellable booking.
- Parking available and not down a rough side road.
- Hot water, heating/temperature control, and late check-in.
- Recent reviews for cleanliness, noise, parking, and hot water.
- Prefer town centers for food/resupply; avoid remote novelty stays when weather or arrival time is uncertain.

## Rental lead screening pattern

Public search/map results for motorcycle rental may be weak. Treat leads as inquiry targets, not confirmed inventory.

Evidence tiers:

1. Confirmed rental inventory with model/year, real vehicle video, written contract, insurance, rescue.
2. Motorcycle clubs likely connected to local riders and rental/rescue resources.
3. Motorcycle dealers/shops that may refer rental or repair/rescue resources.
4. General car-rental fallback.

Inquiry must ask:

- Exact model/year/version; functional fallback models.
- Whether two-up riding and the specific A/B routes are allowed.
- Daily mileage limits and restricted areas.
- Insurance, deposit, crash, tire, towing, breakdown, late-return liabilities.
- Rescue/towing coverage area.
- Luggage/helmet/rain gear/phone mount/USB.
- Real video/photos of tires, brakes, odometer, old damage, luggage mounts.
- Whether D0 evening inspection and D1 early pickup are possible.

Fail closed:

- No real vehicle video -> do not rely on the lead.
- No written insurance/damage rules -> reject or downgrade.
- Poor bike condition -> switch to shorter fallback or car rental.
- Small scooter only -> local loops only, not remote grassland touring.

## Weather + clothing index pattern

For grassland/forest motorcycle trips, do not summarize weather only as rain/no rain. Produce a riding index:

- Minimum/maximum temperature.
- Apparent temperature.
- Precipitation probability and expected amount.
- Wind speed and gusts, especially open roads and lakes.
- UV index.
- Sunrise/sunset and latest safe arrival time.

Clothing guidance should reflect riding wind chill:

- Base layer: quick-dry long/short sleeve.
- Mid layer: light fleece or warm layer for 8-15°C mornings/evenings.
- Outer: windproof riding jacket.
- Rain: split rain suit or waterproof shell, phone/packing waterproofing.
- Lower body: riding pants or sturdy long pants plus knee protection.
- Gloves: summer riding gloves; optional thin inner gloves.
- Sun: SPF50, sunglasses, neck gaiter, lip balm.

Rule of thumb: in grassland/forest routes, `10-15°C + wind` feels cold while riding even if the afternoon is warm.

## Holiday crowding handling

For Dragon Boat / short holidays:

- Enter early if possible; run core scenic roads before the official holiday peak.
- Avoid making popular paid scenic spots the main activity on the holiday day.
- Treat lodging and vehicle inventory as the tight resources; roads may be more tolerable than hotels/rentals.
- Early-enter + D4 hub return is preferable to starting the loop on the holiday day.

## Output pattern for future plans

Return an executable flow:

1. Final topology and A/B decision tree.
2. Day-by-day A branch and B branch.
3. Weather/clothing/riding-risk table.
4. Hotel package structure and booking order.
5. Rental inquiry script and fail-closed criteria.
6. T-1 / D0 / daily checklists.
7. Explicit downgrade path: shorter route or car rental.
