---
type: task
lane: work
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1"]
created: 2026-05-21T01:31:41+08:00
updated: 2026-05-21T01:38:53+08:00
expires_at: 2026-06-04T01:31:41+08:00
project: manufacturing
architecture_target: 
capability_delta: 
anti_drift_check: 
acceptance_evidence: 候选证据包 JSON schema + 至少一个 fixture 测试 + 无凭据/无物理动作
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: autonomous-execution
max_authority: yolo-execution
permission_tier: autonomous-execution
write_surfaces: ["taskpool", "codebase"]
completion_gate: project-evidence-review-done
lane_semantics: "work/product delivery: project evidence, tests/build, scoped commit, report/push policy as required"
multimodel_triage_result: P2
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: manufacturing-photo-to-print-model-search
evidence:
  - file:/Users/charles/.hermes/scripts/model_candidate_search.py
  - file:/Users/charles/.hermes/scripts/test_model_candidate_search.py
  - command:python3 ~/.hermes/scripts/test_model_candidate_search.py => OK 3 tests
  - command:python3 ~/.hermes/scripts/brainctl.py --json brains validate => passed true
  - command:python3 ~/.hermes/scripts/test_photo_to_print_job.py => OK 3 tests
  - command:python3 ~/.hermes/scripts/test_manufacturing_preflight.py => OK 2 tests
concepts: ["photo-to-print", "model-search", "stl", "3mf", "manufacturing-brain"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#119"
---

# Task - 制造脑 Photo-to-Print S1: 模型搜索连接器与候选证据包

## Objective

实现模型搜索/候选归档：输入对象标签/用途，输出候选 STL/3MF/CAD 来源、license、preview、尺寸假设、风险层级；不自动下载执行不可信模型。

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

- 2026-05-21T01:31:41+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T01:38:08+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-21T01:38:53+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Evidence: file:/Users/charles/.hermes/scripts/model_candidate_search.py

- 2026-05-21T01:38:53+08:00: Lifecycle transition `running` -> `review` by `hermes`. Evidence: file:/Users/charles/.hermes/scripts/model_candidate_search.py, file:/Users/charles/.hermes/scripts/test_model_candidate_search.py, command:python3 ~/.hermes/scripts/test_model_candidate_search.py => OK 3 tests, command:python3 ~/.hermes/scripts/brainctl.py --json brains validate => passed true

- 2026-05-21T01:38:53+08:00: Lifecycle transition `review` -> `done` by `hermes`. Evidence: file:/Users/charles/.hermes/scripts/model_candidate_search.py, file:/Users/charles/.hermes/scripts/test_model_candidate_search.py, command:python3 ~/.hermes/scripts/test_model_candidate_search.py => OK 3 tests, command:python3 ~/.hermes/scripts/test_photo_to_print_job.py => OK 3 tests, command:python3 ~/.hermes/scripts/test_manufacturing_preflight.py => OK 2 tests, command:python3 ~/.hermes/scripts/brainctl.py --json brains validate => passed true
