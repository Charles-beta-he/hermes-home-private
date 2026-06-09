## Rokid Lingzhu SSE bridge for Hermes

Use when connecting Hermes/assistant capabilities to Rokid Glasses through the Rokid Lingzhu custom third-party agent protocol.

## Durable pattern

Rokid Lingzhu can import a custom third-party agent by calling a developer-provided HTTPS SSE endpoint. The safest Hermes architecture is a small bridge service rather than exposing Hermes directly:

```text
Rokid Glasses / Rokid AI App
  -> Lingzhu custom agent SSE
  -> Hermes-Rokid Bridge
  -> local Hermes CLI/Gateway/tools
```

## Minimal bridge contract

Lingzhu request essentials:

- Header: `Authorization: Bearer <agent AK>`
- Header: `Content-Type: application/json`
- Body:
  - `message_id`: preserve for context/routing
  - `agent_id`: custom agent identifier
  - `message[]`: user messages, supports `type: text` and later `type: image`
  - `user_id`: optional Rokid user identifier
  - `metadata.context`: device context such as location, latitude, longitude, weather, battery

SSE response essentials:

```text
event: message
data: {"role":"agent","message_id":"...","agent_id":"...","answer_stream":"...","is_finish":false,"type":"answer"}

event: done
data: {"role":"agent","message_id":"...","agent_id":"...","is_finish":true,"type":"answer"}
```

For MVP, using Hermes CLI behind FastAPI is enough:

```bash
hermes chat -q "$PROMPT" --quiet --max-turns 1
```

Chunk the non-streaming CLI output into SSE `answer_stream` fragments if true streaming is not available yet.

## Recommended local implementation shape

```text
~/.hermes/hermes-rokid-bridge/
  app.py                  # FastAPI bridge: /health and /rokid/sse
  .env                    # ROKID_AGENT_ID, ROKID_AGENT_AK, HERMES_BIN
  run_service.sh          # local bridge service entrypoint
  run_tunnel_named.sh     # fixed Cloudflare named tunnel entrypoint
  current_public_endpoint.env
```

Bridge defaults:

- Bind local service to `127.0.0.1`, not `0.0.0.0`.
- Fail closed if `ROKID_AGENT_AK` is unset.
- Use short, glasses-friendly prompt framing: concise voice/eyewear answers; ask before high-impact actions.
- Treat location, image URLs, and device context as private data.
- Do not expose raw Hermes/Gateway endpoints to the public internet.

## Cloudflare fixed-domain flow

1. Install `cloudflared` if missing.
2. For quick MVP, temporary tunnel works without login:
   ```bash
   cloudflared tunnel --url http://127.0.0.1:8787 --no-autoupdate
   ```
3. For fixed domain, the Cloudflare account must have a Zone. Register/add a domain first; otherwise the `cloudflared tunnel login` authorization page has no selectable Zone.
4. Complete login and verify:
   ```bash
   test -f ~/.cloudflared/cert.pem
   cloudflared tunnel list
   ```
5. Create named tunnel:
   ```bash
   cloudflared tunnel create hermes-rokid
   ```
6. Write config, example:
   ```yaml
   tunnel: <uuid>
   credentials-file: /Users/charles/.cloudflared/<uuid>.json
   metrics: 127.0.0.1:20242
   no-autoupdate: true
   ingress:
     - hostname: rokid.<domain>
       service: http://127.0.0.1:8787
     - service: http_status:404
   ```
7. Route DNS:
   ```bash
   cloudflared tunnel route dns hermes-rokid rokid.<domain>
   ```
8. Run fixed tunnel:
   ```bash
   cloudflared tunnel --config ~/.cloudflared/hermes-rokid.yml run hermes-rokid
   ```

## macOS launchd persistence

Use two LaunchAgents:

- `com.charles.hermes-rokid-bridge` -> runs the local FastAPI/uvicorn bridge.
- `com.charles.hermes-rokid-tunnel` -> runs the fixed Cloudflare named tunnel.

## Rokid/Lingzhu console gating

