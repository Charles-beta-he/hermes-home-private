# Approval workflow map boundary for lifecycle control planes

Use this reference when a Hermes lifecycle/control-plane feature has already reached a proposal-only command registry and needs to advance without enabling real mutation.

## Pattern

After proposed commands and human approval requests exist, add an approval-decision lifecycle before any executor:

1. Record decisions in the canonical ledger, not in the dashboard/task board.
2. Allow only explicit terminal decisions such as `approved` and `rejected`.
3. Treat same-decision retries as idempotent.
4. Reject conflicting second decisions fail-closed.
5. Emit audit events for decisions, e.g. `HumanApprovalGranted` and `HumanApprovalRejected`.
6. Return an explicit `not_executed` execution state from decision APIs.
7. Keep the underlying command in `proposed` or equivalent non-executing state until an executor phase is separately approved.

## Snapshot/projection shape

Extend the read-only snapshot with a human inbox split:

- pending approvals
- recent decided approvals
- counts for both

Then add a ledger-derived workflow map. Do not import an external workflow engine as a second fact source.

A minimal safe command lifecycle graph:

```text
command_proposed
  -> approval_requested
    -> approval_decided
      -> executor_eligible
```

`executor_eligible` should remain explicitly disabled until policy approval. Surface the blocker as data, for example:

```json
{
  "node_id": "executor_eligible",
  "reason": "executor_disabled_phase_boundary"
}
```

## OpenSpec-inspired guardrails

When adopting workflow-graph ideas from spec/artifact systems such as OpenSpec, absorb the class-level graph checks rather than the tool dependency:

- reject duplicate node IDs
- reject missing dependencies
- reject dependency cycles
- compute ready/blocked from the canonical ledger
- treat files/artifacts as evidence, not fact source

## Stop condition

Stop before implementing any lifecycle-affecting executor or write-through adapter unless the user has explicitly decided:

- executor whitelist
- approver role matrix
- approval expiration
- evidence requirements by risk level
- rollback/escape path
- adapter mutation contract

## Verification checklist

- RED test: approval decision API/function is missing.
- GREEN test: approve records a decision event and leaves command non-executed.
- GREEN test: reject records a decision event and leaves command non-executed.
- GREEN test: same decision retry does not create duplicate events.
- GREEN test: conflicting second decision fails.
- RED/GREEN test: workflow schema validation rejects duplicates, missing deps, and cycles.
- GREEN test: snapshot includes workflow ready/blocked state and executor-disabled blocker.
- Smoke test with a temporary home/ledger: propose L2 -> approve -> snapshot reports pending 0, decided 1, blocked at executor.
