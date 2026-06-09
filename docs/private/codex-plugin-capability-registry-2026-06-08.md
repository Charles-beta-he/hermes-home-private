---
type: reference_review
status: bounded_evidence_tranche
created_at: 2026-06-08T14:10:32Z
source_task: 2026-06-08-评估-codex-插件能力面接入-hermes能力清单权限分层与-superpowers-增量吸收
scope: codex_plugin_capability_registry
---

# Codex 插件能力面接入 Hermes：能力 registry 与权限分层

## Evidence read-back

- 视频证据笔记：`/Users/charles/.hermes/docs/private/douyin-codex-plugins-intake-2026-06-08.md`
  - 页面可见标题：第4集 | Codex 干活飞起。
  - 自动章节/OCR 显示能力面：hyperframes、computer use、Chrome、presentation、superpowers。
  - 该笔记明确 Hermes 边界：Codex 插件是 action surface，不是事实源；Hermes taskpool/ledger/evidence 仍是 authority layer；产物必须回读验证；Chrome/Computer Use/Gmail 必须有权限门禁。
- 本机状态命令：`codex plugin list`（2026-06-08T14:10Z 实跑）
  - installed, enabled：`browser@openai-bundled`、`presentations@openai-primary-runtime`、`documents@openai-primary-runtime`、`spreadsheets@openai-primary-runtime`、`gmail@openai-curated`。
  - not installed：`chrome@openai-bundled`、`computer-use@openai-bundled`、`hyperframes@openai-curated`、`superpowers@openai-curated`。
- Read-back plugin manifests:
  - HyperFrames: `/Users/charles/.codex/.tmp/plugins/plugins/hyperframes/.codex-plugin/plugin.json`
  - Superpowers: `/Users/charles/.codex/.tmp/plugins/plugins/superpowers/.codex-plugin/plugin.json`
  - Chrome: `/Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/chrome/.codex-plugin/plugin.json`
  - Computer Use: `/Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use/.codex-plugin/plugin.json`
  - Presentations: `/Users/charles/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/presentations/.codex-plugin/plugin.json`
  - Browser: `/Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/browser/.codex-plugin/plugin.json`
  - Gmail: `/Users/charles/.codex/.tmp/plugins/plugins/gmail/.codex-plugin/plugin.json`

## Capability matrix

| Plugin | Local state | Manifest capability / description | Hermes overlap | Net new value | Permission tier | Default policy |
|---|---:|---|---|---|---|---|
| Browser (`browser@openai-bundled`) | installed, enabled | In-app browser for localhost/file/current tab; navigate/inspect/click/type/screenshot; capabilities Interactive/Read/Write. | Overlaps Hermes browser tools / frontend smoke checks. | Useful as Codex-local dev-page verifier, but not an authority source. | low-to-medium: local dev/browser tab only. | May be default-available for local/dev URLs with read-back evidence. |
| Presentations (`presentations@openai-primary-runtime`) | installed, enabled | Create/edit/inspect/render/verify/export slide decks; capabilities Interactive/Write. | Overlaps Hermes document generation/reporting, not taskpool governance. | Durable deck/PPTX generation and visual deck repair. | medium: file write/export; no account automation unless explicitly requested. | Default-available for local artifact generation with output read-back. |
| Documents / Spreadsheets | installed, enabled | Present in `codex plugin list`; not part of this task's manifest-read scope. | Overlaps Hermes file/document helpers. | Structured office-file generation. | medium. | Allow only for local artifact creation and explicit requested outputs. |
| Gmail (`gmail@openai-curated`) | installed, enabled | Gmail connector for inbox summary, draft replies, organizing threads; capabilities Interactive/Write. | Hermes gateway/email workflows may overlap, but Gmail touches a real account. | Potential mail triage, but high-risk side-effect surface. | high: real account + send/draft/organize semantics. | **Do not default-enable in Hermes-controlled execution**; single-task explicit authorization only, preferably read-only unless send/draft is separately approved. |
| HyperFrames (`hyperframes@openai-curated`) | not installed | HTML+CSS+GSAP video compositions, captions, TTS, audio-reactive visuals, website-to-video; capabilities Read/Write. | Overlaps OculOS/PageAgent/Presentations demo output surfaces, not core taskpool. | Product demo / short video / animated prototype generation. | medium-to-high: write/render media; may fetch/transform web content. | Not installed by default; allow as P2 single-task artifact generator after output path + no-account boundary is stated. |
| Superpowers (`superpowers@openai-curated`) | not installed | Agentic skills methodology: brainstorming, planning, TDD, debugging, parallel execution, code review; capabilities Interactive/Read/Write. | Strong overlap with Hermes skills/taskpool/proof gate. | Useful as pattern library for prompts/checklists, not as runtime authority. | governance-sensitive: could compete with Hermes authority layer. | Do not install as default runtime controller; absorb selectively into Hermes skills/process docs with SSOT references. |
| Chrome (`chrome@openai-bundled`) | not installed | Uses user's existing Chrome state: tabs, logged-in sessions, cookies, extensions; navigate/view/click/type/screenshots; capabilities Interactive/Read. | Overlaps browser tools but with real logged-in state. | Fallback when API/connector unavailable and user explicitly approves. | high: logged-in browser/session exposure. | **Prohibited as default**; single-task explicit approval, site allowlist, read-back, no credential capture. |
| Computer Use (`computer-use@openai-bundled`) | not installed | Controls macOS apps, may use screenshots/page content, interacts with files/apps; desktop automation. | Overlaps edge-worker run_command/browser_screenshot at much higher blast radius. | Last-resort repetitive desktop operation. | critical: desktop control/accessibility + screenshots. | **Prohibited as default**; explicit lease + app allowlist + stop conditions + human-visible audit only. |

