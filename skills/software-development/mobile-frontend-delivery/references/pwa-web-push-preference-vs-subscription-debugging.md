# PWA Web Push: Preference vs Physical Subscription Debugging

Use when a PWA/mobile-web notification settings page shows errors such as "push service unavailable", disables an App Push switch unexpectedly, or a product rule says new users should have app notifications enabled by default.

## Core distinction

Separate two state machines:

1. **User notification preference** — product/business intent: whether the user wants App notifications and which categories are enabled. For new users this may default to `pushEnabled=true` even before OS/browser push is available.
2. **Physical push subscription capability** — device/browser/provider state: service worker readiness, Notification permission, PushManager support, VAPID/FCM/APNs config, subscription endpoint/token registration, backend provider readiness.

Do not let a physical subscription failure rewrite the user's notification preference unless the user explicitly turns the preference off.

## Failure-classification pattern

When `ensurePushSubscription()` returns a status instead of throwing:

- `disabled` / missing VAPID key / provider mismatch: backend/provider config error; toast to user and capture as operational error.
- `unsupported` / `ios-requires-standalone`: platform boundary; toast/guidance, do not mark preference false.
- `permission-denied`: user/system permission boundary; guidance, do not keep re-prompting.
- `requires-user-action`: silent bootstrap is not allowed to ask permission; defer until direct user gesture.
- `permission-not-granted`: user declined this prompt; keep product preference semantics separate from device subscription status unless product explicitly defines decline as preference-off.
- `failed`: unexpected subscription/registration error; capture with feature/status/reason and show toast.

## UI rule

For notification-settings push failures:

- Use the app's global toast/banner system for transient errors.
- Do not render a permanent inline error at the top of the settings page unless it is a durable diagnostic panel.
- If the user enabled App Push and physical subscription fails, leave the preference switch reflecting the server/user preference; the toast explains that system-level push is not currently active.
- Add a separate device/subscription status surface if the product needs to show physical push readiness.

## Error capture rule

Status-returning failures are not caught by ErrorBoundary/Sentry automatically. Explicitly capture operational failures, for example:

```ts
if (result.status !== 'ok') {
  captureError(new Error(`Web Push subscription failed: ${result.status}`), {
    feature: 'web-push',
    status: result.status,
    reason: result.reason,
  });
  toast(statusMessage(result.status), 'error');
}
```

## Iceberg scan checklist

When physical Web Push fails, scan all layers before assigning blame:

### Frontend

- Service worker is registered in production and includes a `push` event handler.
- Permission request is behind a direct user gesture.
- `PushManager.subscribe({ userVisibleOnly: true, applicationServerKey })` uses a valid backend public key.
- Subscription registration endpoint shape matches backend: standard Web Push needs `endpoint`, `keys.p256dh`, `keys.auth`, `contentEncoding`, `deviceInstallId`, `vapidKeyVersion`.
- Logout/unregister happens before clearing auth, and does not confuse native token APIs with browser subscriptions.

### Backend contract

- Public config endpoint exists and returns `enabled=true`, `provider='webpush'`, valid VAPID public key, and key version.
- Authenticated subscription register/delete endpoints exist and persist the browser subscription, not just a legacy FCM/APNs token string.
- Notification preference endpoints exist and default new users according to product policy.
- Dedicated subscription storage exists for standard Web Push; a single `push_token` column is usually insufficient for endpoint + `p256dh` + `auth`.

### Provider/runtime

- Web Push provider is real, not `stub`.
- VAPID private key is configured server-side and matches the public key exposed to the frontend.
- Dispatcher creates an in-app notification first, then sends Web Push as best-effort wake-up.
- Provider failures are recorded and stale subscriptions are disabled on 404/410.

## Verification checklist

- Regression test: physical push disabled/unavailable shows a toast and does **not** call preference rollback such as `updateNotificationPreferences({ pushEnabled: false })`.
- Regression test: the operational failure is captured with feature/status/reason.
- Regression test: silent bootstrap with Notification permission `default` does not call `requestPermission()`.
- Build/typecheck passes.
- Real device/browser proof: subscribe succeeds, backend readback shows subscription/token for current user/device, test push appears in OS notification center, click opens a safe app-relative route and triggers REST sync.

## Anti-conditions

Do not apply this as a reason to ignore a user's explicit choice to disable App notifications. If the user turns the preference off, update the server preference and unregister/unsubscribe as product policy requires.

Do not claim system/background push is working from in-app SSE/polling, a service worker file, or a push-token wrapper alone. OS-level delivery requires provider/config/subscription/readback evidence.
