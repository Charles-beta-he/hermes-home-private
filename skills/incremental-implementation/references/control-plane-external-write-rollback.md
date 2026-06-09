# Control-plane external write rollback slice

Session-derived pattern from enabling a first governed rollback/reopen consumer after a narrow external adapter write-through.

## Durable lesson

When a previous slice deliberately stored `rollback_available=false` / `rollback_reopen_enabled=false`, enabling rollback later is not just adding a new rollback endpoint. The same slice must update the prior write-run schema defaults, CHECK constraints, inserted row values, emitted event payloads, rollback snapshots, API responses, UI indicators, and docs so every projection agrees that completed write runs are now rollbackable.

A real review blocker can hide in this metadata drift even when the rollback executor itself works.

## Safe rollback/reopen gates

For a control-plane rollback consumer after real write-through:

1. Bind rollback to a completed write run, not just an external target id.
2. Require exact command execution digest equality with the write run.
3. Require admin-or-stronger actor role unless local policy says stronger.
4. Restrict adapter and operation explicitly, e.g. `adapter_name == kanban` and prior `operation == closeout`.
5. Validate rollback snapshot identity before mutation:
   - snapshot adapter equals write-run adapter
   - snapshot external ref equals write-run external ref
   - snapshot target status is in a bounded allowed set
6. Require current external target state to still match the rollback precondition, e.g. task is currently `done` before reopening.
7. Restore only the bounded fields captured in the rollback snapshot.
8. Record rollback in three places:
   - rollback run table with UNIQUE write-run key for idempotency
   - external adapter observation for post-rollback state
   - audit event for rollback execution
9. Return existing rollback run on ordinary retry; fail closed on retry with a different digest.
10. Keep broader boundaries explicitly disabled: no taskpool write-through, no conflicting evidence override, no multi-adapter expansion unless separately authorized.

## Verification bundle

Minimum verification before commit:

- Focused tests for happy path, digest mismatch, insufficient role, unsupported adapter, target drift, missing inputs, and idempotent retry.
- Plugin/API test that executes write-through via dashboard API, then rollback via dashboard API, and reads back external target state.
- Smoke with temporary home: closeout → intent → review → authorization → preflight → write → rollback; verify target transitions `ready -> done -> ready` and ledger counts.
- Static scan for secrets, shell execution, eval/exec, unsafe deserialization, and unsafe SQL string formatting.
- Independent review focused on metadata consistency and boundary expansion.

## Review checklist

Ask reviewers specifically:

- Do prior write-run rows/events/snapshots now correctly advertise rollback availability?
- Can a stale digest, second valid target, or edited snapshot reopen the wrong external target?
- Does the rollback path remain adapter-specific rather than silently becoming a generic write executor?
- Are taskpool write-through and evidence override still impossible from the new API/UI path?
