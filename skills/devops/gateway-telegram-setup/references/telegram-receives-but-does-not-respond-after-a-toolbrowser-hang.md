# Telegram receives but does not respond after a tool/browser hang

Extracted from `/Users/charles/.hermes/skills/devops/gateway-telegram-setup/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Telegram receives but does not respond after a tool/browser hang
If logs show an inbound Telegram message followed by a long tool timeout (for example `browser 'open' timed out after 60s`) and no `response ready`, treat it as a stuck request pipeline rather than a Telegram token/auth issue:

```bash
# 1. Correlate inbound -> response/tool errors
grep -n "inbound message\|response ready\|browser 'open' timed out\|Tool .* timed out\|Transient network error" \
  ~/.hermes/logs/gateway.log ~/.hermes/logs/gateway.error.log | tail -80

# 2. Check gateway process, children, and FD pressure
PID=$(launchctl print gui/$(id -u)/ai.hermes.gateway 2>/dev/null | awk '/pid =/ {print $3; exit}')
ps -p "$PID" -o pid,ppid,stat,etime,%cpu,%mem,command
pgrep -P "$PID" -laf || true
lsof -p "$PID" -n -P 2>/dev/null | wc -l
ps aux | grep -E "agent-browser|Chrome for Testing" | grep -v grep || true

# 3. Restart cleanly; if drain hangs, let hermes force launchd restart
hermes gateway restart
```

After `hermes gateway restart`, if `hermes gateway status` reports `Service definition is stale` or `Gateway service is not loaded`, refresh/load the launchd service and verify Telegram connection:

```bash
hermes gateway start
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist 2>/dev/null || true
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway 2>/dev/null || true
sleep 10
hermes gateway status
grep "Connected to Telegram\|✓ telegram connected\|Gateway running" ~/.hermes/logs/gateway.log | tail -20
```

If macOS launchd returns `Bootstrap failed: 5: Input/output error`, `hermes gateway start` may fall back to a tracked background gateway process. First separate true domain-unsupported from domain mismatch/race. In this setup the generated helper may target `user/<uid>` while the existing LaunchAgent is actually loaded under `gui/<uid>`; evidence is `launchctl print user/$(id -u)/ai.hermes.gateway` → not found, while `launchctl print gui/$(id -u)/ai.hermes.gateway` shows the running job. `launchctl kickstart -k user/...` then returns 113 and the subsequent bootstrap can emit exit 5/`Operation already in progress` while the `gui` job is still tearing down. A delayed `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.hermes.gateway.plist` can succeed, proving launchd itself is not permanently unsupported. Root fix is to resolve/control the loaded domain consistently (prefer the domain where the label is already loaded, or install/start/status all on the same domain) and avoid classifying transient bootstrap exit 5 as permanent launchd incapability without checking the other domain and teardown state.

Treat fallback as usable only after all of these are true:

```bash
# Service definition no longer stale, and a gateway PID exists
hermes gateway status
pgrep -fl "hermes_cli.main gateway run"

# Check both domains before concluding launchd is unsupported
launchctl print user/$(id -u)/ai.hermes.gateway 2>&1 | head
launchctl print gui/$(id -u)/ai.hermes.gateway 2>&1 | head

# Wait past Telegram's short getUpdates conflict window and any planned --replace takeovers.
# The latest log segment (not old grep tail matches) must show a stable connected gateway:
sleep 15
tail -80 ~/.hermes/logs/gateway.log | grep -E "Connected to Telegram|✓ telegram connected|Gateway running with|Telegram polling conflict|planned --replace takeover|Gateway stopped"
```

A `Telegram polling conflict ... terminated by other getUpdates request` immediately after restart is often just the previous polling session expiring; wait and re-read the newest log lines before declaring failure. If logs keep showing repeated `planned --replace takeover` or `Gateway stopped`, there may be competing gateway starters; stop, clean stale pid/lock, then start once.

Verification is not just `getMe`: `getMe` and direct Bot API sends prove token/network only, not the gateway inbound/agent pipeline. Send an explicit message to the known DM target and check `success=true` plus `message_id`, then ask the user to reply in Telegram to verify inbound processing:

```text
send_message(action="list")
send_message(action="send", target="telegram:he cheng", message="TG connectivity test — please reply in Telegram")
```

Do not preserve the original stuck request as WIP after a forced restart; ask the user to resend the Telegram message if it was interrupted.