After the bridge and fixed tunnel are verified, Lingzhu console configuration can still be blocked by account state. If entering `项目开发` shows `无法查看空间` and says to complete `实名认证` / `开发者认证`, stop trying to create the agent: the platform will return `403`/`space id error` for space APIs until certification is complete.

Operational sequence:

1. Log in and confirm the account center identity only if credentials were explicitly provided for this session; never store or repeat the password in notes.
2. If the account lacks certification, report that the network bridge is done but console creation is gated by Rokid KYC/developer review.
3. Do not attempt to automate ID-card, face, payment, or developer qualification forms. Ask the user to complete certification in their real browser, then resume agent creation.
4. Once certification is complete, create/import the custom third-party agent with the already-verified fixed SSE URL (`https://rokid.<domain>/rokid/sse`), `agent_id`, and AK.
5. If basic real-name certification is complete but professional/developer certification is still under review, try the console/API anyway before declaring it blocked: Lingzhu may allow custom-agent draft creation/configuration even while later review/publish abilities remain gated.

## Lingzhu/Rizon custom-agent API fallback

Use this only when the user explicitly asks the agent to operate the console and the browser session is already logged in. Do not store or echo credentials, AKs, or cookies.

Known production bases from the frontend source:

- AI platform API: `https://rcs.rokid.com/aiPlatform`
- Metis custom-agent API: `https://rcs.rokid.com/metis`

Frontend requests use the browser cookie `ROKID_ACCOUNT_SESSION` and also send it as an `access_token` header. A Python `requests.Session` populated from Chrome cookies can operate the same APIs for console fallback. Never print the token.

Useful Metis endpoints:

```text
POST https://rcs.rokid.com/metis/agent/addThirdAgent
POST https://rcs.rokid.com/metis/agent/getThirdAgentList
POST https://rcs.rokid.com/metis/agent/updateThirdAgent
POST https://rcs.rokid.com/metis/agent/deleteThirdAgent
```

Draft creation is minimal:

```json
{"modelVendor":"custom"}
```

The response contains the platform/internal `agentId` for the draft. Then update the draft with the Hermes bridge fields:

```json
{
  "modelVendor": "custom",
  "agentId": "<platform_agent_id_from_addThirdAgent>",
  "thirdAgentId": "hermes-rokid",
  "agentName": "Hermes 个人助理",
  "description": "Hermes 个人助理，可通过 Rokid Glasses 进行短对话、信息查询、随手记录和任务规划。",
  "agentAk": "<read from local bridge .env; never print>",
  "agentUrl": "https://rokid.<domain>/rokid/sse",
  "needParam": "question",
  "category": "work",
  "prologue": "你好，我是 Hermes。你可以直接对我说：帮我记一下、总结一下、查一下、规划一下。",
  "globalImageSize": 0
}
```

After API probing, list drafts and delete any accidental empty duplicates. Verify by listing drafts with `agentAk` redacted in output. The page/platform may still require professional certification for publish/review or full in-console debugging; treat API draft creation success as configuration progress, not final publication.

### Review/publish and device-debug progression

When a custom third-party agent draft is configured and the user asks to proceed to real-device debugging, first run the local/public bridge checks and SSE smoke test, then submit the agent for review/publish through the same logged-in browser-cookie API session. The Rizon frontend currently lazy-loads the third-agent UI in async chunk `8529.*.js`; it shows the publish dialog calling `agentStore/developer/cozePublish` via helper `eS.__`.

Use the existing Chrome login cookie (`ROKID_ACCOUNT_SESSION`) without printing it. Populate a `requests.Session` from Chrome cookies, send the cookie value as the `access_token` header, and fetch the custom agent by `thirdAgentId`:

```text
POST https://rcs.rokid.com/metis/agent/getThirdAgentList
payload: {"modelVendor":"custom","pageIndex":1,"pageSize":20}
```

Then submit:

