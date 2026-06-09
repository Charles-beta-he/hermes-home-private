---
type: reference_review
status: complete
created_at: 2026-06-09T00:00:00Z
source_task: t_a429b91f
scope: codex_plugin_capability_registry_reconcile
---

# Codex 插件能力面接入 Hermes：2026-06-09 复核结论

## 1. 本次复核实际读回的证据

1. 抖音视频证据笔记：`/Users/charles/.hermes/docs/private/douyin-codex-plugins-intake-2026-06-08.md`
   - OCR/章节列出 5 个重点插件面：HyperFrames、Computer Use、Chrome、Presentation、Superpowers。
   - 笔记内已明确治理边界：Codex 插件是 action surface，不是 authority/事实源。

2. 当前本机 `codex plugin list` 实跑：
   - 命令：`codex plugin list`
   - 结果：`No marketplace plugins found.`
   - `codex plugin list --available --json` 结果：`{"installed":[],"available":[]}`
   - 这说明当前 CLI 的 marketplace 列表面为空，不能单独作为“已启用插件”事实源。

3. 当前本机 Codex 配置读回：`/Users/charles/.codex/config.toml`
   - marketplace 已配置：
     - `openai-bundled -> /Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled`
     - `openai-primary-runtime -> /Users/charles/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime`
   - plugin enabled 条目实际存在：
     - `documents@openai-primary-runtime`
     - `spreadsheets@openai-primary-runtime`
     - `presentations@openai-primary-runtime`
     - `gmail@openai-curated`
     - `browser@openai-bundled`

4. 当前本机 manifest 读回：
   - HyperFrames: `/Users/charles/.codex/.tmp/plugins/plugins/hyperframes/.codex-plugin/plugin.json`
   - Superpowers: `/Users/charles/.codex/.tmp/plugins/plugins/superpowers/.codex-plugin/plugin.json`
   - Chrome: `/Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/chrome/.codex-plugin/plugin.json`
   - Computer Use: `/Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/computer-use/.codex-plugin/plugin.json`
   - Presentations: `/Users/charles/.cache/codex-runtimes/codex-primary-runtime/plugins/openai-primary-runtime/plugins/presentations/.codex-plugin/plugin.json`
   - Browser: `/Users/charles/.codex/.tmp/bundled-marketplaces/openai-bundled/plugins/browser/.codex-plugin/plugin.json`
   - Gmail connector marker: `/Users/charles/.codex/.tmp/plugins/plugins/gmail/.app.json`

## 2. 安装/启用状态的复核判定

注意：当前 `codex plugin list` 与 2026-06-08 证据笔记里的输出不一致。基于本次工具读回，最稳妥的判定规则应改为：

- “当前已启用”以 `~/.codex/config.toml` 的 `[plugins."..."] enabled = true` 为准。
- “可被 Codex 识别的能力/manifest”以磁盘上的 `.codex-plugin/plugin.json` 或 `.app.json` 为准。
- `codex plugin list` 仅可当作 marketplace 快照观察，不再单独充当安装态 SSOT。

据此，本机当前更稳妥的状态表如下：

| Plugin | 当前判定 | 证据 |
|---|---|---|
| browser | 已启用 | `config.toml` enabled=true + browser manifest |
| presentations | 已启用 | `config.toml` enabled=true + presentations manifest |
| documents | 已启用 | `config.toml` enabled=true |
| spreadsheets | 已启用 | `config.toml` enabled=true |
| gmail | 已启用/已配置连接器入口 | `config.toml` enabled=true + `.app.json` |
| chrome | 未启用 | 无 enabled 条目，只有 bundled manifest |
| computer-use | 未启用 | 无 enabled 条目，只有 bundled manifest |
| hyperframes | 未启用 | 无 enabled 条目，只有 marketplace/plugin manifest |
| superpowers | 未启用 | 无 enabled 条目，只有 marketplace/plugin manifest |

## 3. 能力面、Hermes 重叠与净新增

### Browser
- manifest 描述：Codex in-app browser；面向 localhost/file/current tab；支持 navigate/inspect/click/type/screenshot。
- 与 Hermes 重叠：高度重叠 Hermes browser 工具与 Browser Harness 本地前端验收。
- 净新增：作为 Codex 内嵌执行面的“就地验证器”有价值，但不是新的 authority layer。
- Hermes 策略：默认可用，但仅限 local/dev URL，并要求截图/DOM/assertion 回读。

### Presentations
- manifest 描述：create/edit/render/verify/export presentation deck。
- 与 Hermes 重叠：重叠文档/交付产物生成，不重叠 taskpool authority。
- 净新增：PPTX/slide deck 本地工件生成与视觉修复。
- Hermes 策略：默认可用，但只用于本地工件生成与读回校验。

### HyperFrames
- manifest 描述：HTML+CSS+GSAP video composition、captions、TTS、audio-reactive、website-to-video。
- 与 Hermes 重叠：只与 PageAgent/OculOS/Presentations 在 demo/展示层有部分重叠，不进入主链治理。
- 净新增：把网页/HTML 直接转视频或动效原型，是 Hermes 当前工具面的增量。
- Hermes 策略：不默认安装/启用；仅单任务授权用于 demo/video artifact。

