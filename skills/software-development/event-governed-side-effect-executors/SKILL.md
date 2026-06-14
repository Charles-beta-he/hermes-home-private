---
name: event-governed-side-effect-executors
description: Use when designing or implementing agent/control-plane executors that may mutate lifecycle, adapter state, notification outboxes, or external platforms. Applies to Hermes self-architecture and similar systems where worker outputs must be proposals/evidence until explicit governed boundaries authorize side effects.
---

# Event-governed side-effect executors

## When to use

Use this skill when a task asks to add, review, or harden an agent executor that could:

- mutate canonical lifecycle facts;
- write through to adapters such as taskpool notes, Kanban DBs, Lark, Telegram, or local harness files;
- enqueue or send notifications;
- rollback previous side effects;
- consume outputs from external agents or multi-model reviewers.

Do not use this heavy flow for ordinary read-only Q&A, simple local scripts with no side effects, or one-off UI/content work.

## Core principle

Open capability in narrow, evidence-backed runtime boundaries. A worker/model/proposal is never automatically a fact. Each boundary must consume a verified prior event, bind to immutable digests, check TTL/allowlists/current state, perform at most one scoped side effect, immediately read back, and append the result to a canonical ledger.

## Boundary ladder pattern

1. Report/proposal only
   - Record coverage/gap report or external proposal artifact.
   - No lifecycle mutation, adapter writes, or platform calls.

2. Certification / elevated authorization projection
   - Require evidence-backed reviewers/quorum or elevated actor approval.
   - Bind to exact artifact hashes and expire via TTL.
   - Still no write-through.

3. Ledger-local fact mutation
   - Consume unexpired authorization.
   - Append canonical fact in the local ledger only.
   - External adapter write-through remains closed.

4. External adapter intent and authorization
   - Map canonical fact to an allowlisted adapter/ref/status as an intent.
   - Add readiness, readback, rollback plan, evidence refs.
   - Elevated actor authorizes exact intent digest under TTL.

5. Harness/local write-through
   - First open local fixture or harness write-through.
   - Mutate exactly one safe target.
   - Read back immediately and record verified/mismatch.

6. Adapter-specific write-through
   - Open real adapters one at a time, e.g. taskpool note, Kanban DB.
   - Reject arbitrary SQL, schema mutation, broad reopen, or unrelated lifecycle changes.

7. Digest-bound rollback
   - Consume a previously verified write event by exact request digest.
   - Restore only the recorded previous status/value.
   - Check current state before rollback and read back after.

8. Outbox before platform sends
   - Convert verified write/rollback events to pending outbox items.
   - Store payload hash/summary only; do not store secrets or payload bodies.
   - Require target allowlists, safe paths, and no secret-like keys.

9. Delivery authorization before sender
   - Consume pending outbox item.
   - Require exact outbox_id, channel, target_id, payload_hash, TTL, elevated actor, and readback.
   - Still do not call platform APIs.

10. Channel dry-run before real send
   - Consume delivery authorization.
   - Validate channel-specific platform payload contract.
   - Record platform_payload_hash and compact summary only.
   - Explicitly keep send_executed=false and token_read=false.

11. Real sender preflight while capability remains disabled
   - Consume a fresh `*_delivery_dry_run_verified` event.
   - Bind exact delivery_authorization_id, outbox_id, target_id, payload_hash, platform_payload_hash, and dry-run request digest.
   - Require token_source to be a reference only (`env:`, `keychain:`, `secret-ref:`, `config-ref:`); do not read it.
   - Require sender_capability_enabled=false and append `real_sender_preflight_verified`.
   - This is still no-send/no-token-read; it proves readiness before the final capability-opening boundary.

12. Real sender execution authorization
   - Consume `real_sender_preflight_verified`.
   - Require elevated second approval, exact preflight request_digest, channel, target, payload hash, platform payload hash, token_source, requested capability, TTL, and evidence.
   - Keep token_read=false and send_executed=false; this grants a short-lived future execution capability but still does not call platform APIs.
   - Use a semantic request digest for idempotency so evidence_refs can differ on replay without duplicating the authorization.

13. Real sender execution
   - Only after dry-run, preflight, and execution authorization gates exist.
   - Use an explicit capability flag or operator-controlled switch (`sender_capability_enabled=true`, `executor_mode=send`).
   - Read token only inside the narrow sender boundary, ideally from a token_source reference resolved at execution time; never persist the token value.
   - Recompute platform_payload_hash immediately before sending and reject drift from the prior dry-run.
   - Exercise real HTTP send code with a local HTTP harness before any live platform send; assert URL/path, auth header/token placement, payload body, message-id extraction, and no token persistence.
   - Record message id / platform readback / failure classification.

