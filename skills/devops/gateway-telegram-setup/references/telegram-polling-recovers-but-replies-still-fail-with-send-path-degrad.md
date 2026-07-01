# Telegram polling recovers but replies still fail with `send_path_degraded`

Extracted from `/Users/charles/.hermes/skills/devops/gateway-telegram-setup/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Telegram polling recovers but replies still fail with `send_path_degraded`
When logs show `Telegram polling resumed after network error` followed soon after by `Send failed ... send_path_degraded` or `Failed to deliver response after 2 retries: send_path_degraded`, separate inbound polling recovery from outbound send-path recovery. `start_polling()` may have succeeded while `_send_path_degraded` is still true until the delayed heartbeat clears it; final replies generated during that window can be dropped by short retries. The durable code pattern is: after `start_polling()` succeeds, immediately run a tight Bot API `get_me()` probe and clear `_send_path_degraded` on success; in `send()`, if `_send_path_degraded` is still true, run one bounded preflight `get_me()` probe before returning the retryable fallback error; in the base retry wrapper, treat `send_path_degraded` as a recovery-window signal with longer bounded waits (10s, 30s, 60s) before notifying failure. Keep the slower 60s heartbeat for wedged long-poll detection.

Enterprise UX hardening: Hermes has a plaintext-local delivery outbox (`gateway/delivery_outbox.py`) for generated gateway replies. It records pending/sent/dead_letter delivery state plus the reply body for bounded redelivery after a send-path flap or gateway restart. Default TTL is 24h (`HERMES_GATEWAY_DELIVERY_OUTBOX_TTL_SECONDS`); disable the whole outbox with `HERMES_GATEWAY_DELIVERY_OUTBOX=0`; force metadata-only mode with `HERMES_GATEWAY_DELIVERY_OUTBOX_CONTENT_STORAGE=none`. Startup drains pending plaintext-local rows after adapters connect and before lifecycle notifications, then marks rows sent/dead_letter. The file is compacted on new writes/drains so expired plaintext is removed.

Verification:
```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest -o addopts='' tests/gateway/test_delivery_outbox.py tests/gateway/test_send_retry.py tests/gateway/test_telegram_send_path_health.py tests/gateway/test_telegram_network_reconnect.py tests/gateway/test_telegram_network.py -q
./venv/bin/python -m py_compile gateway/delivery_outbox.py gateway/platforms/base.py gateway/platforms/telegram.py gateway/run.py tests/gateway/test_delivery_outbox.py tests/gateway/test_send_retry.py tests/gateway/test_telegram_send_path_health.py
# Operational smoke: seed DeliveryOutbox.default().create_pending(...), hermes gateway restart, then verify
# `Delivery outbox startup drain: {'claimed': 1, 'sent': 1, 'failed': 0, 'skipped': 0}` and outbox status=sent.
```
