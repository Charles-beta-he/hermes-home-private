# Authorized local projection-state gallery

Applicability: the user asks to continue/advance after a read-only runtime UI projection or local contract slice has already landed, and the remaining safe work is still local, reversible, projection-only, and evidence-backed.

Use this when phrases like `推进至授权可推进项`, `继续推进`, or `safe authorized next items` follow a validated projection surface.

## Pattern

1. Re-read the active profile/ledger/task candidate enough to identify the current validated slice and hard authority boundaries.
2. Classify remaining work:
   - `safe-local-reversible`: projection/readback states, local fixtures, dashboard aggregates, tests, docs/ledger/profile receipts.
   - `needs-exact-authority`: taskpool lifecycle write/ingest, external dispatch, model routing with real providers, hardware/device actuation, deploy/push/publish, credential/payment/destructive actions.
3. Continue the `safe-local-reversible` ladder instead of stopping at the previous green slice.
4. For runtime UI/control-room surfaces, add state coverage before adding controls:
   - success/stable state;
   - gated/blocked human-authority state;
   - budget/error/known-limits state;
   - aggregate counts/distributions;
   - all side-effect flags false.
5. Verify with deterministic tests, runtime readback, and browser/visual readback when UI is involved.
6. Write evidence back to the scoped report/ledger/profile/task candidate and commit scoped changes when the repo workflow allows.
7. Stop only when every remaining item crosses a concrete authority/evidence boundary.

## Anti-conditions

Do not use this pattern to open executor routes, taskpool lifecycle writes, real model/provider routing, external sends, hardware/device actions, deploy/push/publish, credential entry, payment, or destructive operations. Those require exact target, rollback/abort path, receipt, and fresh readback.

## Verification checklist

- Projection endpoint/readback returns all added states.
- Dashboard aggregate reflects the added states.
- UI visibly shows the states as read-only rows/cards, not controls.
- Tests prove no execution/side-effect route was added.
- Browser/visual readback confirms no hidden execution controls are visible.
- Scoped report/ledger/profile/task records name the boundary and proof.
