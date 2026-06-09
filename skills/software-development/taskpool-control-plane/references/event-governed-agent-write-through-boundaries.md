# Event-governed agent write-through boundary pattern

Use this when evolving Hermes/taskpool from projection-only agent architecture into real write-through execution while preserving the canonical ledger as SSOT.

## Proven staged chain

Do not jump from worker output directly to external adapter mutation. Use a digest-bound chain where every later step consumes the exact prior ledger record:

1. `start_bounded_runtime_run` records the run only.
2. External worker proposal is recorded as an artifact pointer/hash, not a fact.
3. Multi-model certification promotion binds to the proposal artifact hash and reviewer evidence.
4. Elevated done authorization binds to the certification hash and TTL.
5. Ledger-local canonical fact mutation appends `canonical_lifecycle_status=done` only after consuming the done authorization.
6. External adapter write intent maps the canonical done fact to an allowlisted adapter target and records readiness/readback/rollback plans.
7. External adapter write authorization requires an elevated actor, unchanged adapter/ref/status/canonical digest/intent digest, TTL, and evidence.
8. Narrow executor performs exactly one adapter-specific write and immediate read-back verification.

This preserves the rule: workers propose; certification/human gates authorize; canonical ledger mutates first; adapter projections write only after a separate explicit authorization.

## Boundary progression that worked

- Local-file adapter harness: consume write authorization, update a fixture `adapter_state_path`, read back, prove idempotency.
- Taskpool note closeout: consume taskpool authorization, reject slug/path/symlink escapes, mutate only markdown frontmatter `status: done`, append an audit marker, read back status.
- Kanban DB closeout: consume kanban authorization, reject DB symlink/missing-table/missing-task drift, mutate only one SQLite `tasks.status` cell to `done`, read back status.
- Digest-bound taskpool/Kanban rollback: consume a previously verified closeout write event by exact write `request_digest`, restore only that event's recorded `previous_status`, check the current state first, read back, and prove idempotency.

Each executor should return both `write_executed` and `readback_verified`, and append `*_write_verified` or `external_adapter_rollback_verified` only after read-back succeeds. On mismatch, append a mismatch event instead of claiming success.

## Implementation checklist

- Start every slice with RED tests for the next boundary; keep previous boundaries projection-only until the new executor is explicit.
- CLI must expose a separate action and JSON payload per boundary; do not overload a projection command to execute writes.
- Require exact `authorization_id`, `intent_id`, adapter, target_ref, target_status, and digest matches.
- Require non-expired authorization TTL and non-empty evidence refs.
- For rollback, require a verified write event, exact write request digest, `target_status == previous_status`, current-state drift check, non-empty rollback evidence, and idempotent replay that does not re-append ledger.
- Ensure idempotent replay: a repeated successful authorization/intent/target tuple returns the existing verified event without a second mutation or ledger append.
- For filesystem-backed targets, reject symlinks in the target chain and final target before writing.
- For SQLite-backed targets, use parameterized SQL only, check the expected table/row before mutation, and update one status cell only.
- Always run a full CLI smoke using a temporary ledger and temporary fixture target, not only direct function tests.

## Stop boundaries

A narrow closeout executor does not grant broad adapter authority. Keep these disabled until separate slices authorize them:

- arbitrary taskpool lifecycle mutations;
- arbitrary Kanban SQL/schema changes;
- Lark/Telegram real sends;
- broad reopen or arbitrary rollback targets not bound to a verified write event;
- external agent tools, shell commands, or file edits;
- memory/skill/provider/cron changes from worker output.

## Documentation wording

Say precisely what is enabled: e.g. `taskpool note closeout write-through` or `Kanban DB closeout write-through`. Do not claim full adapter write-through or autonomous task completion unless every adapter and rollback path is actually implemented and verified.