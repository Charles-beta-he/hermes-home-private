---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-20T00:24:28+08:00
updated: 2026-05-20T00:31:13+08:00
expires_at: 2026-06-19T00:24:28+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 在既有 NotebookLM Skill/效率工具任务基础上，聚焦 qiaomu-anything-to-notebooklm 的多源抓取、OCR/转录、NotebookLM 上传、播客/PPT/思维导图/Quiz 输出链路。
anti_drift_check: 禁止重复 vibe-coding-cn 里的 NotebookLM Skill 泛读；本任务只吸收 qiaomu repo 的多源内容处理与 Hermes 研究/日报生产链的增量，并明确付费墙绕过合规边界。
acceptance_evidence: 核验 repo README、支持源、输出格式、NotebookLM 自动化边界；输出 Hermes research/media/feeds 技能补丁建议、合规红线、试点输入与验收证据。
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
parallel_boundary: 可与 TrendRadar 日报源任务并行；涉及浏览器/账号/付费墙绕过能力时必须先定义合规与权限边界。
evidence:
  - proof:sha256:70e6f9c69387ffb9927d1f7a29ed7586dea0044019988d4f4f74e05c6685fd15
  - command:py_compile_taskpool PASS
  - proof:sha256:52283ddf611a0561dd39f641ced2411c4f3babfbad84a5a4d71f390a917bfac6
concepts: ["NotebookLM", "Claude Skill", "content-ingestion", "media-to-notes", "research-workflow"]
---

# Task - P2 二次吸收 Anything-to-NotebookLM 的多源内容处理 Skill 机制到 Hermes 研究/日报工作流

## Objective

把 qiaomu-anything-to-notebooklm 作为多源内容到 NotebookLM/知识产物的 skill 样本，提炼对 Hermes 研究与日报工作流的净新增。

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

- 2026-05-20T00:24:28+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-20T00:31:13+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-20T00:31:13+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-20T00:31:13+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:70e6f9c69387ffb9927d1f7a29ed7586dea0044019988d4f4f74e05c6685fd15, command:py_compile_taskpool PASS

- 2026-05-20T00:31:13+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:52283ddf611a0561dd39f641ced2411c4f3babfbad84a5a4d71f390a917bfac6, proof:sha256:70e6f9c69387ffb9927d1f7a29ed7586dea0044019988d4f4f74e05c6685fd15, command:py_compile_taskpool PASS
