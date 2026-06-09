---
name: macos-network-admin
description: "Use when diagnosing macOS network/proxy/VPN issues — system proxy misconfiguration, proxy app not running, subscription URL unreachable, DNS failures, or 'sites won't load' reports. Covers macOS `networksetup` proxy management, proxy process discovery, Clash/Mihomo/FlClash/Shadowrocket config extraction, and the proxy chicken-and-egg problem."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - macos
    - network
    - proxy
    - vpn
    - troubleshooting
    - clash
    - mihomo
    - flclash
    - shadowrocket
    - devops
    - devops
---

# macOS Network Admin

## Overview

Systematic diagnosis and resolution of macOS network/proxy/VPN issues. Covers the full chain: system proxy settings → proxy process → proxy app → subscription/config → upstream reachability.

## When to Use

- User reports "sites won't load", "can't reach Google/GitHub", "internet broken"
- Suspected proxy misconfiguration or proxy app failure
- Need to check, set, or clear macOS system proxy settings
- Proxy/VPN app configuration extraction (subscription URL, port, mode)
- DNS resolution failures for proxied domains
- The "chicken-and-egg" problem: need proxy to fetch subscription, need subscription to start proxy

## Diagnostic Flow (5-Phase)

### Phase 1: Connectivity Triage

Test domestic vs international sites to isolate the problem:

```
curl -s -o /dev/null -w 'HTTP %{http_code}' https://www.baidu.com --max-time 10
curl -s -o /dev/null -w 'HTTP %{http_code}' https://www.google.com --max-time 10
curl -s -o /dev/null -w 'HTTP %{http_code}' https://github.com --max-time 10
```

| Domestic OK | International OK | Diagnosis |
|---|---|---|
| ✅ | ✅ | Network fine — problem is elsewhere |
| ✅ | ❌ | Proxy/GFW issue — continue to Phase 2 |
| ❌ | ❌ | Physical network down — check Wi-Fi/Ethernet |

### Phase 2: System Proxy Settings

```bash
# Read current proxy state
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
networksetup -getsocksfirewallproxy Wi-Fi

# Clear all proxy settings
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off
networksetup -setsocksfirewallproxystate Wi-Fi off
networksetup -setproxyautodiscovery Wi-Fi off
```

Key indicators: "Enabled: Yes" + proxy pointing to localhost (127.0.0.1:XXXX) means a local proxy app is expected to be running.

### Phase 3: Proxy Process & Port Check

```bash
# Check if proxy software is running
ps aux | grep -iE 'clash|mihomo|v2ray|sing-box|surge|trojan|shadowsocks|proxifier|flclash' | grep -v grep

# Check if the configured proxy port is listening
lsof -i :7892    # or whatever port the system proxy points to

# Check common proxy ports
lsof -i :7890 -i :7891 -i :7892 -i :1080 -i :10808
```

If the port is not listening but the system proxy points to it → proxy app is not running.

### Phase 4: Find the Proxy App & Config

See `references/macos-proxy-app-config-discovery.md` for the full extraction playbook.

Quick steps:
1. `ls /Applications/ | grep -iE 'clash|verge|proxy|vpn|lite|fmapp'`
2. Find bundle ID from `Info.plist`
3. Config at `~/Library/Application Support/<bundle-id>/`
4. Preferences at `~/Library/Preferences/<bundle-id>.plist`
5. Decode plist: `plutil -convert json -o - <plist>`

**Shadowrocket-specific**: Config lives at `~/Library/Group Containers/group.com.liguangming.Shadowrocket/`. See `references/shadowrocket-config-analysis.md` for rule.db binary format, policy group decoding, and TUN mode diagnostics.

### Phase 5: Subscription/Upstream Verification

Test each URL in the subscription chain:
```bash
curl -s -o /dev/null -w 'HTTP %{http_code}' 'https://subscription-url...' --max-time 10
nslookup subscription-domain.com
nc -z -w 5 subscription-domain.com port
```

## Common Pitfalls

1. **Chicken-and-egg**: Proxy app needs network to fetch subscription config, but network needs proxy to reach subscription server. Solution: temporarily connect via phone hotspot or different network.

2. **Clearing proxy without understanding why it was set**: If the proxy was intentional (for GFW bypass), clearing it "fixes" nothing — you lose access to international sites. Always test international reachability AFTER clearing.

3. **Stale subscription server**: VPN providers change subscription domains. The old URL may DNS-fail even though the service is fine. Check the provider's dashboard for the current URL.

4. **macOS Wi-Fi vs Ethernet**: `networksetup` commands use the service name. If the user is on Ethernet, replace `Wi-Fi` with `Ethernet` or `USB 10/100/1000 LAN`. Check with `networksetup -listallnetworkservices`.

5. **FlClash/Clash mixed-port**: FlClash (肥猫云) uses `mixed-port: 7892` by default. This is a single port handling HTTP+SOCKS. The system proxy should point to this port for both HTTP and HTTPS.

6. **Encrypted config files**: Some apps (FlClash/肥猫云) store `config.yaml` as encrypted/encoded data. The real config is in the macOS Preferences plist (`~/Library/Preferences/<bundle-id>.plist`), which stores subscription URLs, API base URLs, and app settings as JSON.

## References

- `references/macos-proxy-commands.md` — complete `networksetup` proxy command reference
- `references/macos-proxy-app-config-discovery.md` — how to find proxy app config files by bundle ID
- `references/shadowrocket-config-analysis.md` — Shadowrocket rule.db binary format, policy group decoding, TUN mode diagnostics

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Findings include evidence, severity/rubric calibration, and false-positive controls.
