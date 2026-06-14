# UVISA-scoped notification SSE reconnect/debugging note

Scope/applicability: this reference is only for the UVISA 2.0 frontend/backend notification system. Use it when investigating user-visible "网络异常" toasts or transient errors around `/api/notifications/stream` in the UVISA repos. Do not apply these endpoint names, file paths, or contract assumptions to other projects.

Anti-conditions: if the failure is from wallet/assets/rates/exchange/transaction REST APIs, payment flows, auth refresh, or a non-UVISA codebase, use the generic network/API debugging path instead. If current source shows no SSE error-to-toast wiring, first suspect stale deployment or a different REST endpoint failure.

## Durable facts to re-check in current code

Backend:
- `api/api-public/.../NotificationController.java` exposes `GET /api/notifications/stream` and returns an `SseEmitter`.
- `NotificationSseBroker` uses a long-lived `SseEmitter` with heartbeat and timeout; timeout/client disconnect is expected lifecycle, not a business failure.
- `GlobalExceptionHandler` should classify SSE timeout/client disconnect/no-resource converter failures as non-business responses and avoid writing an `ApiResponse` JSON body into an already-started `text/event-stream` response.

Frontend:
- `src/services/notificationRealtime.service.ts` uses `fetch(.../notifications/stream)` as an invalidation-only channel.
- Real notification state converges through `/notifications/sync?afterSeq=...`; SSE frames are hints only.
- `src/hooks/useAppBootstrap.ts` wires visibility/online/polling/SSE invalidation into `syncNotifications`.
- Global network toasts usually come from axios interceptor `onNetworkError` in `src/lib/api.ts`; the SSE stream uses `fetch`, so it should not participate in generic axios network-error broadcast unless someone explicitly wires `onError` to toast.

## Debugging sequence

1. Verify deployed/local branch freshness first; stale frontend bundles can keep old toast wiring alive even after source looks correct.
2. Inspect both sides of the chain before patching:
   - Backend stream endpoint and broker lifecycle (`NotificationController`, `NotificationSseBroker`).
   - Backend exception handler for SSE timeout/disconnect semantics.
   - Frontend SSE service and the caller that passes `onError`.
   - Global network toast source (`api.ts`/`App.tsx`) to see whether the SSE error can actually reach it.
3. Treat `/notifications/stream` close/error/abort/timeout/no-body as stream lifecycle, not a user-action failure. The client should silently reconnect; only wallet/assets/rates/transaction/core REST failures should toast.
4. Add targeted tests around the classification and reconnect behavior:
   - abort (`AbortError`) is silent.
   - fetch/stream drop (`TypeError: Failed to fetch` or `network error`) is silent.
   - backend timeout/no-content style response is silent and schedules reconnect.
   - a non-lifecycle code error can still call diagnostic `onError`.
5. Verify with targeted Vitest, TypeScript build, and scoped eslint on touched files. Whole-repo lint may fail on pre-existing unrelated debt; report it separately rather than treating it as proof the SSE fix failed.

## Implementation pattern

Keep the SSE service contract explicit:
- `onError` is diagnostic-only.
- Lifecycle failures are filtered by a helper such as `isSilentStreamLifecycleError`.
- Reconnect remains in `finally` with the existing timer when not cancelled.
- Avoid TypeScript constructor parameter properties if the repo enables `erasableSyntaxOnly`; use plain functions/objects or explicit property assignment.

Backend/proxy-safe pattern for Cloudflare 524 reports:
- Prefer a short-lived SSE lifecycle over a 30-minute stream when the endpoint is served behind Cloudflare or similar proxy. A practical contract is server timeout around 55 seconds plus frontend silent reconnect.
- Keep heartbeat clearly shorter than the lifecycle/proxy read window, e.g. 10 seconds, and send an initial `connected` frame promptly.
- Return `ResponseEntity<SseEmitter>` rather than a bare `SseEmitter` when response headers need to be explicit. Set `produces = text/event-stream`, `Content-Type: text/event-stream`, `Cache-Control: no-cache, no-transform`, and `X-Accel-Buffering: no`.
- Add backend contract tests for response type/headers and timeout bounds; a previous UVISA regression test asserted timeout is between 30s and 60s so Cloudflare cannot turn a long-lived stream into a 524.
- Run app-level exception-handler tests with Maven `-am` in this repo; without `-am`, app tests can compile against stale locally installed sibling artifacts and fail with unrelated missing domain classes.

## Pitfalls

- If the user explicitly chooses “短生命周期”, do not continue optimizing for a long-lived SSE stream; implement bounded lifecycle + reconnect as the product direction.
- Do not fix this by suppressing all global network toasts; that would hide real failures on wallet, assets, exchange, transaction, etc.
- Do not make SSE the source of truth. The UVISA design is invalidation-only SSE plus DB-backed `/notifications/sync` repair.
- Do not infer that browser/network tools are broken from SSE close events; SSE long-poll lifecycle is expected to close and reconnect.

3. Inspect backend SSE flushing assumptions: `SseEmitter` timeout, initial `connected` frame, heartbeat interval, and whether intermediaries may buffer chunks. A 25s heartbeat in source does not prove Cloudflare/Railway actually receives flushed bytes.
4. If user-visible notification state is intact and no toast is emitted, treat the red Network row as lifecycle noise. The real correctness proof is `/notifications/sync?afterSeq=...` convergence plus silent reconnect behavior.
5. If the Network noise must be reduced, prefer deployment/protocol fixes over hiding real errors:
   - set SSE-friendly headers (`Content-Type: text/event-stream`, `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no` where supported);
   - send/flush an immediate initial comment or `connected` frame;
   - shorten heartbeat to 10-15s if proxy read timeout requires it;
   - or intentionally complete/reconnect before Cloudflare’s timeout window, or move the stream to a non-Cloudflare/proper realtime channel.

## Pitfalls

- Do not fix this by suppressing all global network toasts; that would hide real failures on wallet, assets, exchange, transaction, etc.
- Do not make SSE the source of truth. The UVISA design is invalidation-only SSE plus DB-backed `/notifications/sync` repair.
- Do not infer that browser/network tools are broken from SSE close events; SSE long-poll lifecycle is expected to close and reconnect.
- Do not call a local backend targeted-test compile failure the SSE root cause when the errors are unrelated stale-branch symbols; report it separately as local verification blockage and keep root-cause evidence scoped to the stream path.
