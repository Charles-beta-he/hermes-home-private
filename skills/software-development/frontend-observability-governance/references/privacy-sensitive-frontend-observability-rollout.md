# Privacy-Sensitive Frontend Observability Rollout

This reference captures a reusable rollout pattern from a frontend monitoring hardening session. It intentionally omits project names, paths, commits, and credentials.

## Objective Model

Success criteria:

- React/render errors, API/network/server errors, runtime errors, unhandled rejections, and API contract violations are captured through one governed wrapper.
- Expected business/auth failures do not flood monitoring.
- Sensitive data is masked before leaving the browser.
- Backend correlation fields (`traceId`, `timestamp`) survive frontend envelope adaptation.
- Existing user-facing UX remains intact.
- The work is backed by tests, build, and scoped commit.

Constraints:

- If the user defers monitoring credentials, do not configure DSN/token or sourcemap upload.
- Financial/account-sensitive frontends must preserve backend audit/ledger as source of truth; browser telemetry is diagnostic only.

## Implementation Slices

### 1. Governance module

Create a local module with these functions/types:

- `normalizeClientError(error, context)`
- `shouldReportClientError(normalized)`
- `sanitizeForTelemetry(value)`
- `installGlobalErrorHandlers(capture, getContext?)`
- typed error kind/severity/source/context fields

Classification baseline:

- business/auth: not reportable by default
- network/server: sampled
- render/runtime/contract/unknown: reportable

### 2. Vendor wrapper

Expose only a local wrapper such as `captureClientError`. Vendor SDK imports should live in one adapter file only.

Wrapper responsibilities:

- call normalizer
- apply reportability/sampling
- set safe tags: kind/severity/source/domain/status/code/traceId
- attach sanitized extra/client context
- run recursive sanitizer in before-send/equivalent
- set user ID only if needed; do not send email/phone

### 3. Global/runtime integration

Install global handlers at app boot after SDK init:

- `window.error`
- `unhandledrejection`

The handler should be disposable for tests and should avoid duplicate captures when possible.

### 4. API integration

In the API client/interceptor:

- Keep existing toast/offline/auth redirect behavior.
- Report governed network/5xx errors.
- Avoid reporting expected business 4xx/auth flows.
- Preserve endpoint/status/code/traceId as safe metadata.

In envelope adaptation:

- Keep `traceId?: string | null`.
- Keep `timestamp?: string`.
- Do not drop these while normalizing `data/message/code`.

### 5. Contract sentinels

At high-risk parsers/normalizers, replace silent numeric fallback with a reporting helper:

```ts
function contractMoneyNumber(raw: unknown, field: string, context: SafeContext): number {
  const value = Number(raw ?? 0);
  if (Number.isFinite(value)) return value;
  captureClientError(new Error(`Invalid numeric field: ${field}`), {
    source: 'api',
    kind: 'contract',
    severity: 'fatal',
    field,
    endpoint: context.endpoint,
    traceId: context.traceId,
  });
  return 0;
}
```

Only safe metadata should be attached. Do not attach raw payloads, exact confidential amounts, account/bank/card data, tokens, PINs, OTPs, or addresses.

### 6. Guard tests

Useful tests:

- business 4xx is not reportable
- server/network sampling works
- contract/render/runtime are reportable
- nested sensitive fields and URL query params are masked
- global handlers capture runtime/unhandled rejection
- envelope adapter preserves traceId/timestamp
- no app file imports the vendor SDK directly except the adapter
- invalid financial numeric fields report contract errors with safe metadata

A simple SDK-import guard can recursively scan source files and fail if `@vendor/sdk` or raw `captureException` appears outside the local adapter/test allowlist.

### 7. Documentation

Create a project doc/ADR describing:

- reported vs non-reported classes
- sampling table
- sanitization table
- replay/privacy policy
- traceId/eventId usage
- source map/credential work that is deferred or required
- alerting expectations
- browser verification checklist
- backend audit boundary

## Verification Sequence

Recommended closeout gate:

1. Run targeted observability tests.
2. Run adjacent tests for ErrorBoundary/API envelope/API network behavior and any touched domain service.
3. Run build/typecheck.
4. Run full tests when the user asked for full rollout.
5. If full tests reveal a nearby product-contract test failure, fix the product contract rather than weakening the test. Prefer stable keys for tests when label text legitimately changed.
6. Stage only intended files; inspect cached diff/name list; commit scoped changes.
7. Report any remaining untracked/unrelated files separately.

## Anti-Patterns

- Configuring production credentials before sanitization/reportability exists.
- Treating all Axios errors as exceptions.
- Sending raw request/response objects as telemetry extras.
- Dropping `traceId` during adaptation and trying to recover it later.
- Binding monitoring tests to transient UI labels instead of stable keys or semantic fields.
- Claiming observability is complete without either browser/mock verification or vendor-ingest verification, depending on whether credentials are in scope.
