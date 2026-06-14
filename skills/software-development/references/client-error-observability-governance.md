# Client Error Observability Governance

Use when landing frontend/user-client error capture, Sentry-style reporting, runtime error handlers, or noisy API error reporting in a production app.

## Core pattern

Build a governance layer between capture sources and the reporting backend:

1. Normalize every source into one `ClientError` model:
   - `kind`: `business | auth | network | server | render | runtime | contract | unknown`
   - `severity`: `info | warning | error | fatal`
   - `source`: `api | render | runtime | unhandledrejection | contract | manual`
   - route, URL, method, status, code, traceId, domain, retryable, reportable
2. Classify before reporting:
   - 4xx business errors: user-visible, not reportable by default.
   - auth/session errors: handled by auth flow, not crash noise by default.
   - network failures: reportable but sampled; keep user toast separate.
   - 5xx server failures: reportable but sampled; preserve backend traceId.
   - render/runtime/unknown: reportable.
   - contract/protocol errors in finance flows: always report; these are correctness risks, not ordinary UI failures.
3. Sanitize twice:
   - before setting custom extras/tags;
   - again in Sentry `beforeSend` or equivalent last-mile hook.
4. Global capture should include:
   - ErrorBoundary/render crash path;
   - API interceptor path for network/5xx;
   - `window.error`;
   - `unhandledrejection`.
5. Do not require the Sentry token/DSN to land governance. The code should no-op cleanly when no DSN is configured.

## Default sampling policy

Reasonable starting point for a financial user app:

- `business`, `auth`: 0%
- `network`: 20%
- `server`: 50%
- `render`, `runtime`, `contract`, `unknown`: 100%

Keep sampling adjustable through env vars where supported:

- traces sample rate
- replay session sample rate
- replay-on-error sample rate

## Privacy redaction checklist

Filter these keys and string contents before telemetry leaves the browser:

- Authorization / auth headers
- token, access_token, refresh_token, auth_token
- cookie, session, credential
- password, PIN, OTP, verification code
- direct contact identifiers: email, phone, mobile
- query params carrying token/phone-like values

For Sentry user context in finance apps, prefer only a stable user id/hash. Do not send email or phone.

## TDD slices

Write behavior tests before implementation:

1. 4xx business response normalizes as `business`, `reportable=false`.
2. 5xx response normalizes as `server`, `reportable=true`, sampled by threshold.
3. contract/protocol error is always reportable.
4. sanitizer removes tokens, auth headers, OTP/PIN and direct contacts from nested payloads.
5. installed global handlers normalize `window.error` and `unhandledrejection`.
6. ErrorBoundary still renders fallback and forwards through the governed capture path.
7. API network/5xx keeps existing UI broadcast/toast behavior while also entering governed capture.

## Integration checklist

- Keep user-facing UI behavior separate from telemetry. A global toast is not an error report, and a reportable error does not always need a user toast.
- Preserve existing auth refresh/session-expired logic; do not reclassify normal 401 flows as crashes.
- Attach route, domain, status, code and traceId as tags/extras for debugging.
- Add release/dist/build metadata when available.
- If full-suite verification fails on unrelated tests, still run targeted tests for the new governance paths and classify unrelated failures explicitly.

## Pitfalls

- Reporting every 4xx business rejection will exhaust free/paid Sentry quotas and bury real crashes.
- Session Replay can leak context even when text masking is enabled; keep replay sample low and sanitize event extras independently.
- Do not wait for a DSN/token to implement governance. The governance layer is useful and testable without live Sentry credentials.
- Do not store secrets or DSNs in repository docs or tests.
