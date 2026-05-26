# Rokid Platform — API Endpoints, Pitfalls, and Investigation Notes

## Known Working Metis API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/metis/thirdPartyAgent/add` | Create custom agent |
| POST | `/metis/thirdPartyAgent/configUpdate` | Update agent config |
| POST | `/metis/thirdPartyAgent/getList` | List user's agents |
| POST | `/metis/thirdPartyAgent/submit` | Submit for platform review |

All under `https://rcs.rokid.com`. Auth: `access_token` header = `ROKID_ACCOUNT_SESSION` cookie from Chrome.

## Workspace Investigation (2026-05-21)

The Rizon frontend (`rizon.rokid.com/custom-agent`) requires workspace membership. Without it: "无法查看智能体 — 请检查你的网址或加入对应工作空间后重试".

### What was tried (all 404):
- `rcs.rokid.com/metis/space/*` (create, list, getPersonalSpace, etc.)
- `rcs.rokid.com/space/*` (same variants)
- `rcs.rokid.com/api/coze_space/get_team_info`
- `rcs.rokid.com/api/space/*`
- `rizon.rokid.com/api/space/*`
- `rizon.rokid.com/api/coze_space/*`

### Frontend JS analysis (`coze-frontend/1.8.9`):
- SPA bundle at `static.rokidcdn.com/prod/coze-frontend/1.8.9/static/js/`
- `index~1.9e06faa2.js` contains `/api/coze_space/*` paths (60+ endpoints)
- Frontend has `has_personal_space` check, `createSpace` action, `getPersonalSpaceID()` store method
- But these APIs are behind a gateway that returns 404 without workspace context
- **Resolution**: User must create workspace through the Rizon web UI. No API shortcut found.

## Account Center / Developer Toggle

URL: `https://home.rokid.com/home/userinfo`

The "开发者模式" toggle only appears after BOTH:
1. 实名认证 (personal/identity certification) — approved
2. 开发者认证 (developer certification) — visible only after #1, requires separate approval

Without both: agentStore APIs return 403, no developer toggle visible.

## Icon Pitfalls

- Must be valid PNG/JPG URL accessible from Rokid's servers
- Emoji or text-based icons cause silent failures
- Recommended: 512x512 PNG, public URL
- After clearing a bad icon, reconfigure + resubmit

## Cookie Expiry Pattern

ROKID_ACCOUNT_SESSION cookies refresh every ~3 minutes in Chrome. This is a hard refresh cycle, not a session timeout. Must re-extract before every API call batch.

```python
# CORRECT: fresh extraction each time
def get_rokid_headers():
    import browser_cookie3
    cj = browser_cookie3.chrome(domain_name='.rokid.com')
    for cookie in cj:
        if 'ROKID_ACCOUNT_SESSION' in cookie.name:
            return {"access_token": cookie.value, "Content-Type": "application/json"}
    raise RuntimeError("No Rokid session cookie found — log in to home.rokid.com first")
```

## Agent Config Fields Reference

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | Agent ID from add response |
| `agentName` | string | Display name |
| `agentDesc` | string | Description |
| `openSseUrl` | string | SSE endpoint URL |
| `categoryId` | int | 0 = default |
| `icon` | string | Image URL |
| `pluginSwitch` | int | 1=enable plugins |
| `capabilitySwitch` | int | 0=default |
| `voiceId` | string | `zhifeng_fudan_university` (male) / `zhiyuan_fudan_university` (female) |
| `prologue` | string | Greeting message |
| `recommendedQuestions` | string | JSON array string |
| `status` | int | 0=draft, 1=published |

## SSE Metadata Shape Pitfall

Real glasses SSE requests may put read-only device facts directly under `metadata` instead of `metadata.context`:

```json
{
  "metadata": {
    "battery": "89",
    "current_time": "2026-05-22 18:44:28",
    "latitude": "30.24243",
    "longitude": "120.04926",
    "location": "中国浙江省杭州市...",
    "weather": "当前天气雾，24度"
  }
}
```

