---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: multi-agent-orchestration
dependency_order: ["1) 核验 ruvnet/ruflo GitHub 与 npm/package 元信息，澄清 Ruflo/claude-flow 命名与安装入口 -> 2) 阅读 README/docs/.claude-plugin/.claude/AGENTS/SECURITY/package scripts，列出 init/install 写入面 -> 3) 提取 swarm/agent matching/AgentDB/RAG/MCP/hooks/daemon/Claude Code/Codex/Rust-WASM 机制证据 -> 4) 对比 Hermes 多脑/taskpool/多模型治理/长任务可恢复/外部 agent 编排需求 -> 5) 做安全与供应链评估：npm alpha、hooks/daemon、MCP 权限、workspace 写入、agent 指令注入、向量记忆泄露 -> 6) 只在隔离目录设计 dry-run/不执行生产安装，输出 adopt/defer/reject 与集成路径。"]
created: 2026-05-22T13:44:27+08:00
updated: 2026-05-22T13:54:03+08:00
expires_at: 2026-06-12T13:44:27+08:00
project: hermes-agent
architecture_target: LX
capability_delta: 可能为 Hermes 多脑/taskpool 提供百级 agent 编排、AgentDB/向量能力匹配、Claude Code/Codex 插件化、MCP server、hooks/daemon、故障容错与全流程编码/测试/安全/架构协同的参考；长期可吸收为多脑调度、能力画像匹配、并行验证与自学习任务路由机制。
anti_drift_check: 不得直接在现有 Claude Code/Hermes 生产环境安装 Ruflo 插件或运行 npx ruflo init；不得改写 ~/.claude、项目 .claude、MCP 配置、hooks、daemon 或 agentdb；不得把 README 营销指标当作事实，必须用仓库/包/文档/代码证据核验；体验只能在隔离临时目录或容器内 dry-run，且先审查 install/init 会写入的文件。
acceptance_evidence: 产出 evidence-first 评估文档，包含 GitHub repo 元信息、package 名称与 repo/README 命名关系、Stars/Forks/Issues/Tags/Commit/License/Security、安装入口与写入面、Claude Code/Codex/MCP/hooks/daemon/AgentDB/RAG/Rust/WASM 机制证据、与 Hermes 多脑/taskpool 的可吸收点、明确拒绝/需门禁能力、最小无害 PoC 步骤、验证命令和回滚条件。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: 百级多智能体/Claude Code 插件/MCP/hooks/daemon 会影响 Hermes 多脑架构、开发环境安全与任务池调度，需要架构、安全、agent workflow 多视角审查，避免直接安装造成配置污染。
expected_participants: ["multi-agent-architect", "dev-environment-security-reviewer", "taskpool-orchestrator-reviewer"]
truth_gate: repo-evidence-install-surface-and-safety-boundary-present
evidence_bundle: "User request 2026-05-22: Ruflo may help multi-brain; source text claims 100+ AI agents, self-learning + AgentDB vector retrieval, Rust/WASM, enterprise security, coding/testing/security/architecture flow. Browser verification 2026-05-22: https://github.com/ruvnet/ruflo public repo; title says leading agent orchestration platform for Claude, multi-agent swarms, RAG, Claude Code/Codex integration; About topics include multi-agent, swarm, codex, MCP, claude-code; observed Stars 54k, Forks 6.1k, Issues 409, PRs 150, main branch, 269 branches, 1482 tags, latest commit 8e97433 about 2 hours ago, 6,582 commits, MIT license, SECURITY.md present. package.json raw check: package name claude-flow, version 3.7.0-alpha.78, description says Ruflo enterprise AI agent orchestration for Claude Code with 60+ specialized agents, MCP integration; scripts include build/test/security/audit; dependencies include @claude-flow/* and @ruvector/*."
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "Pre-add triage: P2 evolution. 与 Hermes 多脑、taskpool、Claude/Codex 外部 agent 编排高度相关，但安装插件/MCP/hooks/daemon 会改写开发环境且包处于 alpha 命名链路复杂，先做安全架构与写入面评估，不进入直接安装。"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260522-054740-755453-p811-012ef46d-dad5de9a/discussion_result.json
multimodel_last_checked_at: 2026-05-22T13:54:03+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260522-054740-755453-p811-012ef46d-dad5de9a/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-22-评估-ruvnet-ruflo-对-hermes-多脑taskpool-与百级-ai-agent-协同编排的可吸收增量-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 可与资讯/文档/源码阅读并行；不得与 Hermes/Claude Code 生产配置修改、MCP server 注册、hooks/daemon 启动、全局 npm install、真实项目 init 并行；任何安装体验必须另建隔离 PoC 并人工确认写入面。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-054435-080628-p98968-9399906a-d2382b38/discussion_result.json"
  - proof:sha256:7c0021ddc7195fb25763d028f8b312b53c99e0ed233f89def8f930b48131362d
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-054740-755453-p811-012ef46d-dad5de9a/discussion_result.json
concepts: ["ruflo", "ruvnet", "claude-flow", "multi-agent", "swarm", "Claude Code", "Codex", "MCP", "AgentDB", "RAG", "WASM", "Rust", "taskpool", "multi-brain"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#343"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 评估 ruvnet/ruflo 对 Hermes 多脑、taskpool 与百级 AI agent 协同编排的可吸收增量

## Objective

判断 ruvnet/ruflo 是否值得进入 Hermes 多脑/taskpool/多智能体编排技术雷达，重点评估其百级 agent swarm、AgentDB/RAG 能力匹配、Claude Code/Codex 插件、MCP server、hooks/daemon、Rust/WASM/高性能组件与企业级容错对 Hermes 长任务、多模型治理和多脑协同的可吸收增量。

## Acceptance Criteria

- [ ] Task note exists with capability_delta/anti_drift_check/acceptance_evidence; first execution is safety-first repo/install-surface evaluation only, with no production Claude/Hermes config mutation.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-22T13:44:27+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-22T13:44:34+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-22T13:44:34+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-22T13:50:37+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-054435-080628-p98968-9399906a-d2382b38/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T13:50:37+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-054435-080628-p98968-9399906a-d2382b38/discussion_result.json

- 2026-05-22T13:54:03+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-054740-755453-p811-012ef46d-dad5de9a/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T13:54:03+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:7c0021ddc7195fb25763d028f8b312b53c99e0ed233f89def8f930b48131362d, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-054435-080628-p98968-9399906a-d2382b38/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-054740-755453-p811-012ef46d-dad5de9a/discussion_result.json
