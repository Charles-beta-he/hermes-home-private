# UVISA Android PWA/Chrome shortcut + unfinished login root-cause pattern

Scope: UVISA C-end Android/Chrome tasks where scanning/opening the web app, entering email OTP, reaching the post-login payment-PIN page, then using Chrome "Install app" / "Add to home screen" / "Create shortcut" lets a new home-screen icon open the app home page before payment PIN is completed.

Anti-conditions:
- Do not apply to iOS Web Clip `.mobileconfig` profile install tasks; use `uvisa-ios-pwa-profile-install` for those.
- Do not treat this as only a manifest/start_url problem until auth state has been traced.
- Do not assume a home-screen icon is standalone PWA. Android/OEM Chrome can create a browser shortcut that reopens in Chrome with the address bar.

## Root-cause investigation order

1. Classify the launch container from evidence.
   - Standalone PWA: no browser address bar, `display-mode: standalone` or `navigator.standalone` style evidence, `appinstalled`/standalone launch proof.
   - Chrome/web shortcut: visible Chrome address bar, tab counter, overflow menu, or a Chrome bottom sheet wording such as "shortcut opens in Chrome".

2. Read served manifest from the real acceptance URL.
   - Check `start_url`, `scope`, `display`, manifest link in served HTML, and status/content-type.
   - For current UVISA evidence, `start_url: "/"` and `/` routes to `HomeScreen`, so launch URL alone can land on the home route.

3. Trace auth bootstrap before proposing a PWA fix.
   - In `auth.store.ts`, check when `localStorage.auth_token` / `refresh_token` are written.
   - Check whether OTP/password verification calls `consumeAuthToken()` before the post-login payment-PIN step.
   - Check store initialization: if `isAuthenticated` is derived from `!!localStorage.getItem('auth_token')`, a fresh shortcut launch can resurrect authenticated state.
   - Check ShellLayout route guard: if it gates only on `isAuthenticated`, `/` will render home when the token exists.

4. Verify the payment-PIN page's role in the state machine.
   - If `/verify/pin` is reached only after `isAuthenticated=true`, it is a logged-in follow-up route, not an authentication-completion gate.
   - Root cause wording should say: "unfinished payment-PIN verification is persisted as fully authenticated state" rather than "PWA start_url is wrong".

5. Use tests/history as evidence.
   - Existing tests that assert "verifyCode success sets token and isAuthenticated=true" prove this is modeled behavior, not a random runtime glitch.
   - `git blame` can separate older auth-state behavior from newer PWA install UI changes.

## Correct root-cause statement shape

Bad: "PWA start_url opens `/`, change it to `/login`."

Good: "The shortcut launches `/` (manifest start_url), and `/` is HomeScreen. It bypasses PIN because OTP success already wrote a full `auth_token` and set `isAuthenticated=true`; ShellLayout therefore allows `/` on fresh launch. The shortcut exposed an auth-state-machine bug: an incomplete post-login PIN step is modeled as fully authenticated."

## Verification checklist for future fixes

- OTP/password success that still requires login PIN must not write a full route-guard token into durable storage.
- Fresh launch from `/` with unfinished PIN must not render balances/wallet/home.
- Normal fully completed login must still let a standalone PWA/shortcut open home.
- Browser shortcut vs standalone PWA evidence must be reported separately from auth-state evidence.
