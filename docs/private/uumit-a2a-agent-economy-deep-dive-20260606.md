# UUMit / A2A / Agent Economy Deep Dive — 2026-06-06

## Scope

Evidence-first review of public UUMit surfaces after Douyin video discovery. This is not an endorsement and no credentials were used. No destructive/write operations were performed except requesting a public temporary sandbox key endpoint once.

## Sources inspected

- Douyin video: `https://www.douyin.com/video/7647133082906412454` (via prior browser extraction)
- Website: `https://uumit.com/`
- Developer docs: `https://uumit.com/docs/`
- About/FAQ/changelog/community/blog/playground pages
- Public API base: `https://api.uumit.com`
- Public OpenAPI: `https://api.uumit.com/api/v1/public/openapi.json`
- Agent Card: `https://api.uumit.com/.well-known/agent.json`
- MCP SSE probe: `https://api.uumit.com/mcp/sse`
- A2A JSON-RPC unauth probe: `https://api.uumit.com/a2a`
- OpenClaw/UUMit skill pack: `https://oss.uumit.com/skills/uumit-agent.zip`
- RDAP: Verisign RDAP for `uumit.com`
- TLS certs for `uumit.com`, `api.uumit.com`, `oss.uumit.com`

## Factual findings

### 1. Public product positioning

UUMit describes itself as an "AI 原生全球能力网络" connecting human users and AI/Agent callers through task discovery, matching, settlement, Agent Card, MCP and A2A.

About page states a three-layer architecture:

- Standard protocol layer: Google A2A, MCP, Agent Card
- UUMit core business: UT settlement, credit system, matching engine, capability pool
- Foundation claim: derived from UU 跑腿 with 10 years operation, 70M registered users, 8M runners, 230+ cities

Company and filing surface:

- Footer ICP: `粤ICP备2026031014号`
- Company shown on About page and TLS OV cert: `深圳极核优星信息技术有限公司`
- `uumit.com` RDAP registration: 2026-03-19, expiration 2027-03-19, nameservers `NS1.ENAME.NET`, `NS2.ENAME.NET`
- Website TLS cert subject includes organization `深圳极核优星信息技术有限公司`, issuer GeoTrust/DigiCert, valid May 7 2026 to Nov 21 2026
- API/OSS certs are DV certs expiring Jul 8 2026

### 2. Public API is real and sizeable

`GET https://api.uumit.com/api/v1/public/openapi.json` returned a live OpenAPI 3.1 document:

- title: `UUAgent Public API`
- version: `0.1.0`
- paths: 164
- operations by method: GET 90, POST 75, PUT 10, DELETE 9, PATCH 2
- schemas: 286
- prominent tags: API Plaza 46, tasks 24, public 21, orders 13, capabilities 13, auth 12, skills 9, a2a-transactions 9, wallet 5, interop 4, external-agents 4, console-webhooks 4

Public live probes:

- `GET /api/v1/public/community-stats` returned `total_agents: 7079`, `total_users: 19379`, `total_income_ut: 2423800.0`, `active_agents: 513`.
- `GET /.well-known/agent.json` returned a valid Agent Card-like JSON, 7393 bytes.
- `GET /api/v1/capabilities?page=1&page_size=3` returned live marketplace capability items without auth.
- `GET /api/v1/demands?page=1&page_size=3` returned live demand records without auth.
- `POST /api/v1/public/playground/sandbox-key` returned a temporary read-only key: 30 min expiry, 4 remaining requests, GET only.
- `GET /mcp/sse` returned HTTP 200 `text/event-stream` and an MCP endpoint event: `event: endpoint`, `data: /mcp/messages/?session_id=...`.
- unauthenticated `POST /a2a` returned JSON-RPC error `-33005 Authentication failed: 认证失败`, confirming route and auth enforcement.

### 3. Protocol model

#### Agent Card

Public endpoint:

- platform-level: `GET https://api.uumit.com/.well-known/agent.json`
- per-agent: `GET /api/v1/agents/{agent_id}/.well-known/agent.json` and `/card`

Observed card fields:

- name: `UUAgent Platform`
- description: `AI 原生全球能力网络平台，提供 P2P 任务市场和 A2A 能力交易`
- protocol: `a2a/1.0`
- authentication: API key header `X-Api-Key`
- capabilities: streaming, pushNotifications, stateTransitionHistory, extension URNs
- skills include `task_publish` and others, with UUMit extension fields for pricing, settlement and task lifecycle tools.

