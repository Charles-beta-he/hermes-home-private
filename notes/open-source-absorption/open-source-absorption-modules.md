# Open-source Absorption Modules — 开源项目学习任务模块化归档

Generated: `2026-06-16T03:49:25.139912+00:00`

## 目标与长期稳定方案

目标：把历史开源项目学习/评估任务从“散落任务笔记”升级为可持续演化的模块系统。后续每次学习外部项目，都先进入模块 registry，再根据证据决定是否沉淀为 skill、taskpool 实现、控制台投影或明确拒绝。

长期稳定闭环：
1. Source review：只读验证外部项目身份、README/docs/license/风险边界。
2. Pattern extraction：抽取可迁移机制，不做 stack cargo-cult。
3. Module mapping：映射到 18 个顶层模块之一；Data Agent/MLOps 作为 Evidence Retrieval 与 Vision/Media 的交叉子域，不单独膨胀顶层模块。
4. Safety gate：声明权限、外部副作用、数据/隐私/物理执行边界。
5. Minimal verifiable slice：只落最小可验证切片，必须有 readback/test/proof。
6. Durable landing：合格经验进入 skill/doc/code/dashboard；未合格进入 watch/reject，不污染全局 memory。

## 当前扫描摘要

- 模块数：18
- 匹配任务引用：162
- 主任务引用：141
- 支撑/收敛/补证任务引用：21
- 状态分布：`{"unknown": 1, "archived": 7, "done": 152, "running": 1, "review": 1}`
- 架构目标分布：`{"unknown": 7, "local-brain": 92, "taskpool": 37, "skill-graph": 24, "provider-quota": 2}`

## 18 个模块

### 1. 多智能体团队编排 / `agent_team_orchestration`

- Priority: `P2`
- Scope: planner/executor/verifier/reviewer 等角色编排、handoff、团队 runtime、产物生成与评审闭环。
- Stable target: 形成 role registry + handoff protocol + team-run receipt；任何新增 agent 角色必须声明输入/输出/权限/验收证据。
- Next verifiable slice: 抽取已完成 OpenSwarm/oh-my-codex/OpenAgents 任务中的角色协议，生成最小 role registry 草案。
- Task refs: 7 total / 3 primary / 4 support
- Representative tasks:
  - `done` `P2` Feynman 开源 AI 研究代理架构分析与 Hermes 吸收评估 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估.md`
  - `done` `P2` 为 2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估 细化 framing 收敛前置任务 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-31-为-2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估-细化-framing-收敛前置任务.md`
  - `done` `P2` 为 2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估 细化 patch normalization 收敛前置任务 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-31-为-2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估-细化-patch-normalization-收敛前置任务.md`
  - `done` `P2` 为 2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估 细化 quota observability 收敛前置任务 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-31-为-2026-05-30-feynman-开源-ai-研究代理架构分析与-hermes-吸收评估-细化-quota-observability-收敛前置任务.md`
  - `done` `P2` 补证闭环｜Task - Feynman 开源 AI 研究代理架构分析与 Hermes 吸收评估｜missing_multimodel_certification — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-补证闭环task---feynman-开源-ai-研究代理架构分析与-hermes-吸收评估missing-multimodel-certification.md`

### 2. 长期任务 / Mission / `long_running_mission`

- Priority: `P2`
- Scope: objective ledger、tick、stage-report、human handoff、resume gate、预算续航。
- Stable target: Mission ledger 为 SSOT；所有阻塞、预算扩展、恢复都可从 ledger + stage report 追溯。
- Next verifiable slice: 把 mission resume/budget continuation 检查表转成模块验收门。
- Task refs: 0 total / 0 primary / 0 support
- Representative tasks:
  - none yet; module kept as forward-compatible slot.

### 3. 任务池治理 / `taskpool_governance`

- Priority: `P1`
- Scope: 开源项目经验进入 taskpool 后的 claim、eligibility、dispatch、proof、ratification、review→done 生命周期。
- Stable target: 任务状态只能由证据驱动推进；dispatch、proof、review、done 全部可读回验证。
- Next verifiable slice: 补一份 taskpool 模块 contract：状态源、投影、proof sidecar、失败回滚。
- Task refs: 12 total / 12 primary / 0 support
- Representative tasks:
  - `done` `P2` 吸收 AI Agent 五大核心技术革新到 Hermes 自演化主链 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-吸收-ai-agent-五大核心技术革新到-hermes-自演化主链.md`
  - `done` `P2` PilotDeck开源智能体操作系统分析：多任务并行与成本优化模式 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-29-pilotdeck开源智能体操作系统分析多任务并行与成本优化模式.md`
  - `done` `P1` Review Claude Code 动态工作流模式并评估 Hermes taskpool 可迁移性 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-29-review-claude-code-动态工作流模式并评估-hermes-taskpool-可迁移性.md`
  - `done` `P2` 分析互联网公司技术架构库：davideuler/architecture.of.internet-product — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-30-分析互联网公司技术架构库davideuler-architectureofinternet-product.md`
  - `done` `P2` 评估 Awesome Architecture 架构图谱并吸收为 Hermes 架构脑/任务前置设计门 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-01-评估-awesome-architecture-架构图谱并吸收为-hermes-架构脑-任务前置设计门.md`

