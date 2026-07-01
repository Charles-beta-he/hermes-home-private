# Telegram send-path degraded recovery

Use when Telegram logs show polling recovered but replies still fail with `send_path_degraded`.

## Symptom

Recent logs contain both:

```text
Telegram polling resumed after network error (attempt N)
Send failed ... send_path_degraded
Failed to deliver response after 2 retries: send_path_degraded
```

This means inbound polling may have recovered while outbound gateway sends are still blocked by the adapter's send-path health flag.

## Root-cause pattern

In `gateway/platforms/telegram.py`, `_handle_polling_network_error()` sets `_send_path_degraded = True` on network/proxy errors. A successful `start_polling()` proves only that polling restarted. The flag may remain true until `_verify_polling_after_reconnect()` runs its delayed heartbeat and `bot.get_me()` succeeds. Replies produced during that recovery window can be rejected immediately by `send()` with `send_path_degraded` and exhausted by short base retries.

Common trigger: proxy/node instability causing `httpx.ProxyError: 503 Service Unavailable`, followed by polling recovery and a near-immediate final reply.

## Debug checklist

1. Confirm service is alive:
   ```bash
   hermes gateway status
   ps aux | grep -E "hermes_cli.main gateway run|hermes gateway run|gateway run" | grep -v grep || true
   ```
2. Correlate the latest polling and send events:
   ```bash
   tail -160 ~/.hermes/logs/gateway.log | grep -E "polling resumed|network error|inbound message|response ready|Send failed|send_path_degraded|Failed to deliver"
   tail -120 ~/.hermes/logs/gateway.error.log | grep -iE "proxyerror|send_path_degraded|failed to deliver|api call failed|timeout"
   ```
3. Verify Bot API reachability through the configured proxy, but do not treat `getMe` alone as end-to-end proof.
4. Send an explicit smoke message with `send_message`; require `success=true` and `message_id`.
5. If an in-flight user reply was lost during the degraded window, ask the user to resend that message or recover it from session/log context if available.

## Durable fix shape

Prefer code fixes that make recovery explicit rather than just increasing retries:

1. After `start_polling()` succeeds in `_handle_polling_network_error()`, immediately run a bounded `bot.get_me()` probe. If it succeeds, clear `_send_path_degraded` before scheduling the delayed heartbeat.
2. In `send()`, if `_send_path_degraded` is true, optionally perform one bounded self-healing `get_me()` probe before returning `send_path_degraded`.
3. For final conversation replies, consider a pending outbox / deferred-send path so transient send degradation does not silently drop already-generated responses.
4. Keep the delayed heartbeat probe because `start_polling()` plus `get_me()` still does not prove the long-poll task will keep making progress.

## Regression tests to add/update

- Network error sets `_send_path_degraded=True`.
- Successful reconnect plus immediate `get_me()` clears `_send_path_degraded`.
- Immediate send after the successful reconnect path sends normally and does not return `send_path_degraded`.
- If the immediate probe fails, `_send_path_degraded` remains true and the existing retry/fatal ladder still applies.
- If a send-side self-healing probe is added, cover both probe-success and probe-failure branches.

## Anti-conditions

Do not apply this diagnosis when:

- Telegram is not connected at all and `getMe` fails through every configured route.
- The failure is a polling conflict (`409 Conflict`) from competing gateways; use the polling-conflict recovery path instead.
- The error is `Too many open files`; diagnose FD exhaustion first.
- The issue is model/API failure before a final response is generated; this is not an outbound send-path problem.
