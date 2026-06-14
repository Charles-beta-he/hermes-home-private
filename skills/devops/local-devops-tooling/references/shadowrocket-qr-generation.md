---
name: shadowrocket-qr-generation
description: "Generate phone-scannable Shadowrocket add QR codes from local macOS Shadowrocket databases without leaking proxy credentials."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [macos, shadowrocket, proxy, qr, sqlite, verification]
---

# Shadowrocket QR Generation from Local DB

Use when the user asks for a QR code to add an existing Shadowrocket/Webshare/proxy node on a phone, especially after a local Shadowrocket node was edited or refreshed.

## Classification

Reusable procedure / verification checklist. Concrete node names, IPs, ports, usernames, passwords, generated file paths, and validation results from a session are session evidence only; do not store them in memory or SKILL.md.

## Workflow

1. Locate candidate Shadowrocket DBs, preferring the live container DB, then iCloud-synced DBs:

```bash
~/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db
~/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/sub.db
~/Library/Mobile Documents/iCloud~com~liguangming~Shadowrocket/Documents/*.db
~/Library/Group Containers/group.com.liguangming.Shadowrocket/**/*.db
```

2. Query the `config` FTS table, not only ordinary SQLite tables. Proxy rows commonly look like:

```text
section='proxy'
name='<node name>'
value='http, <host>, <port>, <username>, <password>'
```

3. Pick the requested node. If the user says "latest", sort by `coalesce(created,0) desc, docid desc` within the relevant proxy rows. Do not guess from screenshots if the DB has the actual config.

4. Build the proxy URL with percent-encoded credentials and node fragment:

```text
http://<urlencoded-user>:<urlencoded-password>@<host>:<port>#<urlencoded-node-name>
```

5. For Shadowrocket add flow, encode that proxy URL inside:

```text
shadowrocket://add?url=<percent-encoded-proxy-url>
```

6. Generate a PNG QR for phone scanning. In CLI contexts, also print an ASCII QR if useful, but prefer writing a PNG path because terminal-rendered QR blocks can be distorted by font/line-height.

7. Verify without exposing secrets:
   - Confirm the QR payload shape (`shadowrocket://add?url=<encoded proxy url>`), not the raw credentials.
   - Optionally probe the explicit proxy with `curl -x` and `-U`, but redact credentials from logs and final output.
   - If validation returns `407` / invalid authentication, report: "QR can add the saved configuration, but the saved credentials may be stale or unsynced." Do not present the node as working.

## Minimal Generator Pattern

```python
import os, sqlite3, urllib.parse, qrcode, pathlib

DB = os.path.expanduser('~/Library/Containers/com.liguangming.Shadowrocket/Data/Documents/Databases/shadowrocket.db')
con = sqlite3.connect(DB)
name, value, created = con.execute('''
select name,value,created from config
where section='proxy' and lower(value) like 'http,%'
order by coalesce(created,0) desc, docid desc limit 1
''').fetchone()
proto, host, port, user, pw = [p.strip() for p in value.split(',', 4)]
proxy_url = f"http://{urllib.parse.quote(user, safe='')}:{urllib.parse.quote(pw, safe='')}@{host}:{port}#{urllib.parse.quote(name)}"
add_url = 'shadowrocket://add?url=' + urllib.parse.quote(proxy_url, safe='')
out = pathlib.Path.home() / 'Desktop' / f'shadowrocket-add-{name}.png'
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=4)
qr.add_data(add_url); qr.make(fit=True)
qr.make_image(fill_color='black', back_color='white').save(out)
print(out)
```

## Reporting Pattern

Report only:

```text
节点名：<name>
Host：<host>
Port：<port>
PNG：<path>
验证：<working / failed with redacted reason>
```

Never print raw username/password or full proxy URL in the final answer unless the user explicitly asks for credentials and it is safe in the current channel.

## Pitfalls

- A QR that adds a config is not proof the proxy works. Validate separately when usability matters.
- `curl -x http://user:pass@host:port` can leak credentials in shell history/process listings. Prefer `curl -x http://host:port -U user:pass` inside a short-lived script and redact output.
- Shadowrocket supports raw proxy URLs, but `shadowrocket://add?url=...` is the safer phone-scan payload for opening the add flow directly.
- Multiple DBs can contain backups or iCloud copies. Check live container DB first and surface which DB was used.