### Superpowers
- manifest 描述：planning、TDD、debugging、parallel execution、code review 等 agentic workflow。
- 与 Hermes 重叠：与 Hermes skills/taskpool/proof gate 强重叠。
- 净新增：主要是 prompts/checklists/methodology，而不是执行权限能力。
- Hermes 策略：不作为运行时控制器接入；只做“增量吸收”为 skills/流程模板。

### Chrome
- manifest 描述：使用用户现有 Chrome state（tabs、cookies、logged-in sessions、extensions）。
- 与 Hermes 重叠：与 browser/computer_use 都有交叉，但 blast radius 显著更高。
- 净新增：能直接利用真实登录态完成 SaaS/browser 任务。
- Hermes 策略：默认禁止；仅在单任务显式授权、目标站点白名单、只读优先、全程可审计时开放。

### Computer Use
- manifest 描述：控制 macOS apps，可能读取截图/页面内容，触达任意 app/file。
- 与 Hermes 重叠：与 Hermes `computer_use` 在能力上高度重叠；OculOS 路线提供的是更 deterministic 的 AX/API 控制，而不是更大权限面。
- 净新增：对 Codex 内部工作流来说是通用桌面控制，但对 Hermes 来说不是净新增，只是另一套高权限执行面。
- Hermes 策略：默认禁止；只有显式 lease、app allowlist、stop 条件、回放证据齐备时才允许。

### Gmail
- manifest/config 描述：真实账户读写/整理语义。
- 与 Hermes 重叠：Hermes 已有 email/gateway/send_message 路线；Gmail 插件触及真实账户，风险更高。
- 净新增：利用账户上下文做邮件整理/草稿，但副作用强。
- Hermes 策略：默认禁止写；若用户明确要求 Gmail 且确认账号范围，可单任务只读或草稿级授权，send 必须二次确认。

## 4. 权限分层结论

推荐沿用以下 5 层，而不是按“有没有插件”二元管理：

1. `codex_plugin.local_artifact`
   - 例：Browser(localhost/file)、Presentations、Documents/Spreadsheets(local only)
   - 默认可用

2. `codex_plugin.external_read`
   - 例：非登录态网页读取
   - 需声明 URL/source 与回读证据

3. `codex_plugin.account_read`
   - 例：Gmail 只读、Chrome 已登录态只读
   - 必须单任务显式授权

4. `codex_plugin.account_write`
   - 例：Gmail draft/send、Chrome 操作 SaaS 表单
   - 必须单动作审批 + 提交前预览

5. `codex_plugin.desktop_control`
   - 例：Computer Use
   - 最高权限；必须 lease/allowlist/stop condition/audit replay

## 5. 与 Hermes 现有路线的最终边界

- Browser / Presentations：可作为 Hermes 的“局部交付执行面”，但不改变 taskpool/evidence/ledger 的 authority。
- HyperFrames：可吸收为 P2 artifact lane，不进入主链默认依赖。
- Superpowers：应吸收其方法论，不应把它当新的 runtime governor。
- Chrome / Gmail / Computer Use：都属于高权限 side-effect surface，只能是单任务授权能力，不能默认打开。
- OculOS / Hermes computer_use / Browser Harness 已覆盖大部分浏览器/桌面验证与控制需求；Codex Chrome/Computer Use 对 Hermes 不是主链能力缺口，而是更高风险的替代执行面。

## 6. 最小可行接入规范

若未来 Hermes 要正式接入 Codex plugin surface，每次调用前至少要声明：

```yaml
codex_plugin_contract:
  plugin: <name@marketplace>
  local_state: enabled | manifest_only | unavailable
  permission_tier: local_artifact | external_read | account_read | account_write | desktop_control
  authority: budget-handoff | autonomous-execution | explicit-user-approval
  allowed_targets: []
  forbidden_targets: [credentials, payment, external_account_mutation_without_approval]
  expected_artifacts: []
  readback_required: true
  taskpool_authority: hermes_taskpool_remains_ssot
```

## 7. 对本任务的完成性判断

本任务要求的三类证据已满足：
- 已引用抖音视频证据笔记；
- 已实跑当前本机 `codex plugin list` 并解释其语义漂移；
- 已读取 HyperFrames / Superpowers / Chrome / Computer Use / Presentations manifest；
- 已明确哪些当前已启用，哪些只能在单任务授权下可启用；
- 已给出 capability registry、权限分层策略、默认可用/条件可用/默认禁止清单，以及与 Hermes/OculOS/Browser Harness 的边界结论。

最终建议：
- 不安装任何新 Codex 插件；
- 只把 Browser / Presentations 视作可默认纳入的低到中风险本地工件面；
- HyperFrames 做 P2 artifact lane；
- Superpowers 只吸收方法论；
- Chrome / Gmail / Computer Use 保持 fail-closed，必须单任务显式授权。
