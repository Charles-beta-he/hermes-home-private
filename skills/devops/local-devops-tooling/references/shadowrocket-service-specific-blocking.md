---
name: shadowrocket-service-specific-blocking
description: "Diagnosing service-specific IP blocking through Shadowrocket VPN/proxy — when general internet works but specific services (OpenAI, etc.) fail with SSL_ERROR_SYSCALL or connection resets. Covers TUN mode fake DNS detection, multi-site isolation testing, and Webshare residential proxy limitations."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [macos, shadowrocket, proxy, vpn, openai, webshare, ssl, diagnostics]
---

# Shadowrocket Service-Specific Blocking

Use when VPN/proxy is connected and general sites work, but specific services fail with `SSL_ERROR_SYSCALL`, `Connection reset`, or `Proxy CONNECT aborted`.

## Key Pattern

**Symptom**: `curl: (35) LibreSSL SSL_connect: SSL_ERROR_SYSCALL` on target service, while other HTTPS sites return 200.

**Root cause**: The VPN/proxy exit IP is on the target service's blocklist. Common with OpenAI/Cloudflare, which aggressively block datacenter, VPN, and residential proxy IPs.

**Not the same as**: VPN completely broken (all sites fail) or DNS issue (nslookup fails).

## Diagnostic Flow

### Step 1: Multi-Site Isolation Test

Test 4+ sites across different providers to isolate the scope:

```bash
for site in google.com github.com api.openai.com chatgpt.com cloudflare.com; do
  result=$(curl -m 8 -sS -o /dev/null -w "%{http_code} %{time_total}s" "https://$site/" 2>&1)
  echo "  $site -> $result"
done
```

Interpretation:
| Pattern | Diagnosis |
|---|---|
| All fail | VPN/proxy completely broken — check node, TUN mode, proxy group |
| Only target service fails | Service-specific IP blocking — this document |
| All international fail, domestic OK | GFW/proxy routing issue — check rules |

### Step 2: Detect TUN Mode Fake DNS

Shadowrocket TUN mode hijacks DNS and returns fake IPs in the `198.18.x.x` range:

```bash
nslookup chatgpt.com
# Server:  198.18.0.2        ← Shadowrocket fake DNS server
# Address: 198.18.0.19       ← Fake IP assigned by TUN intercept
```

If DNS returns `198.18.x.x`, Shadowrocket TUN is intercepting. The real IP is hidden. TCP to port 443 will "succeed" (TUN intercepts it), but if the proxy can't forward the TLS handshake, you get `SSL_ERROR_SYSCALL`.

Compare with `always-real-ip` config in Shadowrocket DB:
```bash
sqlite3 "$HOME/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db" \
  "SELECT value FROM config WHERE name='always-real-ip';"
```

### Step 3: Test Target via Direct Proxy (Bypass TUN)

Test the target service through the proxy explicitly, bypassing TUN mode:

```bash
curl -m 15 --proxy 'http://user:pass@proxy-host:port/' -sS -o /dev/null \
  -w "HTTP %{http_code} in %{time_total}s\n" https://chatgpt.com/
```

If this also fails with `Proxy CONNECT aborted`, the proxy's exit IP is blocked by the target service.

### Step 4: Verify Proxy Actually Works for Other Sites

```bash
curl -m 15 --proxy 'http://user:pass@proxy-host:port/' https://ipinfo.io/json
```

If ipinfo works but chatgpt.com doesn't → confirmed service-specific blocking.

## Webshare Residential Proxy Specifics

Scope: apply this section only when diagnosing Webshare Direct/static proxies or Webshare API-managed proxy lists for a specific target service. Anti-condition: do not treat an old failure as a standing provider-wide verdict; retest current candidates and target endpoints.

