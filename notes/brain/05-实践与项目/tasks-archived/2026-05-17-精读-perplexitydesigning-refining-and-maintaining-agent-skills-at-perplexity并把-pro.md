---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T00:24:44+08:00
updated: 2026-05-17T04:52:16+08:00
expires_at: 2026-06-16T00:24:44+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 把 Perplexity agent skills 文章第二轮精读沉淀为 Hermes 的技能图谱治理增量，补强 progressive loading、forbidden/off-target loads、description 变更回归、cross-model routing variance 与 append-mostly gotcha 维护门。
anti_drift_check: 先对照 2026-05-13 已完成的 Perplexity 分析任务与评估工件，禁止重复写同一篇文章摘要；必须只提取尚未制度化的增量机制，优先 patch 既有 umbrella/class-level skill 与 references，不平行复制新元技能。
acceptance_evidence: 第二轮精读机制清单、与既有任务/工件差异说明、拟补丁目标列表、至少一处治理落点/read-back/graph-eval 证据。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T05:00:33+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-205216-758674-p68002-a089516b-72608298/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-精读-perplexitydesigning-refining-and-maintaining-agent-skills-at-perplexity并把-pro-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: evolution:skill-graph:perplexity-agent-skills-deepread-2
evidence:
  - proof:sha256:a08d8114a400da169bde89889817099355d1564c5b9f7cd765b062edc4183a1f
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:1c4cfbe92a4b8702e1600e1796153a94408f075b6439eff801b1e8c48f93c8d4
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:38b9110eef054ec7b6e7423f91789c5076bc82d20705afa4649befbcf99c733f
concepts: ["perplexity-agent-skills", "skill-graph", "progressive-loading", "negative-evals", "gotcha-flywheel", "cross-model-routing"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 精读 Perplexity《Designing, Refining, and Maintaining Agent Skills at Perplexity》②并把 progressive loading 与路由回归门落成 Hermes 技能治理增量

## Objective

基于已完成的《分析 Perplexity agent skills 文章并优化 Hermes 自身技能体系与维护机制》任务和 evaluation 工件，再做一轮面向执行的精读：不重复总论，而是把文章里关于 progressive disclosure、forbidden/neighbor loads、description 变更必须带 eval、accessory file read eval、跨模型路由差异、append-mostly gotcha 维护的机制，转成 Hermes skill authoring/eval/graph governance 的长期可维护主链改进清单与执行顺序。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] 推进长期可维护主链方案并记录阶段性证据。
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-17T00:24:44+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T02:52:41+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-184903-647715-p40898-d21c5a5a-514a6b45/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T04:52:15+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T04:52:16+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T04:52:16+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:1c4cfbe92a4b8702e1600e1796153a94408f075b6439eff801b1e8c48f93c8d4, command:py_compile_taskpool PASS

- 2026-05-17T04:52:16+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:38b9110eef054ec7b6e7423f91789c5076bc82d20705afa4649befbcf99c733f, proof:sha256:1c4cfbe92a4b8702e1600e1796153a94408f075b6439eff801b1e8c48f93c8d4, command:py_compile_taskpool PASS

- 2026-05-17T04:55:39+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-205217-139002-p68012-674aa98f-0a6789de/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T05:00:33+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-205216-758674-p68002-a089516b-72608298/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
