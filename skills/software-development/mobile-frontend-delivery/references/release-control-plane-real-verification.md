# Release Control Plane Real Verification Notes

Scope/applicability: use this for class-level verification of silent-release / OTA control-plane implementations where an authenticated admin frontend, backend release APIs, and client manifest endpoint must all be proven together. Anti-condition: skip for design-only mockups, ordinary changelog pages, or sessions where the user explicitly authorizes mock data screenshots.

This reference captures durable verification patterns. Do not store project credentials, OTP codes, concrete release IDs, or one-off environment secrets here.

## Separate three levels of evidence

1. **Render evidence**: the target admin surface renders under real auth, with no local mock rows or fake route data.
2. **Interaction evidence**: forms/drawers/tables accept input and dispatch real service calls.
3. **State evidence**: backend writes/read-backs succeed from the deployed target API and the manifest decision endpoint reflects the new state.

Do not collapse these. A screenshot of a form with real auth is useful render/interaction evidence, but not state evidence until the API write/read-back succeeds.

## Probe endpoint availability before declaring UI fully landed

For admin release-control surfaces, after logging in and before doing destructive or time-consuming UI steps, run a non-mutating probe against the exact endpoints the UI will use, for example:

- admin release list endpoint;
- public/client release manifest endpoint with a harmless platform parameter.

If the backend returns a structured not-found envelope, the frontend may be current while the backend target is older. Report this as an environment/deployment alignment blocker, not a UI bug and not a reason to mock data.

## Dev proxy alignment pitfall

A local admin dev server can still proxy API calls to a remote backend through environment variables or dev-server proxy defaults. Before judging read-back failures, identify the effective target:

- inspect the dev-server config / env default for the API proxy target;
- compare browser request URL and response body;
- check whether the target backend contains the newly compiled controller endpoints.

If the proxy target is a backend that has not deployed the new API, screenshots may prove UI rendering but cannot prove end-to-end release writes.

## Auth token details for browser probes

When probing from the browser console in admin SPAs, use the same token storage as the app's HTTP client. Some admin SPAs store refresh tokens in `localStorage` and access tokens in `sessionStorage`; do not assume `localStorage.token` exists.

Prefer app service calls when available. If probing manually, read the admin auth store/source first and use the access token key it uses. Never persist credentials or OTP codes in a skill or memory.

## Closeout language

When API deployment is missing, close out with an explicit matrix:

- real auth: pass/fail;
- target page render: pass/fail;
- create/edit modal render: pass/fail;
- backend endpoint availability: pass/fail with exact code/message;
- write/read-back: pass/fail or blocked;
- remaining action: deploy backend or point the dev proxy to a local backend with migrated DB.
