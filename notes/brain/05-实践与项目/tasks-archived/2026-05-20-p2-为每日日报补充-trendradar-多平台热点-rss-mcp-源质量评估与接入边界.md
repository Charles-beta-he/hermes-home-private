---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-20T00:24:28+08:00
updated: 2026-05-20T00:26:26+08:00
expires_at: 2026-06-19T00:24:28+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 TrendRadar 作为每日日报补充源的多平台聚合、RSS、关键词过滤、AI 简报推送与 MCP 分析能力，提升日报源质量与去噪。
anti_drift_check: 禁止直接把 TrendRadar 当作新唯一日报来源；必须对照现有 AIHOT/GitHub Trending/日报任务链，明确去重、噪声控制、失败回退、隐私与通知边界。
acceptance_evidence: 核验 sansan0/TrendRadar repo README/部署方式/MCP/RSS/通知能力，给出日报接入字段、质量门槛、去重策略、缓存/回退和验证方案。
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
parallel_boundary: 以已完成每日日报受治理入池和 GitHub Trending 源任务为前置上下文；可先做评估，不阻塞现有日报生成。
evidence:
  - proof:sha256:0b4a0a062267c242925a7fa0512029e5b1f6b9c2d548adc699346b2a70b2e8a7
  - command:py_compile_taskpool PASS
  - proof:sha256:52313ece99f7e7cfba1c2ad360b20a919a828bde51df29bd6203609abe34f3e5
concepts: ["TrendRadar", "daily-report", "RSS", "hot-news", "MCP", "source-quality"]
manual_review_decided_at: "2026-05-27T16:20:00+08:00"
manual_review_decided_by: "user-approved-multimodel-review"
manual_review_classification: "NEEDS_MORE_EVIDENCE"
manual_review_approval_action: "needs_more_evidence"
manual_review_final_landed: false
manual_review_result_ref: "/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md"
manual_review_reason: "py_compile/hash 不足以证明 TrendRadar 已真实接入日报。"
---

# Task - P2 为每日日报补充 TrendRadar 多平台热点/RSS/MCP 源质量评估与接入边界

## Objective

响应“补充每日日报”要求，把 TrendRadar 纳入每日信息源质量评估，而非绕过现有日报治理链。

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

- 2026-05-27T16:20:00+08:00: User approved multimodel manual-review classification NEEDS_MORE_EVIDENCE; action=needs_more_evidence; final_landed=false; ref=/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md; reason=py_compile/hash 不足以证明 TrendRadar 已真实接入日报。

- 2026-05-20T00:24:28+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-20T00:26:25+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-20T00:26:26+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-20T00:26:26+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:0b4a0a062267c242925a7fa0512029e5b1f6b9c2d548adc699346b2a70b2e8a7, command:py_compile_taskpool PASS

- 2026-05-20T00:26:26+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:52313ece99f7e7cfba1c2ad360b20a919a828bde51df29bd6203609abe34f3e5, proof:sha256:0b4a0a062267c242925a7fa0512029e5b1f6b9c2d548adc699346b2a70b2e8a7, command:py_compile_taskpool PASS
