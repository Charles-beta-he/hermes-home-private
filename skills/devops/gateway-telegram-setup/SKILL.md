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

## First-party mobile dialog bridge pattern

When Telegram is used as the reference architecture for a Hermes-owned mobile app or avatar, do not stop at token/config setup. Map Telegram-style update/session/delivery concepts into a first-party mobile Gateway lane: device identity, conversation id, client message id, stable session key, durable idempotent replay, Gateway-held credentials, online-first dialog, and local/offline fallback only. If Hermes api_server is not immediately operable, prefer a server-side local Hermes CLI bridge over handing the user a manual config chore; keep secrets out of mobile and verify with real curl/simulator output. See `references/first-party-mobile-dialog-bridge.md` for the reusable implementation checklist and anti-conditions.

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
Prefer log/readback checks while the Hermes gateway is already running:
```bash
hermes gateway status
tail -120 ~/.hermes/logs/gateway.log | grep -E "Connected to Telegram|✓ telegram connected|Gateway running with|Telegram polling resumed|Telegram polling conflict" | tail -20
```

Only call Bot API `getUpdates` when the gateway is stopped or you intentionally accept a short polling conflict. A direct `getUpdates` call competes with the gateway's long-polling session and can produce `HTTP 409 Conflict: terminated by other getUpdates request`. If this happens during a check, wait ~20-30s and re-read logs for `Telegram polling resumed after conflict retry ...` before declaring failure.
```bash
# Use only when gateway polling is not active, or as a deliberate conflict test.
curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates?limit=1" | \
  python3 -c "import sys,json; print(f'Pending: {len(json.load(sys.stdin).get(\"result\",[]))}')"
# 0 pending can indicate gateway is consuming updates, but log/status readback is safer.
```
- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side-effects were verified by read-back or direct inspection.
- [ ] The final result still matches the trigger and acceptance shape of this skill.
## Network / Proxy Diagnosis (GFW block)

Detailed `Network / Proxy Diagnosis (GFW block)` guidance moved to `references/network-proxy-diagnosis-gfw-block.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Common Pitfalls

### Telegram live-location updates are edited location messages
When inspecting or extending inbound location support, remember that Telegram live-location updates arrive as edited message updates while still matching `filters.LOCATION` through `Update.effective_message`. Do not treat `filters.LOCATION` as normal `message`-only. For the verified PTB fixture, state key (`chat_id + message_id`), throttling model, privacy constraints, and test checklist, see `references/telegram-live-location-handling.md`.

### Boot health / recovery notification for Telegram Gateway
When Telegram responsiveness is part of a startup or post-restart check, use the lightweight operational-readiness pattern in `references/boot-health-and-recovery-notification.md`. Verify both sides of the path: gateway polling logs (`Connected to Telegram`, `✓ telegram connected`, `Gateway running with ... platform(s)`) and an explicit send result with `success=true` plus `message_id`. `getMe` alone proves only token/API reachability, not that Hermes is consuming inbound updates.

If `hermes gateway start` reports launchd bootstrap exit 5 but starts a fallback background process, do not call it fully fixed just because Telegram reconnects. Report current recovery separately from reboot/autostart risk, and keep the repair ladder low-risk: refresh service definition, clear stale pid/lock, restart gateway, then verify logs/send. Avoid token/provider/config rewrites during boot health.

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

### Telegram live location sharing
Hermes Telegram adapter treats live location as sensitive high-frequency ingress. Current long-term-safe pattern: keep live-location state process-local only, keyed by `(chat_id, message_id)`; never persist live coordinates into memory, skills, docs, config, or session summaries beyond the actual user-facing event text needed for the current turn. First `location.live_period` update should dispatch one agent event with `live_period_seconds`, `horizontal_accuracy_m`, `heading_degrees`, coordinates, and map link. Subsequent `edited_message` live-location updates should update in-memory state and only wake the agent when the configured time or distance threshold is crossed. Defaults in code: `HERMES_TELEGRAM_LIVE_LOCATION_MIN_INTERVAL_SECONDS` (clamped 10..3600, default 120) and `HERMES_TELEGRAM_LIVE_LOCATION_MIN_DISTANCE_METERS` (clamped 10..10000, default 250). Preserve ordinary location pins, venue handling, group mention gating, observe attribution, forum/topic routing, and channel post behavior.

Focused verification after changes:
```bash
cd ~/.hermes/hermes-agent
./venv/bin/python -m pytest -o addopts='' \
  tests/gateway/test_telegram_live_location.py \
  tests/gateway/test_telegram_group_gating.py::test_unmentioned_location_message_observed_in_group \
  tests/gateway/test_telegram_group_gating.py::test_triggered_location_message_uses_shared_session_in_observe_mode -q
./venv/bin/python -m py_compile gateway/platforms/telegram.py tests/gateway/test_telegram_live_location.py
```
If bare pytest fails with `unrecognized arguments: --timeout=30 --timeout-method=signal`, the active venv lacks `pytest-timeout`; use `-o addopts=''` for focused local verification or install the dev extra before claiming full-suite parity.

### Telegram polling recovers but replies still fail with `send_path_degraded`

Detailed `Telegram polling recovers but replies still fail with `send_path_degraded`` guidance moved to `references/telegram-polling-recovers-but-replies-still-fail-with-send-path-degrad.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Telegram receives but does not respond after a tool/browser hang

Detailed `Telegram receives but does not respond after a tool/browser hang` guidance moved to `references/telegram-receives-but-does-not-respond-after-a-toolbrowser-hang.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
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

### Checking Telegram sent-message recovery / delivery outbox

Detailed `Checking Telegram sent-message recovery / delivery outbox` guidance moved to `references/checking-telegram-sent-message-recovery-delivery-outbox.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
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

### Cron report generated but Telegram delivery failed
For scheduled reports/reminders that “did not send”, use `references/cron-telegram-delivery-debugging.md`.

If the report artifact exists but `jobs.json` still shows an old `last_run_at` or there is no delivery evidence, use `references/cron-startup-audit-and-compensation.md`. That reference covers startup audit classification, run-ledger shape, and bounded compensation filters for split states such as `GENERATED_UNMARKED`, `DELIVERY_UNKNOWN`, and `DELIVERED_UNMARKED`.

Key rule: separate generation from delivery. A job may show `last_status: ok` and still have `last_delivery_error`; read the saved cron output/report artifact before concluding the report failed. If the delivery error says `python-telegram-bot not installed`, verify imports in the Hermes venv with `~/.hermes/.env` loaded and run a short standalone Telegram send smoke. If those pass, treat the message as a potentially over-broad ImportError/stale-runtime symptom, not proof that the dependency is missing. Also check live Telegram adapter pool pressure (`Pool timeout: All connections in the connection pool are occupied`) as a separate transient delivery-path issue.
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
