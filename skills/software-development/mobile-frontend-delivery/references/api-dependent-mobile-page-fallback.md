# API-dependent mobile page fallback verification

Applicability: mobile web/PWA/WebView pages whose visible template branch depends on async API data, route query state, Vuex/session state, or native bridge data.

Anti-conditions: do not treat this as proof that real backend data or role-specific business states are accepted. It only proves the page avoids blank/permanent-loading states when dependencies are missing, slow, or malformed.

## Pitfall

A page can pass static route/import tests while still rendering blank at runtime if its initial state matches no template branch. Common shape:

```vue
<div v-if="role == null">...</div>
<div v-if="role != 0 && role != null">...</div>
```

with `role: 0` in `data()`. Before the API returns, neither branch renders. If the API hangs or local test env lacks the backend, the user sees a blank page.

## Required defensive pattern

1. Initialize state to a branch that has visible UI, or add explicit loading/empty/error branches.
2. Prefer an ordered template chain:
   - `v-if="loading"` visible loading shell/nav
   - `v-else-if="hasCompleteDataForStateA"`
   - `v-else-if="hasCompleteDataForStateB"`
   - `v-else` visible empty/error fallback
3. Guard computed branches with normalized booleans, not raw sentinel values.
4. Treat malformed API response as `{}` / `[]` rather than allowing property access to throw.
5. Catch optional secondary API calls so they do not blank the primary page.
6. For local/mobile acceptance, add a bounded hang fallback timer when an API may never resolve in a disconnected harness. Clear it on success and `beforeDestroy`/unmount.
7. Add a focused regression test that asserts the initial sentinel is not a non-rendering value and that loading/error fallback text/classes exist.

## Verification checklist

- Static regression test: initial state, branch guards, fallback branch, catch paths, and optional timeout are asserted.
- Build passes.
- Browser smoke with simulated auth/session state proves the route renders non-empty before API data.
- If API hangs or is unavailable, the page leaves loading and shows a visible fallback.
- If product acceptance requires successful role/data states, perform a separate real-backend or fixture-backed smoke and label the boundary.

## Reporting boundary

Say: "route no longer blanks under missing/hanging API; real API success states still need environment acceptance" unless the real backend data path was also verified.
