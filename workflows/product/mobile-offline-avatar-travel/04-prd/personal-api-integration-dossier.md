# Personal Travel API integration dossier

Checked: 2026-07-11
Purpose: exact user-assistance packet for real provider access after local open-source workflow coverage.

## P0 — Amap Web Service

Official evidence:
- https://lbs.amap.com/api/webservice/summary — Web Service API is open to all users; application Key required.
- https://lbs.amap.com/api/webservice/guide/create-project/get-key
- https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch
- https://lbs.amap.com/api/webservice/guide/api/newroute

User action:
1. Register/verify an Amap developer account.
2. Create a dedicated application for Hermes Pocket Travel.
3. Create a Web Service Key; restrict scope/quota where available.
4. Put the secret in the local secret store/environment; do not paste it into chat or repository.

Needed configuration names (proposed):
- `AMAP_WEB_SERVICE_KEY`
- optional endpoint override only for tests: `AMAP_WEB_SERVICE_BASE_URL`

Minimum real smoke required before adoption:
- geocode one Chinese hotel;
- POI search one known attraction and one parking entrance;
- driving route between two verified Xinjiang points;
- assert coordinates are GCJ-02/provider-labelled, response timestamp retained, failure/limit errors visible.

Does not prove: live road opening, scenic-area vehicle permission, ticket inventory, food quality.

## P0 — QWeather

Official evidence:
- https://dev.qweather.com/docs/api/
- https://dev.qweather.com/docs/configuration/project-and-key/

User action:
1. Create a QWeather project.
2. Prefer JWT credentials per official guidance; API Key is acceptable for a bounded first smoke.
3. Set quota/billing alerts; published basic-weather pricing showed the first 50,000 monthly calls at zero cost when checked, but account price group must be read back.

Needed configuration names (proposed):
- JWT path: `QWEATHER_PROJECT_ID`, `QWEATHER_KEY_ID`, `QWEATHER_PRIVATE_KEY_PATH`
- or bounded API-key path: `QWEATHER_API_KEY`
- `QWEATHER_API_HOST` from the account/project configuration

Minimum real smoke:
- hourly forecast for an exact Xinjiang coordinate;
- warning lookup;
- wind/visibility fields;
- sunrise/sunset for the same coordinate/date;
- TTL and provider timestamp retained; malformed/expired credential fails closed.

Does not prove: mountain-road opening, local scenic operation, drone permission.

## P1 experimental — Amadeus Self-Service

Official evidence:
- https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/quick-start/
- https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/faq/
- SDK: https://github.com/amadeus4dev/amadeus-python or https://github.com/amadeus4dev/amadeus-node

Access boundary:
- personal self-service test registration is available;
- production requires contract and billing information;
- SDK license does not grant inventory, ticketing, payment, refund, or China coverage.

Proposed secrets:
- `AMADEUS_CLIENT_ID`
- `AMADEUS_CLIENT_SECRET`
- `AMADEUS_ENV=test|production`

Minimum smoke:
- search representative China domestic and international flights;
- compare returned schedules against an airline/airport source;
- test no-result, rate-limit, stale quote, and auth failure;
- keep search, price confirmation, booking, ticketing, cancellation/refund as separate capabilities.

Adoption rule: advisory search only until China coverage/freshness evidence passes. No booking/payment in personal phase one.

## P1 optional — Baidu Maps fallback

Official developer access exists with an AK, POI/geocoding/routing/weather surfaces. Use only if Amap coverage or reliability evidence creates a real fallback need. Do not mix BD-09 and GCJ-02 silently.

Proposed secret: `BAIDU_MAP_AK`.

## Not personal-direct today

- Booking.com Demand API: Managed Affiliate Partner + contract + account-manager access required: https://developers.booking.com/demand/docs/getting-started/prerequisites
- Ctrip/Trip.com/Fliggy ticket/hotel inventory: partner/platform onboarding; no verified anonymous personal production key path.
- VariFlight formal data API: trial/business inquiry, not verified self-service production API.
- 12306: no verified public developer API for personal integration.
- Dianping/Meituan consumer POI/UGC: documented cooperation credentials, authorized cities/fields and offline approval; no verified nationwide personal self-service access.
- Xiaohongshu general travel-note search: no verified ordinary-developer API.
- UOM real-time airspace data: official service exists, but no verified ordinary-developer public API.

Fallback for these surfaces:
- user-authorized screenshot/email/ICS/share-link intake;
- allowlisted official public pages;
- local parsing and OCR;
- explicit official-app/human confirmation for inventory, payment, cancellation, permits, and account data.

## Secret-handling gate

The user enters secrets locally. The agent may verify variable presence and issue a minimal redacted request, but must never print, persist in project docs, or send credentials. Provider responses used as evidence must be redacted for personal data and retain request class, timestamp, endpoint class, status, and content hash.
