# PWA Web Push: Unsupported Browser Channel Visibility

Use when a notification settings surface includes an App/PWA push channel but the current browser cannot enable OS-level Web Push.

## Core rule

Do not show an actionable "App Push" switch in browsers where Web Push cannot be enabled. A disabled-looking or on-looking switch next to a toast such as "current browser does not support PWA push" creates a contradictory state: the product preference appears editable even though the physical channel is impossible.

Keep the two-state-machine distinction from `pwa-web-push-preference-vs-subscription-debugging.md`, but adjust the visible channel list:

- User/server preference may still exist and default to `pushEnabled=true`.
- Physical capability determines whether the App Push channel control is rendered.
- Email/in-app/category preferences should remain visible and editable.
- Category toggles should not disappear just because the App Push control is hidden; they may still apply to email/in-app notification semantics.

## Implementation pattern

1. Reuse the app's support probe, for example `getWebPushSupport()`.
2. Compute capability at render time with a stable memo for the settings page.
3. Build the channel rows conditionally:

```ts
const pushSupport = useMemo(() => getWebPushSupport(), []);
const channels = useMemo(() => [
  ...(pushSupport.supported ? [{ key: 'pushEnabled', title: t('me.notif.pushTitle'), desc: t('me.notif.pushDesc') }] : []),
  { key: 'emailEnabled', title: t('me.notif.emailTitle'), desc: t('me.notif.emailDesc') },
], [pushSupport.supported, t]);
```

4. Keep toggle handlers for push intact for supported browsers; do not delete subscription logic.
5. If product needs an explanation, use a non-actionable diagnostic/info row, not a switch.

## Regression tests

- Mock supported Web Push: App Push row is visible and clicking it calls preference update + `ensureWebPushSubscription({ userInitiated: true })`.
- Mock unsupported Web Push: App Push row is absent, Email row remains, categories remain, and `ensureWebPushSubscription` is not called.
- Typecheck/build still pass.

## Anti-conditions

Do not apply this to native iOS/Android push settings in a native shell where the OS push capability is handled by native permission/token APIs.

Do not rewrite the server preference to `false` merely because the current browser is unsupported; hiding the physical channel control is a UI capability decision, not a user preference mutation.
