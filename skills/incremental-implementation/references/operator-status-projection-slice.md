# Operator status projection vertical slice

Use this when a local operator/mobile/status UI must surface real control-plane lifecycle state without opening executor or external adapter writes.

## Slice order

1. Start with a read-only source contract and fixtures: health/selfcheck, dispatch dry-run, and bounded lifecycle list/summary.
2. Add a failing test that proves lifecycle state is not hidden: blocked count, active task todos, blocked needs-human cards, and warning-vs-blocked priority.
3. Implement the narrow projection only. Do not add lifecycle mutation, reconcile, claim, dispatch, external writes, or force-done to the status endpoint.
4. Run a live smoke against the endpoint with the same headers/device/session shape the UI uses.
5. If the full lifecycle list is large, fix the projection boundary by adding a bounded summary path before raising process buffers. The durable fix is to keep raw task bodies/evidence out of the UI service hot path and emit only lifecycle fields the projection consumes.
6. When a temporary buffer increase was used to unblock smoke, ratchet it back after the bounded summary lands. Add a regression test that the UI service does not invoke the raw list command directly, then live-smoke under the lower buffer.
7. Do not convert the transient buffer failure into a permanent negative rule about the tool.
8. Wire the mobile/UI merge layer so high-signal blocked items cannot be displaced by generic warning noise.
9. Verify with targeted tests, build/typecheck, live smoke, full local gate, residual-process readback, and a scoped commit.

## Acceptance evidence

- Contract test for projection source.
- UI merge test preserving blocked items over warnings.
- Live endpoint smoke returning the expected schema.
- Full local gate or equivalent relevant suite.
- Clean working tree / scoped commit.

## Boundaries

This pattern is read-only/status-only. Real lifecycle writes, external adapter writes, notifications, deploys, and completion transitions need their own governed slices and readback.