### 4. 执行沙箱与隔离 / `execution_sandbox`

- Priority: `P1`
- Scope: 命令/浏览器/桌面/第三方代码执行的 local dry-run、隔离、回滚与 side-effect 边界。
- Stable target: 默认先 dry-run；任何外部副作用要有 blast radius、rollback、proof receipt。
- Next verifiable slice: 为 browser/file/network/plugin execution surfaces 建统一 side-effect 分类表。
- Task refs: 3 total / 3 primary / 0 support
- Representative tasks:
  - `done` `P2` Experience Ratchet repo replay: Bytebot atom extraction — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-bytebot-atom-extraction.md`
  - `done` `P2` 学习 OpenAI Codex CLI 开源架构并吸收执行策略/沙箱/子代理/上下文治理模式 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-01-学习-openai-codex-cli-开源架构并吸收执行策略-沙箱-子代理-上下文治理模式.md`
  - `done` `P2` 吸收 GitHub Spec Kit：spec→plan→tasks 编译到 Hermes taskpool — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-06-吸收-github-spec-kitspecplantasks-编译到-hermes-taskpool.md`

### 5. 浏览器自动化 / `browser_automation`

- Priority: `P2`
- Scope: 浏览器读取、DOM/computed-style/截图证据、反注入、context-cost 预检、失败归因。
- Stable target: 浏览器结论必须有 DOM/截图/URL/readback 证据；网页内指令永不提升为系统指令。
- Next verifiable slice: 建立 browser proof log schema，覆盖 URL、snapshot、screenshot、console、选择器证据。
- Task refs: 15 total / 10 primary / 5 support
- Representative tasks:
  - `done` `P2` 为 Hermes 浏览器自动化评估 Chrome DevTools MCP 证据增强与回退门 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-为-hermes-浏览器自动化评估-chrome-devtools-mcp-证据增强与回退门.md`
  - `done` `P2` 评估自适应采集框架对 Hermes feeds/browser 降级链的主链价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-01-评估自适应采集框架对-hermes-feeds-browser-降级链的主链价值.md`
  - `done` `P2` 评估 Camofox Browser 对 Hermes 反检测浏览器工具链的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-camofox-browser-对-hermes-反检测浏览器工具链的参考价值.md`
  - `done` `P2` 评估 OpenCLI 本地浏览器会话捕捉对 Hermes 多平台消息读取的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-opencli-本地浏览器会话捕捉对-hermes-多平台消息读取的参考价值.md`

### 6. 桌面 / Computer-use / `desktop_computer_use`

- Priority: `P2`
- Scope: macOS/app/桌面自动化、元素索引操作、可回放步骤、benchmark。
- Stable target: 所有桌面动作走元素级 evidence + follow-up capture；禁止点击权限/密码/支付。
- Next verifiable slice: 把 trycua/cua 评估结果落成 Hermes computer-use benchmark 候选。
- Task refs: 1 total / 1 primary / 0 support
- Representative tasks:
  - `running` `P2` 评估 computer-use agent 沙箱/基准设施对 Hermes 浏览器自动化主链的可维护接入门 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-16-评估-computer-use-agent-沙箱-基准设施对-hermes-浏览器自动化主链的可维护接入门.md`

### 7. MCP / 外部连接器 / `mcp_connector`