```text
POST https://rcs.rokid.com/agentStore/developer/cozePublish
payload:
{
  "botId": "<platform agentId>",
  "name": "<agentName>",
  "description": "<description>",
  "prompt": "<description>",
  "versionLog": "<human review note>",
  "logo": "<icon or null>",
  "needParam": "<needParam, usually question>",
  "category": "<category>",
  "categoryName": "",
  "modelVendor": "custom",
  "prologue": "<prologue>",
  "suggestedQuestions": "",
  "suggestedQuestionsShowMode": 0,
  "globalImageSize": <globalImageSize or 0>
}
```

A successful submission returns `code: 0` with `publish_result["1024"].publish_result_status: 1`. Re-list the draft; `displayStatus: "checking"` means the draft has left plain draft state and is normally ready for platform/real-device debug attempts if the account is allowed.

For true-device verification, start a short-lived log watcher on the bridge logs before asking the user to speak into the glasses/app:

```bash
tail -n 0 -F ~/.hermes/hermes-rokid-bridge/bridge.launchd.log ~/.hermes/hermes-rokid-bridge/bridge.launchd.err.log
```

Ask the user to say a unique phrase such as `只回复 ROKID_DEVICE_OK`. Treat success as both: (1) the device receives the expected answer, and (2) the bridge log shows a fresh `POST /rokid/sse` at the same time. This separates real Rokid device traffic from the agent's own curl smoke tests.

Verification commands:

```bash
launchctl print gui/$(id -u)/com.charles.hermes-rokid-bridge
launchctl print gui/$(id -u)/com.charles.hermes-rokid-tunnel
curl -sS http://127.0.0.1:8787/health
curl -sS https://rokid.<domain>/health
```

SSE verification:

```bash
source ~/.hermes/hermes-rokid-bridge/.env
curl -N -X POST https://rokid.<domain>/rokid/sse \
  -H "Authorization: Bearer $ROKID_AGENT_AK" \
  -H 'Content-Type: application/json' \
  -d '{"message_id":"test-1","agent_id":"hermes-rokid","message":[{"role":"user","type":"text","text":"只回复 ROKID_OK"}],"metadata":{"context":{"location":"西安","weather":"晴","battery":"80%"}}}'
```

Use `curl` for both local and public smoke tests. A Python `urllib` probe may inherit macOS/system proxy settings or trigger Cloudflare/proxy behavior differently and return a misleading empty `403` even for `127.0.0.1`; prefer `curl --noproxy '*' -N ... http://127.0.0.1:8787/rokid/sse` for local checks and authenticated `curl -N ... https://rokid.<domain>/rokid/sse` for public checks. After `launchctl kickstart -k`, poll `/health` until it responds before SSE smoke; an immediate curl can race uvicorn startup and falsely report connection refused. When parsing SSE with Python, write curl output to a temp file first; `curl ... | python3 - <<'PY'` feeds the heredoc to Python stdin and loses the curl stream. If curl health and authenticated SSE pass, the bridge path is healthy.

Pass condition: `event: message` with `answer_stream` containing `ROKID_OK`, followed by `event: done` with `is_finish: true`.

## Chrome cookie extraction for Metis API access

To operate the Metis API programmatically, extract the `ROKID_ACCOUNT_SESSION` cookie from the user's Chrome profile using `browser_cookie3`:

```python
import browser_cookie3
cj = browser_cookie3.chrome(domain_name='.rokid.com')
session_token = None
for cookie in cj:
    if 'ROKID_ACCOUNT_SESSION' in cookie.name:
        session_token = cookie.value
        break
```

Then use it as the `access_token` header for all Metis API calls:

```python
headers = {"access_token": session_token, "Content-Type": "application/json"}
resp = requests.post(url, json=payload, headers=headers, timeout=15)
```

Never print the full token value in output. Requires `pip install browser_cookie3`.

## Rejected agent recovery

Custom third-party agents can be rejected by the platform. The `displayStatus` field in `getThirdAgentList` response reveals the reason, e.g. `reject:官方头像，非官方不予使用` means the icon/logo was non-official and the platform rejected it.

Recovery flow:
1. List agents via `getThirdAgentList` and read `displayStatus` for the rejection reason.
2. Fix the issue (e.g. set `icon` to `None` to use platform default, or change other rejected fields).
3. Call `updateThirdAgent` with the corrected fields.
4. Call `agentStore/developer/cozePublish` to re-submit for review.
5. Verify `displayStatus` changes to `checking` (review in progress).

