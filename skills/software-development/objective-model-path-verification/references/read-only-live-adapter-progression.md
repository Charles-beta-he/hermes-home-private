# Read-only live adapter progression

Use when a governed/local runtime workflow has a dynamic evidence contract and the user authorizes the next safe slice, but external execution, dispatch, purchase, navigation, publish/deploy, or destructive actions remain closed.

## Pattern

1. Keep the boundary explicit: `read_only` adapter only; no execution semantics.
2. Convert live source output into the existing evidence contract, not directly into an action.
   - evidence id
   - source kind/name
   - source URL or receipt
   - observedAt
   - expiresAt / TTL
   - confidence
   - outcome hint: pass/warn/fail/blocked
3. Treat `pass` as clearing only that evidence slice. Do not imply neighboring gates pass.
   - Weather pass is not road open.
   - Road open is not driver state/fuel/ticket pass.
   - Ticket availability is not purchase authority.
4. Fail closed on source failure, missing required fields, stale TTL, malformed timestamps, or no matching forecast/record.
5. Add fixture tests for pass/warn/fail/blocked and missing-source cases before relying on a live smoke.
6. Run a minimal live readback smoke only for endpoint shape/reachability. Do not call it certification for future execution.
7. Export the adapter through the package boundary and update test/runtime module mappers for downstream apps that import source TS directly.
8. Record an SSOT note with boundaries kept closed and the next smallest adapter slice.

## Verification checklist

- Targeted adapter tests pass.
- Full package tests and build pass.
- Any downstream app importing the package still passes targeted regression.
- Live readback shows endpoint shape only, with source URL/receipt captured.
- SSOT JSON/markdown readback remains valid.

## Anti-conditions

Do not use this pattern to perform ticket purchases, navigation execution, external sends, publish/deploy/push, credential entry, or destructive cleanup. Those require exact target, rollback/escape hatch, and post-action readback authorization.
