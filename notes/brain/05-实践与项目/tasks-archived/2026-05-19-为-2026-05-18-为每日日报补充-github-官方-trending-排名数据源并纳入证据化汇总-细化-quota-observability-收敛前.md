---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: daily-report:p1:github-trending-source
dependency_order: ["['recommended-order: source-verification -> field-schema -> daily-report-integration -> validation-and-fallback']"]
created: 2026-05-19T14:12:28+08:00
updated: 2026-05-19T18:46:37+08:00
expires_at: 2026-06-17T01:34:34+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: quota observability narrowed brief
anti_drift_check: keep parent objective unchanged while proving quota_state semantics
acceptance_evidence: proof log cites source evidence for quota_state confidence and unknown handling
workflow_contract: "[08-模板/task-workflow-contract-template]"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest triage: P1 evolution candidate; strengthens daily-report evidence quality and upstream signal quality for downstream task creation"
auto_subtask_parent: 2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-045114-221956-p46067-c446de14-117e7db1/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先确认官方 Trending 数据源与字段，再实现日报补充逻辑，最后验证与“日报生成任务”链路衔接。
evidence:
  - "proof: quota_observability narrowed brief completed; parent remains blocked until sibling axes and ratification refresh"
  - classification:axis=quota_observability_complete_parent_still_blocked
  - artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总-细化-quota-observability-收敛前.md
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
  - command:proof-check PASS
  - command:selfcheck PASS
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
---

# Task - 为 2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总`. Do not change the parent objective. Define quota_state source, confidence, staleness, and fail-closed semantics so future ratification can decide whether quota-aware change is required.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总
- Discussion artifact: /Users/charles/.hermes/tick-20260519-045114-221956-p46067-c446de14-117e7db1/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

将 GitHub 官方 Trending 数据源排名补充到每日日报，形成证据化趋势来源，并服务后续日报→任务入池机制。

## Narrowed Scope

- Only resolve quota observability and evidence gaps.
- Do not decide relay ordering or broader fallback policy here.

## Narrowed Brief

### Quota observability contract

- Source of truth: quota/provider state must be recorded as file-backed evidence, not inferred from model tone or partial discussion success. Acceptable evidence locations are the parent task note, the referenced discussion artifact, and any state file emitted under `/Users/charles/.hermes/state/taskpool-multimodel/`.
- Minimum `quota_state` shape for future ratification: `expected_canonical_participants`, `seen_canonical_participants`, `missing_canonical_participants`, `noncanonical_participants`, `provider_parse_errors`, `unavailable_participants`, `confidence`, `staleness`, and `evidence_paths`.
- Confidence levels: `high` only when all expected canonical participants are observed with parseable votes; `medium` when quorum exists but optional/noncanonical drift is present; `low` when a required participant is missing or parse errors affect decision fields; `unknown` when evidence is absent or stale.
- Unknown/unobservable handling: unknown quota/provider state is diagnostic evidence only. It may justify splitting or retry scheduling, but it must not lower the truth gate, convert advisory output into certification, or mark parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` done.
- Parent boundary: this child only defines observability semantics. It does not decide implementation order, fallback threshold, or parent unblocking.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| canonical child-axis note review | done | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总-细化-quota-observability-收敛前.md` |
| parent boundary preserved | done | parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` remains blocked until sibling axes and ratification refresh |

## Proof Log

- 2026-05-19T14:12:28+08:00: Task created from local-brain control point.

- 2026-05-19T18:46:31+08:00: manual bounded child-axis tranche completed for `quota_observability`; this is child-axis evidence only and does not unblock parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` by itself.

## Blockers / Confusions

- None.

## Final Handoff

- Status: review-ready / done-ready for child axis `quota_observability`.
- Evidence: narrowed brief, checked acceptance/workpad boxes, structured frontmatter evidence, and deterministic gates run after batch update.
- Residual risk: parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` remains blocked until every sibling axis is closed and parent-level ratification is refreshed.
- 2026-05-19T18:46:33+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_claim

- 2026-05-19T18:46:33+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_running

- 2026-05-19T18:46:37+08:00: Lifecycle transition `running` -> `review` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_review Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=quota_observability_complete_parent_still_blocked

- 2026-05-19T18:46:37+08:00: Lifecycle transition `review` -> `done` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_done Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=quota_observability_complete_parent_still_blocked
