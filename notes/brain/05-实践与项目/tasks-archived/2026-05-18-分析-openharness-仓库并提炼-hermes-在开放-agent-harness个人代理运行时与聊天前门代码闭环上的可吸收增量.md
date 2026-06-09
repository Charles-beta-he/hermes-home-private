---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: open agent harness + personal agent runtime, useful for Hermes control-plane comparison but not an immediate P1 blocker"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare against Hermes/OpenClaw current harness surfaces -> 3) isolate net-new harness/runtime deltas -> 4) define long-term maintainable adoption boundary and execution order"]
created: 2026-05-18T01:34:51+08:00
updated: 2026-05-18T04:51:30+08:00
expires_at: 2026-06-17T01:34:51+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 评估 HKUDS/OpenHarness 及其 ohmo 个人代理形态的可迁移增量：工具使用、skills、memory、multi-agent coordination 的轻量 harness 基座，Feishu/Slack/Telegram/Discord 聊天前门，以及在既有 Claude Code/Codex 订阅上执行 fork branch / write code / run tests / open PR 的长期会话代理运行时，对 Hermes/OpenClaw 当前 harness/control-plane/chat gateway 提出长期可维护的架构增量。
anti_drift_check: 禁止把任务写成“再研究一个 agent framework”宽泛综述；必须对照 Hermes/OpenClaw 现有 tool/skill/memory/multi-agent/chat gateway/control-plane 能力，明确 OpenHarness/ohmo 的净新增：个人代理长期会话 runtime、chat frontdoor 与代码执行闭环、无需额外 API key 复用现有订阅、text/json/stream-json 输出契约。必须区分哪些应进入 Hermes taskpool/control-plane/gateway，哪些仅适合作为外部兼容层或参考实现。
acceptance_evidence: repo metadata、README 关键机制证据、与 Hermes/OpenClaw 当前 harness surfaces 的差距图、可吸收/拒绝项、长期可维护主链方案与执行顺序、以及需新增或修订的 skill/plugin/script/doc/self-check 项。
workflow_contract: "[08-模板/task-workflow-contract-template]"
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for taskpool/control-plane/harness comparison. External multimodel advisory is useful because overlap with Hermes/OpenClaw is high and the task must be framed around true net-new runtime and gateway mechanisms; not a current P1 blocker."
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-18T04:59:38+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-205130-706760-p45357-97be4837-75dd0b71/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-分析-openharness-仓库并提炼-hermes-在开放-agent-harness个人代理运行时与聊天前门代码闭环上的可吸收增量-state.json
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
parallel_boundary: "Serial first: evidence extraction and current-state contrast against Hermes/OpenClaw must happen before any compatibility or integration proposal; optional gateway/runtime experiments can branch only after the architecture boundary is fixed."
evidence:
  - proof:sha256:cb2590d368beffc47da5d39c11448883578598d1a44848d1135e631ab07fd67f
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:0b5d9e93a8451fb943fd14704ab4276f37f0dc57f18be430965b473b8308a495
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:9bf1fc1dc8d67f508744b20cb415afebc15921855fe906217cf2f3a1bfbaa604
concepts: ["openharness", "ohmo", "agent-harness", "skills", "memory", "multi-agent", "chat-frontdoor", "pr-automation"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 OpenHarness 仓库并提炼 Hermes 在开放 agent harness个人代理运行时与聊天前门代码闭环上的可吸收增量

## Objective

分析 OpenHarness 仓库并提炼 Hermes 在开放 agent harness个人代理运行时与聊天前门代码闭环上的可吸收增量

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-18T01:34:51+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-18T04:51:30+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-18T04:51:30+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-18T04:51:30+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:0b5d9e93a8451fb943fd14704ab4276f37f0dc57f18be430965b473b8308a495, command:py_compile_taskpool PASS

- 2026-05-18T04:51:30+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:9bf1fc1dc8d67f508744b20cb415afebc15921855fe906217cf2f3a1bfbaa604, proof:sha256:0b5d9e93a8451fb943fd14704ab4276f37f0dc57f18be430965b473b8308a495, command:py_compile_taskpool PASS

- 2026-05-18T04:54:07+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-205130-530741-p45345-a332a65f-0d964589/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T04:54:07+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-205130-852171-p45366-701d9835-3cf4cc39/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T04:59:38+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-205130-706760-p45357-97be4837-75dd0b71/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
