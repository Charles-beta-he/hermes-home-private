# Proposal-only command registry checklist

Scope: use for lifecycle/control-plane systems where a UI or API should capture operator intent before any executor is allowed to mutate real workflow state.

Anti-conditions: do not add this layer for a simple read-only view, and do not use it to bypass an existing policy-gated command executor.

## Checklist

- Commands are written to the canonical ledger/store with `status = proposed` or equivalent.
- The API response states the command was not executed.
- Every newly proposed command emits an audit event.
- Idempotency keys dedupe retries without duplicating commands or audit events.
- High-risk commands create a human-approval request instead of executing.
- Snapshot/read APIs expose proposed commands and pending human approvals as projections.
- UI buttons that are not yet approved executors are labeled as propose/copy/record actions, never as if they performed the lifecycle mutation.

## Tests to add

- Low-risk proposal creates one command row and one audit event.
- Repeating the same idempotency key returns the original command and creates no new event.
- High-risk proposal creates a human-approval request and an approval-requested event.
- Proposed command response includes `not_executed` or the local equivalent.
- Snapshot includes command registry and human inbox projections.

## Stop point

Stop before implementing approve/reject/executor semantics unless the user has explicitly approved the policy model: who can approve, whether approval is single-use, expiry, evidence requirements, and the first execution whitelist.
