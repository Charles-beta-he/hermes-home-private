# SPA global runtime hook 401 on public auth routes

Use when a React/Vue/mobile-H5 app shows 401 errors on login, verify, PIN setup, password reset, or other public auth pages after adding a global boot/runtime hook.

## Symptom pattern

- The visible page is a public/auth surface (login, email verify, PIN setup, password reset).
- DevTools shows a newly introduced global/runtime endpoint returning 401, often repeatedly on boot, route change, focus, or visibilitychange.
- The business action on the page may still work, so the 401 looks like unrelated noise.

Example classes of endpoints:
- release manifest / version sync
- feature flag bootstrap
- notification/session probes
- telemetry/event sync
- app-shell/runtime policy fetch

## Root-cause checklist

1. Confirm the failing request is not the visible business request.
2. Locate the global hook mounted near the app root.
3. List every trigger: initial boot, route change, login success, logout, foreground/focus, visibilitychange.
4. Check whether the endpoint requires auth today. Do not assume a runtime/manifest endpoint is public just because conceptually it could be.
5. Check whether the hook guards public routes and unauthenticated state before calling the protected endpoint.
6. Inspect the response interceptor: a protected global probe can trigger token refresh, auth-expired events, redirects, or monitoring noise even when the user is intentionally logged out.

## Preferred fix pattern

- Add a route/auth gate around the global hook call, not a broad interceptor special-case.
- Define explicit public auth routes (`/login`, `/verify`, `/verify/pin`, setup/reset routes as applicable).
- Do not call protected runtime APIs while unauthenticated on those routes.
- Keep the runtime hook active after login and on protected safe boundaries.
- If pre-auth runtime policy is required, split the contract: static/public manifest for unauthenticated boot, authenticated API manifest after login.

## Regression tests

Add hook/component tests for both sides:

- Unauthenticated public route:
  - no runtime manifest/probe call
  - no activation/reload side effect
  - no boot-success marker/report call
- Authenticated protected route:
  - boot sync still runs
  - login/user switch sync still runs
  - route safe-boundary activation still runs

## Anti-conditions

- Do not silence all 401s globally; page-level auth errors still matter.
- Do not mark the endpoint as public without verifying backend/security expectations.
- Do not rely on screenshot-only evidence; pair the UI observation with source tracing and a regression test.
