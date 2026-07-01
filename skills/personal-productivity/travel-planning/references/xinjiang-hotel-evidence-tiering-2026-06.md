# Xinjiang hotel recommendation evidence tiering (2026-06)

Applicability: domestic China road-trip hotel planning, especially Xinjiang/Ili routes with a mix of airport hotels, city-chain hotels, scenic-area guesthouses, and high-altitude towns such as Qiongkushitai, Nalati, Bayinbuluk, Dushanzi/Kuitun.

Anti-conditions: do not reuse named hotels, availability, prices, ratings, or cancellation policies without rechecking current OTA/app evidence for the exact dates and room count.

## Lesson

Do not present hotel names and OTA search keywords as if they are evidence-confirmed recommendations. Separate every lodging suggestion into evidence tiers:

1. **Evidence-confirmed candidate** — a current source was actually read (OTA page/screenshot/app page/official listing/map listing) and provides enough detail to cite: hotel name, date context if available, rating/reviews or location, and relevant tags such as cancellation/parking. Still require final OTA confirmation for room count and price.
2. **Brand/search target** — a reasonable chain/brand or city search target based on route logic (e.g. Atour/JI/Vienna/Hampton in a city) but not yet verified for existence, availability, price, or exact location. Label it as a search target, not a recommended confirmed hotel.
3. **Filter keyword** — scenic/high-risk lodging search phrasing, not a hotel name (e.g. “Qiongkushitai scenic guesthouse”, “Bayinbuluk hot water heating hotel”). Use it to request screenshots/details; never call it a hotel recommendation.

## Workflow

1. Start with route function per night: transfer/rest, scenic experience, double-insurance, high-altitude recovery, or pre-flight anchor.
2. For each night, output lodging options under explicit evidence headers:
   - **Confirmed from evidence**
   - **Search targets to verify**
   - **Keywords only / need screenshots**
3. For scenic guesthouses and high-altitude towns, require detail screenshots before naming a final pick:
   - facilities: hot water, heating/electric blanket/thick quilts;
   - parking or shuttle/transfer instructions;
   - dinner availability and cutoff time;
   - recent negative reviews;
   - cancellation deadline;
   - exact map position and drive-in/road condition notes.
4. If public web evidence is blocked or sparse, say so directly and ask for OTA/native-app screenshots instead of inventing hotel names.
5. When revising a plan after user correction, explicitly downgrade prior unverified names to “search targets” and restate which candidates had actual evidence.

## Output pattern

For each night:

- **Role**: what this night must accomplish.
- **Evidence-confirmed candidates**: only names backed by read evidence/screenshots, with source and caveat.
- **Search targets**: chain/brand/city targets to search.
- **Experience/guesthouse filters**: keywords and mandatory checks.
- **Do not book if**: parking unclear, no late check-in, no heating/hot water, recent concentrated bad reviews, or cancellation policy unsafe.

## User-facing correction trigger

If the user asks “why can’t you give hotel names?” or “do these have evidence?”, immediately clarify tiers and do not continue listing unverified names as recommendations.
