---
name: shadowrocket-webshare-qr-import
description: "Operational pattern for turning Webshare dashboard proxy rows into Shadowrocket-importable QR codes and verifying whether import success equals real proxy/VPN success."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [shadowrocket, webshare, proxy, qr, ios, macos, verification]
---

# Shadowrocket Webshare QR Import

Use when the user has current Webshare proxy rows and wants a phone-scannable Shadowrocket configuration, especially when the phone has no working proxy/VPN yet.

## Key Lessons

1. **Import success is not VPN success.** A QR can add a node while the proxy still fails. Verify by enabling the node and checking real egress with `https://ipinfo.io` or `https://api.ipify.org`.
2. **Shadowrocket app-scheme QR can be ignored by iOS.** If scanning `shadowrocket://add?url=...` causes no visible change, generate a second QR containing the plain proxy URL (`http://user:pass@host:port#name`) and scan it inside Shadowrocket's built-in QR scanner.
3. **Local Shadowrocket DB can be stale.** Nodes from `shadowrocket.db` may differ from the current Webshare dashboard after “Replace Proxy” or IP rotation. If explicit proxy tests return 407 while Webshare shows new Working rows, regenerate from the dashboard/export, not the old DB.
4. **Dashboard “Working” still needs client-side proof.** Treat Webshare status as provider-side evidence only. Client network path can still timeout or fail; final acceptance is phone Shadowrocket connected + external egress IP matches the chosen proxy.
5. **Avoid leaking secrets.** Do not print passwords in final answers. Generate QR files/pages locally and describe host/port/status; redact credentials in reports.

## Procedure

1. Gather current proxy rows from Webshare dashboard/export:
   - `host`
   - `port`
   - `username`
   - `password`
   - country/status if visible
2. Prefer current dashboard/export over previously stored Shadowrocket DB entries when they disagree.
3. For each proxy, generate two QR payloads:
   - App scheme: `shadowrocket://add?url=<urlencoded plain_proxy_url>`
   - Plain proxy URL: `http://<urlencoded-user>:<urlencoded-pass>@<host>:<port>#<urlencoded-name>`
4. If the phone has no VPN/proxy yet, serve a local HTML page on the Mac LAN containing both QRs:
   - bind a simple HTTP server to `0.0.0.0`
   - verify `http://127.0.0.1:<port>/` and `http://<lan-ip>:<port>/` return 200
   - warn that the page contains proxy credentials and must only be used on a trusted LAN
5. On the phone:
   - open the LAN URL or scan the Mac screen
   - first try the direct Shadowrocket add button/QR
   - if no change, open Shadowrocket and use its built-in scanner on the plain proxy URL QR
6. Verification:
   - choose the imported node in Shadowrocket
   - enable VPN and confirm iOS VPN indicator
   - browse to `https://ipinfo.io`
   - verify the exit IP/geo matches the chosen Webshare proxy

## Minimal QR Generation Snippet

```python
import pathlib, urllib.parse, qrcode

root = pathlib.Path('/tmp/shadowrocket-webshare-import')
root.mkdir(parents=True, exist_ok=True)

proxies = [
    {'name': 'Japan-Webshare-1', 'host': '203.0.113.10', 'port': '6375'},
]
username = 'USERNAME'
password = 'PASSWORD'

for p in proxies:
    plain = (
        'http://'
        f"{urllib.parse.quote(username, safe='')}:"
        f"{urllib.parse.quote(password, safe='')}@"
        f"{p['host']}:{p['port']}#"
        f"{urllib.parse.quote(p['name'])}"
    )
    scheme = 'shadowrocket://add?url=' + urllib.parse.quote(plain, safe='')
    qrcode.make(plain).save(root / f"{p['name']}-plain-proxy-url.png")
    qrcode.make(scheme).save(root / f"{p['name']}-shadowrocket-add.png")
```

## Failure Interpretation

- Scan adds a node but browsing fails: import path worked; test auth/connectivity/rules.
- `407`/auth failure from explicit proxy tests: credentials are stale/wrong or provider authorization mode changed.
- Timeout from explicit proxy tests while Webshare says Working: provider-side check passed but current client network path or CONNECT path may be blocked; verify from the phone before declaring unusable.
- Node name appears as mojibake/garbage after scan: usually a display/encoding issue with the fragment/remark; host/port/auth fields matter more than the display name.
