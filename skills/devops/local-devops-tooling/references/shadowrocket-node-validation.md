---
name: shadowrocket-node-validation
description: "Validated workflow for checking individual Shadowrocket proxy/VPN nodes on macOS, including extracting node config from the app database and verifying real egress instead of trusting UI latency."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [macos, shadowrocket, proxy, vpn, sqlite, verification]
---

# Shadowrocket Node Validation on macOS

Scope: general macOS Shadowrocket diagnostics. Do not treat the concrete hostnames, IPs, usernames, or active node names from one session as durable facts.

Use this when the user points at one or more Shadowrocket nodes and asks whether the VPN/proxy addresses work.

## Key Lesson

Shadowrocket UI latency only proves the app's own probe got a response. It does not prove the node works as an HTTP/HTTPS proxy for real traffic. Verify both:

1. current active system egress, and
2. each target node as an explicit proxy.

## Locate Node Config

Common macOS/iPad-app-on-mac locations:

```bash
$HOME/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db
$HOME/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/sub.db
$HOME/Library/Group\ Containers/group.com.liguangming.Shadowrocket/
```

Inspect the main DB:

```bash
sqlite3 "$HOME/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db" '.tables'
sqlite3 -header -column "$HOME/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db" \
  "select docid, section, name, value, option, ext, remarks, created from config where section='proxy';"
```

For a named node:

```bash
sqlite3 -header -column "$HOME/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db" \
  "select name,value from config where name like '%Residential%' or remarks like '%Residential%' or value like '%Residential%';"
```

Observed HTTP node value shape:

```text
http, <host>, <port>, <username>, <password>
```

## Verify Current Active Egress

```bash
scutil --proxy
route -n get default
curl -m 10 -sS https://api.ipify.org
curl -m 15 -sS https://ipinfo.io/json
curl -m 15 -x http://127.0.0.1:<local-proxy-port> -sS https://ipinfo.io/json
```

This distinguishes "the app/system is currently using a different node" from "the requested nodes work".

## Verify Each Target Node

Do not stop at `nc`/TCP success. A residential proxy can accept TCP but never complete HTTP/CONNECT.

Minimal Python probe:

```python
import base64, os, socket, sqlite3, time

DB = os.path.expanduser('~/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db')
conn = sqlite3.connect(DB)
for name, value in conn.execute("select name,value from config where section='proxy'"):
    proto, host, port, user, pw = [p.strip() for p in value.split(',', 4)]
    if proto != 'http':
        continue
    auth = base64.b64encode(f'{user}:{pw}'.encode()).decode()
    req = (
        'CONNECT api.ipify.org:443 HTTP/1.1\r\n'
        'Host: api.ipify.org:443\r\n'
        f'Proxy-Authorization: Basic {auth}\r\n'
        'User-Agent: NodeCheck/1.0\r\n\r\n'
    )
    s = socket.socket(); s.settimeout(8)
    t = time.perf_counter()
    try:
        s.connect((host, int(port)))
        s.sendall(req.encode())
        data = s.recv(2048)
        print(name, host, port, round((time.perf_counter()-t)*1000), data.splitlines()[:1])
    except Exception as e:
        print(name, host, port, 'FAIL', type(e).__name__, str(e), round((time.perf_counter()-t)*1000))
    finally:
        s.close()
```

For full egress checks, use an explicit proxy opener or `curl -x` with credentials and fetch:

- `https://api.ipify.org`
- `https://ipinfo.io/json`
- `https://www.cloudflare.com/cdn-cgi/trace`
- `https://www.google.com/generate_204`

## Reporting Pattern

For each node, report:

- configured host:port
- geo/ASN of the configured host IP
- TCP port result
- actual proxy HTTP/HTTPS result and timeout/status
- whether the current active system exit IP matches the requested node

Example conclusion language:

```text
端口能通，但代理应用层无响应；不要只按 Shadowrocket 延迟判断可用。
当前系统出口是 X，不是这两个节点。
```

## Pitfalls

- Do not print usernames/passwords in the final answer.
- Do not claim a node is usable from TCP success alone.
- Do not overwrite or switch the user's active VPN without explicit permission.
- Shadowrocket DB schema may be FTS3 (`config`, `config_content`, `config_segments`, `config_segdir`); query `config`, not only ordinary tables.
- If a node passes basic validation but the user's target service (e.g., OpenAI) still fails, the node's exit IP may be on that service's blocklist. See `references/shadowrocket-service-specific-blocking.md` for the multi-site isolation and service-specific blocking diagnostic flow.
