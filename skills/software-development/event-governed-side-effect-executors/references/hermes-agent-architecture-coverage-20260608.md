# Hermes agent architecture coverage sequence — 2026-06-08

This reference captures a concrete application of the event-governed side-effect executor ladder for Hermes self-architecture. Use as an example, not as a hardcoded global plan.

## Completed boundary sequence

The session advanced Hermes agent architecture coverage through scoped commits and verified tests:

1. Digest-bound rollback executor
   - Commit: `1255142ea Rollback taskpool and Kanban closeouts`
   - Consumes verified taskpool/Kanban closeout write events by exact request digest.
   - Restores only recorded previous_status after current-state check and readback.

2. Outbound outbox enqueue executor
   - Commit: `50e9dbe82 Enqueue governed outbound outbox items`
   - Consumes verified write/rollback event.
   - Appends pending Lark/Telegram outbox item.
   - Stores payload_hash and payload_summary only.
   - Requires target allowlist and no secret-like payload keys.
   - Does not send.

3. Outbound delivery authorization projection
   - Commit: `08be51b97 Project outbound delivery authorizations`
   - Consumes pending outbox item.
   - Requires elevated actor approval, exact outbox_id/payload_hash/target/channel, TTL, and readback.
   - Records authorized_pending_send.
   - Does not call Lark/Telegram APIs.

4. Telegram sender dry-run
   - Commit: `7a2bd2ded Dry run Telegram outbound delivery`
   - Consumes delivery authorization.
   - Requires channel=telegram and sender_mode=dry_run.
   - Validates Telegram payload contract: chat_id == target_id and text is non-empty.
   - Records platform_payload_hash and summary only.
   - token_read=false, send_executed=false.

5. Lark sender dry-run
   - Commit: `422752530 Dry run Lark outbound delivery`
   - Consumes delivery authorization.
   - Requires channel=lark and sender_mode=dry_run.
   - Validates Lark text payload contract: receive_id == target_id, msg_type=text, content.text non-empty.
   - Records platform_payload_hash and summary only.
   - token_read=false, send_executed=false.

6. Real sender preflight
   - Commit: `50177d0d6 Preflight real outbound senders`
   - Consumes Telegram/Lark `*_delivery_dry_run_verified` event.
   - Requires exact channel, delivery_authorization_id, dry_run_request_digest, outbox_id, target_id, payload_hash, and platform_payload_hash.
   - Requires dry-run freshness via `dry_run_max_age_seconds`.
   - Requires token_source to be a reference only (`env:`, `keychain:`, `secret-ref:`, `config-ref:`), while keeping token_read=false.
   - Requires sender_capability_enabled=false and send_executed=false.
   - Records `real_sender_preflight_verified`; real platform sender remains closed.

7. Real sender execution authorization
   - Commit: `46c237a27 Authorize real outbound sender execution`
   - Consumes `real_sender_preflight_verified`.
   - Requires elevated second approval, exact preflight request_digest, channel, target, payload_hash, platform_payload_hash, token_source, explicit sender_capability_requested=true, TTL, and evidence.
   - Records `real_sender_execution_authorized` with authorization_status=`approved_not_executed`.
   - token_read=false and send_executed=false; this is still no platform API call.
   - Idempotency uses the semantic authorization request while excluding evidence_refs, so replay evidence can differ without duplicate ledger rows.

8. Telegram real sender execution
   - Commit: `ee3909348 Execute authorized Telegram outbound sender`
   - Consumes `real_sender_execution_authorized` for channel=telegram.
   - Requires exact authorization_id, preflight_request_digest, outbox_id, target_id, payload_hash, platform_payload_hash, token_source, sender_capability_enabled=true, executor_mode=send, and evidence.
   - Recomputes platform_payload_hash before send and rejects drift.
   - Reads token only from the env token_source inside the sender boundary, embeds it in the Telegram Bot API URL, calls sendMessage, records message_id, and never stores token value.
   - Local HTTP harness verifies endpoint path/token placement, payload body, message-id extraction, CLI smoke, and rejection paths before any live send.

9. Lark real sender execution
   - Commit: `ded130ed8 Execute authorized Lark outbound sender`
   - Consumes `real_sender_execution_authorized` for channel=lark.
   - Requires exact authorization_id, preflight_request_digest, outbox_id, target_id, payload_hash, platform_payload_hash, token_source, sender_capability_enabled=true, executor_mode=send, receive_id_type allowlist, and evidence.
   - Recomputes platform_payload_hash before send and rejects drift.
   - Reads token only from the env token_source inside the sender boundary, sends it as an Authorization header with Bearer token to `/open-apis/im/v1/messages?receive_id_type=...`, records data.message_id, and never stores token value.
   - Local HTTP harness verifies path/query, Authorization header, payload body, message-id extraction, CLI smoke, and rejection paths before any live send.

## Files touched in the pattern

- `hermes_cli/event_governed_agents.py`
- `tests/hermes_cli/test_event_governed_agents.py`
- `docs/private/agent-architecture-coverage-plan-20260608.md`

## Verification pattern used

For each slice:

- Add RED tests first for the boundary.
- Implement executor function and CLI flags.
- Run focused tests for new cases.
- Update SSOT plan/decisions.
- Run:
  - `python3 -m py_compile hermes_cli/event_governed_agents.py tests/hermes_cli/test_event_governed_agents.py`
  - `PYTHONPATH=. python3 -m pytest -o addopts='' tests/hermes_cli/test_event_governed_agents.py -q`
  - a real temp smoke that exercises the full chain and inspects output fields;
  - `git diff --check`
- Make a scoped commit.

## Output invariants

For outbox / authorization / dry-run / preflight / execution-authorization stages:

- no platform API calls;
- no actual messages;
- no token reads;
- no raw platform payload persistence;
- hash + compact summary only for dry-runs;
- token_source is a reference only for preflight and execution authorization;
- sender_capability_enabled remains false for preflight;
- execution authorization may record sender_capability_requested=true but must still keep send_executed=false and token_read=false;
- readback_verified true for accepted paths;
- idempotent replay does not duplicate ledger/outbox rows.

For real sender execution stages:

- platform API calls are allowed only after exact execution authorization and explicit sender_capability_enabled=true / executor_mode=send;
- token_read=true is allowed only inside the sender boundary;
- token_value_stored must remain false;
- recompute platform_payload_hash immediately before sending and reject drift;
- record platform_message_id and failure classification, not raw token values;
- prove the sender with a local HTTP harness before live platform use.

## Channel contracts

Telegram dry-run payload:

```json
{
  "chat_id": "<target_id>",
  "text": "non-empty text"
}
```

Lark text dry-run payload:

```json
{
  "receive_id": "<target_id>",
  "msg_type": "text",
  "content": {"text": "non-empty text"}
}
```

## Next safe boundary after this session

After Telegram and Lark real sender execution are implemented and locally HTTP-harness verified, the next safe boundary is delivery verification/readback and retry governance, not broader worker/tool permission reopening.

Recommended next slices:

- consume `telegram_delivery_sent` / `lark_delivery_sent` by exact request_digest and platform_message_id;
- add platform-specific readback verification where available, or a governed acknowledgement projection when readback is impossible;
- classify failures into retryable transport failures, platform rejections, authorization/token failures, and payload contract failures;
- bind retries to the original execution authorization, payload hash, platform payload hash, target, and a bounded retry policy;
- preserve token non-persistence and require fresh authorization or unexpired authorization for retry;
- keep external agent tools/file edits/shell command capabilities closed unless a separate executor-specific boundary authorizes them.
