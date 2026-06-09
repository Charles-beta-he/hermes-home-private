---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-18T11:35:26+08:00
updated: 2026-05-18T11:43:26+08:00
expires_at: 2026-06-12T21:36:05+08:00
project: hermes-agent-cache-optimization
architecture_target: provider-quota
capability_delta: fallback threshold narrowed brief
anti_drift_check: separate threshold policy from relay implementation so the parent scope does not drift
acceptance_evidence: proof log states threshold semantics and the evidence gate for noop-vs-change
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: not_certified
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-18T11:46:57+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260518-033703-108400-p60718-0ab7a5da-975cc426/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-fallbac-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - "proof: manual convergence closeout by hermes; narrowed brief written against the latest parent FAIL artifact, with dependency order frozen as quota_observability -> patch_normalization -> fallback_threshold"
  - command:py_compile_narrowed_briefs PASS
  - artifact:/Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
  - classification:legacy_autorun_proof_hash=sha256:4525674926458b56585948206f7f5852ed43bf69e6a7fccf34eb27e589cc664f
  - command:py_compile_narrowed_briefs_PASS
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Define fallback thresholds, downgrade policy, and the minimum evidence required to justify noop vs change on budget exhaustion behavior.

## Acceptance Criteria

- [x] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Narrowed Brief — Fallback Threshold

- Trigger threshold: when the parent FAIL round still shows quota confidence at 0.1-0.2, `patches=[]`, and the live disagreement is unresolved noop-vs-change rather than a certified semantic reject, fallback logic must stay downstream of observability and patch classification instead of mutating the parent cache architecture immediately.
- Allowed fallback actions: 1) freeze dependency order as `quota_observability -> patch_normalization -> fallback_threshold`; 2) preserve `run_agent.py` stable/context layering and avoid stuffing transport rescue logic into shared prompt prefixes; 3) allow one bounded retry only after quota visibility and patch-normalization evidence exist; 4) if a provider remains `failed_closed` or `unobservable`, record degraded transport evidence rather than treating it as semantic noop consensus.
- Noop vs change criteria: noop is only acceptable when 4/4 canonical participants either ratify no patch or justify no-op against the grounded evidence bundle. If concrete patches still exist in the planner minority set, `current_best.patches=[]` remains unresolved, and quota observability is still low-confidence, the correct outcome is staged change sequencing rather than parent-level noop.
- Evidence anchors: parent FAIL artifact `/Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json` shows `planner_patch_summary.certification_intent=unresolved_noop_vs_change`, `concrete_patch_count=5`, and unresolved I-003 sequencing the mainline as quota first, patch normalization second, fallback last. That makes fallback a valid narrowed brief now, but not the first implementation slice to land in code.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `python3 -m py_compile /Users/charles/.hermes/scripts/brain_task_orchestrator.py /Users/charles/.hermes/hermes-agent/run_agent.py` | PASS | deterministic syntax guard passed after writing narrowed brief |
| parent discussion artifact review | PASS | confirmed `planner_patch_summary.certification_intent=unresolved_noop_vs_change`, `concrete_patch_count=5`, unresolved I-003 orders quota -> patch -> fallback |

## Proof Log

- 2026-05-18T11:35:26+08:00: Task created from local-brain control point.
- 2026-05-18T11:41:20+08:00: Recorded fallback-threshold narrowed brief against the latest parent FAIL artifact; froze execution ordering as quota observability first, patch normalization second, fallback threshold third so transport rescue logic cannot mask the upstream noop-vs-change dispute.
- 2026-05-18T11:41:55+08:00: Deterministic syntax guard passed via `python3 -m py_compile /Users/charles/.hermes/scripts/brain_task_orchestrator.py /Users/charles/.hermes/hermes-agent/run_agent.py` after note writeback.

## Blockers / Confusions

- This slice is intentionally not the first implementation patch to land; the parent artifact still says quota observability and patch normalization must precede fallback-threshold code changes.

## Final Handoff

- Status: ready_for_review
- Evidence: classification:legacy_autorun_proof_hash=sha256:4525674926458b56585948206f7f5852ed43bf69e6a7fccf34eb27e589cc664f; command:py_compile_narrowed_briefs PASS; artifact:/Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
- Residual risk: parent remains blocked until quota_observability + framing/patch-normalization slices are also closed and a fresh ratification round converges.

- 2026-05-18T11:36:06+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: auto-claim-and-handoff

- 2026-05-18T11:37:02+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: manual_bounded_convergence_execution

- 2026-05-18T11:42:31+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-033607-347324-p60285-21ec0368-c3ff35c1/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T11:43:25+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed_brief_recorded Evidence: classification:legacy_autorun_proof_hash=sha256:4525674926458b56585948206f7f5852ed43bf69e6a7fccf34eb27e589cc664f, command:py_compile_narrowed_briefs_PASS, artifact:/Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json

- 2026-05-18T11:43:26+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed_brief_accepted_as_convergence_evidence Evidence: classification:legacy_autorun_proof_hash=sha256:4525674926458b56585948206f7f5852ed43bf69e6a7fccf34eb27e589cc664f, command:py_compile_narrowed_briefs_PASS, artifact:/Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
- proof:legacy autorun proof hashes preserved as classification because current autorun proof chain no longer validates historical hashes; no new verification fabricated
- classification:legacy_autorun_hash_migrated_due_to_current_chain_mismatch

- 2026-05-18T11:46:57+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-033703-108400-p60718-0ab7a5da-975cc426/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
