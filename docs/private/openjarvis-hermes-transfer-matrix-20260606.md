# OpenJarvis → Hermes 可迁移模式矩阵（证据补充）

- 任务：`2026-06-05-评估-openjarvis-本地优先-agent-原语对-hermes-local-brain-taskpool-的可迁移治理模式`
- 证据时间：2026-06-06
- 源仓库：<https://github.com/open-jarvis/OpenJarvis>
- GitHub API 确认：`open-jarvis/OpenJarvis`，default branch `main`，license `Apache-2.0`，主要语言 `Python`
- 范围：只做 read-only source intake / gap analysis；不安装 OpenJarvis、不运行其 agent、不采集 secrets、不放宽 Hermes taskpool / mission-envelope / proof gates。

## 1. OpenJarvis 源侧事实

### 1.1 Repo identity

- `README.md` 自述为 “Personal AI, On Personal Devices”。
- 目标是 local-first personal AI：默认本地运行，必要时才调用云端。
- 框架关注三类约束：accuracy、energy/FLOPs/latency/dollar cost、local trace learning loop。
- 安装入口包含 `jarvis` CLI、uv、Ollama、starter model。
- `pyproject.toml` 项目名 `OpenJarvis`，Python `>=3.10,<3.14`，license `Apache-2.0`。

### 1.2 目录/包结构摘录

由 GitHub contents API 读到的顶层结构：

- `src/openjarvis/agents/`：agent implementations，如 `orchestrator.py`、`native_react.py`、`deep_research.py`、`proactive_agent.py`、`loop_guard.py`。
- `src/openjarvis/core/`：config / credentials / events / registry / typed core primitives。
- `src/openjarvis/engine/`：执行引擎与模型/运行时选择相关层。
- `src/openjarvis/intelligence/`：intelligence primitives。
- `src/openjarvis/learning/`：local trace learning / routing / optimization。
- `src/openjarvis/tools/`：tool adapters，如 file read/write、git、HTTP、browser、knowledge、memory manage、MCP adapter。
- `src/openjarvis/mcp/`：MCP integration surface。
- `src/openjarvis/security/`：安全/文件权限辅助。
- `src/openjarvis/server/`、`channels/`、`scheduler/`、`sessions/`：service/channel/session orchestration。
- `docs/architecture/`、`docs/learning/`、`docs/testing/`：体系结构、学习循环、测试文档。

## 2. 可迁移模式矩阵

### 模式 A：local-first capability router（本地优先能力路由）

- OpenJarvis 侧：README 明确把本地模型与本地设备作为默认执行面，云端作为必要 fallback；`core/config.py` 有硬件检测与 engine recommendation 基础。
- Hermes 现有路径/接口影响：
  - `~/.hermes/scripts/model-router.py`：可吸收“local-first + cloud fallback as exception”的路由维度，但不得绕过当前 provider allowlist / quota confidence gate。
  - `~/.hermes/scripts/p10-health.sh`：可增加本地模型健康、fallback 触发率、云端调用比例观测，不改变评分语义。
  - `~/.hermes/config/quorum.yaml` / provider routing 配置：可把 local-first 作为 policy input，而不是在任务执行器里硬编码。
- 推荐 Hermes slice：新增一个只读 routing report：统计最近 N 次模型调用中本地/云端比例、fallback 原因、quota/latency 失败分类；输出 JSON，不自动改路由。
- 验证命令：`python3 ~/.hermes/scripts/model-router.py --help` + 只读报告 schema 校验；不得需要真实 provider secret。

### 模式 B：tool/agent primitive registry（工具与 agent 原语注册表）

- OpenJarvis 侧：`core/registry.py`、`tools/*`、`agents/*` 暴露了 agent/tool/channel 的模块化注册思路。
- Hermes 现有路径/接口影响：
  - `~/.hermes/scripts/agent_protocol.py`：可补充 tool contract / result envelope 的静态检查。
  - Hermes MCP/native tool discovery：可把工具 capabilities 明确分为 read/write/external/network/secrets-sensitive。
  - `brain_task_orchestrator.py` handoff artifact：可追加 task-bound allowed tool class，避免 worker 只靠自然语言边界。
- 推荐 Hermes slice：为 worker handoff 生成 `capability_manifest`，列出允许 toolset、禁止 surface、required proof prefix；先 warn-only 输出到 handoff，不做 fail-closed。
- 验证命令：fixture task → handoff artifact 包含 `capability_manifest`；`proof-check` 仍 PASS。

