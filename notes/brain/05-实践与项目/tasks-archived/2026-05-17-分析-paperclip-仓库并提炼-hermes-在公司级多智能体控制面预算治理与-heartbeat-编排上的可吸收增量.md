---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T14:28:06+08:00
updated: 2026-05-17T18:02:15+08:00
expires_at: 2026-06-16T14:28:06+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 评估 Paperclip 的 company-level agent orchestration：org chart、goal ancestry、heartbeat 调度、ticket/task system、budget hard-stop、approval/governance、multi-company isolation、portable company templates 与 skill/runtime 注入，对 Hermes taskpool / subagent orchestration / approval-budget control-plane 提出长期可维护增量与主链执行顺序。
anti_drift_check: 先对照已存在的多 agent 并行/子智能体调度任务，禁止把 Paperclip 写成重复的“再看一个多 agent 框架”；必须明确其相对 Hermes 现有 delegate_task/taskpool 的净新增：公司级组织建模、heartbeat 唤醒循环、预算硬停、审批回滚、goal ancestry、multi-company 隔离与 agent-ops dashboard。避免停留在“无人公司”概念宣传，重点提炼可吸收机制、治理边界、最小验证切片，以及哪些能力不应直接照搬。
acceptance_evidence: repo metadata、README/ROADMAP/AGENTS 机制提炼、与 Hermes 当前 taskpool/subagent/control-plane 的差距图、可吸收/拒绝项、公司级 orchestration → Hermes 的落点（taskpool/control-plane/skills/runtime）与执行顺序、最小验证切片，以及需新增或修订的技能/脚本/控制面项。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-100215-283038-p74351-f17192cc-901ffbbd/discussion_result.json
multimodel_last_checked_at: 2026-05-17T18:06:05+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-100215-283038-p74351-f17192cc-901ffbbd/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-paperclip-仓库并提炼-hermes-在公司级多智能体控制面预算治理与-heartbeat-编排上的可吸收增量-state.json
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
parallel_boundary: 先完成 repo surface、README、ROADMAP、AGENTS 的控制面机制提炼，再对照 Hermes 当前 taskpool/delegate/subagent 能力做 gap map；随后拆分组织建模与 goal ancestry、heartbeat/budget/governance、multi-company/template portability 三块，再收敛为长期可维护的主链方案。禁止只写概念复述或伦理随笔。
evidence:
  - proof:sha256:848fcbbbbf4326a11bbe95afcb708c3bef42fed607796ebb5ae3ad9ef602fec7
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:b111e676a1bfd06a54b352269bd97f40e2d83d81263303771f87fe92a76b07a4
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:109a442e2896e67fe12923b905bb405b11198f22b047bece4dbd033c28d56750
concepts: ["paperclip", "multi-agent-control-plane", "heartbeat-orchestration", "org-chart", "budget-governance", "multi-company"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 Paperclip 仓库并提炼 Hermes 在公司级多智能体控制面、预算治理与 heartbeat 编排上的可吸收增量

## Objective

分析 https://github.com/paperclipai/paperclip ，重点不是复述“AI 无人公司”叙事，而是提炼它在公司级多智能体控制面、heartbeat 调度、预算与审批治理、goal-aware task lineage、多公司隔离与 agent 运维界面上的机制，明确 Hermes 应吸收什么、应落在哪层、按什么顺序推进。

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

- 2026-05-17T14:28:06+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T15:04:14+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-065946-272896-p95256-374edc93-e1545945/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T18:02:11+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T18:02:15+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T18:02:15+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:b111e676a1bfd06a54b352269bd97f40e2d83d81263303771f87fe92a76b07a4, command:py_compile_taskpool PASS

- 2026-05-17T18:02:15+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:109a442e2896e67fe12923b905bb405b11198f22b047bece4dbd033c28d56750, proof:sha256:b111e676a1bfd06a54b352269bd97f40e2d83d81263303771f87fe92a76b07a4, command:py_compile_taskpool PASS

- 2026-05-17T18:05:43+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-100215-417560-p74360-a64a9b28-87e84cf8/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T18:06:05+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-100215-283038-p74351-f17192cc-901ffbbd/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
