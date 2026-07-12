# Open-source workflow absorption for evidence-bound domain systems

## Applicability

Use when open-source repositories can cover engineering workflow layers—capture, parsing, OCR, scheduling, normalization, state projection, archival—but cannot grant authority to the upstream data or transaction.

Typical domains: travel, finance, health, compliance, logistics, ticketing, regulated or platform-owned data.

Anti-conditions:
- do not use this pattern to justify private-interface scraping, CAPTCHA bypass, Cookie/session custody, or login automation;
- do not infer API/data rights from an MIT/Apache/GPL code license;
- do not claim runtime integration merely because adapter contracts or architecture documents exist;
- do not install a heavy upstream runtime until a real source artifact and acceptance test justify it.

## Reusable absorption loop

```text
source/repo evidence
  -> capability + license/data-rights split
  -> transferable workflow extraction
  -> provider-neutral owned contract
  -> negative gates and provenance invariants
  -> focused tests
  -> consumer/source-mode regression tests
  -> project-level test/build/gate
  -> remaining real-API dossier
```

### 1. Split code rights from data authority

For every repository record separately:

- code license and per-file exceptions;
- upstream API terms and credential requirements;
- data redistribution rights;
- source authority and freshness;
- whether results can be advisory, confirmed, or transaction-authoritative;
- whether integration is library, isolated service, reference-only, or rejected.

A permissive SDK license does not prove that inventory, prices, comments, orders, permits, or private platform data may be retrieved or redistributed.

### 2. Absorb workflow before dependency

Prefer an owned provider-neutral contract before installing upstream code:

```text
Authorized/public source artifact
  -> immutable identity + SHA-256 + observedAt + media type + source reference
  -> extractor run identity/version/status
  -> located evidence spans: quote + DOM/bbox/page locator + confidence
  -> authority tier: official | user-authorized | open-reference | secondary
  -> derivation: observed | parsed | inferred
  -> normalized domain candidate
  -> advisory | needs-confirmation | blocked
```

This allows Playwright, Trafilatura, PaddleOCR, KItinerary, mail/calendar parsers, WARC tools, or official SDKs to remain replaceable adapters instead of becoming domain truth.

### 3. Fail closed

Block promotion when any of these is present:

- login required, CAPTCHA/antibot, paywall, or private interface;
- missing source reference, observed time, content hash, or field locator;
- extractor failure/empty result;
- artifact/extraction/span provenance mismatch;
- OCR confidence below the declared threshold;
- inferred result presented as observed fact.

Require human/official readback for:

- inventory and availability;
- payment, booking, cancellation, refund, or account changes;
- permits and regulated actions;
- safety-critical route/road/weather decisions;
- secondary/open-reference evidence.

### 4. Test negative requirements explicitly

Minimum tests:

1. valid official/public artifact becomes advisory only;
2. login/CAPTCHA/private-interface input is blocked even if parsing says success;
3. low-confidence OCR is blocked and retains bbox/page locator requirements;
4. inventory/transaction/permit/safety candidates require confirmation;
5. inferred/open-reference values cannot become authoritative facts;
6. malformed hash/source/provenance is rejected.

### 5. Verify consumers after adding exports

Pitfall: a TypeScript package may build successfully with NodeNext imports such as `./newModule.js`, while a Jest/Babel consumer executes package source directly and cannot resolve the new specifier.

When adding a public export:

- run package tests and `tsc`;
- inspect consumers that alias the package to `src/index.ts`;
- if a Jest `moduleNameMapper` maps package-relative `.js` specifiers to `.ts`, add the new module mapping there;
- run the consumer-native suite, not only workspace Vitest;
- then run the project production/readiness gate.

Capture the durable lesson as “verify source-mode consumers and maintain their mapper,” not as a claim that Jest or the package is broken.

## Official provider adapter slice

After the provider-neutral evidence contract is green, the next safe slice is a read-only official-provider adapter with an injected fetch boundary. Use strict RED→GREEN tests before any credential-backed smoke.

Adapter rules:

- accept credentials through constructor/config only; never read or persist them inside the domain package;
- send API keys in the provider-recommended header when available; if a provider requires a query parameter, redact it from every evidence URL, log, error, fixture, and receipt;
- retain provider name, endpoint class, provider update time, local observation time, TTL, coordinate system, and normalized units;
- distinguish HTTP failure, provider-level error code, missing/incomplete schema, stale data, and valid response;
- return blocked evidence for HTTP/provider/schema failures instead of throwing away the evidence trail or fabricating a default;
- keep route/weather success advisory: route computation does not prove road opening; weather success does not prove traffic, ticket inventory, driver fitness, or permits;
- add source-mode consumer mappings whenever a new NodeNext `./module.js` export is consumed directly from TypeScript source.

Minimum tests for a secret-bearing read-only adapter:

1. the real request path receives the credential, but the returned evidence URL and claim do not contain it;
2. valid provider data is normalized with explicit coordinate system/units, timestamp, and TTL;
3. HTTP failure blocks;
4. provider error code blocks;
5. incomplete response schema blocks;
6. missing credentials fail before any request;
7. package build, source-mode/native consumer suite, workspace tests/build, and readiness gate remain green.

Before real smoke, inspect only whether required environment-variable names are configured—never print values. If missing, stop at the credential gate and report exact variable names. If configured, run the smallest redacted read-only smoke and retain request class/status/hash rather than raw secrets or personal payloads.

## Real-API dossier shape

After local/open-source workflow coverage, classify remaining providers:

- P0 required official API;
- P1 experimental or fallback;
- partner/business-only;
- no verified personal API, with compliant fallback.

For each real API record:

- official documentation URLs;
- user-side registration steps;
- environment variable names only, never values;
- minimum redacted smoke cases;
- coordinate/timezone/freshness/TTL rules;
- rate-limit and auth-failure behavior;
- claims the API still cannot prove;
- explicit separation between search, quote confirmation, booking, payment, cancellation, and refund.

## Closure evidence

Do not close on docs alone. Require fresh evidence for:

- owned contract code;
- negative and positive tests;
- package build;
- source-mode/native consumer regression if applicable;
- project-level tests/build/readiness gate;
- SSOT progress/readback update;
- explicit statement of credentials, runtime adapters, provider smokes, deploy/push, and human gates that remain unproven.
