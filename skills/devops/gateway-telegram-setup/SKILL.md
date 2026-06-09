---
name: gateway-telegram-setup
description: Use when you need to debug and configure Hermes Gateway Telegram integration — config structure pitfalls, env var overrides, verbose verification, stale PID cleanup.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - gateway
    - telegram
    - debugging
    - config
    - messaging
    related:
    - systematic-debugging
    - hermes-agent
    related_skills:
    - hermes-agent
---

# Gateway Telegram Setup & Debugging

## Overview

Debug and configure Hermes Gateway Telegram integration — config structure pitfalls, env var overrides, verbose verification, stale PID cleanup.

## When to Use

- Telegram bot not connecting after config changes
- Gateway shows "No messaging platforms enabled"
- Gateway starts but hangs with no output
- Migrating Telegram config between env vars and config.yaml
- `send_message` cannot send to bare `telegram` because no home channel is configured
- Don't use for: requests that do not need you need to debug and configure Hermes Gateway Telegram integration — config structure pitfalls, env var overrides, verbose verification, stale PID cleanup; choose a more specific child skill or a broader routing skill that actually matches the task.
## Critical Config Structure

**Gateway reads `platforms:` at the TOP LEVEL, NOT `gateway.platforms:`**

```yaml
# ✅ CORRECT — Gateway reads this
platforms:
  telegram:
    enabled: true
    token: '8685837705:AAGh...'

# ❌ WRONG — Gateway ignores this
gateway:
  platforms:
    telegram:
      enabled: true
      bot_token: 8685837705:...
```

Source: `gateway/config.py` line 539 reads `yaml_cfg.get("platforms")` — the top-level key.

**Key field mapping:**
- YAML key is `token`, NOT `bot_token`
- `PlatformConfig.from_dict()` reads `data.get("token")` at line 182

## Env Var Override (Recommended)

`gateway/config.py` `_apply_env_overrides()` (line 857-862) auto-enables Telegram from env:

```bash
# ~/.hermes/.env
TELEGRAM_BOT_TOKEN=8685837705:AAGh...
GATEWAY_ALLOW_ALL_USERS=true  # or TELEGRAM_ALLOWED_USERS=id1,id2
```

This is the simplest approach — no config.yaml changes needed for basic setup.

## Verification Checklist

### 1. Test config loading directly
```bash
cd ~/.hermes/hermes-agent
python3 -c "
import os; from hermes_cli.env_loader import load_hermes_dotenv; load_hermes_dotenv()
from gateway.config import load_gateway_config
cfg = load_gateway_config()
for p, c in cfg.platforms.items():
    if c.enabled: print(f'{p.value}: enabled={c.enabled}, token_len={len(c.token) if c.token else 0}')
print('Connected:', cfg.get_connected_platforms())
"
```

### 2. Test bot token validity
```bash
TOKEN=$(grep "TELEGRAM_BOT_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2-)
curl -s "https://api.telegram.org/bot${TOKEN}/getMe" | python3 -m json.tool
```

### 3. Run gateway with verbose output
```bash
hermes gateway stop
hermes gateway run -vv 2>&1 | head -50
# Look for: "✓ telegram connected" and "Gateway running with 1 platform(s)"
```

**Why `-vv` is essential:** Default log level is WARNING. Connection success messages are INFO level and won't appear in `gateway.log` without verbose flag.

### 4. Verify polling is active
```bash
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates?limit=1" | \
  python3 -c "import sys,json; print(f'Pending: {len(json.load(sys.stdin).get(\"result\",[]))}')"
# 0 pending = gateway is consuming updates (good)
```
- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side-effects were verified by read-back or direct inspection.
- [ ] The final result still matches the trigger and acceptance shape of this skill.
## Network / Proxy Diagnosis (GFW block)

When Telegram connects from mainland China, `api.telegram.org` is blocked by the GFW. Gateway logs show repeated `Timed out` / `Connect attempt N/8 failed` with 300s retry backoff.

### Quick triage

```bash
# 1. DNS — usually works even behind GFW
nslookup api.telegram.org

# 2. Direct TCP — times out behind GFW
curl -s -o /dev/null -w "HTTP %{http_code}, Time: %{time_total}s" --connect-timeout 10 https://api.telegram.org
# HTTP 000 + 10s timeout = GFW block

# 3. System proxy status (macOS)
networksetup -getwebproxy Wi-Fi        # Enabled: Yes/No + host:port
networksetup -getsecurewebproxy Wi-Fi  # same

# 4. Proxy process running?
ps aux | grep -iE "clash|v2ray|trojan|shadowsocks|ss-local|privoxy|surge|sing-box|tuic|hysteria" | grep -v grep

# 5. Gateway logs
grep -iE "timeout|connect.*failed|fallback.*failed" ~/.hermes/logs/gateway.error.log | tail -10
```

