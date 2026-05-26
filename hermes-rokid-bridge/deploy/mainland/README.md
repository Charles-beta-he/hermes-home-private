# Rokid mainland entry deployment

Purpose: provide a China-mainland-friendly HTTPS/SSE entry for Rokid glasses.

Do not use Cloudflare Tunnel as the mainland primary entry. Keep `https://rokid.hecheng.dev/rokid/sse` only as overseas/fallback.

Recommended production shape:

```text
Rokid glasses / Rizon
  -> https://<ICP-approved-mainland-domain>/rokid/sse
  -> mainland ECS + Nginx/Caddy on 443
  -> hermes-rokid-bridge on 127.0.0.1:8787
```

## Required inputs

- Mainland ECS/VPS with public IPv4, ports 80/443 open.
- ICP-approved domain or subdomain, e.g. `rokid-cn.example.cn`.
- TLS certificate. Use the cloud provider certificate console or `certbot` if the domain is correctly resolved.
- local `.env` auth value; do not commit or paste it into docs.

## One-server deployment

On the server:

```bash
sudo mkdir -p /opt/hermes-rokid-bridge
sudo useradd --system --home /opt/hermes-rokid-bridge --shell /usr/sbin/nologin hermes-rokid || true
```

Copy this project to `/opt/hermes-rokid-bridge`, then create `/opt/hermes-rokid-bridge/.env`:

```env
ROKID_AGENT_ID=hermes-rokid
# Copy the existing Rokid auth-value line from the local bridge .env.
ROKID_DEV_MODE=false
```

Install runtime:

```bash
cd /opt/hermes-rokid-bridge
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install fastapi uvicorn pydantic httpx pytest
```

Install service:

```bash
sudo cp deploy/mainland/systemd/hermes-rokid-bridge.service /etc/systemd/system/hermes-rokid-bridge.service
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-rokid-bridge
sudo systemctl status hermes-rokid-bridge --no-pager
```

Install Nginx site:

```bash
sudo cp deploy/mainland/nginx/rokid-mainland.conf /etc/nginx/conf.d/rokid-mainland.conf
sudo sed -i 's/rokid-cn.example.cn/<your-domain>/g' /etc/nginx/conf.d/rokid-mainland.conf
sudo nginx -t
sudo systemctl reload nginx
```

## Verification

Local server:

```bash
curl -i http://127.0.0.1:8787/health
```

Public mainland domain:

```bash
curl -i https://<your-domain>/health
ROKID_SMOKE_VALUE_VALUE=<value> ./deploy/mainland/scripts/smoke_sse.sh https://<your-domain>
```

Expected SSE sequence:

```text
event: message
...
event: done
```

## Rizon configuration

Set `openSseUrl` to:

```text
https://<your-domain>/rokid/sse
```

Keep:

```text
Agent ID: hermes-rokid
```

Then submit/re-submit for review.

## Mainland invariants

- First ACK must be emitted immediately; do not wait for model/tool calls.
- Nginx buffering must be off for `/rokid/sse`.
- Health endpoint must be reachable from mainland networks.
- Do not put Cloudflare CDN or any proxy that buffers SSE in front of the endpoint.
- Keep Cloudflare endpoint as fallback only.
