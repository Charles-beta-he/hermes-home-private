# Hermes Rokid Bridge

Minimal Rokid Lingzhu custom-agent SSE bridge for Hermes.

## Current production endpoint

- Health: `https://rokid.hecheng.dev/health`
- SSE: `https://rokid.hecheng.dev/rokid/sse`
- Agent ID: `hermes-rokid`
- Auth value: see local `.env`; do not paste it into docs.

## Local run

```bash
cd ~/.hermes/hermes-rokid-bridge
./run.sh
```

## LaunchAgents

Bridge service:

```bash
launchctl print gui/$(id -u)/com.charles.hermes-rokid-bridge
launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-bridge
```

Named Cloudflare tunnel service:

```bash
launchctl print gui/$(id -u)/com.charles.hermes-rokid-tunnel
launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-tunnel
```

## Health

```bash
curl http://127.0.0.1:8787/health
curl https://rokid.hecheng.dev/health
```

## SSE test

Use `curl` for public smoke tests. Python `urllib` can be affected by local/system proxy settings and may show a misleading Cloudflare `403` even when the tunnel and bridge are healthy.

```bash
# Put the local .env auth value into ROKID_SMOKE_VALUE for this one command.
ROKID_SMOKE_VALUE='<copy value from .env>' ./deploy/mainland/scripts/smoke_sse.sh https://rokid.hecheng.dev
```

Expected: non-empty `event: message` ACK, answer chunks, then `event: done` with `is_finish: true`.

Recommended regression smoke cases after bridge changes:

- 能力菜单：`你能做什么` → short voice menu includes `今天任务 / 日报 / 记一下 / 后台进度 / 确认执行`.
- 图片输入 without vision route → says image was received and asks for text or “后台分析图片”; it must not hallucinate image content.
- 高影响动作：`帮我发 Telegram 给张三说十点开会` → confirm-first draft; it must not claim `已发送`.

## Long-term glasses entry invariants

- Missing `user_id` must not fall back to the shared `agent_id` session. Use an anonymous/message-scoped session key to avoid one user's voice draft confirming another user's task.
- L0/L1 answers must be voice-safe: no Markdown tables, no long dumps; post-clamp model output before streaming to the glasses.
- Device context (`metadata.context`) and image URLs are private. They can guide prompts, but image-only input must go through an explicit vision/background route before any content description.
- High-impact actions such as messaging, calendar, navigation, device control, and task commits are confirm-first and require execution evidence before saying done.

## Lingzhu fields

- Overseas/fallback SSE URL: `https://rokid.hecheng.dev/rokid/sse`
- Mainland primary SSE URL: use an ICP-approved mainland HTTPS domain such as `https://rokid-cn.<domain>/rokid/sse`; see `deploy/mainland/`.
- Agent ID: `hermes-rokid`
- Check value: copy the existing value from `.env`; do not paste it into docs.
- Input type: text is production-ready; image input is accepted but currently returns a safe placeholder unless routed to background/vision work.

## Mainland deployment

Cloudflare Tunnel is not the production primary path for China-mainland glasses users. Use a mainland ECS/VPS + ICP-approved domain + Nginx streaming proxy, with Cloudflare kept only as fallback.

Deployment assets:

- `deploy/mainland/README.md` — rollout steps and verification gates.
- `deploy/mainland/nginx/rokid-mainland.conf` — SSE-safe Nginx config (`proxy_buffering off`, no gzip/cache).
- `deploy/mainland/systemd/hermes-rokid-bridge.service` — Linux service unit.
- `deploy/mainland/scripts/smoke_sse.sh` — authenticated health + SSE smoke check.
