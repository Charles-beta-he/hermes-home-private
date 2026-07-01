# Xinjiang/Ili self-drive: low-touch hotel booking + rental SUV selection (2026-06)

Applicability: scenery-first China domestic self-drive trips where the user has fixed flights, local rental car pickup/return, 4 travelers with luggage, and peak-season lodging constraints. This note is scoped to Ili/Sayram/Nalati/Duku-style routes, but the patterns generalize to long-distance scenic self-drive.

Anti-conditions: do not treat named hotels, prices, or OTA inventory as durable facts. Recheck current inventory in Ctrip/Meituan/Qunar/Fliggy/official app. Do not override live weather, road closures, or user-confirmed bookings.

## Confirmed-flight anchors

When the user shares a flight screenshot, parse it into hard schedule anchors and patch only the affected windows:

- late arrival night: require airport/near-pickup lodging, 24-hour front desk, confirmed late check-in;
- first rental day: do not over-optimize early pickup after a post-midnight arrival; protect sleep before a long transfer;
- final day: back-solve car return and airport buffer from departure time;
- penultimate night: prioritize a lodging zone that makes car return/flight reliable, not scenic upside.

For this session pattern:

- 00:40 arrival -> assume hotel arrival 01:30–02:30; do not pick up car at night; 10:30–11:00 pickup is safer.
- 18:40 departure -> aim to complete car return / reach airport area by ~15:30; penultimate night should be 独山子/奎屯/乌苏 rather than remaining in 那拉提/巴音布鲁克.

## Rental SUV selection for 4-person scenic long drives

For 4 travelers + multi-day luggage on long paved scenic routes, prioritize cabin/boot space and long-distance comfort over hard-core off-road image.

Recommended order when budget is not the constraint:

1. mid/large SUV: 大众揽境 / 途昂 / 揽巡 or equivalent;
2. other roomy 6/7-seat SUVs: 英菲尼迪 QX60 / 星途揽月 / similar;
3. balanced compact/midsize SUVs: 哈弗大狗 / H6 / CS75 PLUS / 瑞虎8 / 捷途X70 / 传祺GS4;
4. hard-core SUVs such as 坦克300 / BJ40 only when large SUVs are unavailable or their insurance/condition is worse.

Why: Xinjiang Ili/Nalati/Duku main routes are primarily paved/mature roads. The major risks are fatigue, weather, wind chill, road controls, luggage friction, and return logistics. A larger comfortable SUV often beats a hard-core off-roader for couples/4-person long trips.

Always confirm before booking:

- exact model vs “same group” random assignment;
- fuel car vs EV/hybrid and refueling/charging practicality;
- luggage fit with third row folded;
- route permission for Ili, Nalati, Bayinbuluk, Duku;
- unlimited mileage;
- roadside rescue coverage area;
- tires/glass/undercarriage insurance;
- deposit/violation deposit/refund timing;
- vehicle age/mileage/tire condition;
- ability to switch to an equal-or-larger vehicle if condition is poor.

## Low-touch hotel booking mode

When the user wants reduced manual intervention, stop asking for page-by-page screenshots. Produce a nightly booking target list with:

- preferred zone;
- acceptable hotel types/brands;
- hard conditions;
- fallback zone;
- cancel/double-insurance rule.

Use OTA apps/sites (Ctrip, Meituan/Dianping, Qunar, Tongcheng/eLong, Fliggy) for inventory, pricing, room type, cancellation, and review evidence. Use Gaode/Baidu primarily to verify location, drive time, parking access, highway/airport routing, and nearby food.

Only ask for screenshots when a bottleneck lodging is unclear, especially:

- remote village民宿 such as 琼库什台: parking/接驳, dinner, hot water, heating/electric blanket, road condition, recent bad reviews;
- high/cold overnight such as 巴音布鲁克: heat/hot water/bedding/late check-in;
- late-arrival airport hotel: 24-hour front desk / confirmed late check-in;
- final pre-flight night: parking, late arrival, highway/airport access.

## Lodging topology for Ili + Duku flight-in self-drive

For a route with fixed Urumqi flights and Duku return:

- D0 Urumqi: airport/near pickup, 24-hour front desk; no city-center tourism.
- D1 Bole/Sayram: default Bole city business hotel unless lake lodging is clearly good; protect sleep after late arrival.
- D2 Yining: parking + dinner access; do not pay for city sightseeing location if scenery is the objective.
- D3 Zhaosu: county hotel for early Xiata access.
- D4 Zhaosu/Tekes double insurance: stay Zhaosu if Xiata is deep/tiring; push Tekes if Xiata is short/early.
- D5 Qiongkushitai/Tekes/Xinyuan: only stay Qiongkushitai if hot water/heating/dinner/parking or transfer are verified; otherwise use Kalajun/Tekes/Xinyuan stable option.
- D6 Xinyuan/Nalati: practical base for Nalati.
- D7 Bayinbuluk vs Nalati/Xinyuan double insurance: push Bayinbuluk only if Nalati ends early, weather/body state are good, and lodging basics are acceptable.
- D8 Dushanzi/Kuitun/Usu: hard pre-flight return anchor; prioritize Dushanzi/Kuitun for next-day airport return.

## Output shape

For low-touch booking, return:

- “Book now” nights;
- “Double-insure” nights;
- “Fill later” nights;
- per-night hard filters;
- minimum questions to confirm in app/vendor chat;
- what to do if no suitable option exists.
