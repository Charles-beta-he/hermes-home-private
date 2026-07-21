# openai/codex-plugin-cc 参考项目审查与 Hermes 吸收记录

日期：2026-07-21
参考仓库：https://github.com/openai/codex-plugin-cc
固定提交：`db52e28f4d9ded852ab3942cea316258ae4ef346`
版本：`v1.0.6`
许可证：Apache-2.0
本地快照：`/Users/charles/.hermes/runs/codex-plugin-cc-reference-review-20260721`

## 1. 结论

这个项目表面上是“在 Claude Code 内调用 Codex”，真正值得学习的是一套分层模型桥接架构：

```text
用户路由/命令
  -> 薄 Agent 或确定性命令
  -> provider runtime adapter
  -> 共享 app-server broker
  -> session-scoped job lifecycle
  -> schema/result renderer
  -> review/stop gate
```

它最强的部分不是提示词，而是将命令、Skill、Agent、脚本运行时、后台任务、证据输出和停止门禁拆开。Hermes 应吸收这些稳定合同，不应直接导入其 Claude Code 专用插件、提示词或运行时默认值。

## 2. 实证范围

已读取：

- README、package.json、插件 manifest；
- 3 个内部 Skill；
- codex-rescue Agent；
- 8 个 slash commands；
- SessionStart、SessionEnd、Stop hooks；
- stop-review prompt；
- review JSON Schema；
- app-server/broker/job/state/git/process/render 运行时代码；
- 测试、release、近期 commit 和 open issue 样本。

本地验证：

- `npm test`：91 tests，91 pass，0 fail；
- `node --check plugins/codex/scripts/*.mjs plugins/codex/scripts/lib/*.mjs`：通过；
- 当前代码规模约：Skills 540 行、Commands 263 行、runtime 5424 行、tests 3715 行。

这些证据证明固定提交的测试与语法检查通过，不证明跨平台、并发、长时间后台运行或生产安全已经完成。

## 3. 三个 Skill 的真实职责

### codex-cli-runtime

主模式：Wrapper / Guardrail。

合同非常窄：只允许 rescue subagent 调用一次 `codex-companion task`，可做的 Claude 侧工作只有提示词收紧；不得自行读仓库、调查、轮询、总结、修复或调用其他子命令。默认写能力由路由意图决定，模型和 effort 仅在用户显式指定时传入。

可迁移原则：外部模型桥接 Skill 应只声明路由、authority 和输出合同；argv 解析、状态、重试、进程和持久化交给确定性代码。

### codex-result-handling

主模式：Reviewer / Guardrail。

要求保留 verdict、severity、路径行号、推断/不确定性；review 后必须停止并询问用户，禁止自动修复；调用失败时不能由 Claude 补写一个“看起来合理”的替代结果。

可迁移原则：Reviewer 与 Executor 分离；模型评审不能隐式开启写权限；失败结果不能被渲染层粉饰为成功。

### gpt-5-4-prompting

主模式：Generator / Inversion。

它把提示词拆成可选合同块：task、output contract、follow-through、completeness、verification、missing-context、grounding、citation、action-safety、research、dig-deeper。核心不是 XML 本身，而是“先提高合同质量，再提高 reasoning effort”。

可迁移原则：提示词模块应是按风险/任务类型选装的合同，不是每次堆叠全部规则。

## 4. 架构级可迁移模式

### 4.1 命令、Skill、Agent、runtime adapter 四层分离

- Command：用户入口和确定性参数/交互；
- Skill：行为与权限合同；
- Agent：被限制的能力包装器；
- Runtime：协议、进程、状态、后台作业和 readback。

这比“一个大 Skill 里既分析又执行又轮询”更安全，也避免递归 Skill 调用。

### 4.2 按能力路由 authority

- review/adversarial-review：只读；
- rescue implementation：可写；
- diagnosis/research：只读；
- review 发现问题后：需要新的用户选择才能修复；
- 全局 npm 安装：先询问。

Hermes 应继续使用每条 route 的 authority matrix，而不是给某个模型一个全局永久权限。

### 4.3 输出必须是可验证 artifact contract

review schema 强制 verdict、summary、findings、severity、file/line、confidence、recommendation、next_steps。结构化输出和 renderer 组合，优于只靠自然语言“请认真审查”。

Hermes 的 reviewer/arbiter 应保留：schema validation、证据锚点、不确定性、malformed-output 降级以及 no-substitute-answer。

