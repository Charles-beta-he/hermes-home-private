# Auth step-up token exchange debugging

Applicability: frontend/backend auth flows where a login response can be a pending/limited session and a second factor (PIN, device trust, MFA, OTP) must exchange it for a formal authenticated session.

Anti-conditions:
- Do not apply to ordinary post-login transaction/payment PIN checks that should only return `{success:true}` and continue a payment flow.
- Do not assume a project-specific endpoint returns formal tokens unless both client and server code prove that contract.

## Debugging path

1. Split the flow into two explicit token classes:
   - pending/step-up token: allowed only to call the step-up endpoint; must not be written as `auth_token` or treated as authenticated shell state.
   - formal token: persisted to auth storage, marks `isAuthenticated=true`, and clears pending state.
2. Trace the routing decision immediately after primary login:
   - no required credential setup -> home if trusted, otherwise step-up screen;
   - credential setup required -> setup route, not verification;
   - pending token + credential already set -> step-up verification route.
3. Trace the step-up screen request:
   - exactly one call on full input (guard duplicate effects / rapid input);
   - Authorization uses the pending token;
   - body carries a route/type/purpose value that distinguishes login-device from transaction checks when the endpoint is shared.
4. Compare client and server response contracts before judging UX behavior:
   - client success criteria should require a formal `token`/`accessToken` plus user/profile data before calling the formal-token consumer;
   - server endpoint used by login-device step-up must actually return that formal token payload;
   - if server returns only `{success:true}`, the root cause is contract mismatch, not a second PIN verification.
5. Verify with targeted tests at all three boundaries:
   - service test: step-up call includes pending-token Authorization and parses formal token payload;
   - store/state test: pending token is not persisted, formal token is persisted, pending state is cleared;
   - routing test: new/first-login users who need setup route to setup, while returning users with existing PIN route to verification only when needed.

## Pitfalls

- A shared `/pin/verify` endpoint may serve both transaction PIN checks and login-device token exchange. Treat them as separate contracts even if the URL is the same.
- A route named "verify payment PIN" does not imply two verifications. Count network calls and state transitions: setup route vs verify route vs transaction PIN route.
- If the frontend has tests proving token exchange but the backend implementation still returns only `{success:true}`, do not claim the flow is integrated; call out the FE/BE contract gap.
- Global authenticated-shell guards should not re-run the login-device PIN check after formal token exchange. They should only handle setup gates or protected-route redirects; otherwise a successful step-up can loop back into verification.
