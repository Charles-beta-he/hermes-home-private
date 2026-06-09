---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-20T00:19:52+08:00
updated: 2026-05-20T00:26:26+08:00
expires_at: 2026-06-19T00:19:52+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 将 agent 专用代码片段搜索能力纳入 Hermes/Codex/Claude Code 代码定位策略，减少 grep+read 大文件 token 浪费。
anti_drift_check: 禁止只记录安装命令；必须验证 Semble 与现有 search_files/ripgrep/代码索引链路的差异、成本、准确率、MCP 安全边界。
acceptance_evidence: 核验 Semble 项目/安装方式/基准声称，完成与 Hermes 当前搜索工具对比，给出 opt-in MCP 接入方案、回退路径和 token 节流验证指标。
workflow_contract: "[08-模板/task-workflow-contract-template]"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-20T00:26:01+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-161958-832006-p20673-aa5f0cd7-69d93b17/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-20-p2-评估-semble-mcp-代码搜索对-hermes-token-节流与代码定位链路的可吸收增量-state.json
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
parallel_boundary: 先证据核验与对比，再决定是否接入 MCP；不得在未验证安全边界前默认启用全局代码索引服务。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-161958-832006-p20673-aa5f0cd7-69d93b17/discussion_result.json"
  - proof:sha256:f7821df9744a87ddfc27a100aa9b7b2b3fec7545dc0ef0cf2ebc5f16bb7aa88a
concepts: ["Semble", "MCP", "code-search", "token-saving", "repository-index"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["accuracy_keyword", "architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - P2 评估 Semble MCP 代码搜索对 Hermes token 节流与代码定位链路的可吸收增量

## Objective

把用户提供的 Semble agent 专用代码搜索信息转成 Hermes token 节流与代码定位工作流的受治理评估任务。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] Execute the smallest verifiable slice.
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-20T00:19:52+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-20T00:19:58+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-20T00:19:58+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-20T00:26:01+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-161958-832006-p20673-aa5f0cd7-69d93b17/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-20T00:26:01+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-161958-832006-p20673-aa5f0cd7-69d93b17/discussion_result.json

- 2026-05-20T00:26:26+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:f7821df9744a87ddfc27a100aa9b7b2b3fec7545dc0ef0cf2ebc5f16bb7aa88a, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-161958-832006-p20673-aa5f0cd7-69d93b17/discussion_result.json