### 模式 C：learning loop with local traces（本地轨迹学习闭环）

- OpenJarvis 侧：README 把 local trace data learning loop 作为核心目标；`learning/` 下含 routing / optimization / training 子目录。
- Hermes 现有路径/接口影响：
  - `~/.hermes/logs/`、`route_outcomes.db`：已有 routing/outcome traces，可结构化为可学习样本，但要脱敏并保留 source boundary。
  - `~/.hermes/scripts/self-improvement-pipeline.py`：可吸收“trace → hypothesis → bounded experiment → proof artifact”流程。
  - `~/.hermes/skills/software-development/experience-ratchet` / `hermes-experience-ratchet`：可承接跨任务经验沉淀，但不得把 WIP 状态写入 memory。
- 推荐 Hermes slice：生成“learning candidate”离线报告，只从匿名/本地 trace 聚合失败类型与潜在 routing 改进；不自动训练模型、不上传 trace。
- 验证命令：输入 fixture JSONL → 输出候选项 JSON；校验无 raw prompt、无 secret-like token、无 personal path 泄露（除允许的 Hermes 内部 path hash）。

### 模式 D：energy / latency / dollar as first-class eval constraints

- OpenJarvis 侧：README 把 energy、FLOPs、latency、dollar cost 与 accuracy 并列为评估约束。
- Hermes 现有路径/接口影响：
  - `v_state.py` / P10 health：可把 cost/latency/quota confidence 接为观测项。
  - `consult_models.py` / multimodel intervention：可记录每轮 token、provider、latency、失败原因，作为 expensive certification 的经济门证据。
  - `taskpool` priority / authority tier：可根据任务 P-level 与 expected value 调整是否触发多模型。
- 推荐 Hermes slice：为 multimodel tick 生成 `cost_observability` sidecar；只读，不影响当前 gate。
- 验证命令：对已有 `discussion_result.json` 样本生成 cost sidecar，缺字段时 fail-closed 为 `unknown` 而非伪造。

## 3. 不迁移 / 负例

### 负例 1：不直接移植 OpenJarvis agent runtime

- 原因：Hermes 的 canonical taskpool 是 `brain_task_orchestrator.py` + Kanban/brain notes + proof/evidence gates。直接引入 OpenJarvis agent runtime 会形成第二套执行控制面，违反 SSOT。
- 安全边界：OpenJarvis agent/channel/server 可以作为参考，但不能替代 Hermes task lifecycle、claim lease、review/done gate。

### 负例 2：不自动导入 OpenJarvis local trace learning

- 原因：local traces 可能包含 prompt、文件路径、用户偏好、secret-adjacent data。未经脱敏/权限声明就用于训练或上传，会违反 Hermes memory governance 与用户隐私边界。
- 安全边界：只允许离线、脱敏、fixture-first 的 learning-candidate report；不得把 trace 自动写入 durable memory 或外部服务。

### 负例 3：不把云 fallback 写成静默降级

- 原因：用户偏好“安全默认但避免过硬 UX”，危险/降级路径应显式确认或可审计。OpenJarvis 的 cloud-only-when-needed 思路可吸收，但 Hermes 不能静默把本地失败降级到更贵/更外部的 provider。
- 安全边界：fallback 必须记录 reason、provider、cost/latency、是否 user-visible；高风险任务应要求授权或保留审计。

## 4. 长期主线建议

1. **先观测，不改执行**：补 model/router/taskpool sidecar reports，证明本地/云端/多模型成本与失败原因可见。
2. **再声明能力，不授权越权**：在 handoff 中增加 capability manifest，让 worker 边界机器可读。
3. **最后才做策略闭环**：基于已脱敏 trace 的候选报告，进入 experience-ratchet / skill-ratchet，不直接训练或改路由。

## 5. 本地验证结论

本证据满足任务验收：

- 有 OpenJarvis 可迁移模式矩阵。
- 覆盖至少 3 个 Hermes 现有路径/接口：`model-router.py`、`p10-health.sh`、`agent_protocol.py`、MCP/native tool discovery、`brain_task_orchestrator.py` handoff、`route_outcomes.db`、`self-improvement-pipeline.py`、multimodel intervention。
- 含至少 2 个负例：不移植 runtime、不自动导入 trace learning、不静默 cloud fallback。
- 所有建议均为 fail-closed / read-only / fixture-first 方向，不弱化 taskpool proof、permission、mission-envelope gates。
