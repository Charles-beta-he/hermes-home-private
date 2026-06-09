# Digest-bound closeout and rollback executors

Session-derived pattern for moving a governed taskpool/agent architecture from projection-only adapter writes into narrow real mutations without losing SSOT/evidence boundaries.

## Control-plane chain

Use this ordered ledger chain; do not skip directly from worker output to adapter mutation:

1. start runtime run
2. external worker proposal artifact pointer/hash
3. multi-model certification promotion bound to proposal hash
4. elevated done authorization bound to certification hash + TTL
5. ledger-local canonical fact mutation (`canonical_lifecycle_status=done`)
6. external adapter write intent with readiness/readback/rollback plan
7. elevated external adapter write authorization with unchanged adapter/ref/status/digests + TTL
8. adapter-specific closeout executor
9. optional digest-bound rollback executor

## Closeout executor contract

A closeout executor is not broad adapter authority. It must be adapter + operation allowlisted and perform exactly one mutation.

### Local-file harness
- consume valid write authorization
- update fixture `adapter_state_path` only
- read back status
- use this before touching real projections

### Taskpool note closeout
- adapter must be `taskpool`
- target_ref must be a safe slug: non-empty, not `.`/`..`, no `/` or `\\`, not ending `.md`
- reject symlink ancestor directories and final-note symlink
- ensure resolved note parent stays inside `taskpool_tasks_dir`
- mutate only frontmatter `status: done`
- append a concise audit marker
- read back frontmatter status

### Kanban DB closeout
- adapter must be `kanban`
- DB path must exist, be regular, and not be a symlink
- require `tasks` table and target task row
- use parameterized SQL only
- mutate only `tasks.status` for the target id
- read back `SELECT status FROM tasks WHERE id=?`

## Rollback executor contract

Rollback is allowed only as a recovery for a previously verified closeout event.

Require:
- adapter in `{taskpool, kanban}`
- exact run_id / authorization_id / intent_id / target_ref match
- exact verified write event request digest (`write_request_digest`)
- target_status equals the write event's recorded `previous_status`
- current state equals `expected_current_status` before mutation
- non-empty rollback evidence refs

Perform:
- taskpool: mutate only frontmatter status back to recorded previous_status, append rollback marker, read back
- kanban: parameterized `UPDATE tasks SET status=? WHERE id=?`, read back

Idempotency:
- if an identical rollback verified event already exists, return it with `idempotent_replay=true`
- do not mutate again and do not append another ledger row

## Tests and smoke verification

Use TDD per slice:

1. RED tests for success + rejection paths before implementation.
2. GREEN implementation with separate CLI flag and JSON payload for the new boundary.
3. Full focused test suite.
4. CLI smoke using temp ledger and temp fixtures (markdown note and/or SQLite DB), not only direct function tests.
5. `py_compile` and `git diff --check`.
6. Update the architecture SSOT document and scoped commit.

Minimum rejection coverage:
- missing authorization / missing verified write event
- expired or drifted authorization
- request digest drift
- target/status drift
- missing evidence refs
- symlink/path escape for taskpool
- symlink/missing table/missing row for Kanban
- current-state mismatch before rollback

## Outbound outbox contract before real senders

For Lark/Telegram, do not jump directly from closeout/rollback to platform APIs. Add an enqueue-only outbox executor first.

Require:
- source event must be a verified write/rollback event, e.g. `taskpool_note_write_verified`, `kanban_db_write_verified`, or `external_adapter_rollback_verified`
- exact `source_request_digest` must match the source ledger event
- channel allowlist should be explicit and small, e.g. `{telegram, lark}`
- `target_id` must be present in the request's target allowlist
- `evidence_refs` must be non-empty
- reject symlink outbox files or symlink parent directories
- reject payloads containing secret-like keys such as `token`, `password`, `secret`, `api_key`, `authorization`, or `credential`

Perform:
- append one JSONL outbox item with `delivery_status=pending` and `send_executed=false`
- persist only `payload_hash` plus a bounded `payload_summary` (<= 240 chars); do not persist full payload text or credentials in the ledger/outbox
- read back the outbox row by `outbox_id`/`payload_hash`/`delivery_status`
- append a ledger event such as `outbound_outbox_item_enqueued`

Idempotency:
- identical `run_id + source_request_digest + target_id + payload_hash` returns the existing outbox event with `idempotent_replay=true`
- do not append another outbox row or ledger row on replay

## Outbound delivery authorization projection

Before any real Lark/Telegram sender, add a projection-only delivery authorization boundary. This is still not a sender: it must not call platform APIs, read tokens, or produce a message-id claim.

Require:
- a prior `outbound_outbox_item_enqueued` ledger event for the same `run_id`
- exact `outbox_id` match to the outbox event `request_digest`
- outbox JSONL readback by `outbox_id`
- elevated actor role and `decision=approved`
- `channel` in the delivery allowlist (currently `{telegram, lark}`)
- `channel` present in both the outbox ledger event and the outbox readback row
- exact `target_id` and `payload_hash` match in both ledger event and outbox readback row
- outbox `delivery_status=pending`
- unexpired `expires_at` TTL and non-empty delivery authorization evidence refs

Perform:
- append a ledger projection such as `outbound_delivery_authorization_projected`
- set `delivery_status=authorized_pending_send`
- set `send_executed=false`
- keep `readback_verified=true` only when the outbox JSONL row was read back and matched
- derive a stable `delivery_authorization_id` from `run_id + outbox_id + channel + target_id + payload_hash`

Idempotency:
- identical `delivery_authorization_id` returns the existing authorization with `idempotent_replay=true`
- do not append another ledger row on replay

Rejection coverage:
- non-elevated actor, non-approved decision, expired/invalid TTL
- missing or drifted outbox event/readback row
- channel not allowlisted or not present in outbox item
- target_id/payload_hash drift
- outbox no longer pending
- missing evidence refs

Next boundary after delivery authorization:
- add a channel-specific sender dry-run first; require exact `delivery_authorization_id`, `outbox_id`, `payload_hash`, `target_id`, and channel
- for dry-run, do not read tokens or call platform APIs; emit only platform payload hash / request preview artifact
- only after that add a real sender that calls the platform API and records message_id/readback verification
- keep sender disabled by default until real credentials/targets and platform readback are available
