# Telegram reliable delivery — enterprise patterns

Use when Telegram polling recovers but outbound replies can still be lost or when designing a production-grade pending outbox / redelivery path for Hermes Gateway.

## Applicability

- Applies to Hermes Gateway outbound Telegram delivery reliability after proxy/network turbulence, process restart, rate limits, or transient send-path degradation.
- Applies when the goal is production semantics: no silent loss, bounded retries, duplicate suppression, operator visibility, and clear privacy/TTL policy.
- Anti-condition: do not use this to justify blindly retrying ambiguous Telegram send timeouts; a timeout may have reached Telegram and retrying can duplicate messages.
- Anti-condition: do not persist private message or assistant reply content unless the user explicitly approves a content-storage policy and TTL.

## Public evidence patterns

- Stripe idempotency: use idempotency keys so connection-error retries do not perform the same operation twice; avoid sensitive data in keys; keys can be pruned after at least 24h; compare parameters on key reuse.
- Slack Events API: short bounded retries, retry reason headers, and optional delayed retries for 24h; delivery is best-effort and observable.
- AWS SQS DLQ: retry budget first, then dead-letter queue; choose max receive count high enough for resilience but avoid endless hot-path loops.
- Temporal retry policies: put failure-prone external side effects in retry-governed activities; keep deterministic workflow state separate from delivery attempts.
- Twilio webhooks: retry count, retry policy, total timeout, and idempotency token are explicit connection-level controls.
- GitHub webhooks: failed deliveries are visible and can be manually/script-redelivered; automatic redelivery is not always the default.
- Telegram Bot API: inbound updates are retained up to 24h; flood control can expose `retry_after`; offsets must prevent duplicate update processing.

## Hermes target model

### Layer 0 — low-risk recovery already appropriate

- After polling reconnect succeeds, immediately probe Bot API (`get_me`) and clear `_send_path_degraded` on success.
- When `send()` sees `_send_path_degraded`, run one bounded preflight probe before returning retryable failure.
- Treat `send_path_degraded` as a recovery-window signal in the base retry wrapper: wait longer (for example 10s, 30s, 60s) before notifying failure.
- Keep slower heartbeat probing for wedged long-poll detection.

### Layer 1 — metadata-only outbox (safe default)

Record delivery metadata without reply body:

- `delivery_id`: random UUID.
- `dedupe_key`: HMAC/hash over platform, chat/thread/session/logical turn, and content hash; never raw content.
- `platform`, `chat_id`, optional `thread_id`, `reply_to`, `session_key`.
- `content_sha256` only; no plaintext body.
- `status`: pending | sending | sent | dead_letter | expired | suppressed_duplicate.
- `attempt_count`, `last_error`, `next_attempt_at`, `created_at`, `expires_at`, `sent_message_id`.
- `policy`: content_storage=none, auto_redeliver=false.

Value: proves a final reply existed and failed delivery without crossing privacy boundaries. Limitation: cannot auto-redeliver after process crash because content is not stored.

### Layer 2 — content outbox (human gate)

Full automatic redelivery requires storing the generated reply body. Stop for explicit user decision:

- Plaintext-local + TTL: practical for personal assistant mode, but persists private output under Hermes state.
- Encrypted-local + TTL: better enterprise shape, but requires key-management design; do not invent weak encryption silently.

### Retry classification

- Retryable: connection failed before request, connect timeout, `send_path_degraded`, Telegram `retry_after`/flood control after the specified delay.
- Ambiguous: read timeout/write timeout after request may have reached Telegram; do not blind retry without idempotency/dedupe proof.
- Non-retryable: BadRequest, Forbidden, permanent auth/config failures; move to dead_letter or surface operator action.

### Operator surface

- Status/list command or projection: pending/dead_letter counts by platform/chat/age.
- Inspect metadata with content redacted by default.
- Manual redeliver by `delivery_id` only after confirmation when content exists.
- Logs should include `delivery_id`, dedupe prefix, attempt count, retry reason, and next attempt time.

## Verification checklist

- RED tests for degraded send preflight recovery, failed probe fallback, and reconnect immediate probe.
- Tests for recovery-window delay sequence and exhaustion notice.
- Outbox tests for dedupe, TTL expiry, dead_letter transition, manual redelivery, crash/restart drain, and non-retryable classification.
- `py_compile` gateway files and focused Telegram/send retry tests.
- Runtime verification: restart gateway, wait for `Connected to Telegram`, `✓ telegram connected`, `Gateway running`, then explicit Telegram send returns `success=true` and `message_id`.
