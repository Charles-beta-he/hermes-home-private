# UVISA Web Push settings failure debugging

Applicability: UVISA user app (`uvisa-app-2.0`) notification settings page when the user sees a toast while toggling App/Web Push notifications, especially Chinese copy such as `推送开启失败，请稍后重试`.

Anti-conditions:
- Do not use this as proof that production backend endpoints are missing without checking the currently connected backend/environment.
- Do not generalize these endpoint names to other projects; this is UVISA-scoped.
- Do not conflate foreground SSE notification sync with background Web Push subscription.

## Visible-copy to status map

Re-read `src/screens/me/NotificationSettingsScreen.tsx` before relying on sequence: the current implementation subscribes the browser first and only then persists `pushEnabled: true`. Older revisions used the opposite order.

Typical Chinese toast mapping:

- `保存失败，请稍后重试` → an exception escaped the toggle flow, commonly the post-subscription `PUT /api/notifications/preferences`; verify the current call order instead of assuming preference save ran first.
- `推送服务暂不可用` → `ensureWebPushSubscription()` returned `disabled` (backend push config disabled, provider not `webpush`, or no public key).
- `当前浏览器暂不支持 PWA 推送` → `unsupported`.
- `请先将 U-VISA 添加到主屏幕后再开启推送` → iOS-like browser is not standalone PWA.
- `系统通知权限已被拒绝，请到浏览器或系统设置中开启` → browser notification permission is `denied`.
- `未获得系统通知权限，已为您关闭推送` → permission prompt returned non-`granted`.
- `推送开启失败，请稍后重试` → `failed`: an exception or incomplete subscription occurred during the Web Push subscription/register phase.

## Current trigger chain for enabling App Push

1. `NotificationSettingsScreen` renders the App push row only when `getWebPushSupport().supported` is true.
2. User taps the App push switch from off to on; the row becomes busy/disabled.
3. Frontend calls `ensureWebPushSubscription({ reason: "settings", userInitiated: true, ignorePreferenceGate: true })`.
4. The ensure path reads push config, requests permission when needed, waits for an active Service Worker, gets/creates a `PushSubscription`, and registers it through `POST /api/me/push-subscription`.
5. Only after status `ok` does the current screen call `updateNotificationPreferences({ pushEnabled: true })`.
6. A non-`ok` ensure result is captured as `Web Push subscription failed: <status>` and mapped through `statusMessage(status)`; an escaped exception rolls UI state back and shows the generic save failure.

Always verify this order in current source: an earlier UVISA revision persisted preferences before subscribing.

## `failed` root-cause candidates

Read `src/lib/webPush.ts::ensureWebPushSubscription()` and verify each boundary:

- `GET /api/platform-config/push` rejects, times out, returns 404/500, or returns malformed config.
- Backend config contains an invalid VAPID public key; `urlBase64ToUint8Array(cfg.publicKey)` throws.
- `navigator.serviceWorker.ready` rejects or never resolves in the current runtime.
- `registration.pushManager.getSubscription()` / `.subscribe(...)` throws.
- Returned `PushSubscription.toJSON()` lacks `endpoint`, `keys.p256dh`, or `keys.auth`.
- `POST /api/me/push-subscription` rejects or returns a backend/API error.

## Long SSE request vs Web Push enable timeout

A Network row for `GET /api/notifications/stream` lasting roughly 35–55 seconds and ending with HTTP 200 is normally the intentional short-lived SSE lifecycle, not proof that App Push activation timed out.

Before linking the two:

1. Read the backend SSE timeout/heartbeat and explicit event-stream headers in the current target branch or deployed revision. UVISA has used a 55-second stream with heartbeat plus client reconnect.
2. Read `useAppBootstrap`: foreground SSE is started independently and is not awaited by the settings toggle.
3. Check the negotiated protocol. Under HTTP/2, do not reuse the HTTP/1.1 “six connection slots are exhausted” explanation without concrete connection evidence.
4. Trace the actual Web Push stages separately: push config → permission → Service Worker readiness → `getSubscription`/`subscribe` → backend registration → preference update.

A stronger UVISA timeout candidate is an unbounded browser promise:

- `navigator.serviceWorker.ready` can remain pending until an active worker exists.
- `pushManager.getSubscription()` and `pushManager.subscribe()` may also stall or reject.
- If Service Worker registration is deferred until `window.load` plus an idle callback, a fast user action after first install/cache clear can begin waiting before registration/activation finishes.
- A busy UI that awaits the whole ensure flow remains disabled until that promise settles unless each browser boundary has a deadline.

Do not call this fully runtime-confirmed from source alone. Confirm with per-stage timings in an authenticated affected browser. But source evidence of unbounded awaits plus deferred registration is enough to reject SSE duration as the direct causal explanation and to define the next reproduction.

## Test-gap checklist

Happy-path unit tests often set `navigator.serviceWorker.ready = Promise.resolve(...)`, which structurally hides this class of defect. Add negative coverage for:

- `serviceWorker.ready` remains pending beyond the product deadline;
- explicit Service Worker registration remains pending, rejects, and can be retried after rejection;
- a shared registration helper deduplicates concurrent bootstrap/settings callers without permanently caching a rejected registration;
- Service Worker registration rejects or activation never completes;
- `pushManager.getSubscription()` remains pending/rejects independently of `subscribe()`;
- `pushManager.subscribe()` remains pending/rejects;
- backend subscription registration reaches the HTTP-client timeout;
- every timeout releases the settings-row busy state, keeps the switch truthful, emits the correct stage-specific diagnostic, and does not persist `pushEnabled: true`;
- the settings integration covers both Service Worker readiness timeout and PushManager subscription timeout, not just one status mapping.

Keep timeouts stage-specific. A generic axios timeout covers HTTP calls only; it does not bound browser-owned promises. If the product requirement is an end-to-end deadline rather than a per-stage deadline, propagate a remaining-time budget across registration, readiness, lookup, and subscribe; independent 10-second wrappers can otherwise accumulate serially.

When Service Worker registration is extracted into a shared helper used by both update checks and Web Push setup, review the extraction as a shared lifecycle change rather than a pure refactor: verify deduplication, rejected-promise reset, final registration identity, and unchanged update-check behavior.

## Endpoint existence checklist

For the currently connected backend, verify wrappers against controllers before making claims:

Frontend wrappers usually live in `src/services/webPushSubscription.service.ts`:

- `GET /platform-config/push` → expected public config endpoint under backend `/api/platform-config/push`.
- `POST /me/push-subscription` → expected user subscription registration under backend `/api/me/push-subscription`.
- `DELETE /me/push-subscription` → expected unsubscribe/revoke endpoint.
- `GET /notifications/preferences` / `PUT /notifications/preferences` → preference storage contract.

Backend evidence should come from current `api-public` controllers or route tests, not docs alone.

## Reporting shape

When answering a screenshot/root-cause question, keep it short:

1. Quote the visible toast text and route/screen.
2. Name the user action required to trigger it.
3. Separate preference-save failure from Web Push subscription failure.
4. Map the exact toast to the status value.
5. List the likely failing API/browser boundary with file/line evidence.
6. If a current backend scan shows missing endpoints, phrase it as environment/repo evidence: “in this checked backend revision I did not find route X,” not as a universal product fact.