- Priority: `P2`
- Scope: MCP、A2A、外部 app connector、direct-tool、connector provenance、gated write。
- Stable target: read/write 分层；connector 必须声明 provenance、auth scope、side-effect class、disable path。
- Next verifiable slice: 统一 MCP/Connector capability card schema。
- Task refs: 13 total / 13 primary / 0 support
- Representative tasks:
  - `archived` `P2` P2 评估 Semble MCP 代码搜索对 Hermes context 节流与代码定位链路的可吸收增量 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-p2-评估-semble-mcp-代码搜索对-hermes-context-节流与代码定位链路的可吸收增量-2.md`
  - `done` `P2` 评估 Anthropic Harness Design 四层方法与 claude-for-legal 对 Hermes 长任务能力供给的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-anthropic-harness-design-四层方法与-claude-for-legal-对-hermes-长任务能力供给的参考价值-2.md`
  - `done` `P2` 评估 Anthropic Harness Design 四层方法与 claude-for-legal 对 Hermes 长任务能力供给的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-anthropic-harness-design-四层方法与-claude-for-legal-对-hermes-长任务能力供给的参考价值-3.md`
  - `done` `P2` 评估 Anthropic Harness Design 四层方法与 claude-for-legal 对 Hermes 长任务能力供给的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-anthropic-harness-design-四层方法与-claude-for-legal-对-hermes-长任务能力供给的参考价值.md`
  - `done` `P2` 评估 OpenAgents Workspace/Network 对 Hermes 多智能体协作与外部工作区集成的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-openagents-workspace-network-对-hermes-多智能体协作与外部工作区集成的参考价值-2.md`

### 8. 远程触手 / 运维执行 / `remote_hands`

- Priority: `P3`
- Scope: SSH/SFTP/WebSocket 终端、远程主机画像、批量任务、远端执行 safety gate。
- Stable target: 远端主机能力画像与命令权限分层先行，写操作需要显式授权和回滚。
- Next verifiable slice: 从 Moso 任务抽取 host capability profile 草案。
- Task refs: 8 total / 6 primary / 2 support
- Representative tasks:
  - `done` `P2` 评估 Moso/毛竹 对 Hermes 远程 AI 运维与本地触手架构的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-moso-毛竹-对-hermes-远程-ai-运维与本地触手架构的参考价值-2.md`
  - `done` `P2` 评估 Moso/毛竹 对 Hermes 远程 AI 运维与本地触手架构的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-moso-毛竹-对-hermes-远程-ai-运维与本地触手架构的参考价值-3.md`
  - `done` `P2` 评估 Moso/毛竹 对 Hermes 远程 AI 运维与本地触手架构的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-moso-毛竹-对-hermes-远程-ai-运维与本地触手架构的参考价值-4.md`
  - `done` `P2` 评估 Moso/毛竹 对 Hermes 远程 AI 运维与本地触手架构的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-moso-毛竹-对-hermes-远程-ai-运维与本地触手架构的参考价值.md`
  - `done` `P2` 为 2026-06-02-评估-moso-毛竹-对-hermes-远程-ai-运维与本地触手架构的参考价值-2 细化 patch normalization 收敛前置任务 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-为-2026-06-02-评估-moso-毛竹-对-hermes-远程-ai-运维与本地触手架构的参考价值-2-细化-patch-normalization-收.md`

### 9. 证据检索 / RAG / `evidence_retrieval`

