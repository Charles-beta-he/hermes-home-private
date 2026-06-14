# Domestic air + rail intermodal screening pattern — 2026-06

## Context

Session-derived pattern from planning a Dragon Boat Festival trip from Hangzhou to Hailar/Hulunbuir where the user challenged a flight-only assumption and asked to consider combined flight + train transfers.

Use this when a destination has poor direct late-flight access but nearby rail gateways may have overnight trains.

## Core lesson

Do not reject a destination only because the direct flight is inconvenient. For domestic China trips, explicitly test:

1. Fly from origin to a larger regional gateway in the evening.
2. Transfer to an overnight train toward the target city.
3. Arrive early enough to preserve the first travel day.

But also fail closed on transfer feasibility: a theoretically good overnight train is not usable if the arriving flight lands too late to reach the railway station with realistic buffer.

## Screening workflow

1. Identify candidate air gateways around the target.
   - For Hailar/Hulunbuir examples: Harbin, Qiqihar, Daqing, Changchun, Shenyang, Beijing, Hohhot, Ulanhot.
   - Prefer gateways with dense flights from the origin and overnight rail onward.

2. Probe evening flights from origin to each gateway.
   - Record landing airport, arrival time, price, and whether it is same-day or +1.
   - Do not treat scheduled arrival as station-ready time. Add realistic buffers for deplaning, luggage, ride-hailing, station security, and possible delay.

3. Probe railway onward legs using 12306 source data when possible.
   - Fetch station codes from `https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`.
   - Initialize a 12306 cookie/session before querying left tickets; otherwise queries may redirect to an error page.
   - Query: `https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=YYYY-MM-DD&leftTicketDTO.from_station=FROM&leftTicketDTO.to_station=TO&purpose_codes=ADULT`.
   - Parse train number, departure, arrival, duration, and seat/berth availability.

4. Evaluate transfer feasibility.
   - Same-city airport-to-station transfers still need buffer; airport arrival 20:40 rarely makes a 20:55 station departure.
   - Cross-city transfers, e.g. Harbin airport to Daqing rail station, are high risk unless there is a large buffer and reliable ground transport.
   - If a missed train destroys the trip, do not recommend it as primary.

5. Compare against flight-flight transfer.
   - If flight-flight gets the user to the target the next morning with less transfer risk, prefer it over air+rail even if rail looks elegant.

## Hailar example findings from this session

Useful rail gateways found:

- Harbin -> Hailar overnight trains can be good on paper:
  - K927 around 18:19/18:36 -> 05:09.
  - K7089 around 19:05 -> 05:35.
  - K2623 around 20:46/21:12 -> 06:37.
  - K7091 around 20:55 -> 06:15.
- Qiqihar -> Hailar also has useful night trains:
  - Around 22:09 -> 05:09.
  - Around 22:35 -> 05:35.
- Daqing -> Hailar also has useful night trains:
  - Around 20:20 -> 05:09.
  - Around 20:50 -> 05:35.
  - Around 22:38 -> 06:15.

But for Hangzhou 6/16 evening departure in this session:

- Hangzhou -> Harbin evening flights landed too late for realistic connection to the good Harbin -> Hailar night trains; even a 20:40 landing was not realistic for a 20:55 rail departure.
- Hangzhou -> Qiqihar / Daqing evening flight options were unavailable in the checked web source.
- Hohhot -> Hailar by train was too slow, around 28+ hours, so it was unsuitable.
- Therefore the best executable chain remained flight-flight: Hangzhou evening -> Hohhot, then Hohhot morning -> Hailar.

## Output guidance

When presenting intermodal options:

- Separate `theoretically possible` from `recommended`.
- Show the exact break point: flight landing time, station departure time, transfer buffer, and what happens if delayed.
- Prefer a slightly less clever chain that preserves sleep, first-day usability, and failure recovery.
- If the intermodal chain only works under zero-delay assumptions, label it as an extreme/non-recommended option, not a plan.
