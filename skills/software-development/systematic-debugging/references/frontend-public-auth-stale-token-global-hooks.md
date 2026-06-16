# Frontend public-auth stale-token global hooks

Use this when a login / OTP / forgot-password / public support page shows 401 / `10002 登录态已失效` even though the visible user flow is public.

## Symptom pattern

- UI is on a public auth page such as `/login`, `/verify`, `/forgot-login-pwd/*`, or public customer support.
- Network shows a protected request such as `/api/cs/session`, `/api/me`, `/api/wallet/*`, `/api/notifications/*`, followed by `/api/auth/refresh`.
- Response body may be canonical backend envelope: `{ code: 10002, message: "登录态已失效", data: null }`.
- The page may redirect back to `/login` after the interceptor clears tokens.

## Root-cause checklist

1. Separate visible user action from root-level mounted components.
   - In React, hooks execute before `if (hide) return null` branches matter for side effects.
   - A component can be visually hidden but still trigger a hook that fires API calls.
2. Search root/shell components for global widgets and bootstraps:
   - floating customer-service FABs
   - notification/SSE bootstraps
   - wallet/home preloads
   - profile/session heartbeats
   - release/version runtimes
3. Check whether the guard is based only on `localStorage.auth_token`.
   - A stale token makes “has token” true even on public pages.
   - The request then 401s, the axios interceptor attempts `/auth/refresh`, and stale refresh failure turns into auth-expired redirect.
4. Reproduce minimally by seeding stale tokens and a persisted auth store, then loading the public route:
   - `localStorage.auth_token = stale`
   - `localStorage.refresh_token = stale`
   - persisted auth store says `isAuthenticated=true`
   - navigate to `/verify` or `/login`
   - inspect resource entries for protected endpoints and refresh.

## Fix pattern

Prefer preventing the protected hook from mounting on public routes:

```tsx
export default function CustomerServiceFab() {
  const loc = useLocation();
  const hide = isPublicPath(loc.pathname) || loc.pathname === '/me/customer/chat';
  if (hide) return null;
  return <CustomerServiceFabInner />;
}

function CustomerServiceFabInner() {
  const active = useHasActiveSession();
  if (!active) return null;
  return <Link to="/me/customer/chat" />;
}
```

Do not write:

```tsx
const active = useHasActiveSession();
const hide = isPublicPath(loc.pathname);
if (hide || !active) return null;
```

The hook has already fired by the time the `hide` branch returns.

Alternative: make hooks accept an explicit `enabled` flag and ensure they no-op before starting side effects. The wrapper split is usually simpler and avoids conditional-hook mistakes.

## Public support vs authenticated chat model

When a login page has a “contact support” entry, split the product surfaces:

- `/login` / `/verify` button → public support hub (`/me/customer`): static contact info, FAQ, service hours, safe offline help; no session/history API.
- `/me/customer` → public by default; if logged in it may show a “continue chat” CTA, but it should not eagerly probe protected chat state unless explicitly desired and guarded.
- `/me/customer/chat` → authenticated-only; protect at route level (for example `<RequireAuth><ChatScreen /></RequireAuth>`) and allow `/api/cs/session` only there or in authenticated app surfaces.

Anti-condition: if the support page intentionally provides unauthenticated live chat, build a separate anonymous/public session API and do not reuse the authenticated `/api/cs/session` endpoint behind stale-token guards.

## Verification

- Unit test: render the root/global component on `/verify` with stale token present and assert protected services are not called.
- Browser proof: public auth page resource list contains static assets and `/version.json`, but no protected endpoints such as `/api/cs/session` and no `/api/auth/refresh`.
- If a 401 remains, identify the request name first; do not assume the selected DevTools request is the only trigger.