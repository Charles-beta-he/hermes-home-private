---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1 prepare isolated profile/data dir -> 2 start AgentMemory localhost only -> 3 verify health/tools -> 4 minimal memory roundtrip -> 5 cleanup and document compatibility matrix"]
created: 2026-05-21T20:29:35+08:00
updated: 2026-05-21T20:45:12+08:00
expires_at: 2026-06-20T20:29:35+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 在不修改默认 Hermes 配置的前提下，用临时 profile/隔离数据目录验证 AgentMemory MCP/server 可达性、工具枚举、health、只读 recall 与受控写入回滚，为后续共享记忆服务接入提供证据。
anti_drift_check: 禁止直接启用 upstream Hermes plugin 或替换 MEMORY.md/USER.md；禁止污染默认 ~/.hermes/config.yaml；必须使用 isolated data dir 和临时配置，完成后清理或记录残留。
acceptance_evidence: 临时 profile 配置片段、AgentMemory health 输出、MCP tools/list 证据、最小 remember/recall 或 read-only 查询证据、清理记录、失败/降级原因。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2: AgentMemory source-backed Hermes memory evolution task; high leverage but must remain default-off and evidence-gated before runtime adoption"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-21T20:32:52+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-122943-000072-p19413-923f7ab8-ccc58a81/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-implement-agentmemory-isolated-mcp-compatibility-spike-for-hermes-temporary-prof-state.json
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
parallel_boundary: 按依赖顺序推进：compatibility spike -> policy wrapper -> retrieval bridge/consolidation -> governance selfcheck；禁止未验证前改默认配置或启用外部 shared memory。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122943-000072-p19413-923f7ab8-ccc58a81/discussion_result.json"
  - proof:sha256:2f74ef7f880d9016d3c067dcde55cc94a977b294ef04762bcff9393880876839
  - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - proof:sha256:6985399b5312eac6177be1b85c005cd28d8223a66a6cded0b162854d32e94116
  - command:py_compile_taskpool PASS
  - proof:sha256:d76151d388ecb290acbb74ddfe6a342964e596e82b4e69937b8692447d954353
concepts: ["agentmemory", "mcp", "temporary-profile", "compatibility-spike", "memory-provider"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#246"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
manual_review_decided_at: "2026-05-27T16:20:00+08:00"
manual_review_decided_by: "user-approved-multimodel-review"
manual_review_classification: "PARTIAL_STAGE"
manual_review_approval_action: "needs_more_evidence"
manual_review_final_landed: false
manual_review_result_ref: "/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md"
manual_review_reason: "spike 可作为阶段性成果；需补 health/tools/list/remember-recall/cleanup 证据。"
---

# Task - Implement AgentMemory isolated MCP compatibility spike for Hermes temporary profile

## Objective

把 AgentMemory 源码分析中的可吸收能力转成 Hermes 可执行进化任务，保持默认关闭、安全优先、证据驱动。

## Acceptance Criteria

- [ ] 临时 profile 配置片段、AgentMemory health 输出、MCP tools/list 证据、最小 remember/recall 或 read-only 查询证据、清理记录、失败/降级原因。

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-27T16:20:00+08:00: User approved multimodel manual-review classification PARTIAL_STAGE; action=needs_more_evidence; final_landed=false; ref=/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md; reason=spike 可作为阶段性成果；需补 health/tools/list/remember-recall/cleanup 证据。

- 2026-05-21T20:29:35+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T20:29:42+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T20:29:42+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T20:32:52+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-122943-000072-p19413-923f7ab8-ccc58a81/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:32:52+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122943-000072-p19413-923f7ab8-ccc58a81/discussion_result.json

- 2026-05-21T20:42:08+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:2f74ef7f880d9016d3c067dcde55cc94a977b294ef04762bcff9393880876839, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122943-000072-p19413-923f7ab8-ccc58a81/discussion_result.json

- 2026-05-21T20:44:06+08:00: Lifecycle transition `done` -> `pending` by `hermes-agent`. Force: true. Reason: User asked to add AgentMemory evolution improvements to taskpool; queued work items are not completed implementation. Evidence: command: brain_task_orchestrator transition --to pending after add-time advisory auto-close

- 2026-05-21T20:45:11+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T20:45:12+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T20:45:12+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:6985399b5312eac6177be1b85c005cd28d8223a66a6cded0b162854d32e94116, command:py_compile_taskpool PASS

- 2026-05-21T20:45:12+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:d76151d388ecb290acbb74ddfe6a342964e596e82b4e69937b8692447d954353, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122943-000072-p19413-923f7ab8-ccc58a81/discussion_result.json, proof:sha256:2f74ef7f880d9016d3c067dcde55cc94a977b294ef04762bcff9393880876839, command: brain_task_orchestrator transition --to pending after add-time advisory auto-close, proof:sha256:6985399b5312eac6177be1b85c005cd28d8223a66a6cded0b162854d32e94116, command:py_compile_taskpool PASS