Do not assume only `metadata.context` carries location/battery. The bridge should normalize both shapes into the same read-only device context, with nested `metadata.context` taking precedence if both exist. Otherwise the glasses may say "这次请求没有带定位信息" even though latitude/location were present in top-level metadata.

## Current Custom-Agent List Response Pitfall

`POST /metis/agent/getThirdAgentList` may return only store/list fields, not the full editable config. In the live Hermes custom-agent response (2026-05-22), important fields included:

- `status: -1`
- `displayStatus: reject:环境链接不通...`
- `permissions: null`
- `icon: null`
- `agentUrl: https://.../rokid/sse`

Treat `status=-1`/`reject:*` as a hard platform approval blocker for true glasses runtime/plugin execution, even if the public SSE health endpoint is now fixed. `permissions:null` means do not assume native plugin permissions are granted. `icon:null` is also suspicious because platform docs/UI require a valid PNG/JPG icon for stable review/publish; fix config before resubmission if user approves.

## "请检查网络" Error on Glasses

After skill reinstall (agent delete + re-add), glasses show this if:
1. Agent config not set (missing SSE URL, prologue)
2. Agent not submitted for review
3. Agent still in "checking" status (platform review pending)

Fix: reconfigure → resubmit → wait for approval.

## Lingzhu native-plugin receipt pitfall

Rokid/Lingzhu custom-agent SSE requests may only include read-only context fields such as `weather`, `location`, `battery`, and `network`; they do not always include an explicit native-plugin execution receipt. Do not stop low-risk/read-only intents at “recognized plugin but no receipt”. Production bridge behavior should be:

- If a platform receipt exists (`pluginReceipts` / `plugin_receipts` / `lingzhu_plugin_receipts`), answer from the receipt.
- For low-risk/read-only capabilities, answer from current payload context or deterministic local fallback:
  - weather -> `metadata.weather` / `metadata.context.weather` plus location/time when present;
  - location -> normalized location/lat/lng from metadata;
  - device status -> battery/network/device fields;
  - calculator -> local safe arithmetic parser.
- For high-risk/control capabilities (photo, navigation, exit, payment), still fail closed without a platform receipt and avoid fake completion wording such as “已拍照/付款成功/已退出”.

This keeps glasses-visible plugin intents usable while preserving real-world action safety.

## Mainland glasses SSE connectivity and X2D status pattern

For China mainland glasses runtime, do not use Cloudflare Tunnel as the production primary入口. Use a mainland ECS with direct DNS/HTTPS and Nginx reverse proxy to the FastAPI bridge. Nginx must keep SSE streaming semantics: HTTP/1.1 upstream, no proxy buffering, no gzip buffering, and read timeouts long enough for SSE while the app still sends a quick ACK within the 8.5s Rokid budget.

Known working production shape:
- Public URL: `https://rokid-cn.hecheng.dev/rokid/sse`
- ECS app listens locally on port 8787.
- `/health` is public, `/rokid/sse` requires the Rokid bearer token.

X2D/Bambu manufacturing status must be cache-driven, not cloud-to-LAN direct:
1. Local Mac reads the LAN-only printer with read-only telemetry access.
2. Local script writes `~/.hermes/brains/rokid-glasses/manufacturing_status_cache.json`.
3. Cron/no-agent job `sync-rokid-manufacturing-status-to-ecs` runs every minute and copies the JSON to ECS path `/opt/hermes-rokid-bridge/.hermes/brains/rokid-glasses/manufacturing_status_cache.json`.
4. ECS bridge only formats and speaks this cache. It must not control the printer from the cloud.

Voice copy should say `云端安全缓存播报，未执行控制`, not `未连接打印机`; the cloud is intentionally not connected to the LAN printer. Verification: POST a real SSE request through the public domain and assert the combined answer contains `X2D`, `RUNNING`, progress/remaining/layer/nozzle/bed/tray, and does not contain `不可用` or `未连接打印机`.

Deployment pitfall: never `rsync --delete` the bridge directory in a way that deletes the remote `.venv`. Exclude `.venv`, runtime `.env`, and cache directories when syncing code to ECS, then restart systemd and verify `/health` plus a live `/rokid/sse` smoke test.
