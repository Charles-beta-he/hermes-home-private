---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: "P1: 十二项直接覆盖工具调用、提示词版本化、上下文窗口、执行状态、API 生命周期、人机审批、状态机、错误压缩、Agent 拆分与触发集成，是 Hermes 控制平面核心审计框架"
dependency_order: ["1) 建立 12 项清单到 Hermes 模块映射；2) 标注已满足/部分满足/缺失；3) 选 P1 缺口进入最小闭环补丁；4) 生成 regression/selfcheck 项避免退化"]
created: 2026-05-18T19:46:35+08:00
updated: 2026-05-18T21:08:00+08:00
expires_at: 2026-06-17T19:46:35+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 把 Agent 生产化原则转成 Hermes 可执行的架构审计矩阵和补丁顺序，提升稳定性、可控性、扩展性、协同性。
anti_drift_check: 不要只复述12Factor列表；必须逐项映射到 Hermes 现有模块/skill/hook/taskpool字段，区分已落地、待补齐、明确不做，并给出执行顺序。
acceptance_evidence: 提交 12Factor→Hermes 映射表、Top 3 缺口的证据、一个可执行补丁/任务拆分建议，以及自检或 proof gate 的验证方式。
workflow_contract: architecture_gap_audit; evidence-first; no broad survey without landing zone
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: "用户输入列出12项: NL→tool、prompt lifecycle、context window、tool calls as structured output、unified state、API lifecycle、HITL、state machine、自主流程、error compression、small focused agents、workflow triggers、stateless service。"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest triage: 用户给出完整12项机制与生产化背景；与 Hermes control-plane/taskpool 高重合，判定 P1 架构审计任务；执行涉及核心变更时应 evidence-first 并可触发真实多模型认证"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 审计可并行于 Dreaming/awesome-design-md；若改 task_router/token_compressor/hook 需串行并先跑 selfcheck。
evidence:
  - artifact:/Users/charles/.hermes/kanban/workspaces/t_04865df8/12factor-hermes-audit.md
  - classification:child_task=t_69cf5e57:todo
  - classification:child_task=t_cc6fa3c1:todo
  - classification:child_task=t_ef38d9ba:todo
concepts: ["12Factor Agents", "production agents", "state machine", "context management", "API lifecycle", "stateless service"]
---

# Task - 用 12Factor Agents 生产化范式审计 Hermes Agent 控制平面与任务池架构缺口

## Objective

将用户提供的 12Factor Agents 范式作为 Hermes 生产化审计框架，找出控制平面、任务池、上下文、提示词/工具/状态管理的可落地缺口与执行顺序。

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| 12Factor Agents README fetch | pass | `curl -L https://raw.githubusercontent.com/humanlayer/12-factor-agents/main/README.md` 抓取 12 项定义，确认审计基线。 |
| Hermes/runtime source audit | pass | 审计 `run_agent.py`、`agent/prompt_builder.py`、`agent/context_compressor.py`、`agent/token_compressor.py`、`agent/result_spiller.py`、`gateway/platforms/api_server.py`。 |
| taskpool/control-plane source audit | pass | 审计 `brain_task_orchestrator.py`、`brain_task_dispatch_tick.py`、`plugins/kanban/dashboard/plugin_api.py`，确认 lifecycle / dual-state / dispatch 证据。 |
| Workspace artifact written | pass | `/Users/charles/.hermes/kanban/workspaces/t_04865df8/12factor-hermes-audit.md` |
| Follow-up task split | pass | `t_69cf5e57`, `t_cc6fa3c1`, `t_ef38d9ba` |

## Proof Log

- 2026-05-18T19:46:35+08:00: Task created from local-brain control point.
- 2026-05-18T21:08:00+08:00: 完成 12Factor Agents → Hermes 控制平面/任务池映射审计，产出工作区报告 `/Users/charles/.hermes/kanban/workspaces/t_04865df8/12factor-hermes-audit.md`。结论：8 项已覆盖、2 项部分覆盖、2 项缺口明显；Top 3 缺口为统一运行状态/事件账本、提示词版本化、统一 launch-pause-resume 运行句柄。
- 2026-05-18T21:08:00+08:00: 依据审计结果拆分 3 个后续任务：`t_69cf5e57`（RunEnvelopeV1 / event ledger）、`t_cc6fa3c1`（PromptManifestV1）、`t_ef38d9ba`（RunController）。

## Blockers / Confusions

- None.

## Final Handoff

- Status: done
- Evidence: 审计报告 `/Users/charles/.hermes/kanban/workspaces/t_04865df8/12factor-hermes-audit.md`；源码证据覆盖 `run_agent.py`、`prompt_builder.py`、`context_compressor.py`、`token_compressor.py`、`result_spiller.py`、`api_server.py`、`brain_task_orchestrator.py`、`brain_task_dispatch_tick.py`、`plugins/kanban/dashboard/plugin_api.py`。
- Residual risk: 本次为 evidence-first 架构审计，不直接修改 Hermes 运行时代码；Top 3 缺口仍需后续工程任务落地并通过 selfcheck / proof gate 验证。
