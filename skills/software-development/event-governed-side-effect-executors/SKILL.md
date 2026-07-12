---
name: event-governed-side-effect-executors
description: Use when designing or implementing agent/control-plane executors that may mutate lifecycle, adapter state, notification outboxes, or external platforms. Applies to Hermes self-architecture and similar systems where worker outputs must be proposals/evidence until explicit governed boundaries authorize side effects.
---

# Event-governed side-effect executors
## When to Use

- Use when the user's request explicitly matches `event-governed-side-effect-executors` or this skill's documented domain.
- Use when this skill is already selected by the Hermes skill router and the task still fits the current goal.
- Don't use for: adjacent workflows with a more specific skill, generic Q&A, or tasks that lack evidence for this skill's domain.


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

Detailed `Implementation checklist` guidance moved to `references/implementation-checklist.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
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
- Proactive nudges, sentinels, and scheduled agents default to local receipt-only operation. External delivery requires exact platform, target, payload hash, authorization TTL, rollback/stop path, and post-send readback; otherwise keep `deliver=local`, `no_agent=true`, success-silent behavior and record only local receipts.
- Preflight idempotency keys must include the drift-sensitive fields being protected (channel, authorization, dry-run digest, outbox, target, payload hash, platform payload hash, token source, capability flag). Do not key only on platform_payload_hash, or later drift/unsafe capability requests can be mistaken for replay.
- Execution authorization idempotency should digest the semantic authorization request, not volatile evidence_refs. Include preflight/channel/target/payload/platform hash/token_source/capability/TTL/actor/decision, but allow evidence_refs to differ on safe replay.
- For SSOT-to-derived-graph writers, a leaf-only symlink check, schema-string-only validation, or one-sided relation cleanup is insufficient. Bind one exact target, validate the complete owned graph, clean relations touching either owned endpoint, prove the server's real storage format, and require a current-byte independent APPROVE before calling the boundary certified. See `references/governed-local-knowledge-graph-projection.md`.

## Session-derived pitfall: broad internal authorization still needs staged local boundaries

Scope: internal agent/workflow executors that may mutate local lifecycle state, adapter ledgers, worker receipts, or agent lifecycle coverage. Applicability: a human grants broad/project-level authority but the executor still has multiple side-effect tiers. Anti-condition: do not use this to justify external sends, publish/deploy/push, destructive operations, payment/credential entry, broad fan-out, or arbitrary shell/tool execution.

When a user grants broad authority, do **not** collapse the ladder into arbitrary worker launch or adapter mutation. Turn the grant into explicit bounded runtime slices:

1. Bind authority to exact target nodes, `max_workers`, `max_turns`, `max_cost`, allowed toolsets, write boundary, rollback, and readback.
2. If the next authorized slice is a local runtime/domain-store bootstrap, require an exact packet naming allowed target files/stores and prohibited neighboring actions. Write only those targets, capture before/after hashes, append an idempotent receipt, and keep generated reconciliation plans `execute=false` until a later adapter/executor boundary is explicitly opened. Derive idempotency from stable semantic inputs, not volatile timestamps. See `objective-model-path-verification/references/autonomous-runtime-governance-p4-bootstrap.md`.
3. For agent-lifecycle coverage requests, first land local artifacts/runtime schemas/tests and mark existing agents as `covered`, `advisory`, `blocked`, or `certified`; do not treat coverage as permission to execute those agents.
3. Reject invalid authority values instead of silently coercing them. Examples: `max_workers=0`, `max_turns=0`, non-numeric limits, negative cost, empty toolsets, unsupported write boundaries, and non-ready/missing target nodes fail closed.
4. Prefer the next narrow boundary: local state-machine execution first, adapter-specific local receipts second, real adapter write-through third, live worker/subagent spawn later. Each layer consumes the previous layer's receipt by exact ID.
5. For task/mission-style integration, first write idempotent adapter receipts under the local ledger/state store with evidence refs, readback, and rollback metadata. Do not call adapter CLIs, schedulers, or external services from the receipt boundary.
6. Add tests for success, rejection, idempotent replay, and an isolated-home smoke that proves only the intended local receipt keys/tables changed.
7. Run independent review after implementation; treat findings such as silent limit coercion as blockers and add regression tests before committing.

## References

- `references/structured-semantic-authority-gates.md` — class-level pattern for structured semantic envelopes: separate route from execute/learning/side-effect authority, validate registry and nested field types, wire the same fail-closed gate through dispatch/lifecycle/force, and certify with non-empty negative fixtures plus latest-slice adversarial review.
- `references/read-only-control-console-projections.md` — pattern for projecting Mission/taskpool/control-plane ledgers into localhost dashboards safely: read-only DB access, public snapshot redaction, shell-quoted command drafts, Human Inbox mapping, and browser harness checks without hiding core UI.
- `references/local-control-console-capability-sessions.md` — pattern for moving localhost dashboards from read-only projection to short-lived, registered, audited capability sessions without exposing arbitrary execution or tokens in public snapshots.
- `references/hermes-agent-architecture-coverage-20260608.md` — session-specific sequence for the Hermes agent architecture coverage plan: rollback, outbox, delivery authorization, Telegram/Lark dry-runs, tests, and commits.
- `references/control-console-worker-execute-boundary.md` — Scope: localhost/operator approval consoles. Applicability: starting an existing governed background worker job after verified record/apply/dispatch ledgers and claimed readback. Anti-condition: creating a second worker system, arbitrary shell/tool execution, external sends, or direct done closeout.
- `references/singleton-safe-option-projections.md` — Scope: localhost/operator decision gates. Applicability: exactly one safe non-mutating option remains. Anti-condition: not approval, dispatch, worker execution, done closeout, external writeback, send, publish, or delete. Covers allowlisted singleton `auto_decision`, draft/preselect UI state, and consumer-side sanitization.
- `references/goal-workflow-governed-local-execution.md` — pattern for opening a Hermes goal/workflow executor one boundary at a time: exact ready-node selection, strict max_workers/max_turns/max_cost validation, local state/checkpoint receipts, rollback/readback, and taskpool/mission `authorized_not_written` handling before adapter write-through.
- `references/live-platform-sender-smoke.md` — live Telegram/Lark/Feishu smoke pattern: separate credential validity from receive-target authorization, record ledger evidence, and avoid token persistence.
- `references/project-level-high-risk-live-boundary-drain.md` — procedure for consuming broad project-level authorization into exact live boundaries (subagent smoke, taskpool lifecycle, mission report/dispatch, local cron heartbeat, exact push, destructive smoke) while stopping class-only external/deploy/destructive requests until exact targets exist.
- `references/high-risk-sequential-execution-drain.md` — procedure for ordered real-execution drain after a user asks to execute every high-risk class: execute exact/reversible smokes, record receipts, classify attempted-but-unverified sends correctly, and stop payment/credential/fan-out at hard gates when exact targets are missing.
- `references/high-risk-boundary-coverage-with-canary.md` — pattern for "100% coverage" requests over high-risk side-effect classes: implement a governance/readback coverage matrix, keep class-only real side effects closed, and use only a disposable local canary for destructive coverage when no exact production target exists.
- `references/high-risk-gate-control-plane.md` — pattern for requests to enable many high-risk classes at once: open local/fail-closed gates with receipts/readback, heartbeat and canary proof, while live sends/deploys/deletes/credential-payment stay exact-target gated.
- `references/external-jspace-real-open-boundary-drain.md` — **Scope:** scoped reference for agent/workspace projection layers being promoted toward real side-effect boundaries. **Applicability:** consume broad authority into exact local lifecycle write-through, local no-agent heartbeat, disposable canary, and a boundary matrix. **Anti-condition:** do not infer external/deploy/payment/fanout/worker targets from class-level authorization.
- `references/governed-local-knowledge-graph-projection.md` — Pattern for promoting a canonical file-backed knowledge corpus into a rebuildable local MCP graph: verify the real storage format, preserve foreign records, reconcile an owned namespace atomically, bind backup/rollback/readback receipts, and keep graph matches authority-neutral.
## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.
## Verification Checklist

- [ ] The current user request still matches this skill's trigger class.
- [ ] Required files, tools, commands, or external state were checked before action.
- [ ] Outputs, edits, or side effects were verified by readback or direct inspection.
- [ ] Boundaries, unresolved assumptions, and any deferred work were stated clearly.
