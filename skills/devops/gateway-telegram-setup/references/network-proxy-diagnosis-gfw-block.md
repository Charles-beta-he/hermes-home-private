# Network / Proxy Diagnosis (GFW block)

Extracted from `/Users/charles/.hermes/skills/devops/gateway-telegram-setup/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

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