### Resolution

1. Start proxy tool (Clash/V2Ray/etc.) — verify it's listening: `lsof -i :7892` (or whatever port)
2. Enable system proxy or set env vars:
   ```bash
   # Option A: system proxy (macOS)
   networksetup -setwebproxystate Wi-Fi on
   networksetup -setsecurewebproxystate Wi-Fi on

   # Option B: env vars in ~/.hermes/.env (gateway reads these)
   HTTP_PROXY=http://127.0.0.1:7890
   HTTPS_PROXY=http://127.0.0.1:7890
   ```
3. Restart gateway: `hermes gateway restart`
4. Verify: grep gateway logs for `✓ telegram connected`

### Pitfall: gateway proxy env inheritance

Gateway launched via launchd inherits the **launchd session's** environment, not your shell's. If you set `HTTPS_PROXY` in `.zshrc` but the launchd plist doesn't source it, the gateway won't see it. Use `~/.hermes/.env` for gateway-scoped proxy vars — `gateway/config.py` loads it explicitly.

### Pitfall: fallback IPs also blocked

Gateway's Telegram network layer tries fallback IPs (149.154.167.x) when DNS resolution succeeds but TCP fails. Behind the GFW, these are also blocked. The only reliable fix is a working proxy — DoH/fallback-IP strategies don't bypass the GFW.

### Pitfall: gateway auto-pauses Telegram after consecutive failures

After ~10 consecutive connection failures, the gateway **automatically pauses the Telegram platform** to avoid log spam and resource waste. The platform shows as paused in `hermes gateway status`. When this happens, even restarting the gateway may not help if the underlying network issue (proxy down, GFW block) isn't resolved first.

**Detection:** `grep "pausing\|paused" ~/.hermes/logs/gateway.error.log` or check `hermes gateway status` for platform pause state.

**Recovery sequence:**
1. Fix the underlying issue first (start proxy, verify connectivity)
2. Then restart gateway: `hermes gateway restart`
3. Verify: `grep "telegram connected" ~/.hermes/logs/gateway.log`

### Pitfall: socks5 proxy in config.yaml vs HTTP_PROXY env var

The gateway proxy setting in `~/.hermes/config.yaml` uses full URL format including scheme:
```yaml
proxy: "socks5://127.0.0.1:1082"
```

The `HTTP_PROXY`/`HTTPS_PROXY` env vars typically use `http://` scheme. The config.yaml `proxy` field is passed directly to httpx/PTB and supports `socks5://` natively. Do NOT mix these — if config.yaml has a `proxy` field, the env vars may be ignored for Telegram connections.

**Quick proxy port scan** to find what's actually listening:
```bash
for port in 7890 7891 1080 1081 1082 2080 33210 10800 10801; do
    nc -z 127.0.0.1 $port 2>/dev/null && echo "Port $port OPEN"
done
```

## Common Pitfalls

### Errno 24 / Too many open files in Telegram gateway
If Telegram replies with `Sorry, I encountered an error (OSError). [Errno 24] Too many open files: ~/.hermes/sessions/.sessions_*.tmp`, diagnose gateway FD exhaustion before blaming session storage:

```bash
launchctl limit maxfiles
PID=$(launchctl print gui/$(id -u)/ai.hermes.gateway 2>/dev/null | awk '/pid =/ {print $3; exit}')
lsof -p "$PID" -n -P 2>/dev/null | wc -l
python3 - <<'PY' "$PID"
import collections, re, subprocess, sys
out=subprocess.check_output(['lsof','-p',sys.argv[1],'-n','-P'], text=True, stderr=subprocess.DEVNULL)
fds=[]; by=collections.Counter()
for line in out.splitlines()[1:]:
    parts=line.split()
    if len(parts)>=5:
        m=re.match(r'^(\d+)', parts[3])
        if m: fds.append(int(m.group(1)))
        by[parts[4]] += 1
print('numeric_fd_count', len(set(fds)), 'max_fd', max(fds) if fds else None, 'by_type', dict(by.most_common(10)))
PY
```

Strong signal: launchd soft maxfiles is 256 and gateway numeric FDs are ~250, often with many CLOSED IPv4 sockets to the local proxy. Short-term: `hermes gateway start`/restart after cleaning stale pid/lock if needed. Persistent local fix in this setup: launchd generated plist includes `SoftResourceLimits NumberOfFiles=4096` and `HardResourceLimits NumberOfFiles=8192`; `~/.hermes/scripts/post-update-check.py --fix` has `launchd_gateway_nofile_limit` to reapply after updates.

