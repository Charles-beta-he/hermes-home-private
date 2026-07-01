# Xiaohongshu fake-IP browser triage

Applicability: macOS browser or Hermes browser/computer-use session cannot open Xiaohongshu with `ERR_SSL_PROTOCOL_ERROR`, `SSL: WRONG_VERSION_NUMBER`, or `tlsv1 alert protocol version`, especially while Shadowrocket/Clash-style fake-IP DNS is active.

Anti-conditions: do not save this as a general claim that Xiaohongshu or the browser tool is broken. This is a network/proxy diagnosis path. Do not type passwords/SMS codes; let the user scan/login if needed.

## Symptom pattern

- Browser shows `ERR_SSL_PROTOCOL_ERROR` for `https://www.xiaohongshu.com`.
- Direct TLS probe returns wrong-version/protocol errors.
- DNS resolves Xiaohongshu domains to `198.18.0.0/15` fake-IP addresses.
- macOS proxy exceptions include `198.18.0.0/15`, causing the browser to bypass the local proxy and connect directly to fake IP.

## Read-only checks

```bash
python3 - <<'PY'
import ssl, socket
host='www.xiaohongshu.com'
try:
    ctx=ssl.create_default_context()
    with socket.create_connection((host,443),timeout=10) as sock:
        with ctx.wrap_socket(sock,server_hostname=host) as ss:
            print('TLS OK', ss.version())
except Exception as e:
    print(type(e).__name__, e)
PY

python3 - <<'PY'
import socket
for host in ['www.xiaohongshu.com','www.xiaohongshu.com.cn','edith.xiaohongshu.com','www.xhslink.com']:
    try:
        print(host, socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)[:3])
    except Exception as e:
        print(host,e)
PY

scutil --proxy | sed -n '1,80p'
```

If the host resolves to `198.18.x.x` and `scutil --proxy` excludes `198.18.0.0/15`, the browser is likely bypassing proxy for fake-IP.

## Temporary user-login browser workaround

Use public DNS to find a real IP, then open an isolated Chrome profile with host resolver override and no proxy. This avoids mutating system proxy settings and keeps the user login isolated.

```bash
for dns in 223.5.5.5 119.29.29.29 8.8.8.8; do
  echo DNS $dns
  dig @$dns +short www.xiaohongshu.com A | sed -n '1,10p'
done
```

Probe a candidate real IP:

```bash
curl -I --max-time 15 --noproxy '*' \
  --resolve www.xiaohongshu.com:443:<REAL_IP> \
  https://www.xiaohongshu.com/explore
```

Open temporary Chrome:

```bash
rm -rf /tmp/hermes-xhs-profile
open -na "Google Chrome" --args \
  --user-data-dir=/tmp/hermes-xhs-profile \
  --no-first-run \
  --host-resolver-rules='MAP www.xiaohongshu.com <REAL_IP>, MAP www.xiaohongshu.com.cn <REAL_IP>, MAP edith.xiaohongshu.com <REAL_IP>, EXCLUDE localhost' \
  --no-proxy-server \
  https://www.xiaohongshu.com/explore
```

Notes:

- Chrome will display a command-line flag warning; it is expected for the temporary profile.
- Prefer QR login controlled by the user. Stop at passwords, SMS, captcha, payment, identity, or biometric gates.
- After evidence collection, close Chrome and delete `/tmp/hermes-xhs-profile`.

## When to choose another path

- If real-IP probing fails or the site triggers risk controls, ask for Xiaohongshu app screenshots/screen recordings and OCR them.
- If the task is only high-level brainstorming, do not spend time forcing web login; use weak evidence clearly labeled as such.
