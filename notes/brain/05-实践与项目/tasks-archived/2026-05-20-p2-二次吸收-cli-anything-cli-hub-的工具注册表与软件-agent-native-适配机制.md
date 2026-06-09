---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-20T00:24:28+08:00
updated: 2026-05-20T00:47:57+08:00
expires_at: 2026-06-19T00:24:28+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 在已完成安全 repo-to-tool adapter scaffold 基础上，增量评估 CLI-Hub 注册表、社区 CLI 安装/管理、preview/trajectory loop 对 Hermes 工具生态的新增机制。
anti_drift_check: 禁止重复已完成的 CLI Anything 安全 adapter scaffold；本任务只做 second-pass registry/hub/agent-native 软件适配增量，不重写旧任务结论。
acceptance_evidence: 核验 HKUDS/CLI-Anything 与 clianything.cc/CLI-Hub，明确相对现有 scaffold 的净新增、权限模型、安装审查、工具注册/撤销流程与可验证试点。
workflow_contract: "[08-模板/task-workflow-contract-template]"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 必须以已完成 repo-to-tool adapter scaffold 为前置上下文；可与外部工具评估并行，但注册任何可执行 wrapper 前需 review gate。
evidence:
  - proof:sha256:12292fa6161b49c7d9fb7849008065d8aec3264374d1ade2586b09694edf3fcd
  - command:py_compile_taskpool PASS
  - proof:sha256:d9c30ef8ba28101df1e22b5e3f3ca1a86e26a1ff66b335a45beda1e63611f42c
concepts: ["CLI-Anything", "CLI-Hub", "agent-native-software", "tool-registry", "repo-to-tool-adapter"]
manual_review_decided_at: "2026-05-27T16:20:00+08:00"
manual_review_decided_by: "user-approved-multimodel-review"
manual_review_classification: "NEEDS_MORE_EVIDENCE"
manual_review_approval_action: "needs_more_evidence"
manual_review_final_landed: false
manual_review_result_ref: "/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md"
manual_review_reason: "需补工具注册表/权限模型/script/config 的真实落地证据。"
---

# Task - P2 二次吸收 CLI-Anything/CLI-Hub 的工具注册表与软件 agent-native 适配机制

## Objective

基于用户补充的 CLI-Anything 官方 repo 与 CLI-Hub，创建窄范围 second-pass 任务，避免与既有 done 任务重复。

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

- 2026-05-27T16:20:00+08:00: User approved multimodel manual-review classification NEEDS_MORE_EVIDENCE; action=needs_more_evidence; final_landed=false; ref=/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md; reason=需补工具注册表/权限模型/script/config 的真实落地证据。

- 2026-05-20T00:24:28+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-20T00:47:56+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-20T00:47:56+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-20T00:47:57+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:12292fa6161b49c7d9fb7849008065d8aec3264374d1ade2586b09694edf3fcd, command:py_compile_taskpool PASS

- 2026-05-20T00:47:57+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:d9c30ef8ba28101df1e22b5e3f3ca1a86e26a1ff66b335a45beda1e63611f42c, proof:sha256:12292fa6161b49c7d9fb7849008065d8aec3264374d1ade2586b09694edf3fcd, command:py_compile_taskpool PASS
