# Frontend auth state-machine routing regressions

Use when a SPA login/onboarding flow regresses after a commit changes token consumption, authenticated-shell gates, or first-login routing order.

## Durable lesson

Do not fix a routing symptom by moving a backend response from a `pending` auth state into the formal authenticated state unless the product flow really intends shell gates to run immediately. In onboarding flows, `pending token` vs `formal auth token` is often the state-machine boundary that prevents global gates from preempting local setup order.

## Investigation path

1. Compare the parent commit and suspect commit, not only current code:
   - token consumer / store state changes
   - route screen navigation after login success
   - shell/global route gates
   - tests that assert authenticated vs pending state
2. Trace the exact backend response shape through the state machine:
   - `authStage`
   - `requiredStep`
   - token fields
   - user flags such as `hasPaymentPin`, `paymentPinSet`, `paymentPasswordSet`, `loginPasswordSet`
3. Write the route chain as state transitions, not just URLs:
   - pending token stored or formal token persisted?
   - `isAuthenticated` true or false?
   - `user` populated or `pendingLoginUser` populated?
   - which gate can observe that state?
4. Identify preemption hazards:
   - If `isAuthenticated=true`, global shell gates can run before local login/onboarding navigation.
   - If `isAuthenticated=false` with `pendingLoginToken`, global authenticated gates should not run; local auth screens must route based on pending state.

## Fix pattern

Prefer preserving the original state-machine boundary and adding the missing branch at the local decision point:

```ts
if (pendingLoginToken) {
  return pendingLoginUser?.hasPaymentPin === false ? "/pin-setup" : "/verify/pin";
}
```

Avoid replacing it with:

```ts
// Risky: makes shell gates run early and may reorder onboarding.
consumeAuthToken(responseWithRequiredStepSET_PAYMENT_PIN);
```

### Narrowing after review correction

If review shows the real defect is only "before navigating to payment-PIN verification, check whether a payment PIN exists", keep the fix scoped to the local route decision. Do **not** also change `isPendingPinAuth`, token persistence, or `SET_PAYMENT_PIN` authenticated-vs-pending semantics unless the user/product explicitly confirms that global shell gates must no longer run for that response.

Use this split when explaining impact:

- Local route precheck fix: `pendingLoginToken + pendingLoginUser.hasPaymentPin === false` routes to `/pin-setup` instead of `/verify/pin`; lowest blast radius.
- State-boundary fix: `SET_PAYMENT_PIN` remains pending rather than formal authenticated state; larger blast radius because it changes `isAuthenticated`, persisted token writes, and whether `/setup-login-pwd` shell gate can preempt.
- If `SET_PAYMENT_PIN` still enters formal auth and `user.loginPasswordSet === false`, `/setup-login-pwd` can still preempt `/pin-setup`; the local precheck alone does not address that class.

```

## Cold-restart / killed-app gap

When the bug says “user kills the app in the background during login, then reopens into a blank Home/account”, inspect persistence and hydration as part of the state machine, not as a separate UI bug.

Trace these sources separately:

1. Durable token store (`localStorage`, keychain, secure storage) — may survive app kill.
2. UI/user snapshot store (`sessionStorage`, in-memory Zustand/Redux, React context) — may be lost on cold restart.
3. Auth stage marker (`pendingLoginPin`, `pendingSetup`, `fullyAuthenticated`) — often missing entirely.
4. Startup shell gate — often checks only `!!token` / `isAuthenticated` and allows protected routes while `user === null`.
5. Bootstrap profile fetch — may be asynchronous and may swallow failures, leaving `token=true + user=null` visible as a blank authenticated shell.

Root-cause pattern:

```text
OTP/password accepted → token persisted durably → user still must complete PIN/setup
app killed → session/in-memory user and pending stage lost, durable token remains
restart → isAuthenticated = !!token, user = null
shell gate sees authenticated and renders Home; async /me failure is swallowed
```

Fix patterns, from strongest to weakest:

- Backend/token contract: do not issue full access+refresh tokens until login is complete; issue a scoped login-challenge token that can only call the next login-step endpoints.
- Frontend state contract: persist an explicit auth stage (`pendingLoginPin`, `pendingPinSetup`, `authenticated`) next to the token, and route cold starts by stage before protected shell render.
- Startup gate hardening: `isAuthenticated && user === null` must show a bootstrap/verification boundary, not Home; if `/me` fails or token scope is invalid, clear auth and return to login or pending-step route.
- Do not rely on local screen navigation after the login response as the only guard; navigation state is lost on process kill.

## Verification checklist

- Add a store test proving `SET_PAYMENT_PIN` / setup-required responses remain pending if the intended flow is payment-PIN setup before formal auth.
- Add a cold-start hydration test for `token present + user missing + pending stage present/missing` to prove Home is not rendered as a blank authenticated account.
- Add a pure route-resolution test for pending users with and without the setup flag.
- Verify both OTP and password login paths use the same route resolver.
- Verify bootstrap/profile-fetch failure is classified: either clear auth or keep the user at a non-Home loading/pending boundary; do not silently render protected pages with `user=null`.
- Run targeted store/routing tests and a type/build gate. If the build fails in an unrelated pre-existing area, report the exact unrelated file/error separately instead of claiming full build pass.

## Applicability / anti-conditions

Applies to frontend auth/onboarding routing bugs in SPAs with pending-login tokens and authenticated shell gates. Do not use this to override a product requirement that explicitly says login-password setup must precede payment-PIN setup; in that case the earlier shell-gate behavior may be correct.