## Implementation checklist

For every executor function and CLI path:

- Define accepted input event type(s) and exact digest fields.
- Normalize and validate IDs, channel, target, status, and mode.
- Require evidence_refs for accepted paths.
- Require TTL for authorizations.
- Reject symlink paths and unsafe parent paths for file/DB/outbox targets.
- Reject secret-like payload keys such as token, password, secret, api_key, authorization, credential.
- Store hashes/summaries instead of raw payloads or credentials.
- Write idempotently: replay of the same digest should not duplicate side effects.
- Append structured ledger records with schema_version, run_id, run_status, accepted_as, runtime_boundary, request_digest, blocked_reasons, and readback fields.
- Add CLI flags for each boundary and JSON payload input.
- Add tests for success, rejection, idempotency, and CLI smoke.
- For localhost control consoles that need “one-click opening”, implement it as a short-lived capability session over a registered allowlist, not as arbitrary execution. Keep tokens out of public snapshots, bootstrap auth through a same-origin HttpOnly cookie when possible, require `capability_allowed(action)` on every registered side-effect endpoint, and for `mission.decide` run a real mission-backed E2E when authorized: create a minimal handoff, prove pre-arm/invalid-answer rejection, submit the exact valid option, read back mission resume, stage-report the evidence, and reset the public snapshot to unarmed/no-token before committing. If the console must be resident, supervise it via a local process manager such as macOS LaunchAgent, keep per-session action tokens out of the persistent service plist, and verify UI/API readiness separately. See `references/local-control-console-capability-sessions.md` and `process-lifecycle-control-plane/references/macos-launchagent-local-console.md`.
- Scope: localhost/operator consoles with approval-request or operator-decision controls. Applicability: when UI copy implies a decision, adapter mutation, or executor action landed. Anti-condition: do not use for external sends, arbitrary shell/tool execution, or destructive production mutation. Do not ship visual-only buttons for this class; advance through explicit layers: draft-only → local decision ledger → adapter apply/readback → executor dispatch → governed worker execute. For “full landing” / “全盘推进” requests, do **not** treat the current safe stop as the completion target. Model the production-grade chain first, then keep adding the next narrow capability boundary until the intended user-visible effect is genuinely carried to the safe boundary. If the user asks for “一次性开放”, implement one short-lived arm that opens the registered capability set, but preserve per-boundary validation, audit, idempotency, current-state readback, and explicit non-goals. For Human Inbox resume flows, record/apply/dispatch/worker-execute should be separate registered actions that can be called in one UI chain; `taskpool.executor.dispatch` means governed claim-and-handoff, while `taskpool.worker.execute` means starting the existing agent-team background worker job after verified claimed readback, not arbitrary shell, external sends, or direct done closeout. Scope: localhost/operator approval consoles with mixed local-decision and executor capabilities. Applicability: the same capability session can contain execution-capable actions while the currently selected request is only a safety gate, evidence gate, or other non-execution approval projection. Anti-condition: do not apply this to ordinary non-gated action buttons with no side-effect ladder. Do not foreground a permission-scope matrix in the Human Inbox just because these capability boundaries exist; the operator experience should reduce manual intervention by showing the next action, not a wall of permissions. Capability/safety status belongs at the concrete action point, in receipts/readback, or in a secondary diagnostics panel. If a permission/status display is explicitly required, make it request-aware: safety/Execution Flow Gate selections must still block dispatch/worker even when the short-lived capability session is armed, and UI allowed flags must bind to both capability and request context (for example `capabilityAllowed && !isSafetyGate`). See `references/control-console-human-inbox-write-through.md` and `references/control-console-worker-execute-boundary.md`.
- For option/decision controls, keep UI state event-driven rather than local-draft-driven. Unauthorized clicks may show a transient global explanation, but must not render as selected or persist a selected-looking card state. Once a choice is recorded in the local ledger and read back through the snapshot, use that ledger event as the source of truth, lock/disable the target’s alternate choices, and reject conflicting writes for the same target unless an explicit override/supersede event type exists. A plain idempotency key on `(target, option)` is insufficient: also reject `(same target, different option)` to avoid silent “latest wins” semantics. Scope: localhost/operator decision controls. Applicability: a gate has exactly one safe, non-mutating next step. Anti-condition: do not auto-approve, dispatch workers, mark done, send/publish/delete, or write external adapters. For singleton safe gates, let the task/control-flow layer emit `auto_decision`, but keep it as draft/preselect state only: consumers must sanitize to an allowlist, require upstream `auto_decision` to match the single sanitized option, and never synthesize execution authority from a singleton. See `references/control-console-option-event-locking.md` and `references/singleton-safe-option-projections.md`.
- For real senders, add a local HTTP server smoke that proves the production HTTP path without hitting the external platform; verify auth header/token placement, endpoint path/query, payload body, response parsing, and token non-persistence.
- Before a live platform smoke, verify credentials and target separately: credential/token exchange proves only credential validity, while the receive target must come from the current user request, configured home target, or an explicit allowlist for this run.
- Run py_compile, focused/full tests, a real temp smoke, and git diff --check.
- Update the SSOT architecture/coverage document before committing.
- Make a scoped commit.

