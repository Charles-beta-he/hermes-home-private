---
name: rokid-rizon-platform
description: "Use when managing Rokid Rizon platform integration — third-party agent creation, Metis API, account certification, token management, agent lifecycle, workspace, and glasses-to-Hermes SSE bridge."
triggers:
  - rokid
  - rizon
  - 灵珠
  - metis API
  - 第三方智能体
  - rokid glasses agent
  - Rokid SSE
---

# Rokid / 灵珠 Platform Integration

## Architecture

```
Glasses (灵珠 App) ←SSE→ Hermes Bridge (/rokid/sse) ←→ Hermes Agent
                                ↑ registered via
Rizon Frontend (rizon.rokid.com) ←→ Metis API (rcs.rokid.com/metis/*) ←→ Agent Store DB
```

- **Rizon frontend**: `https://rizon.rokid.com` — React SPA (`coze-frontend`), manages workspaces, native agents, custom agents
- **Metis API**: `https://rcs.rokid.com/metis/` — backend for third-party agent CRUD
- **Agent Store API**: `https://rcs.rokid.com/agentStore/` — native agent store (different from custom agents)
- **Custom agent page**: `rizon.rokid.com/custom-agent` (requires workspace membership)

## Prerequisites (strict order)

1. **实名认证 (Personal Certification)** — ID verification on Rokid account
2. **开发者认证 (Developer Certification)** — developer agreement, only visible AFTER 实名认证 passes
3. Both must be approved (takes hours to one business day) before the "开发者模式" toggle appears at `/home/userinfo`

Without both certifications: agentStore APIs return 403 with "space id error"; no developer toggle visible.

## Token Management

```python
import browser_cookie3
cj = browser_cookie3.chrome(domain_name='.rokid.com')
session_token = None
for cookie in cj:
    if 'ROKID_ACCOUNT_SESSION' in cookie.name:
        session_token = cookie.value
        break
headers = {"access_token": session_token, "Content-Type": "application/json"}
```

### CRITICAL: Cookie Expiry ~3 Minutes
Chrome refreshes `.rokid.com` cookies every ~3 minutes. **Must re-read cookies fresh before every API call sequence.** Do NOT cache the token across calls. If you get 401 or unexpected auth failures, refresh cookies first.

## Third-Party Agent Lifecycle

### Create Agent (Metis API)
```python
requests.post("https://rcs.rokid.com/metis/thirdPartyAgent/add",
    json={
        "agentName": "name",
        "agentDesc": "description",
        "categoryId": 0,
        "icon": "https://valid-icon-url.png",  # must be valid PNG/JPG
        "openSseUrl": "https://your-domain/rokid/sse",
    }, headers=headers)
# Returns: {"thirdPartyAgentInfo": {"agentId": "119..."}}
```

### Configure Agent
```python
requests.post("https://rcs.rokid.com/metis/thirdPartyAgent/configUpdate",
    json={
        "id": agent_id,         # from add response (as string)
        "agentName": "...",
        "agentDesc": "...",
        "openSseUrl": "https://domain/rokid/sse",
        "categoryId": 0,
        "icon": "url",
        "pluginSwitch": 1,      # enable plugins (web_search, etc.)
        "capabilitySwitch": 0,  # agent capability
        "voiceId": "zhifeng_fudan_university",  # male
        # "voiceId": "zhiyuan_fudan_university",  # female
        "prologue": "你好，我是 Hermes 个人助理",
        "recommendedQuestions": '["...","..."]',  # JSON string
        "status": 1,            # 1=publish, 0=draft
    }, headers=headers)
```

### Submit for Review
```python
requests.post("https://rcs.rokid.com/metis/thirdPartyAgent/submit",
    json={"id": agent_id}, headers=headers)
```

### Agent Status Flow
```
draft (status=0) → published/waiting (status=1) → checking → published/rejected
```

### List Agents
```python
# Current custom-agent list endpoint verified live on 2026-05-22.
requests.post("https://rcs.rokid.com/metis/agent/getThirdAgentList",
    json={"modelVendor": "custom", "pageIndex": 1, "pageSize": 20}, headers=headers)
```

If older docs mention `/metis/thirdPartyAgent/getList`, treat that as stale for the current Rizon custom-agent UI unless a fresh browser-network capture proves otherwise.

## SSE Endpoint

- URL pattern: `https://domain/rokid/sse`
- Must return `text/event-stream` with `event: card`
- Heartbeat: comment line every ≤15s
- Per-session timeout: 8.5s
- First frame: ACK JSON `{"cards":[{"card_type":"text","content":"✅ 语音链路已通"}]}`
- Gateway dispatches to SSE via `/rokid/*` catch-all route

## Lingzhu native plugin routing baseline

For the local Hermes bridge at `/Users/charles/.hermes/hermes-rokid-bridge`, treat Lingzhu platform plugins as the L0 device capability layer:

- device status/battery/location/weather → Lingzhu information plugin first
- photo/navigation/exit → Lingzhu glasses-control plugin first, confirmation required
- Alipay AI Pay → critical risk, amount/merchant/second confirmation plus platform receipt required
- calculator → Lingzhu calculator or Hermes local fallback; never forge a plugin result

