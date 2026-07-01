# UVISA Android PWA pending-login auth gate

Use when a UVISA C-end task reports that Android Chrome / PWA shortcut / “添加到主屏幕” opens the app home page after OTP/password login but before the post-login payment-PIN verification is completed.

## Applicability

- UVISA C-end React/PWA login flow.
- Android Chrome or OEM browser shortcut/install path is part of reproduction.
- User has passed the first login factor (email OTP or login password) and lands on `/verify/pin` or payment-password verification, but has not completed that PIN step.

## Anti-conditions

- Do not treat this primarily as a manifest/start_url/install-prompt bug. PWA is the reproduction entry; the security bug is usually auth-state promotion too early.
- Do not solve by forcing `manifest.start_url` to `/login` alone; that breaks valid fully-authenticated PWA relaunch behavior and does not fix direct `/home` or reload paths.
- Do not persist pending-login tokens in `localStorage` or mark `isAuthenticated=true` before the required PIN step has passed.

## Diagnostic model

Symptom pattern:
1. Clear Chrome storage.
2. Open UVISA web/PWA URL.
3. Enter email + OTP/password.
4. Reach the post-login payment-PIN verification screen.
5. Without entering PIN, use Chrome menu → add/install shortcut.
6. Open the desktop shortcut.
7. App shows home/assets page instead of login/PIN gate.

Likely root cause:
- OTP/password success handler consumes the full auth token immediately (`localStorage.auth_token`, `refresh_token`, `isAuthenticated=true`).
- Shell/auth gate only checks `isAuthenticated`, so a fresh PWA launch at `/` or `/home` treats the user as fully logged in.
- The post-login PIN page is only a route-level UX step, not an auth-state boundary.

## Preferred fix: staged authentication

Split login into explicit phases:

- `anonymous`: no access to protected routes.
- `pendingLoginPin`: first factor passed, PIN still required; may access only `/verify/pin`.
- `authenticated`: full session; protected routes allowed.

Implementation rules:
1. OTP/password success must branch before writing durable auth:
   - If the server says the current device is trusted and no PIN step is required, consume the token normally.
   - If the PIN step is required, store a pending-login payload only in `sessionStorage`/in-memory state and navigate to `/verify/pin`.
2. Pending-login payload may contain the temporary token/user data needed to call login-PIN verification, but it must not set `localStorage.auth_token` and must not set `isAuthenticated=true`.
3. `/verify/pin` must accept `pendingLoginPin` as its entry condition; it should not require full `isAuthenticated`.
4. The login-PIN verify request must send the pending token explicitly (for example a `tokenOverride`/challenge-token path) rather than relying on the global API client reading `localStorage.auth_token`.
5. On successful PIN verification, promote pending login to full auth: write `auth_token`/`refresh_token`, set `isAuthenticated=true`, clear pending state, then navigate to `/home`.
6. On back/cancel/failure-abandon, clear pending state and return to `/login`.
7. Shell/auth gate should fail closed:
   - `authenticated` → protected routes allowed.
   - `pendingLoginPin` → only `/verify/pin` allowed; any other route clears pending or redirects to login/PIN as product requires.
   - `anonymous` → only public routes allowed.
8. A fresh PWA launch with no completed auth must not restore pending-login across browser sessions. If pending state is absent or stale, route to `/login`.

## Backend hardening option

Frontend staged auth fixes the visible bypass, but the strongest model is backend challenge-token separation:

- OTP/password success on an untrusted device returns a `login_challenge_token`, not a full access token.
- That token can call only the login-PIN verification endpoint and cancellation/logout endpoints.
- Business APIs (`/wallet`, `/me`, `/transactions`, etc.) reject challenge tokens.
- PIN success then issues the real access/refresh tokens.

Use this when the task is security-sensitive or when direct API replay with a pre-PIN token would expose protected data.

## Verification checklist

Unit/component tests:
- OTP/password success requiring PIN does not write `localStorage.auth_token` or mark `isAuthenticated=true`.
- It sets `authPhase=pendingLoginPin` and routes to `/verify/pin`.
- `/verify/pin` can render under pending state but protected routes cannot render under pending state.
- PIN success promotes to authenticated and writes durable tokens.
- PIN cancel/back clears pending state and returns to login.
- Trusted-device login still enters `/home` normally.

Browser/PWA proof:
1. Clear Chrome storage.
2. Login through OTP/password until `/verify/pin`.
3. Do not enter PIN.
4. Add/install shortcut from Chrome menu.
5. Open shortcut from desktop/home screen.
6. Assert home/assets balances and wallet lists are not visible.
7. Assert the app returns to login or a safe re-auth/PIN gate.
8. Complete PIN, reopen shortcut, and assert fully-authenticated relaunch still works.

Evidence rule:
- For Lark closeout, include the exact Android/PWA shortcut path and visible target screen proof. A screenshot that only shows install success is insufficient; it must prove whether post-shortcut launch does or does not reach protected home content.
