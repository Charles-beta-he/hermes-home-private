---
name: frontend-observability-governance
description: "Use when designing, implementing, auditing, or extending frontend monitoring/observability for web/PWA/mobile apps: error capture, browser telemetry SDK governance, sampling, noise reduction, PII sanitization, traceId propagation, contract-error detection, and monitoring CI gates."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [frontend, observability, telemetry, privacy, traceid, contract-errors, pwa]
    related_skills: [mobile-frontend-delivery, frontend-state-domain-correctness, test-driven-development, systematic-debugging]
---

# Frontend Observability Governance

## Scope and Applicability

Scope: frontend web/PWA/mobile-web applications, especially financial, account, identity, or other privacy-sensitive products where browser telemetry can leak sensitive user data or flood monitoring with expected business errors.

Applicability: use this skill when the task involves frontend error capture, browser monitoring SDKs, telemetry privacy, API trace correlation, runtime/unhandled errors, Web Vitals visibility, or monitoring guardrails.

Anti-conditions: do not use this skill for backend-only audit/logging, pure analytics/funnel design with no error/privacy governance, or one-off UI bugs that have no monitoring implications.

Falsifier: if the project already has a governed frontend observability layer with taxonomy, sanitization, trace propagation, SDK wrapper, and tests, use that project-specific runbook first and apply this skill only as an audit checklist.

## Overview

Frontend observability is not just installing a vendor SDK. The durable pattern is to build the governance layer before external delivery: classify errors, decide reportability and sampling, sanitize recursively, preserve correlation IDs, detect contract breaks at high-risk parsing boundaries, and add guardrail tests so future code cannot bypass the policy.

## Default Workflow

1. **Map existing surfaces first**
   - ErrorBoundary / route boundaries
   - API client/interceptors
   - global runtime handlers
   - network/offline banners/toasts
   - analytics/Web Vitals modules
   - current browser telemetry SDK init and whether credentials are configured only in deployment env
   - actual deployment platform from project profile/repo config before writing production closeout steps (for example Railway vs Vercel; build-time `VITE_*` env vs runtime server env; service names and target environment)

2. **Establish the objective model**
   - Success: render/API/runtime/contract errors are visible without leaking PII or flooding monitoring.
   - Non-goal if stated: do not configure vendor DSN/token or sourcemap upload when the user defers credentials.
   - Constraints: preserve existing UX such as toast throttling, auth redirects, ErrorBoundary fallback, offline banners.

3. **Implement a local governance module before vendor delivery**
   - Normalize errors into a typed client-error model.
   - Classify kind/severity/source/status/code/domain/route/traceId.
   - Decide reportability and sampling by kind.
   - Sanitize every event before it reaches the vendor SDK.
   - Provide one exported capture wrapper and ban direct SDK calls outside the wrapper.

4. **Use TDD for behavior that prevents regressions**
   - RED: business 4xx does not report; contract/runtime/render does report; sanitization masks PII.
   - GREEN: implement normalize/report/sanitize/global-handler behavior.
   - Regression tests for API envelope `traceId` propagation and direct-vendor-import guard.

5. **Integrate without breaking UX**
   - ErrorBoundary calls the wrapper with `source: 'render'`.
   - API 5xx/network errors keep existing user-visible toast/offline behavior and also enter governed capture.
   - business/auth errors generally remain user/API-domain responses, not monitoring noise.
   - global runtime handlers capture `window.error` and `unhandledrejection`.

6. **Add contract-error sentinels at high-risk parsing boundaries**
   - Amount/rate/fee/currency precision/status enum/order state/transaction state/KYC/auth state.
   - If backend sends an impossible or non-finite value, report `kind: 'contract'`, severity fatal/error, and include only safe metadata: endpoint, field, currency, operation, traceId.
   - Do not include full amounts, raw payloads, account numbers, bank data, tokens, PIN/OTP, or card/ID data.

7. **Document the policy**
   - What is reported / not reported.
   - Sampling rates.
   - Sanitization rules.
   - Replay privacy rules when session replay exists.
   - traceId/eventId usage.
   - Source map/token work intentionally deferred or required.
   - Alert/CI/browser verification checklist.

8. **Verify closure**
   - Targeted tests for governance, ErrorBoundary, API interceptors/envelopes, contract sentinels, and guardrails.
   - Build/typecheck.
   - Full test suite when the user asks for full rollout.
   - Commit only the scoped observability changes and leave unrelated untracked files unstaged.

## Recommended Error Taxonomy

Use a stable taxonomy so sampling and alert rules are intelligible:

- `business`: expected domain 4xx / validation / insufficient state; usually do not report.
- `auth`: login/session/401 flows; generally do not report unless contract-breaking.
- `network`: offline, timeout, DNS, connection reset; sample.
- `server`: 5xx and backend unavailable; sample higher than network.
- `render`: React/Vue render crash; report.
- `runtime`: `window.error`, unhandled promise rejection; report.
- `contract`: impossible API shape/value/status or financial invariant breach; always report.
- `unknown`: report conservatively, then refine classification.

Typical privacy-sensitive app sampling baseline:

- business/auth: 0% reportability
- network: low sample, e.g. 10-20%
- server: medium sample, e.g. 50%
- render/runtime/contract/unknown: 100%

## PII and Financial Data Rules

