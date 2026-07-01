# UVISA first-login credential/PIN routing debug path

Applicability: UVISA C-end auth/login tasks where a newly opened/onboarded user logs in and sees an unexpected `请输入支付密码`, `/pin-setup`, or `/setup-login-pwd` screen, or where first-login login-password setup vs first-time Payment PIN setup vs returning-user untrusted-device PIN verification is ambiguous.

Anti-conditions: do not use this to change general payment-action verification (`/pay/verify/pin`) semantics. Do not assume all users without a trusted device should bypass PIN; this note is only about distinguishing first-time credential setup from returning-user untrusted-device PIN verification.

## Key distinction

There are three separate C-end auth surfaces:

1. First-time login-password setup: `/setup-login-pwd`
   - Screen: `src/screens/auth/SetupLoginPwdScreen.tsx`
   - Trigger: authenticated shell sees `user.loginPasswordSet === false`.
   - Expected before Payment PIN setup when the backend explicitly says the just-authenticated user has no login password.

2. First-time Payment PIN setup: `/pin-setup`
   - Screen: `src/screens/auth/PinSetupScreen.tsx`
   - Copy: `auth.setPin` / `auth.reenterPin`
   - Expected when the authenticated user has no UVISA payment PIN yet and `loginPasswordSet !== false`.

3. Returning-user / untrusted-device Payment PIN verification: `/verify/pin`
   - Screen: `src/screens/auth/VerifyPinOnLoginScreen.tsx`
   - Copy: `auth.untrustedDevicePinTitle` = `请输入支付密码`
   - Expected only when the user already has a Payment PIN and the just-authenticated browser is not backend-trusted.

## Frontend routing chain

Applicability: UVISA C-end auth shell/login handoff in `uvisa-app-2.0` only, when diagnosing first-login credential/PIN route selection. Anti-conditions: do not generalize these route names, field defaults, or component paths to other projects; re-verify current source before changing behavior.

First inspect the render-time shell gate in `src/App.tsx`. It runs before protected pages mount. The effective order is login-required, login-password setup, then Payment PIN setup:

```ts
const needsLoginPwdSetup = isAuthenticated && user?.loginPasswordSet === false && loc.pathname !== '/setup-login-pwd';
const needsPinSetup = isAuthenticated && user?.loginPasswordSet !== false && user?.hasPaymentPin === false && loc.pathname !== '/pin-setup';
```

Then inspect the login handoff in `src/screens/auth/VerifyCodeScreen.tsx` after OTP/password login: pending login token routes to `/verify/pin`; otherwise `user.hasPaymentPin === false` routes to `/pin-setup`; trusted browsers go `/home`; untrusted returning users go `/verify/pin`.

Therefore:

- unexpected `/setup-login-pwd` means the authenticated store has `user.loginPasswordSet === false`.
- unexpected `请输入支付密码` for a new user means the frontend did not see `user.hasPaymentPin === false`, or the response was held as a pending login token for verification.

## Recent-regression commit pitfall

Applicability: UVISA C-end auth regressions where a recent commit appears to have introduced forced `/setup-login-pwd`, `/pin-setup`, or `/verify/pin` routing. Anti-conditions: do not blame a merge-tip commit just because it is newest; compare path-scoped diffs and route-feeding state transitions.

A commit can make a pre-existing shell gate start firing without touching the gate itself. In the June 2026 test-branch regression, `/setup-login-pwd` had already existed, but the relevant auth-store change reclassified `requiredStep === 'SET_PAYMENT_PIN'` responses:

- before: `authStage === 'PENDING_PIN'` was treated as pending login, leaving `isAuthenticated=false` and routing through `/verify/pin` pending-token flow;
- after: `requiredStep === 'SET_PAYMENT_PIN'` is not pending verification, so `consumeAuthToken(...)` stores a real authenticated user; if that user has `loginPasswordSet === false`, the pre-existing shell gate redirects to `/setup-login-pwd`.

Debug recipe:

1. Compare the route gate and the state normalizer separately. The route code may be unchanged while its inputs changed.
2. For the suspect commit, inspect `src/stores/auth.store.ts` around `isPendingPinAuth`, `normalizePaymentPinFlag`, and `consumeAuthToken`.
3. Inspect the commit's added/changed tests; tests that assert `isAuthenticated=true`, `pendingLoginToken=null`, `loginPasswordSet=false`, or `hasPaymentPin=false` often reveal intended route activation.
4. If ordinary existing users are forced into setup, capture the actual `/auth/verify` or `/auth/login-with-password` response and sessionStorage `auth-store` before changing frontend defaults.

## Killed-app / cold-start blank Home pitfall

Applicability: UVISA C-end reports where OTP/password login has succeeded, the app is killed before completing `/verify/pin` or first-login setup, and reopening lands on `/home` with blank account/profile. Anti-conditions: do not apply to ordinary post-login `/me` display bugs where login completed and only a specific profile field is missing.

Current contract checkpoints discovered from source:

