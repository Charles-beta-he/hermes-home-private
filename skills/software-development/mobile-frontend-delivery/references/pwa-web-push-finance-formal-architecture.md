# PWA Web Push for Finance Apps — Formal Architecture Pattern

Applicability: use when a PWA/mobile-web finance app needs production-grade OS-level push notifications, especially when the app already has an in-app notification center and Service Worker/PWA release mechanics.

Anti-conditions:
- Do not use for a quick native-only FCM/APNs integration with no PWA/browser target.
- Do not treat Web Push as the notification source of truth; this pattern assumes an authenticated in-app notification record exists.
- Do not loosen existing finance-app Service Worker cache safety, especially `/api/*` no-cache rules, to make push/offline work easier.

## Core decision

Use standard Web Push + VAPID as the formal PWA path. Keep FCM/APNs as native-shell or compatibility channels, not as the only PWA architecture.

Why:
- Browser PWA subscriptions are standard `PushSubscription` objects: `endpoint`, `keys.p256dh`, `keys.auth`, optional `expirationTime`.
- Safari/iOS Home Screen PWA feasibility should be detected and degraded explicitly rather than forced into a Chromium/FCM-only shape.
- Subscription lifecycle, revocation, and multiple browsers/devices are easier to model as first-class subscriptions than as generic device tokens.

## End-to-end chain

1. User explicitly taps an enable-push action in settings/notification center; never request permission on app startup.
2. Frontend checks HTTPS/localhost, `serviceWorker`, `PushManager`, `Notification`, installed/browser mode, and current permission state.
3. Frontend fetches public config from backend, e.g. `GET /api/public/push-config` returning `enabled`, `provider=webpush`, and VAPID public key.
4. Frontend waits for `navigator.serviceWorker.ready`, calls `pushManager.subscribe({ userVisibleOnly: true, applicationServerKey })`, and registers the serialized subscription.
5. Backend stores the subscription in a dedicated table keyed by `user_id + endpoint_hash`, with `device_install_id`, browser/platform metadata, enabled/revoked state, success/failure timestamps, and failure count.
6. Business code creates an authenticated in-app notification first; this is the source of truth.
7. An async dispatcher/outbox reads the notification event, user preferences, and enabled subscriptions, then sends Web Push via VAPID.
8. Service Worker receives push, calls `showNotification`, and on click focuses/opens the app to the notification detail route.
9. App fetches the notification detail over authenticated APIs; push payload is only a pointer/reminder.

## Frontend pattern

Recommended modules:
- `pwa/pushSupport.ts`: returns support/permission/degraded state with user-facing reason.
- `services/pushSubscription.service.ts`: config/register/unregister/status API wrapper.
- `deviceInstallId`: stable browser-install UUID stored in localStorage/IndexedDB; do not rely on User-Agent hash as device identity.

Subscribe payload shape:

```ts
interface WebPushSubscriptionPayload {
  endpoint: string;
  expirationTime?: number | null;
  keys: { p256dh: string; auth: string };
  platform: 'web';
  browser: 'chrome' | 'edge' | 'safari' | 'firefox' | 'unknown';
  deviceInstallId: string;
  userAgentHash?: string;
}
```

Permission UX:
- Show an explicit enable control only after login or on a notification settings surface.
- If permission is `denied`, do not repeatedly prompt; show settings/browser guidance.
- If push is unsupported, explain the platform boundary (for example, add to Home Screen or use a supported browser).

Logout policy for finance apps:
- At minimum, unlink the current user/device subscription server-side on logout.
- For stricter finance privacy, also call `subscription.unsubscribe()` so the browser subscription cannot continue receiving reminders until re-enabled.

## Service Worker pattern

Add only push/click notification behavior; preserve existing release/cache behavior.

Payload should be sanitized before use. Notification click should accept only app-relative paths. Default target should be notification detail, not a direct business-action route.

```js
self.addEventListener('push', event => {
  if (!event.data) return;
  let payload = {};
  try { payload = event.data.json(); } catch { payload = {}; }
  const notificationId = payload.notificationId;
  const url = typeof payload.url === 'string' && payload.url.startsWith('/')
    ? payload.url
    : (notificationId ? `/notifications/${notificationId}` : '/notifications');
  event.waitUntil(self.registration.showNotification(payload.title || 'Notification', {
    body: payload.body || 'You have a new notification',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    tag: notificationId || undefined,
    renotify: false,
    data: { notificationId, url, category: payload.category },
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const rawUrl = event.notification.data?.url || '/notifications';
  const url = typeof rawUrl === 'string' && rawUrl.startsWith('/') ? rawUrl : '/notifications';
  event.waitUntil((async () => {
    const windows = await clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of windows) {
      if (new URL(client.url).origin === self.location.origin) {
        await client.focus();
        client.postMessage({ type: 'APP_NOTIFICATION_CLICK', url });
        return;
      }
    }
    await clients.openWindow(url);
  })());
});
```

## Backend pattern

Add:
- Public push config endpoint exposing only VAPID public key and enabled/provider state.
- Authenticated subscription controller:
  - `POST /api/me/push-subscription`
  - `DELETE /api/me/push-subscription`
  - `GET /api/me/push-subscription/status?deviceInstallId=...`
- Dedicated subscription table rather than overloading a single `push_token` field.
- Server-side notification preferences; localStorage preferences are UI cache only.
- WebPushChannel that accepts endpoint/p256dh/auth, not just a generic token string.
- Send records per subscription/provider/result/failure code.

Failure handling:
- 404/410 from push service => mark subscription revoked/disabled.
- 401/403 => treat as configuration/key problem; do not blindly revoke all users.
- 429/5xx/network => record failure and retry/backoff as policy allows.
- One subscription failure must not block other subscriptions.
- Push failure must never roll back the business transaction that produced the notification.

## Privacy and payload rules

Allowed payload fields:
- `notificationId`
- `category`
- generic `title`/`body`
- app-relative `url`, normally `/notifications/{id}`
- coarse event time if needed

Forbidden in lock-screen/system push payloads:
- Full amounts or balances
- Card/bank/passport/KYC identifiers
- Counterparty names
- OTPs, PINs, credentials, access/refresh tokens
- External URLs
- Detailed fraud/risk/failure reasons

## Verification checklist

- [ ] Desktop Chromium/Firefox HTTPS: subscribe, server stores subscription, test push appears, click opens notification detail.
- [ ] Android installed PWA: background push appears, click opens the installed app and detail route.
- [ ] iOS/Home Screen: capability is verified or degraded honestly; unsupported Safari tab is not claimed as supported.
- [ ] Permission denied path does not re-prompt and gives settings guidance.
- [ ] Logout prevents subsequent pushes to that user/device.
- [ ] Server-side preferences suppress Web Push while preserving in-app notification truth.
- [ ] 404/410 disables a stale subscription.
- [ ] Payload inspection shows no sensitive data.
- [ ] Service Worker still does not cache finance APIs and still preserves the app's release/update policy.
