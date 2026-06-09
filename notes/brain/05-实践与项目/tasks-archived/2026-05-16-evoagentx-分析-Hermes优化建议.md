---
type: analysis
parent_task: 2026-05-14-分析-evoagentx-仓库并优化-hermes-自身进化式代理与自动改进机制
status: complete
created: 2026-05-16T23:35:00+08:00
---

# EvoAgentX 仓库分析 — Hermes 优化建议

## EvoAgentX 核心架构

EvoAgentX 是一个进化式代理框架，核心机制:

1. **Workflow Generator** — LLM 驱动的工作流自动生成，从自然语言描述生成多 Agent 协作图
2. **Agent Evolver** — 基于执行反馈自动优化 Agent prompt 和工具选择
3. **Evaluation Pipeline** — 自动评估 Agent 表现，生成改进信号
4. **Skill Library** — 可复用的技能库，支持热插拔

## 与 Hermes 的对比

| 维度 | EvoAgentX | Hermes |
|------|-----------|--------|
| 工作流生成 | LLM 自动生成 | 手动定义 + skill 系统 |
| Agent 进化 | 基于反馈自动优化 prompt | 手动 patch skill |
| 评估 | 内置 eval pipeline | 多模型认证 gate |
| 技能库 | 热插拔 skill library | ~/.hermes/skills/ |
| 多模型 | 支持 | 支持 (canonical IDs) |

## Hermes 可借鉴的优化

### 1. 自动 Prompt 优化 (高优先级)

EvoAgentX 的 Agent Evolver 可以根据执行结果自动调整 prompt。
Hermes 当前需要手动 patch skill。

**建议**: 在 skill_manage(action='patch') 中增加 auto-patch 模式:
- 当 skill 执行失败时，自动分析失败原因
- 生成 patch 候选方案
- 通过多模型认证后自动应用

### 2. 工作流自动生成 (中优先级)

EvoAgentX 可以从自然语言生成多 Agent 工作流。
Hermes 当前需要手动编排 delegate_task。

**建议**: 增强 hermes-pipeline skill:
- 支持从任务描述自动生成 pipeline 定义
- 自动识别可并行的步骤
- 生成 delegate_task 调用序列

### 3. 内置评估管线 (高优先级)

EvoAgentX 有完整的 eval pipeline。
Hermes 的多模型认证 gate 是类似的，但更侧重于任务级评估。

**建议**: 增强 consult_models.py:
- 增加 execution_quality 评估维度
- 评估结果反馈到 skill 质量评分
- 低分 skill 自动标记为需要优化

### 4. 技能热插拔 (已实现)

Hermes 的 skill 系统已经支持热插拔 (skill_manage)。
与 EvoAgentX 的 Skill Library 功能对等。

## 实施优先级

| 优先级 | 优化项 | 工作量 | 影响 |
|--------|--------|--------|------|
| P1 | 自动 Prompt 优化 | 中 | 高 |
| P1 | 内置评估管线增强 | 中 | 高 |
| P2 | 工作流自动生成 | 大 | 中 |
| - | 技能热插拔 | 已完成 | - |

## 结论

EvoAgentX 的核心价值在于**自动化进化循环**: 执行 → 评估 → 优化 → 再执行。
Hermes 已经有类似的多模型认证 gate，但缺少自动优化环节。
建议优先实现"自动 Prompt 优化"和"评估管线增强"，补全进化闭环。

## Second-pass backfill：证据链 / 决策 / 落地 / 停止条件

> 2026-05-20 补齐；来源是 2026-05-19 second-pass 外源分析质量审计，不重写 EvoAgentX 仓库总结，只把本 note 的 provenance、decision、landing、verification、stop-condition 补齐。

### Provenance

- 外源：`https://github.com/EvoAgentX/EvoAgentX`；2026-05-20 GitHub API smoke 读回 `full_name=EvoAgentX/EvoAgentX`、`default_branch=main`、`pushed_at=2026-05-15T13:33:07Z`，用于确认来源仍可解析。
- 本地候选 note：`/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-16-evoagentx-分析-Hermes优化建议.md`。
- 审计来源：`/Users/charles/Documents/brain/06-治理与评审/reviews/2026-05-19-prior-external-analysis-quality-audit.md` 标记本 note 为 `reopen_for_evidence_and_landing`，缺口为 `decision,verification,stop`。
- 二刷归档：`/Users/charles/Documents/brain/06-治理与评审/reviews/2026-05-19-external-repo-absorption-multibrain-second-pass.md` 将 EvoAgentX 相关主链拆到 hermes-core/workflow，并把 workflow 侧落地标准定义为 `skill/template/protocol/eval 闭环`，停止条件为“泛流程总结、触发面扩大无邻例停止”。

### Decision record