- Backend `AuthController` OTP and password login return full `accessToken`, `refreshToken`, `token`, `currentDeviceTrusted`, and `user` in `tokenBody(...)`; there is no separate login-temporary token in this path. Verify current source before changing because this is a security/state-machine boundary.
- Frontend `consumeAuthToken(...)` writes `auth_token` and `refresh_token` to `localStorage` and sets `isAuthenticated=true` as soon as `/auth/verify` or `/auth/login-with-password` succeeds.
- Frontend persisted auth store uses `sessionStorage`, while the token truth source on init reads `localStorage`. On WebView/PWA cold restart, `localStorage` can survive while `sessionStorage`/in-memory `user` is gone, producing `isAuthenticated=true` + `user=null`.
- `ShellLayout` only gates on `!isAuthenticated` and setup flags on `user`; with `user=null`, `needsLoginPwdSetup` and `needsPinSetup` are false, so `/home` can render before profile recovery.
- `useAppBootstrap`/`fetchProfile` failures are swallowed, so a failed `/me` does not necessarily bounce the user out of the blank authenticated shell.

Debug recipe:

1. Capture storage at cold start: `localStorage.auth_token`, `localStorage.refresh_token`, `sessionStorage.auth-store`, and any pending-login marker.
2. Check the current URL and whether it is protected, public, or wildcard-routed to Home.
3. Inspect `src/stores/auth.store.ts` init and `consumeAuthToken(...)` before assuming HomeScreen is the defect.
4. Inspect `src/App.tsx` shell gates for `isAuthenticated=true && user=null` behavior.
5. Inspect whether `/me` succeeds with the token issued before PIN verification; if it fails, verify whether the frontend clears auth or silently leaves Home mounted.
6. Compare OTP and password paths; both should follow the same stage model.

Preferred fix direction:

- Best: backend issues a scoped login-challenge token before PIN/setup completion; full access+refresh is issued only after the final login step.
- Acceptable frontend hardening: persist an explicit auth stage such as `pendingLoginPin`/`pendingSetup`/`authenticated` and route cold starts by that stage before rendering protected pages.
- Minimum stopgap: if `auth_token` exists but `user` is missing, hold a startup verification boundary; on `/me` failure clear auth or route back to the correct pending login step, not Home.

## Auth store normalization pitfall

Inspect `src/stores/auth.store.ts` `normalizePaymentPinFlag(data)`:

- `needsPinSetup === true` => false
- `hasPaymentPin` / `paymentPinSet` at top level => use it
- `data.user.hasPaymentPin` / `data.user.paymentPinSet` => use it
- otherwise default true

The default true protects existing users on older backends that omit the field, but it also means a new-user login response that omits explicit `false` will be treated as "has PIN" and then fail into `/verify/pin` on untrusted devices.

## Backend contract checkpoints

For C-end login token responses, inspect `api/api-public/src/main/java/com/uvisa/api/pub/AuthController.java`:

- `tokenBody(...)` should include `currentDeviceTrusted` and `user: profileOf(res.user())`.
- `profileOf(User u)` should derive:
  - `hasPaymentPin = u.getPaymentPinHashInternal() != null && !blank`
  - `paymentPinSet = hasPaymentPin`
  - `loginPasswordSet` from `login_password_hash`

For profile refresh, inspect `api/api-public/src/main/java/com/uvisa/api/pub/MeController.java` `me()` and ensure it returns the same credential flags.

For PAD/onboarding creation, inspect identity user insert paths such as:

- `api/api-admin/src/main/java/com/uvisa/api/admin/pad/PadService.java` `upsertIdentityUserFromSession`
- `api/api-admin/src/main/java/com/uvisa/api/admin/pad/PadOnboardingCardService.java`

A normal newly opened user should not have `payment_pin_hash` inserted by onboarding; the login/profile response should therefore expose `hasPaymentPin=false`.

## Minimal evidence to collect

1. Capture the actual login response for the affected user:
   - `/api/auth/verify` for OTP login, or
   - `/api/auth/login-with-password` for password login.
2. Confirm whether the response has:

```json
{
  "data": {
    "currentDeviceTrusted": false,
    "user": {
      "loginPasswordSet": false,
      "hasPaymentPin": false,
      "paymentPinSet": false
    }
  }
}
```

3. If `hasPaymentPin/paymentPinSet` are absent or not false, treat it as backend contract/deployment drift or a missing-login-path field, not a PinSetupScreen bug.
4. If they are false but routing still goes `/verify/pin`, inspect auth store persistence/hydration and `normalizeUserProfile` merge behavior.

## Fix guidance

Preferred backend-side fix: every token-issuing login path must include explicit `user.hasPaymentPin=false` and `user.paymentPinSet=false` for users whose `identity_users.payment_pin_hash` is NULL/blank. Also keep `/api/me` aligned.

Frontend hardening option: support explicit `needsPinSetup: true` from backend. Avoid blindly changing the default of missing Payment PIN flags from true to false unless old-backend existing-user behavior has been accounted for, because that can force returning users into `/pin-setup`.

## Verification

- Targeted frontend tests around `auth.store`, `PinSetupScreen`, and `VerifyPinOnLoginScreen` are useful for guarding routing semantics.
- Backend targeted tests should assert token/profile contract includes `hasPaymentPin=false` when `payment_pin_hash` is null. If backend compile is blocked by unrelated duplicate files or missing classes, report that blocker separately; do not treat it as proof the auth contract path failed.
