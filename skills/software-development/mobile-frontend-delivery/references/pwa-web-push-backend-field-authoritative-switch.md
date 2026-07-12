# PWA Web Push switch when a backend field is authoritative

## Applicability

Use when backend/product owners state that an existing API field such as `pushEnabled` is the authoritative “App Push subscribed/enabled” state, not merely a local browser readiness hint. This pattern applies only after readback proves the field is exposed through the current frontend API contract.

## First verify the field is already exposed

Before adding a new status endpoint, inspect the existing preference/status API end to end:

1. Backend persistence/query reads the candidate enabled field.
2. Controller/API maps it into the public response, commonly as `pushEnabled`.
3. Frontend service already reads that response, commonly through a notification-preferences endpoint.
4. Settings-screen tests cover the response shape and switch rendering.

If these are present, the frontend can proceed without a new backend endpoint.

## Switch semantics

When the backend field is authoritative, render the switch from server state:

- backend enabled value truthy / `pushEnabled=true` => switch checked.
- backend enabled value falsey / `pushEnabled=false` => switch unchecked.

Do not additionally require local `Notification.permission`, `PushSubscription`, or local storage success markers for `checked`; that would contradict the backend contract and can make a server-enabled user appear off.

## Activation order

If product says “enabled = subscribed”, avoid optimistic writes:

1. User clicks an off App Push switch.
2. Run user-initiated Web Push subscription/registration first.
3. Only after subscription/register returns `ok`, write the backend enabled field true.
4. If subscription fails, show/capture the failure and do **not** write the backend enabled field true.

This preserves the meaning of the backend enabled bit as “subscribed/enabled”, not just “the user tried to enable”.

When turning off:

1. Write the backend enabled field false.
2. Unregister/unsubscribe the current browser subscription.
3. Keep in-app notifications unaffected.

## Preference-gate pitfall

Existing subscription helpers may refuse to subscribe when the backend enabled field is false, to respect opt-out during silent ensures. Settings activation is different: the user has just clicked to enable and the backend field has not been set true yet. Add an explicit option such as `ignorePreferenceGate` or a separate settings-activation path so the helper can subscribe before marking the backend field on.

Do not use this bypass for silent bootstrap/background ensures.

## Verification checklist

- Backend/API readback: confirm the existing API exposes the backend field; do not infer from a DB screenshot alone.
- Test: backend enabled true renders the App Push switch checked.
- Test: clicking from off calls subscription first and only then writes enabled true.
- Test: subscription failure does not write enabled true and does not false-rollback unrelated state.
- Test: clicking from on writes enabled false and unregisters subscription.
- Run the Web Push unit tests and a production build/typecheck.

## Anti-conditions

Do not apply this when the backend field is strictly an account-level notification preference and not a subscription state. In that case use `references/pwa-web-push-preference-device-ready-switch.md` and/or add a separate device-status row.

Do not let Web Push failure block or delete in-app notification records; the in-app notification center remains the message truth source.