- Priority: `P1`
- Scope: 本地证据索引、BM25+RRF、rerank、章节树、citation bundle、source-grounded retrieval；Data Agent/MLOps 中的数据源、schema、标注配置、评测证据归入本模块。
- Stable target: 先证据后结论；所有任务/skill/日报可以被 source→claim→evidence 反查；Data Agent/Label Studio 类任务按 dataset evidence contract 管理。
- Next verifiable slice: 为任务库与 skill 库生成轻量 evidence index，不改变原始记录。
- Task refs: 33 total / 30 primary / 3 support
- Representative tasks:
  - `unknown` `unknown` Evolution Lane 认证死循环 — 根因分析与预防方案 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-16-evolution-lane-认证死循环-根因分析与预防方案.md`
  - `done` `P2` Experience Ratchet repo replay: AgentMemory atom extraction — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-agentmemory-atom-extraction.md`
  - `done` `P2` Experience Ratchet repo replay: Hermes upstream ratchet atom extraction — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-hermes-upstream-ratchet-atom-extraction.md`
  - `done` `P2` Experience Ratchet repo replay: RAG-Anything atom extraction — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-rag-anything-atom-extraction.md`
  - `done` `P2` 分析评估 Yazi 终端文件管理器并沉淀本地开发工作流 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-分析评估-yazi-终端文件管理器并沉淀本地开发工作流.md`

### 10. 上下文 / 预算控制 / `context_budget_control`

- Priority: `P1`
- Scope: 上下文预算、压缩、摘要、可逆 trace、tool output 瘦身、context savings telemetry。
- Stable target: 压缩必须可逆或可追溯；不同内容类型使用不同摘要/裁剪策略。
- Next verifiable slice: 定义 JSON/log/diff/code/search 五类输出压缩策略与回读测试。
- Task refs: 6 total / 6 primary / 0 support
- Representative tasks:
  - `archived` `P2` 评估本地代码知识图谱作为 Hermes 上下文定位与工具调用降噪层 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-21-评估本地代码知识图谱作为-hermes-上下文定位与工具调用降噪层-2.md`
  - `archived` `P2` 吸收 DeepSeek-Reasonix cache-first coding-agent 架构以强化 Hermes 成本/上下文控制 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-吸收-deepseek-reasonix-cache-first-coding-agent-架构以强化-hermes-成本-上下文控制.md`
  - `done` `P2` Guardrails概念评估报告 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-30-评估guardrails概念对hermes治理门的映射价值.md`
  - `done` `P2` 评估 abtop 对 Hermes AI 编码终端用量与资源观测的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-abtop-对-hermes-ai-编码终端用量与资源观测的参考价值.md`
  - `done` `P1` 评估 Headroom 对 Hermes context/budget 控制平面与可逆压缩证据链的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-headroom-对-hermes-context-context-控制平面与可逆压缩证据链的参考价值.md`

### 11. 记忆治理 / `memory_governance`

- Priority: `P2`
- Scope: 偏好、长期记忆、project profile 分流、漂移检测、stale ghost 防护。
- Stable target: 用户偏好进 memory；项目事实进 profile；流程进 skill；任务进 session/task，防止 ghost。
- Next verifiable slice: 把 open-source absorption 的持久事实限定在 registry，不写入全局 memory。
- Task refs: 11 total / 9 primary / 2 support
- Representative tasks:
  - `done` `P2` Experience Ratchet repo replay: cross-repo consensus synthesis — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-cross-repo-consensus-synthesis.md`
  - `done` `P2` Gap-analyze getzep/graphiti for Hermes temporal context graph memory absorption — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-gap-analyze-getzep-graphiti-for-hermes-temporal-context-graph-memory-absorption.md`
  - `done` `P2` 二次评估 MemPalace 当前基准与 Hermes 已落地本地记忆方案的增量差异 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-二次评估-mempalace-当前基准与-hermes-已落地本地记忆方案的增量差异.md`
  - `archived` `P2` Task - 评估 SkillOpt ReflACT 管线对 Hermes 技能自演化的可迁移性 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-29-task---评估-skillopt-reflact-管线对-hermes-技能自演化的可迁移性.md`
  - `done` `P2` 评估 EverOS/EverCore 长期记忆 OS 对 Hermes 本地大脑的可吸收模式 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-31-评估-everos-evercore-长期记忆-os-对-hermes-本地大脑的可吸收模式.md`

### 12. Skill 图谱 / 经验棘轮 / `skill_graph`

- Priority: `P1`
- Scope: skill candidate staging、触发边界、发布门、去重、routing-surface 回归。
- Stable target: 外部项目经验必须通过 candidate→verification→publish/decline；不把读后感直接变技能。
- Next verifiable slice: 对 18 模块各定义 positive/neighbor/forbidden trigger examples。
- Task refs: 23 total / 18 primary / 5 support
- Representative tasks:
  - `done` `P1` Adopt andrej-karpathy-skills into Hermes coding guardrails: source/license note + gap analysis — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-adopt-andrej-karpathy-skills-into-hermes-coding-guardrails-source-license-note--.md`
  - `done` `P2` Experience Ratchet repo replay baseline: source freshness matrix — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-baseline-source-freshness-matrix.md`
  - `done` `P2` Experience Ratchet repo replay: Karpathy Skills atom extraction — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-karpathy-skills-atom-extraction.md`
  - `done` `P2` Experience Ratchet repo replay: OpenClaw wrong-source supersede atom — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-openclaw-wrong-source-supersede-atom.md`
  - `done` `P2` Gap-analyze mattpocock/skills for Hermes skill-graph absorption — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-gap-analyze-mattpocock-skills-for-hermes-skill-graph-absorption.md`

### 13. 执行证明 / `proof_of_execution`