## Permission tiers for Hermes integration

1. `codex_plugin.local_artifact` — local-only artifact generation and local dev-page verification. Candidate plugins: Browser for localhost/file targets, Presentations for deck artifacts, Documents/Spreadsheets if output is local and read back. Required evidence: command/tool invocation, output path, file/read-back or screenshot/render proof.
2. `codex_plugin.external_read` — reads external sites/resources without logged-in state. Candidate plugin: Browser or non-account web fetch. Required evidence: source URL, capture timestamp, extracted claims, no hidden account state.
3. `codex_plugin.account_read` — touches logged-in accounts or personal workspace state. Candidate plugins: Chrome, Gmail read-only. Required evidence: explicit user authorization, target account/site, scope, redaction, no write/send.
4. `codex_plugin.account_write` — drafts/sends/edits/organizes real-account resources. Candidate plugins: Gmail, Chrome acting in SaaS apps. Required evidence: explicit per-action authorization, preview/read-back before commit, idempotency/rollback statement.
5. `codex_plugin.desktop_control` — controls macOS apps/files/screens. Candidate plugin: Computer Use. Required evidence: explicit lease, app allowlist, forbidden surfaces, heartbeat/stop condition, artifact replay/read-back.

## Default / conditional / prohibited policy

- Default-available under Hermes governance: `browser` for local/dev verification and `presentations` for local deck artifacts, because both are already installed and can be bounded to local output/read-back.
- Conditional single-task authorization: `hyperframes` for demo/video artifacts; `documents`/`spreadsheets` when task explicitly asks for office artifacts; `gmail` only if the user explicitly requests Gmail and approves account scope.
- Prohibited by default: `chrome`, `computer-use`, `gmail` account write/send surfaces, and any connector that can mutate external accounts or bypass Hermes taskpool/evidence/proof gates.
- Not a fact source: no Codex plugin output may directly mutate taskpool status or become closeout evidence without Hermes-side read-back, validation, and structured evidence.

## Minimal viable invocation contract

Before a Hermes-controlled task may use a Codex plugin, the task/handoff must declare:

```yaml
codex_plugin_contract:
  plugin: <name@marketplace>
  local_state: installed_enabled | not_installed | unavailable
  permission_tier: codex_plugin.local_artifact | codex_plugin.external_read | codex_plugin.account_read | codex_plugin.account_write | codex_plugin.desktop_control
  authority: budget-handoff | autonomous-execution | explicit-user-approval
  allowed_targets: []
  forbidden_targets: [credentials, payment, send_message, external_account_mutation]
  expected_artifacts: []
  readback_required: true
  taskpool_authority: hermes_taskpool_remains_ssot
```

Closeout must include at least one plugin-specific artifact/read-back proof, e.g. rendered deck exists and opens, HyperFrames render path + preview, Browser screenshot/DOM assertion for localhost, or Gmail/Chrome explicit approval + dry-run/read-only extraction. `py_compile`, generic `selfcheck`, hash proof, or plugin discussion alone is insufficient.

## Implementation recommendation

- Do not install or enable new Codex plugins from this task.
- Add a future Hermes-side registry only after an SSOT schema is ratified; start with a read-only catalog derived from `codex plugin list` + plugin manifests.
- The first safe implementation slice should be a read-only `codex_plugin_inventory` script/helper that emits JSON rows: plugin, marketplace, installed/enabled state, manifest path, declared capabilities, permission tier, and default policy. It must not mutate Codex config.
- Superpowers should be treated as a process pattern source; any useful workflow should land as Hermes skill/process edits under existing taskpool proof gates, not as a competing runtime controller.