Governance pattern: raising `nofile` is only mitigation. For recurring Errno 24, install/verify an observe-only FD watchdog under `~/.hermes/scripts/` and run it as `no_agent` cron. The watchdog should emit strict JSON, keep bounded FD history, capture lsof snapshots only on warning/critical, surface cron `Errno 24` collateral damage, and explicitly avoid auto-restart/auto-kill. Add a post-update check that py-compiles the watchdog and verifies `auto_restart=false` / `auto_kill=false`. In this user's setup, `~/.hermes/scripts/gateway_fd_watchdog.py` plus cron `gateway-fd-watchdog` is the established pattern.

Deep-dive root-cause workflow: see `references/fd-exhaustion-deep-dive.md` for the evidence commands, likely source-code contributors (Telegram PTB pool budget, auxiliary async client stale-loop cleanup, `/model` client replacement, gateway AIAgent cache), and TDD regression tests. Do not stop at launchd `nofile`; prove FD slope and fix lifecycle contributors.

### Stale PID/Lock files
After crashes, `gateway.pid` and `gateway.lock` may contain dead PIDs:
```bash
rm -f ~/.hermes/gateway.pid ~/.hermes/gateway.lock
hermes gateway restart
```

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

Verification is not just `getMe`: send an explicit message to the known DM target and check `success=true` plus `message_id`:

```text
send_message(action="list")
send_message(action="send", target="telegram:he cheng", message="TG connectivity test")
```

Do not preserve the original stuck request as WIP after a forced restart; ask the user to resend the Telegram message if it was interrupted.

### launchd log truncation
launchd stdout/stderr go to `gateway.log` / `gateway.error.log` but at WARNING level only. The gateway banner ("Hermes Gateway Starting...") prints to stdout, but connection details need INFO level.

### macOS lsof shows system processes
`lsof -p <PID>` on macOS may show unrelated system processes. Use `ps -p <PID>` to verify process state instead.

### ohmo gateway conflict
Check for competing gateway processes: `ps aux | grep "gateway run" | grep -v grep`

### MEDIA attachments silently not delivered from arbitrary local paths

Gateway treats `MEDIA:/path/to/file` emitted by the model as untrusted text. Native attachment delivery only accepts existing files under Hermes-managed media caches or directories explicitly allowlisted by `HERMES_MEDIA_ALLOW_DIRS`. If the file lives on Desktop/Documents/project folders, `BasePlatformAdapter.filter_media_delivery_paths()` drops it and logs `Skipping unsafe MEDIA directive path outside allowed roots`; the user may see no attachment even though the assistant response contained a `MEDIA:` line.

Before sending a generated artifact, copy it into an allowed cache first, then send that path:

```bash
mkdir -p ~/.hermes/cache/documents
cp /absolute/source/file.docx ~/.hermes/cache/documents/
```

Then deliver:

```text
MEDIA:/Users/<user>/.hermes/cache/documents/file.docx
```

Allowed roots include `~/.hermes/cache/documents`, `~/.hermes/document_cache`, `~/.hermes/image_cache`, `~/.hermes/audio_cache`, `~/.hermes/cache/videos`, and `~/.hermes/cache/screenshots`. For explicit sends, prefer `send_message(action="list")` then `send_message(action="send", target="<explicit chat target>", message="MEDIA:/allowed/cache/path")` and verify tool result `success=true` plus `message_id`.

### No home channel for Telegram sends
If `send_message` with bare `target="telegram"` fails with `No home channel set for telegram`, list targets and send to the explicit chat instead of assuming config is broken:

```text
send_message(action="list")
send_message(action="send", target="telegram:<chat name>", message="...")
```

In this user's setup, the DM target has been observed as `telegram:he cheng`. Use a bare platform only after `TELEGRAM_HOME_CHANNEL` is configured. The durable config equivalent is:

```bash
hermes config set TELEGRAM_HOME_CHANNEL <channel_id>
```
1. Skipping prerequisite checks and assuming the environment already matches the workflow.
2. Applying the workflow mechanically without confirming that the request still matches this skill's trigger class.
3. Reporting success before reading back the actual outputs, files, or external side-effects.
## Allowlist Configuration

Without allowlist, all users are denied:
```bash
# In ~/.hermes/.env
GATEWAY_ALLOW_ALL_USERS=true          # Open access (dev only)
TELEGRAM_ALLOWED_USERS=123456,789012  # Specific user IDs
```

Gateway checks: `TELEGRAM_ALLOWED_USERS`, `GATEWAY_ALLOW_ALL_USERS`, `TELEGRAM_ALLOW_ALL_USERS`

## Restart Flow
```bash
# Clean restart
launchctl stop ai.hermes.gateway
rm -f ~/.hermes/gateway.pid ~/.hermes/gateway.lock
launchctl start ai.hermes.gateway

# Or use hermes command
hermes gateway restart
```

## Bot Commands Registered
Gateway auto-registers slash commands from skills. Telegram limits 100 visible commands; overflow uses /commands for full list.
