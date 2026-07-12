# Identity-, Auth-, and Generation-Guarded Async State

Use this pattern when a request result may update UI state after the active entity, authentication context, or request order has changed. Symbol/id equality alone is insufficient.

## Core invariant

A callback may commit state only when all three dimensions still match:

1. **Identity** — the entity/symbol/account captured at request start is still active.
2. **Authority context** — the user/session/auth state that authorized the request is still current.
3. **Generation** — no newer request or context transition has superseded it.

```ts
type RequestContext = {
  entityId: string;
  authenticated: boolean;
  generation: number;
};

function mayCommit(request: RequestContext, current: RequestContext) {
  return (
    current.authenticated &&
    request.entityId === current.entityId &&
    request.generation === current.generation
  );
}
```

## Why identity-only guards fail

An equality check such as `requestedId === activeId` blocks direct A→B late responses but still admits:

- **Logout, same identity:** an authenticated request for A returns after logout while A remains selected.
- **ABA:** request A1 starts, UI switches A→B→A, then stale A1 returns after newer A2.
- **Overlapping mutations:** an older mutation response returns after a newer mutation and rewrites state or emits a stale success toast.

## Implementation checklist

1. Keep current entity, auth state, and monotonic generation in refs/state visible to callbacks.
2. Invalidate generation whenever entity or auth context changes.
3. Capture the generation in every query and mutation invocation.
4. Invalidate older work before issuing a newer state-changing mutation.
5. Require entity + active auth + exact generation in both query and mutation success handlers.
6. Apply the same guard before secondary effects such as success messages, cache writes, navigation, or analytics—not only before `setState`.
7. Preserve the anonymous boundary: unauthenticated actions should navigate/request login without firing the authenticated API.
8. Prefer over-invalidation to stale acceptance. An abandoned render incrementing a generation can cause a harmless refetch; accepting a stale privileged result is worse.

## Deterministic verification matrix

At minimum, model or execute these transitions:

| Case | Expected result |
|---|---|
| A request, then switch to B, late A | reject |
| authenticated A request, logout, late A | reject |
| A1, switch B, switch A and start A2, late A1 | reject |
| A2 returns under current A/auth/generation | accept |
| mutation M1, then M2, late M1 | reject including stale toast |
| anonymous action | login navigation only; zero protected API calls |

Do not accept a source-string harness alone as complete proof. Pair static wiring checks with a deterministic callback-order model or deferred-promise runtime test. A verifier should actively probe logout/same-identity and ABA; direct A→B alone is not sufficient.

## Anti-conditions

- A one-shot request whose owner is guaranteed to unmount and whose cancellation is enforced may use cancellation instead, but verify that the underlying client actually prevents callbacks.
- Generation guards do not replace backend idempotency or authorization.
- Do not copy auth tokens into evidence or test fixtures; model authority as a boolean/epoch.
