# Personal Travel Copilot — Open-source workflow absorption SSOT

Checked: 2026-07-11
Scope: local/reversible workflow coverage for Hermes Pocket Travel. This document does not authorize scraping protected platforms, external writes, booking, payment, credential entry, or production API claims.

## Spec brief

Goal: cover the reusable engineering workflows proven by maintained open-source projects while keeping travel facts evidence-bound and keeping provider authority outside local parsers.

Non-goals:
- no 12306 login, ticket grabbing, CAPTCHA handling, or private endpoints;
- no Dianping/Meituan/Xiaohongshu cookie injection, signature reversal, or bulk content crawling;
- no claim that OCR, HTML extraction, LLM extraction, or open-source code grants upstream data rights;
- no automatic booking, payment, cancellation, permit filing, or external dispatch;
- no replacement of China production routing/weather with OSM-only sources.

Invariants:
- Hermes/Gateway remains canonical for current facts and external side effects;
- mobile/local artifacts are projections, evidence, drafts, and handoff packets;
- every extracted claim retains artifact identity, hash, observed time, locator, confidence, authority tier, and human-confirmation flag;
- blocked/login/CAPTCHA/private-interface inputs fail closed;
- raw screenshots, coordinates, order numbers, and personal data do not enter durable global memory.

## Pinned source map

| Capability | Canonical project | License boundary | Absorbed workflow | Runtime dependency decision |
|---|---|---|---|---|
| local itinerary extraction | https://github.com/KDE/kitinerary | multi-license; core commonly LGPL, verify per file | user-authorized mail/PDF/barcode/calendar -> normalized reservation candidates -> human confirmation | adapter contract now; native library integration later after isolated license/build spike |
| itinerary/Trip model | https://github.com/itskovacs/trip | MIT | Trip/Day/Item/Place/provider adapters/MCP-shaped operations | own TypeScript TripState remains SSOT; no upstream runtime required |
| public-page rendering | https://github.com/microsoft/playwright | Apache-2.0 | render public official page, retain final URL, screenshot/HTML metadata | existing Hermes browser/Playwright surface; no new dependency |
| crawl orchestration | https://github.com/apify/crawlee-python | Apache-2.0 | allowlisted queue, retry, dedupe, rate limit, HTTP/browser split | contract covered; runtime install deferred until a real multi-page official source requires it |
| article extraction | https://github.com/adbar/trafilatura | Apache-2.0 | raw artifact -> extracted text while preserving original artifact | adapter contract covered; optional runtime later |
| screenshot OCR | https://github.com/PaddlePaddle/PaddleOCR | Apache-2.0 | image -> text spans with bounding boxes/confidence -> deterministic field validation -> human gate | provider-neutral OCR artifact contract now; Paddle runtime isolated later |
| evidence archive | https://github.com/webrecorder/browsertrix-crawler | AGPL-3.0 | high-value official page -> WARC/WACZ, redaction and access control | not in MVP; optional isolated service after AGPL/privacy review |
| email MIME | https://github.com/SpamScope/mail-parser | Apache-2.0 | user-authorized EML -> body/attachments without webmail scraping | standard-library-first adapter later |
| calendar | https://github.com/collective/icalendar | BSD-family; verify package metadata | ICS -> timezone-preserving reservation candidates | adapter later |
| flight/hotel client | https://github.com/amadeus4dev/amadeus-python and amadeus-node | MIT code; API contract separate | official API client -> provider envelope -> TripState candidate | blocked on real credentials/China coverage smoke |
| static airport data | https://github.com/davidmegginson/ourairports-data | public-domain style declaration | versioned airport reference dataset | optional local dataset; not real-time authority |
| offline/overseas routing | https://github.com/graphhopper/graphhopper | Apache-2.0 | provider-neutral route/matrix/isochrone adapter | fallback only; China main route remains Amap/Baidu |

## Owned capability workflow

```text
user-authorized artifact OR allowlisted public official URL OR official API response
  -> intake policy gate
  -> immutable source artifact (hash + observedAt + media type + source URL)
  -> extractor adapter (browser/article/OCR/email/calendar/API)
  -> evidence spans (locator + confidence + observed/parsed/inferred)
  -> deterministic normalization and negative validation
  -> TripState candidate (never canonical merely because parsing succeeded)
  -> human/official readback gate where inventory, safety, transaction, permit, or identity matters
  -> live card projection
```

## Gate outcomes

- pass: public/authorized artifact, hash and locator present, extractor succeeded, field passes deterministic checks, authority is sufficient for advisory use.
- warn: extraction succeeded but source is secondary, stale, incomplete, or field needs official readback.
- fail: contradictory or safety-negative evidence; route/action must use fallback.
- blocked: login/CAPTCHA/paywall/private endpoint, missing source artifact/hash/locator, low OCR confidence, or transaction/permit requiring human action.

## First local implementation slice

`packages/offline-core/src/travelEvidenceWorkflow.ts` owns provider-neutral contracts for:
- source artifacts;
- extraction runs;
- located evidence spans;
- TripState candidate promotion decisions;
- fail-closed policy evaluation;
- source-bound evidence ledger entries.

The slice deliberately does not install upstream projects. It makes their transferable workflow consumable by later adapters without granting network or domain authority.

## Acceptance

1. Valid public official-page extraction with hash and locator can become advisory evidence, not confirmed inventory.
2. OCR below threshold remains blocked and requests human confirmation.
3. Login/CAPTCHA/private-interface flags block promotion.
4. Transactional and permit claims always require human/official readback.
5. Inferred values cannot become confirmed facts.
6. Tests cover positive and negative cases.
7. Remaining provider integrations are documented with exact credential, minimal smoke, and boundary requirements.
