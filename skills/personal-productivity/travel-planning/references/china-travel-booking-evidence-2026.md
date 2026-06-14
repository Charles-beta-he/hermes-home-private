# China travel booking evidence pattern — 2026 Dragon Boat travel session

Use this reference when planning China domestic trips where the user expects evidence-backed booking options, not generic itinerary prose.

## Durable pattern

1. Treat OTA web pages as unstable evidence.
   - Ctrip/Fliggy/Qunar/Meituan pages may block anonymous automation with JS/device/IP checks.
   - If a web page returns anti-bot output (for example Ctrip `whaleguard block`), do not present it as a final inability; switch channel.

2. Prefer a layered query strategy:
   - Official/public deterministic APIs where available, e.g. 12306 station/left-ticket APIs for rail.
   - Official or semi-official apps through the user's real macOS/iOS environment when web is blocked.
   - Screenshot/OCR extraction from the user's app results.
   - Public web/search snippets only as discovery leads, not booking truth.

3. For Apple Silicon Macs:
   - Check `platform.machine()` / `sw_vers`; `arm64` Macs can install many iPhone/iPad apps from the Mac App Store if the developer allows it.
   - App Store may show “iPhone 与 iPad App” results with “获取”; app usability is still per-app.
   - Stop for Apple ID password, SMS code, captcha, payment, face/touch verification, or secrets.

4. Rail automation:
   - 12306 station list is available at `https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`.
   - Left-ticket endpoint pattern:
     `https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=YYYY-MM-DD&leftTicketDTO.from_station=FROM&leftTicketDTO.to_station=TO&purpose_codes=ADULT`
   - Use realistic headers (`User-Agent`, `Referer`) and parse JSON. No login is needed for basic availability.
   - For long domestic leisure trips, direct train absence is still useful evidence; do not force rail if it consumes the holiday window.

5. Flight automation evidence tiers:
   - App screenshots / real logged-in app results > airline official app/site > OTA app > public web snippets > generic scrapers.
   - Google Flights scrapers and Kiwi/Amadeus/Skyscanner clients can help but may miss China domestic small-airport inventory and OTA-specific fares.
   - Never imply a fare is bookable unless it came from a current app/site result or official API with enough details.

## Output shape for booking research

Give only decision-useful output:

- `Option`: platform/source, route/date, departure/arrival, transfer city, duration, fare, luggage/seat/return-change notes if visible.
- `Fit`: whether it supports pickup/return/routing constraints.
- `Risk`: login needed, price volatility, overnight transfer, too-early return, anti-bot/unknown.
- `Next action`: book / hold / screenshot needed / call vendor / reject.

## Example station codes from this session

- 杭州东: `HGH`
- 杭州: `HZH`
- 海拉尔: `HRX`
- 阿尔山: `ART`
- 阿尔山北: `ARX`
- 乌兰浩特: `WWT`

These are examples only; always re-fetch station codes at runtime.