### 4.4 后台调用必须有完整生命周期

项目提供 job ID、phase、log、stored result、status、result、cancel、resume、session cleanup。由此可得最小后台能力图：

```text
dispatch -> durable job record -> progress log -> status/result readback
         -> cancel -> liveness/stale reconciliation -> timeout/watchdog -> cleanup
```

只支持 `background=true` 不等于后台能力完整。

### 4.5 Stop gate 必须绑定当前精确切片

stop prompt 只审查“紧邻上一轮直接产生的代码编辑”，并从 repo state 验证是否真的有编辑；setup/status/report-only 直接 ALLOW。该模式可防止旧修改或聚合状态误阻塞当前关闭动作。

Hermes 的完成门禁应保持：当前 claim -> 精确 action slice -> 新鲜 repo/tool evidence -> allow/block。

### 4.6 共享 broker 必须做语义健康检查

共享 app-server 能降低启动成本，但 socket 存在不等于健康。可靠复用需要：

- runtime generation ID；
- connect/initialize deadline；
- 有界语义 round trip；
- fallback/restart；
- PID/liveness reconciliation；
- 单写者或原子状态更新；
- headless run 的 MCP/tool allowlist。

### 4.7 argv 与 shell 边界属于 Skill 安全合同

v1.0.6 的发布内容是移除 git 命令 shell expansion。当前 open issue 又提示 unknown flag 吞入任务、prompt re-tokenization、文字中的 `--model` 变成真实路由参数等风险。

Hermes 适配器应使用结构化 argv、严格 option allowlist、literal subprocess argument array、必要时 `--` 分隔，并测试引号、反斜杠、shell metacharacter 和“正文像参数”的情况。

### 4.8 Session transfer 是隐私与 provenance 边界

项目限制 transcript 来源必须在 `~/.claude/projects` 下，并使用 native importer 生成可 resume thread。任何类似能力都必须验证 source containment、来源身份、接收方、敏感信息边界和最终 thread/readback。

## 5. 风险与未闭环项

GitHub 当前 open issue 样本给出以下风险线索，尚未在本次本地环境逐项复现：

- write job 标记 completed，但 workspace write / rawOutput 证据不可信；
- background task 缺少完整 stall watchdog，宿主终止后可能永久 running；
- workspace-keyed registry 在 cwd/worktree 漂移后不可发现；
- broker race、无界 handshake、并发 state writer；
- Windows 的 Stop hook、transfer、env file、taskkill 等问题；
- 可预测临时目录与未验证 broker metadata 的本地多用户 IPC 风险；
- stop gate 在 Codex 不可用时 fail-open。

这些 issue 是风险线索，不是已经复现的定论。生产吸收前需要固定目标提交后逐项做负向测试。

## 6. Hermes 影响分类

### 已落地：docs / skills / governance

- 在 `agent-skill-design-patterns` 下新增参考：
  `references/openai-codex-plugin-cc-intake.md`
- 根 SKILL.md 已链接该参考。
- 吸收内容包括薄 Wrapper、确定性 runtime、route authority、review schema、精确切片 gate、后台生命周期、broker health、argv/shell 与 session-transfer 边界。

### 可继续评估：local scripts / runtime

- provider-neutral model bridge adapter；
- bounded broker/app-server health handshake；
- 后台任务 liveness/stale reconciliation/watchdog；
- structured review schema + exact-slice completion gate。

### 暂不实施：core loop / taskpool / gateway

本轮未修改 Hermes core agent loop、taskpool、gateway、cron、provider 配置，也未安装 Claude Code 插件。原因是这些属于更高影响的运行时变更，需要单独 spec、exact target、负向测试、回滚和 readback。

## 7. 最终判断

值得学习：架构分层、权限分离、确定性 runtime、结构化 reviewer、后台生命周期、精确切片门禁。

不应照搬：Claude/Codex 专用命令命名、提示词全文、全局插件安装、当前共享 broker 实现和 fail-open gate 默认值。

建议优先级：

1. P1：将“共享 runtime 语义健康 + handshake deadline + fallback”纳入 Hermes provider/model bridge 设计检查；
2. P1：所有后台 delegation 必须具备 liveness/stale reconciliation/watchdog；
3. P1：review 与 fix 必须分权，review 输出 schema 化；
4. P2：建立 provider-neutral session transfer/provenance contract；
5. P2：补 argv/prompt 边界的负向测试矩阵。