## OpenClaw official plugin lessons for Hermes bridge design

Rokid's official `rokid-openclaw-gateway-compatible` plugin is useful as a design reference even when not installing it. Its architecture is:

```text
Rokid AI App / Glasses
  -> RCS WebSocket link (`wss://rcs.rokid.com/claw/ws/link`)
  -> long-lived OpenClaw Gateway plugin
  -> channel runtime / agent route
  -> streamed frames back to device
```

Key lessons to apply to the Hermes-native bridge:

- Prefer a long-lived bridge/runtime over cold-starting a full CLI per utterance. Cold CLI startup is the main source of multi-second/minute latency.
- Maintain a dedicated glasses entry brain: short prompt, small max tokens, voice-friendly output, no full memory/tool context by default.
- Use incremental escalation: fast T0 answer first; only upgrade to full Hermes for explicit long-running/background/tool tasks.
- Preserve request IDs and session keys; treat each device utterance as cancellable. If a new request arrives, abort or mark older work stale and send a terminal `done` frame.
- Stream only user-visible text; suppress reasoning/tool-internal text.
- Model device actions as explicit tool-call frames (`take_photo`, `take_navigation`, `control_calendar`, `notify_agent_off`) instead of pretending the text answer executed them.
- Keep high-impact actions confirm-first unless the device/runtime returns execution evidence.

For Hermes SSE bridge MVP, the practical adaptation is: `direct_xiaomi` fast path + `~/.hermes/brains/rokid-glasses/ENTRY_BRAIN.md` + optional full-Hermes fallback disabled by default. Use full Hermes only as an asynchronous/background escalation path, not blocking the eye-glasses request.

### L1 task-draft / infinite interruption pattern

For glasses voice UX, task creation should be a side-effect-free L1 draft state machine before any taskpool/Hermes L2 execution:

- Store per-user/session drafts in memory keyed by Rokid `user_id` (fall back to `agent_id`).
- Task-start triggers include phrases like `创建任务`, `添加任务`, `添加后台任务`, `后台任务`, `记一下`, `后台处理`, `帮我规划/研究/整理`.
- Rokid/ASR often splits one intent into clipped turns, e.g. `添加后台任务，扩充眼镜端入口权限` -> `后台任务是否添加成功？` -> `常规需求` -> `多模型思考，扩充日常使用，如位置、拍照对话`. The L1 state machine must keep these in the same session draft instead of sending each fragment to the model.
- While a draft exists, subsequent utterances are treated as additive modifications by default; there is no revision cap.
- Replacement phrases (`不对`, `改成`, `换成`, `还是`, `不是`) overwrite the draft title.
- Status follow-ups (`是否添加成功`, `创建成功`, `任务是否`, `后台任务是否`) should read back the current draft plus the next confirmation phrase, not call the model.
- `算了/取消/不用了` clears the draft with zero side effects.
- `确认执行/确认/提交/去做` records a durable L2 upgrade event, then clears the in-memory draft. Do not run full Hermes inline in the SSE request.
- Queue confirmed events as JSONL, e.g. `~/.hermes/brains/rokid-glasses/pending_upgrades.jsonl`, with `status: pending_l2_upgrade`, `session_key`, `title`, `revision`, `history`, and timestamps.
- Add L0 read-only local-brain stats before model calls: phrases like `本地大脑状态`, `任务统计`, `任务池状态`, `今天有什么任务`, `最近任务` should return a short cached summary from `~/.hermes/brains/rokid-glasses/local_brain_stats.json`.
- On macOS, launchd services may not have TCC permission to read `~/Documents/brain`; generate the stats cache with a separate script such as `~/.hermes/scripts/update_rokid_brain_stats_cache.py` and refresh it periodically. The bridge should read the cache from `~/.hermes`, not scan Documents on every request.
- Put ordinary fast-model calls under a network-aware glasses UX budget. For the China/Rokid bridge, real provider/network latency is commonly 4-8s (recent p95 around 7.8s), so production uses `ROKID_MODEL_BUDGET_SECONDS=8.5` with `ROKID_FAST_TIMEOUT_SECONDS=12`; use smaller monkey-patched budgets only in tests. If the model is slow, empty, or fails, use an explicit intent gate before persisting anything: only confirmed task drafts or clear write/background intents (`后台处理`, `后台分析`, `长任务`, `多模型分析`, `发 Telegram`, `创建任务`, `记一下`, etc.) may become `pending_l2_upgrade`. Read-only queries, daily-report questions (`日报`), status/progress queries, and chitchat must fail soft with a natural network-slow message and **must not** enter L2. Do not show debugging copy such as "不会把它误转成后台任务" to the user.
- For Rokid "AI assistant abnormal" prevention, the SSE generator must immediately send a non-empty `answer_stream` ACK such as `收到，我在处理。`; do not send an empty first `message` frame. Wrap the generator so every path, including cache/model exceptions, emits a terminal `event: done` with `is_finish: true`.
- Add L0 cache routes before model calls for ability/help, daily brief, local-brain stats, and mini-kanban/status. Daily brief should be generated by a quiet scheduled script such as `~/.hermes/scripts/update_rokid_daily_brief_cache.py` into `~/.hermes/brains/rokid-glasses/daily_brief_cache.json`; the bridge only reads the cache synchronously.
- Use a long-lived `httpx.AsyncClient` with HTTP/2, keepalive, small connect timeout, and short prompt framing for the L1 fast model. Avoid blocking `urllib` calls inside `asyncio.to_thread` for the hot path. Track request/ACK/L0/model metrics in `/health`, and add a short provider cooldown after upstream failures to avoid repeated slow/error calls filling the glasses screen.
- Add an L2 worker such as `rokid_l2_worker.py` + cron wrapper `process_rokid_l2_queue.py`. The bridge now writes an Intent Ledger + per-task JSON queue under `~/.hermes/brains/rokid-glasses/`: `ledger/events.jsonl` for raw capture events, `candidates/cand_*.json`, `confirmations/cfm_*.json`, `queue/commit_*.queued.json`, and `artifacts/artifact_*.json`. `pending_upgrades.jsonl` is only a compatibility mirror. The worker atomically claims `queued -> committing -> done/failed`, performs the local side effect, read-after-write verifies, then writes an artifact receipt with `output_path`, `checksum`, `title`, `session_key`, and `source_event`. Failed writes become failed/retry/dead-letter, not fake success.
- Add a Rokid Mini-Kanban / Intent Board view before model calls: phrases like `草稿状态`, `眼镜后台进度`, `任务进度`, `刚才的任务` should summarize the current session's in-memory draft plus durable queue counts (`pending_l2_upgrade`, `retry`, `done`) and recent completed title. Do not write every voice draft directly into global `kanban.db`; only confirmed/background work should enter durable queues to avoid polluting the main dispatcher with口误.
- Add L0 background-task control before model calls: phrases like `目前的后台任务有什么`, `当前后台任务`, `取消所有后台任务`, `两个任务都取消`, `取消是否成功` must read or mutate only real Intent Ledger queue files (`queue/*.queued.json`, `*.committing.json`, `*.retry.json`). If the real queue is empty, say there are no real background tasks. Never let the model invent running tasks such as always-listening voice assistant or navigation, and never claim cancellation success unless a real queue file was moved to `*.canceled.json`.
- Add a device-context extractor instead of scattering payload parsing through `app.py`: collect text, image URLs, `metadata.context`, `message_id`, and a safe `session_key`. If Rokid omits `user_id`, never fall back to shared `agent_id`; use a message-scoped anonymous key to avoid cross-user draft confirmation.
- Add an image-input safety route before model calls. Until a reliable vision/background route is enabled, `type=image` should return a short placeholder ("收到了图片，请补充文字或说后台分析图片") and must not let the text model hallucinate visual content from a URL.
- Add a high-impact action registry before the model and a post-model guard after it. Messaging, calendar, navigation, device control, and formal task commits are confirm-first. If the model says `已发送`/`已创建`/`已执行` without tool evidence, rewrite to a confirmation prompt rather than streaming fake completion to the glasses.
- Post-clamp all L1 model answers for voice UX: remove/avoid Markdown tables, hard-limit long output, and append a background/long-content option. Prompt instructions are insufficient; enforce this after model output and before SSE chunking.
- The Intent Ledger and Commit Arbiter are implemented as the current L2 durable substrate before writing brain/taskpool/kanban: persist `capture_event` (raw transcript/hash/device context where available), `intent_candidate` (type/title/confidence/risk/duplicate hints), `confirmation` (one-time token, prompt, user response), `commit_request` (target, idempotency key, status), and `committed_artifact` (output path/external id/checksum). Rules: no confirmation token → no formal write; duplicate/idempotency hit → merge or no-op; high-risk action → strong confirm; every `done` requires read-after-write/tool receipt evidence.
- Use the per-task JSON files as the primary queue for atomic claim/retry/dead-letter (`queued → committing → done/failed`). Keep L0/L1 status reads fast by caching summaries under `~/.hermes` rather than scanning `~/Documents` from launchd. Keep the legacy JSONL mirror only for backward compatibility and operator inspection.
- Verify with TDD around pure state-machine behavior and an SSE smoke test: stats query → create → kanban draft view → additive modify → replacement modify → confirm → queue event → worker creates task → kanban done view → queue ack; add negative tests for `算了/别记/不是任务/撤销刚才那个`, read-only query timeout (`今天日报有什么`) must not enqueue, SSE replay, duplicate confirmation, and worker retry idempotency.

## Pitfalls

- Cloudflare Tunnel login with no Cloudflare Zone shows an authorization page with nothing to select. Fix by registering/adding a domain first, then rerun `cloudflared tunnel login`.
- Lingzhu project spaces require Rokid account certification. `无法查看空间`, `space/list` 403/500, or `space id error` after login usually means the account must finish real-name/developer certification before third-party agents can be created.
- Treat Rokid certification as a human step: do not automate sensitive KYC/developer forms, and do not persist user passwords. Resume only after the user says certification is complete.
- `trycloudflare.com` URLs are useful for MVP but are not stable; do not put them in long-lived docs/configs unless clearly marked temporary.
- `cloudflared` metrics can reveal the current temporary hostname, but fixed named tunnels should use DNS route + config file instead.
- Keep `cert.pem`, tunnel credential JSON, and agent AK chmod `600`; do not paste full secrets into public docs.
- Avoid brand-risk domains such as `rokidagent.com`; prefer user-owned/personal domains and use a subdomain like `rokid.<domain>`.
- **Native vs custom agent confusion**: The Rizon platform has two completely separate agent types. "原生智能体" (native agents) use the platform's built-in model (e.g. doubao/seed) and are edited in the Rizon visual editor. "自定义第三方智能体" (custom third-party agents) connect to an external SSE endpoint via Metis API. Users may create a native agent and wonder why their glasses can't connect to Hermes — they need to switch to the custom third-party agent on the device.
- **Icon rejection**: The platform rejects custom third-party agents with non-official icons (`displayStatus: "reject:官方头像，非官方不予使用"`). Always set `icon` to `None`/null in the API payload to use the platform default. Do not upload custom logos.
- **Chrome cookies are encrypted**: On macOS, Chrome cookie values are encrypted in the SQLite DB. Use the `browser_cookie3` library (which handles Keychain decryption) rather than trying to read the DB directly. Without `browser_cookie3`, the `value` column will be empty and `encrypted_value` is not directly usable.
- **Metis API auth pattern**: All Metis API calls require the `ROKID_ACCOUNT_SESSION` cookie value sent as both a browser cookie AND an `access_token` HTTP header. The `requests.Session` from `browser_cookie3` handles the cookie automatically, but you must manually add the `access_token` header.
- **Login API does not exist at standard paths**: Rokid login is browser-based (OAuth/SMS). There is no `POST /account/login` JSON endpoint. Programmatic access requires extracting the session cookie from an already-logged-in Chrome profile.
