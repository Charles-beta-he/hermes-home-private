# Rokid Lingzhu custom-agent bridge for Hermes

Use this reference when connecting Hermes to Rokid smart glasses through Rokid 灵珠/Rizon custom third-party agents.

## When to use

- User wants Hermes/assistant reachable from Rokid Glasses or Rokid AI App.
- User provides `https://rizon.rokid.com` / 灵珠 platform docs.
- Need a public HTTPS SSE endpoint for a custom third-party agent.
- Need to stabilize a temporary tunnel into a fixed domain.

## Platform facts from Lingzhu docs

Lingzhu supports custom third-party agent import. Required fields include:

- agent name
- agent ID
- agent SSE endpoint URL
- agent auth AK
- description/opening/icon
- input type: text first; add image after MVP

Incoming request shape:

```json
{
  "message_id": "...",
  "agent_id": "...",
  "message": [
    {"role": "user", "type": "text", "text": "..."}
  ],
  "user_id": "...",
  "metadata": {
    "context": {
      "location": "...",
      "latitude": "...",
      "longitude": "...",
      "weather": "...",
      "battery": "..."
    }
  }
}
```

Auth header expected by the bridge:

```text
Authorization: Bearer <agent AK>
```

SSE response events should include `message` chunks and a final `done` event. Data payload fields used by Lingzhu:

- `role: "agent"`
- `message_id`
- `agent_id`
- `answer_stream`
- `is_finish`
- `type: "answer"`

Optional tool calls supported by docs include:

- `take_photo`
- `take_navigation`
- `notify_agent_off`
- `control_calendar`

## Preferred MVP architecture

Do not expose Hermes directly to the public internet. Put a narrow bridge in front:

```text
Rokid Glasses / Rokid AI App
  -> Lingzhu custom third-party agent HTTPS SSE
  -> hermes-rokid-bridge on localhost/cloud/VPS
  -> Hermes CLI/API/Gateway
```

MVP service shape:

```text
~/.hermes/hermes-rokid-bridge/
  app.py
  requirements.txt
  .env
  run.sh
  run_service.sh
  run_tunnel_service.sh
  update_current_endpoint.sh
  current_public_endpoint.env
```

Useful defaults:

```text
ROKID_AGENT_ID=hermes-rokid
ROKID_AGENT_AK=<token_urlsafe secret>
HERMES_BIN=/Users/charles/.hermes/hermes-agent/venv/bin/hermes
HERMES_TIMEOUT_SECONDS=90
```

FastAPI endpoint contract:

- `GET /health` returns `{ok, app, agent_id, auth_configured, time}`
- `POST /rokid/sse` validates Bearer AK, parses Lingzhu JSON, calls Hermes, streams SSE
- optional `POST /rokid/callback/message` can acknowledge Lingzhu callback protocol

Hermes CLI call for MVP:

```bash
hermes chat -q "$PROMPT" --quiet --max-turns 1
```

For glasses UX, prepend a prompt hint: short voice/glasses-friendly replies; if complex, give conclusion + next step; confirm before high-impact actions.

## Public endpoint options in China

1. **Temporary MVP:** `cloudflared tunnel --url http://127.0.0.1:8787 --no-autoupdate --metrics 127.0.0.1:20241`
   - no Cloudflare login needed
   - gives `https://*.trycloudflare.com`
   - address changes when tunnel restarts
   - enough for Lingzhu protocol and real-device testing
2. **Fixed Cloudflare Tunnel:** requires Cloudflare account with at least one DNS Zone/domain.
   - `cloudflared tunnel login` will show an empty zone picker if the account has no domain.
   - buy/add a domain first, then authorize.
   - create named tunnel and route DNS to e.g. `rokid.<domain>`.
3. **Long-term China-stable:** Hong Kong/mainland VPS + Caddy/Nginx + frp/rathole/WireGuard back to local bridge, or deploy the bridge on the VPS.

## Cloudflare fixed tunnel sequence

Prerequisite: `~/.cloudflared/cert.pem` exists after successful browser authorization. If it does not exist, do not keep retrying tunnel creation; finish Cloudflare zone authorization first.

```bash
cloudflared tunnel login
cloudflared tunnel create hermes-rokid
cloudflared tunnel route dns hermes-rokid rokid.<domain>
```

Create config under `~/.cloudflared/config.yml` or a project-specific config:

```yaml
tunnel: <tunnel-uuid>
credentials-file: /Users/charles/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: rokid.<domain>
    service: http://127.0.0.1:8787
  - service: http_status:404
```

Run:

```bash
cloudflared tunnel run hermes-rokid
```

## LaunchAgent pattern on macOS

Use two LaunchAgents for recoverability:

- `com.charles.hermes-rokid-bridge`: runs local FastAPI bridge on `127.0.0.1:8787`
- `com.charles.hermes-rokid-tunnel-temp` or fixed-tunnel variant: runs cloudflared

Use absolute paths in plist and scripts. Validate with:

```bash
plutil -lint ~/Library/LaunchAgents/com.charles.hermes-rokid-bridge.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.charles.hermes-rokid-bridge.plist
launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-bridge
curl -sS http://127.0.0.1:8787/health
```

For temporary trycloudflare endpoint discovery, enable metrics and parse:

```bash
curl -sS http://127.0.0.1:20241/metrics \
  | sed -n 's/.*userHostname="\(https:\/\/[^\"]*trycloudflare.com\)".*/\1/p' \
  | head -1
```

Store current endpoint in `current_public_endpoint.env` with:

```text
PUBLIC_BASE_URL=...
SSE_URL=.../rokid/sse
HEALTH_URL=.../health
AGENT_ID=hermes-rokid
AK_LOCATION=.../.env:ROKID_AGENT_AK
```

## Verification checklist

Before telling the user it is ready:

1. Local health:
   ```bash
   curl -sS http://127.0.0.1:8787/health
   ```
2. Unauthorized request should fail.
3. Authorized local SSE returns `event: message` and final `event: done`.
4. Public health via tunnel returns ok.
5. Public authorized SSE returns a known sentinel such as `ROKID_OK`.
6. Record the exact SSE URL, agent ID, and AK location; do not expose secrets unless user needs to paste them.

## Pitfalls

- `trycloudflare.com` URLs are temporary; do not promise they are stable.
- Cloudflare Tunnel fixed-domain login requires a Cloudflare DNS Zone. Empty zone picker means no domain/zone in that account, not a cloudflared bug.
- Browser automation may not share the user’s local Cloudflare login session and may be blocked by Turnstile; prefer opening the URL in the user’s local browser with `open` when user is present.
- Do not call “fixed tunnel done” until `~/.cloudflared/cert.pem`, named tunnel credentials JSON, DNS route, and public SSE are all verified.
- For `.dev` domains, HTTPS is mandatory by design; this fits SSE but makes local/plain HTTP subdomain testing impossible.
- Keep high-impact Hermes actions behind confirmation when invoked through glasses.