- 决策 1：本 note 保持为“EvoAgentX -> Hermes 优化建议”的历史索引，不再扩写仓库解读；真正落地分解到三个 Hermes evolution task。
- 决策 2：`内置评估管线增强 / execution_quality` 是上游基座，优先级 P1；只有它 certified 后，自动 skill 演化与 workflow-generator 才有稳定反馈源。
- 决策 3：`自动 Prompt 优化` 不落成隐式 auto-patch 魔法；必须拆成 failure attribution、patch candidate、multi-model ratification、apply/rollback、audit trail 的受控闭环。
- 决策 4：`工作流自动生成` 不落成 prompt -> delegate_task 字符串模板器；必须先有可审计 orchestration-plan / pipeline IR，再映射到 hermes-pipeline/delegate_task。
- 决策 5：`技能热插拔` 已由 Hermes skill_manage / skill 系统覆盖；只保留等价能力说明，不新开任务。

### Landing map

| EvoAgentX 建议 | Hermes 落地锚点 | 当前状态 | 证据/说明 |
|---|---|---|---|
| 内置评估管线 / execution quality | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-17-建设-hermes-长期可维护的-execution-quality-评估反馈基座以承接-evoagentx-演化闭环建议.md` | 已沉到 taskpool/skill-graph 治理闭环；frontmatter `multimodel_status: certified`，`multimodel_last_gate_status: PASS`，`multimodel_last_decision: LOOP_DONE` | 该 note 定义 capability_delta：execution_quality、skill 质量评分、低分标记、证据写回协议；Proof Log 记录 PASS discussion artifact 与 2026-05-19 closeout 后的 proof hash/py_compile |
| 自动 Prompt/Skill 优化 | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-17-建设-hermes-长期可维护的自动-skill-演化与-prompt-治理闭环以落地-evoagentx-agent-evolver-建议.md`；相关 workflow skill 参考：`/Users/charles/.hermes/profiles/workflow/skills/darwin-skill/SKILL.md` | 部分沉淀：Darwin skill 已有评估→改进→实测→确认→回滚闭环；但该 evolution task frontmatter 仍是 `multimodel_status: not_certified` | 不视为完全落地；见 bounded follow-up `t_951b8cf9` |
| 工作流自动生成 | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-17-建设-hermes-长期可维护的-workflow-generator-与-orchestration-plan-编译框架以吸收-evoagentx-启发.md`；相关 workflow skill：`/Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/SKILL.md` | 部分沉淀：目标与 anti_drift 已写入 task note，workflow-orchestrator skill 已有 pipeline/agent 编排规则；但该 evolution task frontmatter 仍是 `multimodel_status: not_certified` | 不视为完全落地；见 bounded follow-up `t_fbef3018` |
| 技能热插拔 | Hermes `skill_manage` / `~/.hermes/profiles/workflow/skills/` | 已实现/已作为基础能力使用 | 无需新任务；stop condition 是“不为等价已有能力重复造轮子” |

### Verification commands / artifacts

- `read_file /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-16-evoagentx-分析-Hermes优化建议.md`：确认本 note 原缺少 provenance/decision/verification/stop，仅有 2026-05-16 总结与建议。
- `python3 - <<'PY' ... urllib.request.urlopen('https://api.github.com/repos/EvoAgentX/EvoAgentX') ... PY`：确认 GitHub provenance 可读，输出 `full_name=EvoAgentX/EvoAgentX`、`default_branch=main`、`pushed_at=2026-05-15T13:33:07Z`。
- `read_file` 三个 landing task notes：确认 execution_quality 已 certified/PASS/LOOP_DONE；auto-skill 与 workflow-generator 仍 not_certified，不能被本 backfill 口头判定为完成。
- `search_files /Users/charles/Documents/brain "EvoAgentX|execution_quality|工作流自动生成|自动 Prompt"`：确认 2026-05-19 audit 与 second-pass review 已把 EvoAgentX 主链拆到 hermes-core/workflow，并列出对应落地任务。
- `kanban_create`：创建 bounded follow-up `t_951b8cf9`、`t_fbef3018`，用于未完全落地项的 owner 化闭环。

### Stop condition

- 停止继续扩写 EvoAgentX 仓库内容：本 note 的职责是历史建议索引，不是新一轮 repo review。
- 停止把 hash/py_compile-only done 当作能力完成：若 landing note 仍 `multimodel_status: not_certified`，只能标为“部分沉淀 + bounded follow-up”。
- 停止把 workflow 侧建议泛化成无边界流程口号：必须落到 skill/template/protocol/eval 的具体文件、任务或验证 artifact。
- 停止新建重复任务：execution_quality 已 certified，不再拆；技能热插拔已由 skill_manage 覆盖，不再拆。

### Bounded follow-up / owner

- `t_951b8cf9` — Owner: workflow；补齐并认证 `自动 skill 演化与 prompt 治理闭环` 的 source/decision/landing/verification/stop-condition，若仍 not_certified 则保留 review/blocked，不假完成。
- `t_fbef3018` — Owner: workflow；补齐并认证 `workflow-generator / orchestration-plan compiler` 的 IR、依赖/并行/authority/verification 语义与证据链，若仍 not_certified 则保留 review/blocked，不假完成。