## Test matrix

Minimum tests per boundary:

- success path records expected accepted_as/run_status;
- rejected unverified source;
- rejected drift in digest/target/channel/status;
- rejected expired authorization;
- rejected secret-like payload;
- rejected unsafe path/symlink for file-backed targets;
- idempotent replay produces no duplicate write;
- CLI smoke returns the same accepted_as;
- real temp smoke proves no fabricated output.

## Pitfalls

- Do not combine authorization, dry-run, preflight, and real send in one step.
- Do not call Lark/Telegram APIs from outbox, delivery authorization, dry-run, or preflight projections.
- Do not store raw platform_payload, message body secrets, tokens, or API responses unless that exact real-sender boundary explicitly allows it.
- Do not treat rollback as broad reopen; bind rollback to a verified prior write event and recorded previous state.
- Do not commit with stale SSOT lines like `Commit: this scoped commit` unless the current commit is about to be made; replace previous slices with real commit hashes.
- Keep channel-specific contracts separate: Telegram payloads use chat_id/text and the bot token is embedded in the Telegram Bot API URL; Lark text messages use receive_id/msg_type/content.text and the tenant token is sent as an `Authorization: Bearer <token>` header to `/open-apis/im/v1/messages?receive_id_type=...`.
- Do not treat Lark/Feishu app credentials, tenant token exchange success, or historical open_id/chat_id evidence as authorization to send to a recipient. Live Lark sends require an explicit receive target for the current run; without it, stop at credential validation and report the governance stop.
- Preflight idempotency keys must include the drift-sensitive fields being protected (channel, authorization, dry-run digest, outbox, target, payload hash, platform payload hash, token source, capability flag). Do not key only on platform_payload_hash, or later drift/unsafe capability requests can be mistaken for replay.
- Execution authorization idempotency should digest the semantic authorization request, not volatile evidence_refs. Include preflight/channel/target/payload/platform hash/token_source/capability/TTL/actor/decision, but allow evidence_refs to differ on safe replay.

## References

- `references/read-only-control-console-projections.md` — pattern for projecting Mission/taskpool/control-plane ledgers into localhost dashboards safely: read-only DB access, public snapshot redaction, shell-quoted command drafts, Human Inbox mapping, and browser harness checks without hiding core UI.
- `references/local-control-console-capability-sessions.md` — pattern for moving localhost dashboards from read-only projection to short-lived, registered, audited capability sessions without exposing arbitrary execution or tokens in public snapshots.
- `references/hermes-agent-architecture-coverage-20260608.md` — session-specific sequence for the Hermes agent architecture coverage plan: rollback, outbox, delivery authorization, Telegram/Lark dry-runs, tests, and commits.
- `references/control-console-worker-execute-boundary.md` — Scope: localhost/operator approval consoles. Applicability: starting an existing governed background worker job after verified record/apply/dispatch ledgers and claimed readback. Anti-condition: creating a second worker system, arbitrary shell/tool execution, external sends, or direct done closeout.
- `references/singleton-safe-option-projections.md` — Scope: localhost/operator decision gates. Applicability: exactly one safe non-mutating option remains. Anti-condition: not approval, dispatch, worker execution, done closeout, external writeback, send, publish, or delete. Covers allowlisted singleton `auto_decision`, draft/preselect UI state, and consumer-side sanitization.
- `references/live-platform-sender-smoke.md` — live Telegram/Lark/Feishu smoke pattern: separate credential validity from receive-target authorization, record ledger evidence, and avoid token persistence.