- Priority: `P1`
- Scope: 执行 receipt、proof sidecar、claim→evidence map、可回放与验收证据。
- Stable target: 任何自动闭环都产出 machine-readable receipt；claim 必须链接 evidence。
- Next verifiable slice: 统一 proof sidecar schema，并接入 taskpool/browser/mission 三类来源。
- Task refs: 0 total / 0 primary / 0 support
- Representative tasks:
  - none yet; module kept as forward-compatible slot.

### 14. 安全审查 / `security_review`

- Priority: `P2`
- Scope: 代码/命令/插件/commit/push 安全审查，secret/permission scanner，diff review hook。
- Stable target: 安全审查作为能力供给而不是口号；高风险 diff/外部执行默认 fail-closed。
- Next verifiable slice: 抽取 security-guidance 三层 hook 为 Hermes 本地审查清单。
- Task refs: 5 total / 5 primary / 0 support
- Representative tasks:
  - `done` `P2` 评估 Anthropic Cybersecurity Skills 对 Hermes 安全技能图谱的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-评估-anthropic-cybersecurity-skills-对-hermes-安全技能图谱的参考价值.md`
  - `done` `P2` 评估 Anthropic security-guidance 插件对 Hermes 安全审查与代码生成闭环的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-anthropic-security-guidance-插件对-hermes-安全审查与代码生成闭环的参考价值-2.md`
  - `done` `P2` 评估 Anthropic security-guidance 插件对 Hermes 安全审查与代码生成闭环的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-anthropic-security-guidance-插件对-hermes-安全审查与代码生成闭环的参考价值.md`
  - `done` `P2` 评估并接入 Web Check 外部网站 OSINT 源能力 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-07-评估并接入-web-check-外部网站-osint-源能力.md`
  - `done` `P2` 二次吸收 Anthropic Cybersecurity Skills 与 ERC-8126：构建 Hermes 安全技能图谱自检落地方案 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-14-二次吸收-anthropic-cybersecurity-skills-与-erc-8126构建-hermes-安全技能图谱自检落地方案.md`

### 15. 权限 / 合规 / 敏感推断 / `permission_compliance`

- Priority: `P2`
- Scope: 法律、医疗、生理、声音克隆、物理执行、支付/凭证/外部发送等红线。
- Stable target: 敏感能力只能 read-only 或 gated；同意、用途、日志、撤回路径必须明确。
- Next verifiable slice: 形成 sensitive capability matrix：voice/biometric/legal/physical/browser-auth。
- Task refs: 2 total / 2 primary / 0 support
- Representative tasks:
  - `archived` `P3` 评估 Shadowbroker OSINT 多源聚合对 Hermes 外部情报工具的安全吸收边界 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-评估-shadowbroker-osint-多源聚合对-hermes-外部情报工具的安全吸收边界.md`
  - `done` `P2` FacePhys/微面科技线索：端侧生理感知与视觉会话安全边界评估 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-13-facephys-微面科技线索端侧生理感知与视觉会话安全边界评估.md`

### 16. 语音 / Avatar 交互 / `voice_avatar_interaction`

- Priority: `P3`
- Scope: TTS、实时语音、打断、Live2D/avatar、voice console、provider safety。
- Stable target: 语音/Avatar 是交互层投影，不绕过文本 proof、权限和记忆治理。
- Next verifiable slice: 把 Open-LLM-VTuber/VoxCPM 经验收敛为 voice adapter contract。
- Task refs: 4 total / 4 primary / 0 support
- Representative tasks:
  - `done` `P2` 技术储备：评估 OpenBMB/VoxCPM 作为 Hermes 对话语音层 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-01-技术储备评估-openbmb-voxcpm-作为-hermes-对话语音层.md`
  - `done` `P2` Task - 评估 Open-LLM-VTuber 对 Hermes 语音免提交互、实时打断与 Live2D 陪伴层的可吸收模式 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-05-task---评估-open-llm-vtuber-对-hermes-语音免提交互实时打断与-live2d-陪伴层的可吸收模式.md`
  - `done` `P2` VoxCPM2/OpenBMB：多语言 TTS 与声音克隆安全边界二次评估 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-07-voxcpm2-openbmb多语言-tts-与声音克隆安全边界二次评估.md`
  - `done` `P2` Open-LLM-VTuber：本地语音/Live2D/MCP 交互架构吸收评估 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-13-open-llm-vtuber本地语音-live2d-mcp-交互架构吸收评估.md`

### 17. 视觉 / 媒体理解 / `vision_media_understanding`

- Priority: `P3`
- Scope: 视频理解、时间戳证据、自动剪辑、视觉会话、端侧感知 adapter；Roboflow/video 数据理解类 MLOps 任务作为视觉证据链子域处理。
- Stable target: 视觉结论必须带截图/帧/时间戳/模型来源；敏感推断默认不输出或需授权。
- Next verifiable slice: 定义 video→timestamp evidence report 模板。
- Task refs: 12 total / 12 primary / 0 support
- Representative tasks:
  - `done` `P2` 评估 Agentic 视频/数字人工作流对 Hermes media skill 的吸收边界 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-评估-agentic-视频-数字人工作流对-hermes-media-skill-的吸收边界.md`
  - `done` `P2` 评估 Keye-VL-2.0-30B-A3B：长视频多模态证据理解与 Hermes 外部专家接入 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-01-评估-keye-vl-20-30b-a3b长视频多模态证据理解与-hermes-外部专家接入.md`
  - `done` `P3` 预留信息源：确认并关注 Osiris OSINT 平台 simplifaisoul/osiris 的安全吸收边界 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-02-预留信息源确认并关注-osiris-osint-平台-simplifaisoul-osiris-的安全吸收边界.md`
  - `done` `P2` 评估 LongCat-Video-Avatar 1.5 照片音频数字人口播能力接入 Hermes — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-longcat-video-avatar-15-照片音频数字人口播能力接入-hermes-2.md`
  - `done` `P2` 评估 LongCat-Video-Avatar 1.5 照片音频数字人口播能力接入 Hermes — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-longcat-video-avatar-15-照片音频数字人口播能力接入-hermes.md`

