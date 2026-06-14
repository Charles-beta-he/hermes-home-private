# Frontend client error capture audit

Scope: Class-level workflow for frontend applications when asked where client-side errors are captured, where they are visible, or whether observability/error-boundary handling is production-ready.

Anti-scope: Do not treat this reference as proof of any specific project's current configuration. Always re-read the target repository and deployment environment before claiming where production errors are visible.

## Evidence-first inspection path

1. Boot repository context first when local project instructions require it.
2. Identify entrypoint initialization:
   - Search for Sentry/Rollbar/Bugsnag/GA/Datadog init (`initSentry`, `Sentry.init`, `VITE_SENTRY_DSN`, `beforeSend`, `release`).
   - Read the exact init file and env gates. If DSN/env is absent from repo, do not claim production is configured; say deployment env must be checked.
3. Identify React crash boundaries:
   - Search for `ErrorBoundary`, `componentDidCatch`, `getDerivedStateFromError`.
   - Read placement in the app shell/routes to determine blast radius and user-visible fallback.
4. Identify API/interceptor behavior:
   - Read axios/fetch wrapper, response interceptors, auth refresh, envelope normalization, network/5xx handling, and event broadcasts.
   - Distinguish business 4xx from network/server/runtime errors; business rejects are often user-facing but not crash-report-worthy.
5. Identify product analytics sink separately from error reporting:
   - Search for `sendBeacon`, `/analytics/events`, `gtag`, `track("error")`.
   - Verify whether the backend actually has the endpoint or an ADR says it is deprecated/third-party-only. Do not treat a dead analytics sink as reliable observability.
6. Verify with targeted tests if present:
   - ErrorBoundary tests, network-error broadcast tests, interceptor tests.
   - Report actual command output, not assumed coverage.

## Reporting template

- User-visible surfaces:
  - fallback page / toast / redirect / field-level error, with file paths.
- Engineering-visible surfaces:
  - Sentry or equivalent dashboard, gated by env vars; state whether repo proves or does not prove deployment configuration.
- Non-reliable or transitional sinks:
  - analytics endpoints, console-only logs, mock sinks.
- Gaps:
  - missing global `error`/`unhandledrejection`, missing `beforeSend` PII filtering, no release/dist, no route/domain/traceId context, overbroad boundary, dead analytics sink.
- Next actions:
  - P0 low-risk instrumentation and tests before page rewrites.

## Durable inspection lessons

- A crash-report SDK in dependencies is not enough; the init env gate and deployment variables decide whether errors reach a dashboard.
- A UI fallback/toast proves user-visible handling, not engineering observability.
- `track("error")` or `sendBeacon('/analytics/events')` is only reliable if the target sink exists and is part of the accepted analytics architecture.
- For financial apps, protocol/contract errors (bad money format, unknown status, missing required fields) deserve high-priority reporting even if the UI can recover.

## User-visible network toast triage

When a screenshot shows a generic network toast over an otherwise-rendered page, do not assume the visible page component emitted it. Trace in this order:

1. Search the exact user-facing copy and its i18n key, then search all call sites of that key.
2. Read the app-shell/global listener that displays toasts. For axios/fetch wrappers, inspect whether network/no-response and 5xx failures are converted into window events or app-wide store events.
3. Check whether errors are buffered before the React listener mounts and replayed afterward; first-entry/cold-start bugs often come from buffered bootstrap failures, not the foreground page action.
4. Map route → screen → local data fallback. A detail page can render from cached/session/local list data while its initial remote refresh fails; this produces “page looks fine + global network toast”.
5. Inspect app bootstrap hooks separately from the current screen. Concurrent preloads such as profile, wallets, recent transactions, notifications, card, products, holdings, payees, or release checks can trigger the same global toast on first entry.
6. For report-only investigations, output the exact chain: text key → global listener → interceptor dispatch condition → route/screen fetch → service endpoint → fallback that kept UI visible. Avoid recommending a page-level fix until the actual failing request is identified from logs/network evidence.

## Pitfalls

- Do not answer “errors go to Sentry” unless the SDK init path and DSN/deployment env are verified.
- Do not conflate analytics/product events with crash/error reporting.
- Do not report business validation failures (wrong OTP/PIN, insufficient balance) as application crashes by default.
- Do not rely on browser console visibility as a production operations answer.
