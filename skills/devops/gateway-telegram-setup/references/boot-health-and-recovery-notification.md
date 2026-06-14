# Gateway boot health and recovery notification

Use this reference when Telegram/Gateway reliability should be checked automatically after boot, login, or gateway restart.

## Scope

This is a lightweight operational-readiness check, not a full Hermes update or destructive repair routine.

Appropriate checks:
- Hermes CLI starts and config loads.
- Gateway process exists and service definition is current.
- Gateway logs show `Connected to Telegram`, `✓ telegram connected`, and `Gateway running with ... platform(s)` after the current start.
- Telegram Bot API `getMe` succeeds and webhook/polling state is sane.
- Proxy endpoint is reachable if Telegram is routed through a local proxy.
- Gateway FD count and launchd `maxfiles` are comfortably below limits.
- Recent gateway logs have no `telegram connect timed out`, `ProxyError`, `Gateway started with no connected platforms`, `polling conflict`, `paused`, or `Errno 24` after the latest restart.
- Explicit send verification succeeds with `success=true` and a returned `message_id`.

Anti-conditions:
- Do not run `hermes update`, git pull, provider/model rewrites, token edits, or destructive session/log cleanup as part of boot health.
- Do not treat `getMe` alone as end-to-end recovery; verify gateway polling logs and one explicit send when possible.
- Do not preserve interrupted Telegram requests as WIP after a forced restart; ask the user to resend.

## Recovery ladder

1. Read current status and recent logs before changing state.
2. If the service definition is stale, run `hermes gateway start` to refresh it.
3. If stale pid/lock files or stuck old sessions are suspected, stop gateway, remove `~/.hermes/gateway.pid` and `~/.hermes/gateway.lock`, then start again.
4. If launchd bootstrap returns exit 5 but Hermes falls back to a background process, classify the immediate service as recovered only if the process is running and gateway logs confirm Telegram connected. Still report the autostart risk.
5. Wait long enough for Telegram command registration and polling startup; a short polling conflict can appear while Telegram releases the previous getUpdates session.
6. Verify recovery from logs after the latest start and by explicit message send.

## Report shape

Keep reports short and evidence-backed:

```text
Hermes Gateway boot health: OK/WARN/FAIL
Gateway: OK pid=<pid>
Telegram: OK polling connected at <time>
Proxy: OK <endpoint>
FD: OK <count>/<limit>
Action: restarted gateway / no action
Proof: message_id=<id> / log line=<timestamp>
Risk: launchd bootstrap exit 5; current fallback process is running but reboot autostart may need repair
```

## Optional product skin

For user-facing startup audio or notification, the same health result can be rendered as a sci-fi/mecha `Activation Sequence`, but the underlying report must remain machine-checkable and evidence-based.