### 18. 制造脑 / 3D / 外部控制 / `manufacturing_3d_external_control`

- Priority: `P3`
- Scope: 3D asset、CAD、photo-to-3D、数字孪生、物理执行 ACK/timeout、多频闭环。
- Stable target: 生成资产先 draft-only；物理执行必须 ACK/timeout/kill-switch；不把视觉预览当制造验收。
- Next verifiable slice: 整理 3D asset record + mesh QA + slicer/export 安全门。
- Task refs: 7 total / 7 primary / 0 support
- Representative tasks:
  - `done` `P2` Analyze evo: Python SLAM/odometry trajectory evaluation toolkit (MichaelGrupp/evo) — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-30-analyze-evo-python-slam-odometry-trajectory-evaluation-toolkit-michaelgrupp-evo.md`
  - `done` `P2` 分析 Blueprint 网站功能并强化 Manufacturing Brain 蓝图/CAD/成本/BOM/装配评估能力 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-01-分析-blueprint-网站功能并强化-manufacturing-brain-蓝图-cad-成本-bom-装配评估能力.md`
  - `done` `P2` 评估 Articraft 对 Hermes 制造脑/3D 资产工作台的参考价值 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-articraft-对-hermes-制造脑-3d-资产工作台的参考价值.md`
  - `done` `P2` 评估 solidworks-automation-skill 截图对制造脑 CAD 自动化任务平面的可吸收模式 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-03-评估-solidworks-automation-skill-截图对制造脑-cad-自动化任务平面的可吸收模式.md`
  - `done` `P2` 技术储备：Godot 开源引擎架构与可迁移模式评估 — `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-06-技术储备godot-开源引擎架构与可迁移模式评估.md`

## 最可验证后续推进顺序

P1 先落 6 个模块，因为它们能形成所有后续吸收的稳定骨架：
- `taskpool_governance`：补一份 taskpool 模块 contract：状态源、投影、proof sidecar、失败回滚。
- `proof_of_execution`：统一 proof sidecar schema，并接入 taskpool/browser/mission 三类来源。
- `execution_sandbox`：为 browser/file/network/plugin execution surfaces 建统一 side-effect 分类表。
- `evidence_retrieval`：为任务库与 skill 库生成轻量 evidence index，不改变原始记录。
- `skill_graph`：对 18 模块各定义 positive/neighbor/forbidden trigger examples。
- `context_budget_control`：定义 JSON/log/diff/code/search 五类输出压缩策略与回读测试。

验收门：每个 P1 模块必须至少产出一个 machine-readable contract/schema 或 focused verifier；不能只写总结。

## 边界

- 本次没有执行任何第三方开源代码。
- 本次没有修改历史任务笔记，只生成 projection/registry。
- 后续若要把模块接入 taskpool lifecycle、dashboard 写操作或代码实现，需要按对应权限/测试门推进。