- Webshare dashboard "Working" status only checks basic connectivity (their own health probe), NOT access to specific services like OpenAI.
- A node can show "Working" in the dashboard while being completely unable to reach chatgpt.com.
- Webshare residential IPs are commonly blocked by OpenAI/Cloudflare. Rotating to a new IP may or may not help — the entire IP pool may be flagged.
- `Replace Proxy` in Webshare dashboard gives a new IP, but there's no guarantee it's unblocked.
- If Shadowrocket is enabled, force Webshare testing outside the Shadowrocket tunnel with the physical interface, otherwise the TCP connection to the Webshare proxy may still route through `utun*`:

```bash
networksetup -listallhardwareports  # confirm Wi-Fi is en0 or find the active physical interface
curl --interface en0 -m 12 --proxy 'http://USER:PASS@IP:PORT/' https://ipinfo.io/json
```

- Distinguish target phases: `claude.ai` returning HTTP `403` after CONNECT and TLS is transport-reachable (Cloudflare challenge), while `chatgpt.com` / `api.openai.com` returning `000` with `Recv failure: Connection reset by peer` during CONNECT is a hard target-path failure before TLS.
- Webshare may expose multiple pools/plans under one account. Read `proxy/config/` and use the username shown for that pool; using a dashboard username against the API-managed pool can create false dead-proxy or `407` conclusions.

```bash
curl -H 'Authorization: Token APIKEY' 'https://proxy.webshare.io/api/v2/proxy/config/'
curl -H 'Authorization: Token APIKEY' 'https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page_size=100'
```

- Webshare replacement endpoint: `POST https://proxy.webshare.io/api/v2/proxy/replace/`. Use `dry_run: true` before real replacement. ASN-targeted replacement uses `asn_numbers` (plural list), e.g. `{"type":"asn","asn_numbers":["11426"],"count":2}`. Stop on `not_enough_replacements_in_subscription`; `no_proxies_to_be_replaced` usually means wrong plan/pool or IPs not visible to that API token.

## Shadowrocket Config Issues

### Missing Proxy Group

If rules say `PROXY` but no `proxy_group` section exists in the DB, traffic has nowhere to route:

```bash
sqlite3 -header -column "$DB" "SELECT docid, name, value, option FROM config WHERE section='proxy_group';"
# Empty = no proxy group = PROXY rules broken
```

### HTTP Proxy in TUN Mode

Shadowrocket TUN mode intercepts at the network layer. HTTP proxies work at the application layer. In TUN mode, HTTP proxies may fail to properly forward HTTPS traffic because:
1. TUN intercepts DNS → returns fake IP
2. TUN intercepts TCP to fake IP
3. Shadowrocket tries to route through HTTP proxy
4. HTTP proxy's CONNECT tunnel may not work correctly in this chain

Fix: Use SOCKS5 or VMess proxies for TUN mode, or switch to a config with a proper VPN node.

### Config File vs Database

Shadowrocket configs can exist as:
- `.conf` files (remote subscription, loaded into DB)
- Direct DB entries in `shadowrocket.db`

The DB is the active state. Check which config is active:
```bash
sqlite3 -header -column "$DB" "SELECT docid, section, name, substr(value,1,120) as value, option FROM config ORDER BY docid;"
```

## Fixes

1. **Switch to an unblocked exit IP**: Change VPN node, rotate Webshare IP, or use a different proxy provider.
2. **Switch Shadowrocket config**: If one config has a working non-blocked node (e.g., Japan residential), switch to it.
3. **Add target domains to DIRECT rule**: If the service works from your real IP but not through VPN, route it directly.
4. **Use a different proxy protocol**: SOCKS5 or VMess instead of HTTP proxy for TUN mode.

## Pitfalls

- Don't assume "VPN works" means all sites are reachable. Always test the specific target service.
- Don't trust proxy dashboard "Working" status for service-specific access.
- `SSL_ERROR_SYSCALL` ≠ SSL/TLS configuration issue. It usually means the connection was reset by the remote end (blocked IP).
- Webshare "Replace Proxy" may give another blocked IP. The entire pool may be flagged by the target service.
- Shadowrocket auto-falls back to a previous config when the current one's nodes fail silently — check which config is actually active.
