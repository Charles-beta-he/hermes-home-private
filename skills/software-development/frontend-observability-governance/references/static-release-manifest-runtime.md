# Static release manifest runtime pattern

Use this reference when a frontend/PWA release runtime needs to check version drift or bad releases, but the backend release-manifest API is not proven safe for public/login/auth-expired states.

## Problem shape

Symptoms:
- Login or pre-auth pages show `401 Unauthorized` for `/api/client-release/manifest`.
- Authenticated pages may also fail if the backend release API is behind a contract/auth path that is not yet stable.
- Telemetry endpoints such as `/api/client-release/events` can reintroduce the same auth problem even after switching the manifest read to a static file.

Root cause:
- Release-runtime is an app lifecycle concern, not a business/user action. If it depends on authenticated API state, it can pollute login, token-refresh, and auth-expired flows.

## Preferred client-side fallback

Make the browser runtime read-only until the API contract is explicitly proven safe:

```ts
fetch('/version.json', { cache: 'no-store', credentials: 'omit' })
```

Rules:
- Use `/version.json` for both pre-auth and post-auth phases.
- Do not call `/api/client-release/manifest` from the browser.
- Do not call `/api/client-release/events` from the browser unless the endpoint is confirmed safe and non-blocking for stale/expired tokens.
- Keep local release state, pending release, safe-boundary activation, boot watchdog, and chunk-load bad-release protection independent from backend auth.

## Verification checklist

- Login page loads with no `/api/client-release/manifest` network entry.
- Logged-in route also does not request `/api/client-release/manifest`.
- No `/api/client-release/events` request is produced by boot success, pending release, activation, bad-release marking, or deferred activation.
- `/version.json` returns `200`, `content-type: application/json`, and `Cache-Control: no-store`.
- Focus/visibilitychange events only refetch `/version.json` and do not touch authenticated release APIs.
- Tests assert that authenticated users still use `credentials: 'omit'` static fetch and that API client mocks (`api.get`, `api.post`) are not called.

## Anti-conditions

Do not use this as a permanent architecture claim if the product later needs user-targeted release rollout, staged cohorts, or backend-driven rollback. In that case, reintroduce a backend release API only after its auth behavior is proven for: public routes, stale tokens, expired sessions, refresh races, and logged-in routes.
