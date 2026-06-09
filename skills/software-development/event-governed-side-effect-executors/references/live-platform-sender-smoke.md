# Live platform sender smoke notes

Use these notes when moving an event-governed notification sender from local HTTP harness verification to a live platform smoke.

## Preconditions

- The code boundary already passed local HTTP harness tests for endpoint path/query, token placement, payload body, response parsing, idempotency, and token non-persistence.
- A full governed ledger chain is available: runtime start/source event -> outbox enqueue -> delivery authorization -> channel dry-run -> real sender preflight -> real sender execution authorization -> real sender execution.
- The human has explicitly authorized a live smoke for the target platform.

## Telegram live smoke pattern

- Use the configured home chat/channel only when it is already the authorized Telegram target for the current chat.
- Keep the target identifier out of summaries; report only a redacted/length-only handle if needed.
- Resolve the bot token from an env token_source at the final sender boundary only.
- Expected accepted result fields:
  - `accepted_as=telegram_delivery_sent`
  - `runtime_boundary=telegram_real_sender_executed`
  - `send_executed=true`
  - `token_read=true`
  - `token_value_stored=false`
  - `platform_response_ok=true`
  - `platform_message_id=<id>`
- Store the evidence ledger path in the SSOT, not the token or raw credential.

## Lark/Feishu live smoke pattern

- App credentials or a successful tenant_access_token exchange prove credential validity only; they are not receive-target authorization.
- Do not infer a Lark `open_id`, `chat_id`, `user_id`, `email`, or `union_id` from old task evidence or unrelated files.
- If no explicit receive target exists in the current request/config, stop before real send and report: credentials valid, target missing.
- When an explicit receive target is available, bind it through the same outbox target_allowlist, delivery authorization, dry-run platform payload hash, preflight token_source, execution authorization, and final sender request.

## SSOT update pattern

- Record the live smoke as a new slice or evidence line with accepted_as/run_status/runtime_boundary, token non-persistence, platform message id, and evidence ledger path.
- If a platform was not sent because a target was missing, record the boundary as a governance stop, not a failure of the sender code.
