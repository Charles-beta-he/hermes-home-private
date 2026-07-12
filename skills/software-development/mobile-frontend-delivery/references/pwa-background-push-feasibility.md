# PWA Background Push Feasibility Audit

Use when a user asks whether an existing PWA/mobile web app can support system/background push notifications, especially when the app already has an in-app notification center, polling, SSE/WebSocket invalidation, or backend notification fanout.

## Goal

Separate three layers before recommending implementation:

1. **In-app notification truth source**: DB-backed notifications and REST sync endpoints. This remains authoritative for finance/security state.
2. **Foreground realtime/invalidation**: SSE/WebSocket/polling/visibility refresh while the app is open. This is not background push.
3. **OS-level background push**: Service Worker / Web Push / FCM / APNs delivery while the app is closed or backgrounded.

Do not claim background push is implemented just because the project has a PWA manifest, generated service worker, in-app notifications, SSE, or a `pushToken` API wrapper.

## Evidence checklist

### Frontend / PWA evidence

Check for:

- PWA manifest with `display: standalone`, `start_url`, icons, HTTPS deployment.
- Service Worker registration and whether it is generated or custom-extensible.
- `Notification.requestPermission()` behind a user gesture.
- `navigator.serviceWorker.ready` / `ServiceWorkerRegistration.showNotification()` usage.
- Standard Web Push path: `PushManager.subscribe({ applicationServerKey })`, subscription persistence, VAPID public key.
- Firebase Web Messaging path: `firebase/messaging`, `getToken()`, `onMessage`, `firebase-messaging-sw.js` or equivalent SW integration.
- Service Worker `push` and `notificationclick` event handlers.
- Token/subscription refresh and logout cleanup.
- Click deep-link routing followed by REST resync, not trust in push payload alone.

Red flag: an API wrapper such as `registerPushToken(token, platform)` without permission/token acquisition code is only a contract stub, not a working push implementation.

### Backend evidence

Check for:

- Token/subscription registration endpoint and authenticated current-user binding.
- Device table or subscription table storing provider, platform, token/subscription, revoked state, timestamps.
- Real provider channel: FCM, APNs, or standard Web Push. Distinguish default `stub` channels from production providers.
- Provider credentials/config gates, e.g. Firebase service account, VAPID keys, APNs config.
- Notification dispatcher fanout from durable notification/event creation.
- Template fields for push title/body and localization.
- Invalid-token cleanup (`NotRegistered`, invalid registration, expired subscription) and metrics.
- `updated=0` / missing device row handling: fail visibly or upsert safely; do not silently report success.

### Platform matrix

Report feasibility per target surface:

- **Android Chrome / Desktop Chromium PWA**: usually high feasibility with FCM Web Messaging or standard Web Push.
- **iOS/iPadOS Home Screen PWA**: supported on iOS/iPadOS 16.4+, but only for web apps added to Home Screen and permission requested from a direct user gesture. Do not promise support for ordinary Safari tabs.
- **Native/RN/Capacitor shell**: usually best for finance-grade mobile reliability; use APNs/FCM native SDK tokens and reuse backend registration/fanout when available.

## Recommended decision pattern

1. If backend already has FCM token fanout and frontend lacks push registration, the lowest-risk first slice is usually **Android/Desktop PWA via Firebase Web Messaging**, with iOS explicitly out of scope until a Web Push or native-shell path is chosen.
2. If the requirement is pure PWA including iOS Home Screen, design a **standard Web Push** path with VAPID and a subscription table. A single `push_token VARCHAR` field may be insufficient for endpoint + `p256dh` + `auth` subscription data.
3. If the requirement is finance-grade reliable mobile notifications, prefer **native/RN/Capacitor push** for iOS/Android and keep PWA push as a convenience lane.
4. For all paths, push payloads should be short, non-sensitive, and treated as a wake-up signal; the app must resync via authenticated REST on open/click.

## Finance/security safety rules

- Do not expose full amounts, card numbers, addresses, order IDs, or sensitive failure reasons in push body unless product/security explicitly approves.
- Do not treat notification click as identity confirmation.
- Do not perform money/security actions directly from push.
- Always preserve the in-app notification center as the authoritative read state and audit trail.
- Background delivery failures must not block the business event from being stored in-app.

## Standard Web Push implementation checklist

Applicability: use when implementing formal browser/PWA Web Push from a backend-provided contract. Anti-condition: if the product is native-only or the backend contract explicitly uses provider device tokens, follow the provider/native-token contract instead of forcing standard Web Push fields.

1. **Treat backend docs as a contract, then read back the merged code.** After the backend branch merges, fetch the shared branch and inspect the actual controllers/services/migrations from a clean worktree if the main backend checkout is dirty. Confirm endpoint paths, response envelope adaptation, request body shape, preference fields, VAPID key-version semantics, and migration names before changing frontend code.
2. **Keep browser Web Push separate from native/provider token APIs.** Standard Web Push should register `endpoint + keys.p256dh + keys.auth + contentEncoding + deviceInstallId + vapidKeyVersion` on a subscription endpoint, not a generic device-token endpoint unless the backend explicitly maps those fields.
3. **Use a stable install/device ID generated by the frontend.** Generate once per browser install, store it locally, and send it with subscription/register/unregister calls. Do not rely on User-Agent hash as the primary device identity.
4. **Gate permission requests behind a direct user gesture.** Silent bootstrap/foreground recovery may re-register an existing granted subscription or rotate a changed key, but must not call `Notification.requestPermission()` while permission is `default`. Return a `requires-user-action` status instead.
5. **Handle VAPID key rotation.** Store backend `keyVersion`; if it changes, unsubscribe the old browser subscription, subscribe with the new public key, and POST the fresh subscription. Keep this idempotent and low-frequency during bootstrap.
6. **Extend generated Workbox service workers with a narrow push script when possible.** If the app already uses generated Workbox service workers, prefer an imported push-events script for `push`/`notificationclick` handlers rather than switching the whole app to a custom manifest flow unless cache behavior requires it.
7. **Make notification click routing safe.** Only accept app-relative paths; reject protocol-relative paths, schemes, backslash paths, and external URLs. On click, focus an existing client when possible, post a message for app-side routing/sync, otherwise open a safe fallback.
8. **Server-side preferences are authoritative.** Local preferences can be optimistic cache only. Read/write backend notification preferences and make category keys match the backend contract exactly.
9. **Logout cleanup must run before token removal.** Best-effort unregister the current subscription/device while the auth token is still available, then clear local auth state.
10. **Verify in layers.** Unit-test service endpoints, support detection, user-gesture gating, key rotation, service-worker import/click safety, settings UI behavior, and logout cleanup; then run full build and finally do real HTTPS/device push delivery against a configured backend.

## Verification checklist

- Permission request only occurs after a user gesture.
- Token/subscription is read back from backend storage for the current authenticated device.
- Provider channel is non-stub and initialized with real config in the target environment.
- A test notification reaches the target OS notification center.
- `notificationclick` opens the intended route and triggers REST sync.
- Logout/revoke clears the current device token/subscription.
- Invalid provider tokens/subscriptions are cleaned or quarantined.
- iOS claims are verified on a Home Screen web app, not a Safari tab.
