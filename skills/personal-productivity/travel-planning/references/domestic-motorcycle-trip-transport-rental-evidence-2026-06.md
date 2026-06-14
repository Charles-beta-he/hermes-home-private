# Domestic motorcycle trip transport + rental evidence pattern — 2026-06

## Context

Session-derived pattern from planning a Dragon Boat Festival trip from Hangzhou toward Hailar / Arxan with a hard constraint of **departing on the evening of the 16th** and a preference for **motorcycle travel, grassland/forest scenery, weather-aware routing, and not turning the trip into a forced march**.

The important learning was not a single route; it was the evidence chain for deciding whether a route is actually executable when flights, trains, motorcycle rental, and weather all interact.

## Transport evidence chain

When the user proposes that a flight "should only be about two hours" or suggests air + rail transfer, do not answer from intuition. Probe the actual chain:

1. **Direct flight to target hub**
   - Check whether the hard departure window exists, not only whether the city pair exists.
   - For evening-departure constraints, separate:
     - evening departure;
     - same-day arrival;
     - next-day arrival;
     - total duration and transfer pain.

2. **Nearby flight hub + onward flight**
   - For Hailar / Arxan style destinations, probe major feasible transfer hubs such as Hohhot, Harbin, Qiqihar, Daqing, Changchun, Shenyang, Beijing, and Ulanhot.
   - Compare the whole chain, not one leg.

3. **Nearby flight hub + overnight train**
   - Query 12306 for the onward rail segment when public booking pages are insufficient.
   - Use an opener with cookies and `leftTicket/init` first; 12306 may redirect to error pages without session cookies.
   - Example station-code source: `https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`.
   - Example query shape: `/otn/leftTicket/query?leftTicketDTO.train_date=YYYY-MM-DD&leftTicketDTO.from_station=HBB&leftTicketDTO.to_station=HRX&purpose_codes=ADULT`.
   - Validate not just existence but the connection buffer from airport arrival to train departure.

4. **Reject theoretically possible but operationally brittle chains**
   - If landing time leaves no realistic airport-to-station buffer, mark it as "theoretical only" even if both legs exist.
   - Do not recommend chains that depend on no flight delay, instant baggage, no traffic, and a last-minute station transfer.

## Example findings to reuse as a pattern, not as permanent inventory

In this session, Hailar complete-north-line planning changed after checking actual evidence:

- Hangzhou -> Hailar had no useful evening-departure result for the 16th.
- Hangzhou -> Hohhot had viable evening flights, and Hohhot -> Hailar had a next-morning flight, making air-air transfer the cleanest 16-evening departure chain.
- Harbin -> Hailar had attractive overnight trains, but Hangzhou evening flights landed too late to safely catch them.
- Qiqihar / Daqing -> Hailar trains were plausible, but no matching evening flight from Hangzhou was found in the probed public source.
- Hohhot -> Hailar by train was too slow for the trip window.

The durable lesson: **air-rail is only better if both the rail timing and the airport-to-station transfer buffer are real.**

## Motorcycle rental evidence tiers

For remote domestic motorcycle trips, public search often finds repair shops, clubs, brand dealers, and social-media accounts rather than bookable rental inventory. Classify evidence instead of overclaiming:

1. **Confirmed rental inventory**
   - Exact model/year/version, real current video, written terms, insurance, rescue/towing, route permission, pickup/return windows.

2. **Motorcycle club / local rider resource**
   - Good lead for rental referrals, route advice, repairs, and rescue, but not confirmed rental until contacted.

3. **Brand dealer / repair shop**
   - Good lead for referrals and mechanical support; not rental evidence by itself.

4. **Historical company record / generic car rental**
   - Useful background only; do not treat as current motorcycle availability.

## Hailar vs Arxan rental lesson

For this class of trip:

- If **motorcycle travel is mandatory**, prefer the larger hub with motorcycle ecosystem evidence as the pickup base, even if the route starts south afterward.
- If **comfort / certainty / evening departure** is more important than motorcycle purity, a smaller scenic hub may still be better for car rental or self-drive.
- Do not assume Arxan-style scenic hubs have motorcycle rentals just because they have car rental or repair shops.
- Do not assume a desired model such as a specific ADV is available without real current vehicle proof.

## Inquiry script

Send this to clubs, dealers, repair shops, and rental leads:

```text
你好，我们两个人计划 6/17-6/21 从海拉尔/阿尔山方向摩旅，路线大概是海拉尔—新巴尔虎—阿尔山—海拉尔，天气好可能补莫日格勒河/额尔古纳。想确认：
1. 是否有可租摩托？具体车型、年份、排量？
2. 是否允许双人骑行？
3. 是否允许跑新巴尔虎、阿尔山、莫日格勒河/额尔古纳方向？
4. 租金、押金、日里程限制？
5. 保险包含什么？摔车、倒车、爆胎、拖车、救援怎么算？
6. 是否有三箱/尾箱、手机支架、USB、头盔、雨衣？
7. 能否发实车视频：轮胎、刹车、链条/传动、灯光、里程表、外观旧伤？
8. 6/17 上午或中午能否取车？6/21 能否还车？
9. 如果天气差临时缩短/改汽车，退改怎么算？
```

## Fail-closed rules

- No real current vehicle video -> do not plan around that lead.
- Insurance/damage/towing rules unclear -> do not use for long-distance two-up riding.
- Route permission unclear -> do not run remote grassland / border / forest legs.
- Only scooter/e-bike/small displacement city bike -> local loops only.
- No rescue or repair fallback -> shorten route or switch to car.

## Route planning implication

When motorcycle pickup is uncertain:

- Keep a car/self-drive version of the same scenic topology.
- If Hailar has better motorcycle leads but Arxan is the scenic start, use Hailar pickup + southbound route rather than assuming Arxan pickup.
- If Arxan pickup is unconfirmed, treat Arxan-start as a car-rental/self-drive plan until proven otherwise.