Caution: docs and card have small inconsistencies: docs mention push notifications are not fully implemented and recommend `tasks/sendSubscribe` SSE as substitute, while the live card has fields that can read as more capable. Integrator should not assume full A2A push support.

#### A2A JSON-RPC

Endpoint:

- `POST https://api.uumit.com/a2a`

Documented methods:

- `tasks/send`
- `tasks/get`
- `tasks/cancel`
- `tasks/sendSubscribe` (SSE)

REST mapping:

- `tasks/send` ≈ `POST /api/v1/transactions`
- `tasks/get` ≈ `GET /api/v1/transactions/{id}`
- `tasks/cancel` ≈ `POST /api/v1/transactions/{id}/cancel`
- `tasks/sendSubscribe` = no direct REST equivalent; SSE subscription

Auth:

- Agent path: `X-Api-Key` + `X-Platform-User-Id`
- Human path: JWT bearer in some REST contexts
- Docs warn API Key wins if both are sent; integrations should send exactly one auth mode.

Important lifecycle nuance from the skill pack: `tasks/send` creates a pending transaction; execution requires freeze/settlement flow (`POST /api/v1/transactions/{transaction_id}/freeze` etc.). This is closer to a transaction workflow than a single fire-and-forget tool call.

#### MCP

Endpoint:

- `GET https://api.uumit.com/mcp/sse`

Live SSE handshake observed:

```text
HTTP/2 200
content-type: text/event-stream; charset=utf-8
cache-control: no-store
strict-transport-security: max-age=31536000; includeSubDomains

event: endpoint
data: /mcp/messages/?session_id=...
```

Auth modes documented:

- Preferred: HTTP headers `X-Api-Key` + `X-Platform-User-Id`
- Query params accepted for EventSource-like clients, but docs warn about API key leakage in proxy logs.

Documented MCP tools: 28. Categories:

- read-only/free: discover, search, match, wallet, credit, price suggestion
- write / UT-consuming: invoke, create order/transaction, accept/deliver/settle
- P2P task flow: publish/list/apply/accept/reject/withdraw/cancel
- file upload/download
- API Plaza calls

Key tool names include:

- `uuagent_discover`
- `uuagent_search`
- `uuagent_match_capability`
- `uuagent_wallet`
- `uuagent_query_credit`
- `uuagent_price_suggestion`
- `uuagent_invoke`
- `uuagent_create_order`
- `uuagent_create_transaction`
- `uuagent_accept_order`
- `uuagent_deliver_order`
- `uuagent_settle_transaction`
- `uuagent_register`
- `uuagent_publish_task`
- `uuagent_upload_file`
- `uuagent_get_upload_url`
- `uuagent_complete_upload`
- `uuagent_get_download_url`
- P2P task application tools
- `uuagent_call_data_api`

### 4. Hermes-specific integration claim is real, but should not be enabled blindly

`https://uumit.com/docs/sdk/hermes/` is a real docs page titled `Hermes Agent 接入`.

It instructs users to configure `~/.hermes/config.yaml` with an MCP SSE server:

```yaml
mcp_servers:
  uuagent:
    url: "https://api.uumit.com/mcp/sse"
    transport: "sse"
    headers:
      X-API-Key: "<your-api-key>"
      X-Platform-User-Id: "<your-platform-user-id>"
```

It also documents Device Auth and a skill-pack endpoint. UUMit skill pack HOSTS.md says Hermes should use `agent_platform_type=hermes_agent`, and can be integrated by Device Auth + MCP or by external-agent + webhook + SSE.

Hermes safety mismatch:

- UUMit docs/skill pack are optimized for autonomous monetization and L4 behavior.
- Hermes user profile strongly prefers real verification, explicit confirmation for dangerous paths, and event-driven architecture, but not silent high-risk side effects.
- Therefore direct install or enabling remote MCP/write tools in Hermes should be gated behind a local adapter and explicit policy, not copied into global config wholesale.

### 5. Official UUMit skill pack inspection

Downloaded `https://oss.uumit.com/skills/uumit-agent.zip` to `/tmp/uumit_skill/uumit_agent.zip`.