Implementation anchor files:

- `lingzhu_plugins.py` — declarative plugin registry, receipt parser, fail-closed answer builders
- `route_runtime.py` — `lingzhu_plugin` route before generic high-impact/model fallback
- `app.py` — route handler that only treats native actions as executed when metadata contains a valid Lingzhu plugin receipt
- `rokid_bridge/action_guard.py` — rewrites unsafe fake-completion claims such as `已拍照`, `导航已开始`, `付款成功`
- `docs/lingzhu-plugin-routing.md` — capability table, receipt contract, Rizon config checklist, manual platform probes

Verification command:

```bash
cd /Users/charles/.hermes/hermes-rokid-bridge
uv run --with pytest --with fastapi --with httpx --with pydantic python -m pytest -q
```

Known certified baseline: `118 passed, 2 warnings` with multi-model certification artifacts under `/Users/charles/.hermes/tick-20260522-091715-193999-p19541-62942fd0-3308f8e0/`.

Live smoke evidence from 2026-05-22:
- Rizon API `POST /metis/agent/getThirdAgentList` returned `Hermes 个人助理`, `thirdAgentId=hermes-rokid`, `agentUrl=https://rokid.hecheng.dev/rokid/sse`, `displayStatus=reject:环境链接不通，建议使用眼镜自行测试，无问题后进行上传`.
- If public `https://rokid.hecheng.dev/health` returns Cloudflare 530 / error 1033 while local `127.0.0.1:8787/health` is OK, restart the named tunnel: `launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-tunnel`, then recheck public health before platform submission.
- If tunnel logs show QUIC/UDP instability such as `failed to dial to edge with quic`, `timeout: no recent network activity`, UDP `:7844`, or IPv6 `no route to host`, force the named tunnel to TCP/TLS by adding `protocol: http2` to `/Users/charles/.cloudflared/hermes-rokid.yml`, validate with `cloudflared tunnel --config /Users/charles/.cloudflared/hermes-rokid.yml ingress validate`, then `launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-tunnel`.
- Local and public `/rokid/sse` authenticated smoke with real configured agent AK passed for device-status, photo-without-receipt fail-closed, photo-with-receipt receipt handling, and navigation-without-receipt fail-closed. Do not print the AK.
- Location query pitfall: phrases like `获取本地位置` / `本地位置` must stay in the L0 location route, not model fallback; otherwise coords-only context may produce “无法直接获取”. The bridge also normalizes nested `metadata.context.location={city,latitude,longitude,accuracy}`. Regression tests live in `tests/test_rokid_long_term_entry.py` and `tests/test_lingzhu_plugin_routes.py`.


## China-mainland production entry

For China-mainland glasses users, do not use Cloudflare Tunnel as the primary SSE URL. Cloudflare can remain the overseas/fallback endpoint, but the Rizon `openSseUrl` for mainland production should point to an ICP-approved mainland HTTPS domain backed by a mainland ECS/VPS.

Recommended shape:

```text
Glasses / Rizon → https://rokid-cn.<备案域名>/rokid/sse → mainland Nginx/Caddy → hermes-rokid-bridge:8787
```

Implementation assets in the bridge repo:

- `/Users/charles/.hermes/hermes-rokid-bridge/deploy/mainland/README.md`
- `/Users/charles/.hermes/hermes-rokid-bridge/deploy/mainland/nginx/rokid-mainland.conf`
- `/Users/charles/.hermes/hermes-rokid-bridge/deploy/mainland/systemd/hermes-rokid-bridge.service`
- `/Users/charles/.hermes/hermes-rokid-bridge/deploy/mainland/scripts/smoke_sse.sh`

Mainland verification gates:

```bash
curl -i https://<mainland-domain>/health
ROKID_SMOKE_VALUE=<value-from-local-env> deploy/mainland/scripts/smoke_sse.sh https://<mainland-domain>
```

The Nginx/Caddy proxy must disable buffering/cache/gzip for `/rokid/sse`, preserve streaming, and return the first ACK immediately; otherwise Rizon may report “环境链接不通”.

## Platform UI Gotchas

1. **Workspace required**: `rizon.rokid.com/custom-agent` shows "无法查看智能体" if user has no workspace. Create workspace first on the platform.
2. **Checking status**: After `submit`, agent enters platform review. Takes hours to days. Agent won't work on glasses until approved.
3. **Icon requirements**: Must be valid PNG/JPG URL. Emoji or invalid icons cause silent failures.
4. **Native vs Custom agents**: "铁蛋" etc. are native agents (agentStore). "Hermes 个人助理" is custom third-party (Metis). Different management pages.

## Skill Reinstallation

When user reinstalls the Rokid skill (deletes + readds the third-party agent):
- Agent gets new ID
- Config (voice, plugins, SSE URL, prologue, recommendedQuestions) must be reconfigured
- Agent must be re-submitted for review
- The glasses will show "请检查网络" if the agent config is incomplete (especially missing SSE URL or prologue)

## Reference Files

See `references/rokid-api-and-pitfalls.md` for full API endpoint list, workspace investigation notes, and advanced troubleshooting.
