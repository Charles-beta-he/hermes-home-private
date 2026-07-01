# First-party mobile dialog bridge from Telegram-style gateway patterns

Use this reference when a Hermes-owned mobile app should behave like a first-party Hermes terminal, not just an offline/local demo, and the user asks to reference Telegram or messaging-app connection architecture.

## Applicability

Apply when building or reviewing a mobile assistant / avatar / companion app that should connect to Hermes through Gateway.

Anti-conditions:
- Do not put provider/API/Hermes-core secrets in the mobile app.
- Do not treat offline/local model output as the primary path when the product goal is a connected Hermes avatar.
- Do not jump straight to streaming/SSE before the synchronous final-response contract is verified.
- Do not bypass existing risky-action confirmation just because the text came from voice ASR.

## Best-practice sources to map from

- Telegram: `update_id`, offset/ack, webhook vs long polling, `sendChatAction`, file ids, retry/flood-control responses, login/OIDC-style pairing.
- WhatsApp Cloud API: message id, sent/delivered/read/failed statuses, duplicate webhook retries, explicit read receipts, payload limits.
- Slack: event/envelope ids, fast ack before long work, async responses, rate-limit events, Socket Mode style recoverable long connection.
- Realtime voice systems: ephemeral client secrets, delta events, turn detection, push-to-talk vs realtime stream separation, privacy-preserving user identifiers.

## Minimum safe landing slice

1. Add a Gateway endpoint like `POST /v1/mobile/dialog/turn`.
2. Require device identity, e.g. `x-hermes-device-id` first; later replace/augment with pairing token/device key.
3. Require body fields:
   - `clientMessageId`
   - `conversationId`
   - `text`
   - `inputMode: typed | voice`
   - optional `locale`
4. Derive a stable Hermes session key:
   - `mobile:{deviceId}:{conversationId}`
5. Add idempotency before calling Hermes core:
   - key: `{deviceId}:{conversationId}:{clientMessageId}`
   - duplicate turns replay the prior response and do not call Hermes twice.
6. Gateway, not RN/mobile, calls Hermes core/API-server using server-side credentials.
7. Return a final assistant message and delivery state:
   - `conversationId`
   - `hermesSessionId`
   - `clientMessageId`
   - `assistantMessage`
   - `delivery.state`
8. RN/mobile client submits typed text and safe voice transcripts to this endpoint first.
9. If Gateway/core is unavailable, RN falls back to existing local/offline path and marks the result as queued/readback rather than presenting it as the connected answer.
10. Keep high-risk voice intents (publish/send/delete/submit/deploy/payment/external side effects) on the local confirmation boundary; do not online-submit as execution.
11. If Hermes `api_server` is unavailable or too heavy for the current dev loop, keep operating instead of stopping at manual config: implement a server-side direct bridge from Pocket Gateway to local Hermes CLI, e.g. `hermes --continue mobile:{deviceId}:{conversationId} --oneshot <text>`. This still keeps credentials out of mobile and preserves the Gateway authority boundary. Treat missing external ASR/provider keys as a provider limitation, not a reason to stop first-party dialog wiring.

## User-expectation lesson

For this user's first-party Hermes/Pocket work, frustration at “why can’t you directly operate?” is a signal to push through safe local tooling friction. Do not hand back “configure X” if a local Gateway/CLI/simulator path can be wired and verified by the agent. Stop only at true secret/permission/high-risk/prod/irreversible boundaries, and report those boundaries separately from the working local path.

## Implementation checklist

Gateway:
- Validate text is non-empty and bounded.
- Return structured `VALIDATION_ERROR`, `MESSAGE_TOO_LARGE`, and retryable `HERMES_DIALOG_UNAVAILABLE` errors.
- Do not log request secrets or provider keys.
- Store idempotency/session mapping in process memory only for a disposable first spike. For any “全盘推进”, simulator acceptance, or retry/restart claim, promote immediately to the GatewayStore/SQLite layer before calling Hermes.
- Persist `{deviceId}:{conversationId}:{clientMessageId}` with `hermesSessionId`, serialized assistant message, delivery state, and created timestamp. On replay, return the persisted response plus `idempotentReplay: true` and do not call Hermes again.
- Add tests for missing device, blank text, stable session key, same-process idempotent replay, persisted replay across app/store instances, and upstream failure.

RN/mobile:
- Add a dedicated `mobileDialogClient` rather than reusing offline handoff code.
- Use the same client for typed turns and post-ASR safe voice transcripts.
- Append successful online responses as delivered online assistant messages, not offline evidence answers.
- On failure, fallback locally without dropping the user turn.
- Keep current risk-confirmation logic before submitting voice-derived external actions.

Verification:
- Gateway targeted contract tests.
- Gateway full test/build.
- RN Jest/lint.
- Release simulator build + screenshot readback.
- If Hermes core/API-server credentials are configured, run true E2E: RN/Gateway turn -> Hermes core session -> assistant response.

## Next production layers after sync turn works

Only after the synchronous final-response endpoint is green:
- SSE/streaming endpoint with events such as `assistant.delta`, `tool.progress`, `approval.required`, `assistant.completed`.
- Delivery/read receipt states: accepted, queued, sent, delivered, read, failed_retryable, failed_terminal.
- Device pairing with short-lived challenge, device public key, revocation, and scoped permissions.
- Attachment object store with file ids/blob ids; messages should reference assets, not carry large payloads.
- Push notifications as wake signals only; Gateway remains the source of truth.
