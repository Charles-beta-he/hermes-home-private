# Hermes ↔ Rokid 灵珠自定义三方智能体桥接

Use this reference when the user wants Hermes exposed to Rokid smart glasses / 灵珠平台 as a long-running assistant entrypoint.

## Platform facts from the session

Rokid 灵珠 supports importing a custom third-party agent via an SSE endpoint. The custom-agent registration needs:

- 智能体名称
- 智能体 ID
- 智能体 SSE 接口地址
- 智能体鉴权 AK
- 功能介绍 / 开场白 / 图标
- 入参类型：start with text; add image after MVP

Expected request shape:

- Header: `Authorization: Bearer <AK>`
- Header: `Content-Type: application/json`
- Body includes `message_id`, `agent_id`, `message[]`, optional `user_id`, optional `metadata.context`
- `message[]` entries include `role`, `type` (`text`/`image`), `text`, `image_url`
- `metadata.context` may include `location`, `latitude`, `longitude`, `weather`, `battery`

Expected SSE response shape:

```text
event: message
data: {"role":"agent","message_id":"...","agent_id":"...","answer_stream":"...","is_finish":false,"type":"answer"}

event: done
data: {"role":"agent","message_id":"...","agent_id":"...","answer_stream":"","is_finish":true,"type":"answer"}
```

Supported tool-call commands in the Rokid protocol include:

- `take_photo`
- `take_navigation`
- `notify_agent_off`
- `control_calendar`

Treat these as high-impact actions: add explicit permission gates before returning tool calls that mutate state, navigate, or interact with external services.

## Recommended MVP architecture

Do not expose Hermes itself directly to the public internet. Put a small bridge in front:

```text
Rokid Glasses / Rokid AI App
  -> Rokid 灵珠 custom-agent SSE
  -> Hermes-Rokid Bridge (FastAPI/StreamingResponse)
  -> Hermes CLI or internal Hermes API
```

MVP bridge responsibilities:

1. Provide `POST /rokid/sse`.
2. Fail closed if `ROKID_AGENT_AK` is not configured.
3. Verify `Authorization: Bearer <AK>` exactly.
4. Parse Rokid `message[]` and device context.
5. Add an eye-glasses prompt hint: short answer first, no long tables, ask before high-impact actions.
6. Call Hermes with `hermes chat -q ... --quiet --max-turns 1` for the first version.
7. Convert the result to Rokid SSE `message` chunks plus final `done`.
8. Add `GET /health` for tunnel/launchd checks.

## Local project skeleton

A good local home is:

```text
~/.hermes/hermes-rokid-bridge/
  app.py
  requirements.txt
  .env                    # chmod 600; contains ROKID_AGENT_AK
  run.sh                  # dev runner, creates/uses .venv
  run_service.sh          # launchd runner for bridge only
  run_tunnel_service.sh   # launchd runner for temporary Cloudflare tunnel
  update_current_endpoint.sh
  current_public_endpoint.env
```

Minimal dependencies:

```text
fastapi
uvicorn[standard]
pydantic
```

## Public URL options in China

For MVP:

- Cloudflare `trycloudflare.com` tunnel is the fastest no-login path.
- It can work for immediate Rokid true-device testing.
- It is not stable: URL changes when the tunnel restarts.

For longer-term stability:

- Cloudflare named tunnel + owned domain, after the user completes `cloudflared tunnel login` in their real browser.
- Or a Hong Kong / mainland cloud server with HTTPS reverse proxy to the bridge.
- For mainland 80/443 + custom domain, consider ICP requirements.

## Cloudflare temporary tunnel pattern

Install if missing:

```bash
brew install cloudflared
```

Run temporary tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8787 --no-autoupdate --metrics 127.0.0.1:20241
```

Discover current `trycloudflare.com` URL without relying on stdout capture:

```bash
curl -sS http://127.0.0.1:20241/metrics \
  | sed -n 's/.*userHostname="\(https:\/\/[^\"]*trycloudflare.com\)".*/\1/p' \
  | head -1
```

Check readiness:

```bash
curl -sS http://127.0.0.1:20241/ready
```

## macOS LaunchAgent pattern

For a recoverable local MVP, create two user LaunchAgents:

- `com.charles.hermes-rokid-bridge` — runs `run_service.sh`
- `com.charles.hermes-rokid-tunnel-temp` — runs `run_tunnel_service.sh`

Use `RunAtLoad` and `KeepAlive`; log to files under the bridge directory. After bootstrap:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.charles.hermes-rokid-bridge.plist
launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-bridge
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.charles.hermes-rokid-tunnel-temp.plist
launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-tunnel-temp
```

Verification:

```bash
curl -sS http://127.0.0.1:8787/health
curl -sS http://127.0.0.1:20241/ready
./update_current_endpoint.sh
```

## Fixed Cloudflare tunnel caveat

`cloudflared tunnel login` requires browser account authorization and creates `~/.cloudflared/cert.pem`. If the agent browser hits Cloudflare bot-detection or an empty dashboard page, do not declare Cloudflare unusable. Keep the temporary tunnel running and ask the user to complete the login in their normal browser. Once `cert.pem` exists, continue with named tunnel creation and DNS routing.

## Rokid Lingzhu registration values

For MVP, tell the user to fill:

- SSE URL: `https://<current-host>/rokid/sse`
- Agent ID: configured `ROKID_AGENT_ID`, e.g. `hermes-rokid`
- AK: configured `ROKID_AGENT_AK` from `.env` (do not commit or repeat secrets unnecessarily)
- 入参类型: `文字`

## Verification payload

Use a local JSON payload, then test both local and public endpoints:

```json
{
  "message_id": "test-1",
  "agent_id": "hermes-rokid",
  "message": [{"role": "user", "type": "text", "text": "只回复 ROKID_OK"}],
  "metadata": {"context": {"location": "西安", "weather": "晴", "battery": "80%"}}
}
```

Expected SSE includes:

- first `event: message` with empty/initial stream allowed
- subsequent `event: message` containing `ROKID_OK`
- final `event: done` with `is_finish: true`

## Pitfalls

- Do not expose raw Hermes/Gateway directly; expose only the bridge.
- Do not run with missing AK; fail closed.
- Do not treat `trycloudflare.com` as a fixed production URL.
- Do not preserve real AKs in skills, docs, or examples.
- Rokid/eye-glasses UX needs concise answers by default; avoid long Markdown/table output.
- If a temporary tunnel is restarted under launchd, the public URL changes; refresh `current_public_endpoint.env` from metrics before giving the URL to the user.
