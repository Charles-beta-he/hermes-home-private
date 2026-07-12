# PWA Web Push preference vs current-device ready switch

Use when a PWA notification settings page has legacy users whose server-side App Push preference defaults to on, but Web Push was not physically connected when the preference was created.

## Core distinction

Separate three states:

1. **Server preference**: `pushEnabled=true/false` means the user wants App push reminders in product terms.
2. **Current-device capability**: browser/OS supports Web Push, Notification permission is granted, and Service Worker/PushManager are available.
3. **Current-device subscription readiness**: the browser currently has a `PushSubscription` and the frontend has evidence that it registered successfully with the backend for this install.

For legacy users, `pushEnabled=true` alone must not make the settings switch look enabled, because it can falsely imply the current device is already receiving OS notifications.

## Recommended switch semantics

If the UI label is “App push notification” and users expect it to mean “this device can receive system notifications”, render the switch checked only when:

- server preference `pushEnabled === true`; and
- current browser supports PWA push; and
- `Notification.permission === 'granted'`; and
- `registration.pushManager.getSubscription()` returns a subscription; and
- a local successful-register marker exists, e.g. `WEB_PUSH_ENABLED_KEY === 'true'`.

Without a backend status endpoint, this is a pragmatic current-device readiness approximation. With a future endpoint, prefer server readback such as `GET /me/push-subscription/status?deviceInstallId=...`.

## Click behavior

When the derived switch is off:

- If `pushEnabled=false`, first update the server preference to true.
- If `pushEnabled=true` but the current device is not ready, do **not** rewrite the preference; directly run user-initiated subscription.
- Call `ensureWebPushSubscription({ reason: 'settings', userInitiated: true })` only from the user gesture.
- Set the switch on only after subscription/register returns `ok`.
- On failure, keep the switch off, show/capture the operational error, and do not write `pushEnabled=false`.

When the derived switch is on and the user turns it off:

- This is an explicit opt-out. Update `pushEnabled=false` and unregister/unsubscribe the current device.

## Legacy-user compatibility

For existing users whose App notification preference was default-on before Web Push was connected:

- Keep server preference true as product intent.
- Show the current-device switch off until the device completes permission + subscription + backend registration.
- Do not automatically request notification permission on page load.
- If permission is already granted and a previous local success marker exists, a silent readiness check can mark the switch on.
- If permission is `default`, require a direct user click.

## Verification checklist

- Test: `pushEnabled=true` + no current-device subscription renders the App Push switch off and does not call `updateNotificationPreferences({ pushEnabled: false })`.
- Test: clicking the off switch with `pushEnabled=true` calls subscription but does not redundantly call `updateNotificationPreferences({ pushEnabled: true })`.
- Test: switch turns on only after subscription returns `ok`.
- Test: subscription failure leaves switch off, captures/toasts the failure, and does not rollback the server preference.
- Test: turning off a ready device writes `pushEnabled=false` and unregisters the browser subscription.
- Build/typecheck the frontend after changing this path.

## Anti-conditions

Do not use this pattern if the switch is explicitly described as a pure account-level notification preference rather than current-device system notification readiness. In that case, keep the preference switch checked from server state and add a separate device-status row.

Do not make Web Push failure block in-app notifications. Station/in-app notification storage remains authoritative; Web Push is only a wake-up/reminder channel.
