# PWA Web Push subscription lifecycle analysis

Applicability: use for browser/PWA notification architecture reviews where the question is when the frontend subscribes to background notifications, whether a closed PWA can still receive OS notifications, or whether foreground realtime is being confused with background delivery.

Anti-conditions: do not use this as proof for any named project, endpoint, provider, or production deployment without re-reading that codebase. Concrete endpoint names below are examples only; always verify current wrappers and callers.

## Classification first

Separate these channels before making claims:

1. Foreground realtime invalidation
   - Usually SSE/WebSocket/fetch polling while the page is mounted and authenticated.
   - Stops when the page/app is closed or the browser kills the page.
   - Good for syncing badge/message-center state, not OS background delivery.
2. Background OS notification delivery
   - Web Push plus Service Worker for PWA/browser apps.
   - Native token paths such as FCM/APNs for native shells.
   - Can fire when the page is closed if subscription, permission, SW, backend sender, and platform support are all valid.
3. Service Worker registration
   - Required infrastructure for PWA push, but not itself a push subscription.
   - Do not conflate `navigator.serviceWorker.register(...)` with `pushManager.subscribe(...)`.

## Code search checklist

Search the frontend for:

- `pushManager.subscribe`, `getSubscription`, `PushManager`, `Notification.requestPermission`
- `serviceWorker.register`, `navigator.serviceWorker.ready`, PWA plugin config, `importScripts`
- `self.addEventListener('push')`, `showNotification`, `notificationclick`
- Backend registration wrappers for push subscriptions, push tokens, notification preferences, and platform push config
- Native-shell token paths: `Capacitor`, `FirebaseMessaging`, `FCM`, `APNs`, `PushNotifications`, platform bridge listeners
- Bootstrap hooks and settings screens that call the subscription function

## Subscription timing rubric

Answer “when does the frontend subscribe?” from the actual caller of `pushManager.subscribe(...)` or native token registration, not from the service file alone.

Common timing patterns:

- User-initiated settings toggle: user turns on a push switch, frontend requests permission, subscribes, then posts subscription to backend.
- Login/bootstrap silent ensure: only runs for users who previously enabled push and already granted permission; should not trigger browser permission prompts without a direct user gesture.
- Native token refresh: platform plugin surfaces a token after permission grant or token refresh, then frontend posts it to backend.
- Logout cleanup: unsubscribe locally and revoke the backend row/device token.

## Closed-PWA notification answer

For Web Push, a closed PWA/page can receive OS notifications if all are true:

- Browser/platform supports Web Push for that install mode.
- User granted notification permission.
- A Service Worker is registered and contains a `push` event handler that calls `showNotification(...)`.
- The app previously created a `PushSubscription` via `registration.pushManager.subscribe(...)`.
- The backend saved that subscription and actually sends Web Push to its endpoint.
- User/backend preferences have not disabled push.

Platform caveat: iOS requires an installed Home Screen PWA/standalone context for Web Push; ordinary Safari tabs should not be treated as equivalent.

## Pitfalls

- Do not answer “yes, subscribed” just because a service wrapper exists. Verify it has a real business caller.
- Do not treat foreground SSE/WebSocket as background notification delivery.
- Do not treat SW registration/update code as notification subscription.
- If both native-token and web-push-subscription wrappers exist, identify which one is actually wired; a native-token service may be legacy or test-only.
- If permission is not yet granted, a silent bootstrap ensure should normally return a user-action-required state rather than showing a permission prompt.
- Branch/ref mismatch is a common false root cause in multi-repo apps: before claiming backend push endpoints are missing, verify the branch the user means (often a shared `test`/staging branch) with `git fetch --prune` and inspect the remote ref directly (`git grep <endpoint> origin/<branch>` or `git show origin/<branch>:path`). Report separately: current checkout branch, remote target branch contents, and deployed/runtime evidence. A stale local feature branch can make present `/platform-config/push`, `/me/push-subscription`, or preference endpoints look absent.
- Separate user preference state from device subscription state. A backend/default `pushEnabled=true` can mean “user allows push” while the current device still has no `PushSubscription` or backend subscription row; do not infer active delivery from the switch alone. Check browser permission, `pushManager.getSubscription()`, local subscription markers/key version, and backend registration/readback when diagnosing “switch on but no push”.

## Report shape

Keep the answer concise:

- Current wired channel(s): foreground realtime vs background Web Push/native.
- First subscription trigger: exact screen/hook/event.
- Backend registration endpoint or wrapper, verified in current code.
- Whether closed-app notifications work, with the required conditions.
- Any unwired/legacy token paths found.