- size: 142,068 bytes
- sha256: `a084319242cf68b5a910b1b1358855e9a834f107aae5899ca75a96a302db6ace`
- manifest version: `1.0.37`
- files include `SKILL.md`, `API_REFERENCE.md`, `INTEROP.md`, `SAFETY.md`, `PLAYBOOKS.md`, `HOSTS.md`, `TROUBLESHOOTING.md`, multiple Node scripts for auth/rest/upload/cruise/runtime.

Notable scripts:

- `scripts/auth.js`: Device Auth flow
- `scripts/rest_request.js`: allowlisted REST caller with retry, idempotency, dry-run, auth-file support
- `scripts/runtime_connect.js`: SSE runtime connector for `/api/v1/agent-runtime/connect`
- `scripts/cruise_inbox_tick.js`, `cruise_apply_tick.js`, `cruise_deliver_tick.js`: autonomous periodic candidate discovery/action support
- `scripts/upload_file.js`: file upload, including chunked flow
- `scripts/validate_skill.js`: checks doc/allowlist/deprecated patterns

Critical safety defaults from `memory/runtime/agent-autonomy-config.json`:

```json
{
  "spend": { "auto_spend_max_ut": 100 },
  "job_accept": { "auto_accept_max_ut": 1000 },
  "auto_apply": { "enabled": true, "no_confirm_apply": true },
  "auto_review_applications": { "enabled": true, "no_confirm_required": true },
  "auto_deliver": { "enabled": true, "no_confirm_required": true },
  "autonomy_level": "L4"
}
```

SAFETY.md says:

- queries/search/wallet: automatic
- low-value data API calls and knowledge-store purchases: automatic under threshold
- auto-apply / auto-review / auto-deliver can happen without asking the user if enabled
- publish task, appointment, negotiation, withdrawal, delete, revoke: must confirm
- capability/external-agent/webhook/callback/skill/asset/API publishing: must confirm
- exposing local shell/filesystem/private repos/env vars: default forbidden; explicit user request plus second confirmation required

This is better than a totally unsafe package, but the default L4 automation is still too permissive for direct Hermes global adoption without a policy wrapper.

### 6. Business/economy observations

Observed public market data:

- Capability list includes many `digital_asset` items with 100+ UT prices, quality scores, sales counts often 0 for freshly created items.
- Knowledge store includes both plausible datasets and low-quality / risky marketing assets. Example surfaced item summary explicitly describes “土匪式营销思维” as low-quality, manipulative/grey-market style content.
- Public skill-showcase includes polished sample cards with high review counts and call counts for agents such as `AstraResearch`, `NovaCoder`, `CausalSigma`; these are showcase data and should not be treated as independently verified revenue/usage.

UT/wallet model:

- Docs distinguish CNY human accounts vs UT agent accounts.
- UT has withdrawable vs non-withdrawable buckets.
- Public configs show withdraw enabled, min UT 15, channels alipay/wechat, tier values, and `milestone.withdraw_unlock_ut: 100`.
- Docs mention `POST /api/v1/wallet/withdraw` and withdrawal records, but public OpenAPI sample path list did not obviously include withdraw in the first extracted wallet operations; needs authenticated/manual verification before claiming actual withdrawal readiness.

### 7. Risk assessment

#### Integration risk: high if installed directly

Reasons:

- Remote MCP exposes write/UT-consuming tools to the agent runtime.
- Skill pack defaults include L4 automation, auto-apply, auto-review and auto-deliver.
- API Key + Platform User ID is a powerful pair; leakage or wrong tenant mapping can act as another user.
- Query-param auth is documented as fallback; this increases log-leak risk and should be disabled in Hermes adapter.
- Skill scripts write credentials under skill `memory/uumit-auth.json`; importing into Hermes native skills/profile should be kept profile-scoped and secret-scanned.
- Marketplace contains mixed-quality and potentially grey content; agent auto-purchase/auto-call creates quality and abuse risks.

#### Protocol maturity: medium

Positive:

- Live OpenAPI, Agent Card, MCP SSE, A2A route, docs and downloadable skill pack exist.
- Error handling, idempotency, SSE and auth are documented.
- Public endpoints are coherent enough to build a read-only adapter.

Concerns:

- Domain was registered recently (2026-03-19) and product changelog starts May 2026; platform is early-stage.
- Push-notification/state-history capabilities appear partly aspirational/inconsistent.
- Some showcase data may be seeded/marketing, not real external usage proof.
- Public APIs expose marketplace/user-generated demand/capability metadata without auth; privacy expectations should be reviewed.
- DNS resolution in this environment returned 198.18.x.x proxy addresses, so infrastructure topology was not verifiable from this network.

#### Security model: better than average marketing demos, but not Hermes-ready by default

Good signs:

- Device Auth for CLI/Agent binding.
- API Key + user-context separation.
- Idempotency guidance.
- MCP SSE auth and no JWT for MCP.
- HTTPS, HSTS observed on API responses.
- Skill pack includes explicit safety docs and allowlisted REST wrapper.

Gaps for Hermes:

- Need local confirmation gates that override remote skill defaults.
- Need event-driven but user-auditable job queue, not hidden direct auto-actions.
- Need read-only first, write tools disabled by default.
- Need separate credential store, never YAML plaintext if avoidable.
- Need capability exposure review: never expose shell/files/repos/env by default.
- Need per-tool allowlist: `discover/search/agent-card/openapi` first; wallet only after explicit auth; spending/publishing/withdraw disabled until policy finalized.

## Hermes absorption map

### Absorb now as reference patterns

1. Agent Card as discoverability metadata
   - Useful for Hermes skill/capability registry.
   - Map Hermes skill metadata to an internal Agent Card-like shape.

2. MCP SSE as external capability surface
   - Useful as remote tool bridge, but only through a sandboxing adapter.

3. A2A transaction lifecycle
   - Interesting mapping to Hermes taskpool: `pending -> freeze/fund -> accept -> deliver -> confirm/settle/cancel`.
   - Do not merge directly into taskpool state; treat as external transaction adapter.

4. Device Auth for local agent binding
   - Similar to Gemini OAuth/provider binding patterns.
   - Should be stored in Hermes profile secret store, not skill memory blindly.

5. Skill Pack packaging
   - The manifest + scripts + docs + safety bundle is a useful distribution pattern.
   - Hermes can learn from the `validate_skill.js` / allowlisted REST wrapper pattern.

### Do not absorb directly

1. L4 autonomy defaults
   - Auto-spend 100 UT, auto-accept 1000 UT, no-confirm apply/review/deliver conflict with Hermes safety-default UX.

2. Cron-like巡航 as primary mechanism
   - User explicitly prefers event-driven automation over polling. Use runtime SSE/webhook events as primary; polling only reconciliation.

3. Direct remote MCP in global `~/.hermes/config.yaml`
   - Too broad. Use a profile-scoped adapter with read-only initial toolset.

4. Marketplace monetization promises
   - Treat as experimental; require real earned/withdrawn transaction evidence before any “Agent赚钱” claim.

## Recommended next actions

### Phase 0 — keep as research artifact

- Keep this report as evidence pack.
- Do not install or authenticate UUMit in default Hermes profile yet.

### Phase 1 — read-only adapter spike

Create a Hermes-local adapter that can:

- fetch `/api/v1/public/openapi.json`
- fetch `/.well-known/agent.json`
- list public capabilities/demands with pagination
- verify MCP SSE handshake without credentials
- validate schema drift

No credentials, no write calls, no UT spend.

### Phase 2 — authenticated sandbox only

If the user explicitly approves:

- use Device Auth with `agent_platform_type=hermes_agent`
- store credentials in a dedicated profile/secret path
- enable only read tools + wallet inspection first
- disable query-param auth
- disable all auto-spend/auto-apply/auto-review/auto-deliver defaults

### Phase 3 — governed write/transaction experiments

Only after Phase 2 evidence:

- create a disposable low-value capability or task
- test idempotency with a dry-run/readback pattern
- verify transaction freeze/settle lifecycle
- verify receipts/ledger/withdraw bucket semantics
- never expose local shell/files/repos/env vars

## Bottom line

UUMit is not just a Douyin slogan: public docs, OpenAPI, Agent Card, MCP SSE, A2A JSON-RPC route and a substantial skill pack are live. Technically it is worth watching and extracting patterns from.

But the product is very young, marketplace quality is mixed, and the official skill pack defaults are aggressive L4 monetization automation. For Hermes, the safe stance is: **reference architecture + read-only adapter first; no direct global MCP enablement, no credentials, no auto-spend/auto-apply, no shell/file exposure until a governed adapter and explicit user confirmation exist.**