Always sanitize before vendor SDK delivery and again in `beforeSend`/equivalent.

Mask or drop:

- Authorization, bearer tokens, access/refresh/auth tokens, cookies, secrets
- PIN, OTP, password, passcode, payment verification codes
- phone/mobile/email/address
- card number, bank account, ID/passport numbers, KYC documents
- raw request/response bodies that can contain account, bank, card, or identity data
- URL query params that may carry tokens/phone/email/order-sensitive data

Allowed safe metadata:

- route/screen/domain/source
- HTTP status and stable backend error code
- endpoint path without sensitive query
- traceId/requestId/eventId
- currency and operation kind
- field name for contract errors
- coarse range or category when explicitly needed, not exact confidential amount

## Trace and Correlation Pattern

- Extend frontend `ApiResult<T>`/envelope types with `traceId?: string | null` and `timestamp?: string` when backend provides them.
- Preserve these through service normalization instead of dropping them in envelope adapters.
- Attach `traceId` to telemetry tags/context and optionally display a short error reference in user feedback UI.
- Backend audit ledger/logs remain the source of financial truth; frontend telemetry is for UX/error diagnosis.

## Guardrail Tests

Add tests that fail future regressions:

- Business/auth 4xx does not call the vendor wrapper.
- server/network/render/runtime/contract paths call the wrapper according to sampling.
- sanitization masks nested sensitive keys and URL query params.
- `traceId`/`timestamp` are preserved by the API envelope adapter.
- No app code imports the browser telemetry SDK or calls the raw vendor capture function directly outside the wrapper module.
- Contract sentinels report non-finite/invalid financial fields with only safe metadata.

## Browser Verification Checklist

When credentials/DSN are not configured, use mocks or local SDK spies first. When credentials are configured, verify on the real ingest/backend.

- [ ] Trigger render crash; fallback UI still works; governed capture fires.
- [ ] Trigger unhandled rejection; capture fires once, is sanitized, and preserves the original error message/name rather than reporting a generic normalized wrapper message.
- [ ] Trigger API 500/network offline; existing toast/offline UI remains and governed capture fires/samples.
- [ ] Trigger business 4xx; no monitoring noise; business UX remains.
- [ ] Trigger contract invalid amount/status; capture fires with traceId/field only.
- [ ] Inspect outbound payload or mocked event for PII/token/PIN/OTP absence.
- [ ] If a vendor backend is configured, confirm issue visibility and tags there.

## Common Pitfalls

1. **Starting with credentials instead of governance.** Credentials make leaks/noise real. Build classification/sanitization first.
2. **Reporting business 4xx as exceptions.** This burns quota and hides real regressions.
3. **Letting every file import the vendor SDK directly.** Centralize SDK usage so sanitization and sampling cannot be bypassed.
4. **Dropping `traceId` in envelope adapters.** The one field needed for cross-system diagnosis often disappears during normalization.
5. **Using numeric parsing fallbacks silently.** `Number(raw) || 0` hides financial contract breaks; report non-finite values as contract errors while keeping UI safe.
6. **Uploading raw context/extras.** `extra` frequently contains request bodies, headers, or user data; sanitize recursively and allowlist safe fields.
7. **Equating frontend monitoring with backend audit.** Financial transaction truth belongs in backend ledger/audit events; frontend observability diagnoses client UX and integration failures.
8. **Assuming the deployment platform from a vendor endpoint.** A Sentry/Vercel log-drain URL does not prove the app is hosted on Vercel. Before prescribing production closeout steps, read the project profile/repo deployment config and identify the actual platform, environment, services, and build-time vs runtime env model. For Railway-hosted Vite apps, set `VITE_*` variables on the Railway frontend service/environment, redeploy because Vite consumes them at build time, verify the deployed JS bundle contains the Sentry marker, then use Railway service status/logs/HTTP logs for deploy and trace evidence.
9. **Fixing double-normalized global runtime errors.** If the global `window.error`/`unhandledrejection` handler already returns a normalized client-error object, do not pass that normalized object back through the public `captureClientError(input, context)` wrapper with itself as context. That can lose the original `Error` and turn Sentry issues into generic messages such as `Unknown client error`. Use a lower-level `reportNormalizedClientError(normalized)` path or preserve `normalized.original` when calling the vendor capture, and add a focused test that dispatches `ErrorEvent('error', { error: new Error('runtime boom') })` and asserts the vendor receives `runtime boom`.
10. **Fixing unrelated failing tests without preserving intent.** If full tests reveal a nearby copy/label regression, fix the product contract and update tests by stable keys rather than binding assertions to mutable labels.

## Verification Checklist

- [ ] Error taxonomy and sampling policy are encoded in code and docs.
- [ ] SDK wrapper is the only vendor entrypoint.
- [ ] before-send sanitizer and wrapper sanitizer both run.
- [ ] API traceId/timestamp survive adaptation.
- [ ] Contract sentinels exist at high-risk parsing boundaries.
- [ ] Existing user-facing error UX is preserved.
- [ ] Targeted tests, build, and full tests pass when full rollout is requested.
- [ ] Scoped commit excludes unrelated dirty/untracked files.

## Support Files

- `references/privacy-sensitive-frontend-observability-rollout.md` — concrete rollout pattern: error governance module, telemetry wrapper, traceId propagation, contract sentinel, guard tests, docs, and verification sequence.
