---
type: task
lane: advisory
layer: L2
status: done
priority: P3
created: 2026-05-20T00:24:28+08:00
updated: 2026-05-20T01:16:32+08:00
expires_at: 2026-06-19T00:24:28+08:00
project: frontend-workflow
architecture_target: skill-graph
capability_delta: 为 Hermes 前端/UI 工作流补充轻量动效库选型边界，明确 Anime.js 适合 CSS/SVG/DOM/Object 动效的场景与性能红线。
anti_drift_check: 禁止把任务变成“引入 Anime.js 到所有项目”；必须先与现有 CSS/Framer Motion/原生动画方案比较，并保留不降性能/不破坏 H5 的红线。
acceptance_evidence: 核验 Anime.js 官方 repo/官网/API 定位，输出适用场景、禁用场景、性能/无障碍检查清单，以及是否需要补丁到 UI skill。
workflow_contract: "[08-模板/task-workflow-contract-template]"
required_authority: dispatch-hint
max_authority: budget-handoff
permission_tier: dispatch-hint
write_surfaces: ["taskpool", "brain"]
completion_gate: advisory-evidence-review-done
lane_semantics: "research/advisory: evidence deposition; no execution closeout without promotion"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 可作为 P3 资料任务独立处理；只有明确项目需要动效实现时才进入具体 work 项目。
evidence:
  - "/Users/charles/.hermes/kanban/workspaces/t_f28f5934/animejs-v4-hermes-ui-boundary-assessment.md"
  - "/Users/charles/.hermes/profiles/brain-mirror/skills/ui-skills/skills/baseline-ui/SKILL.md"
  - "/Users/charles/.hermes/profiles/brain-mirror/skills/baseline-ui/SKILL.md"
concepts: ["Anime.js", "frontend-animation", "ui-skill", "motion-performance"]
---

# Task - P3 评估 Anime.js v4 对 Hermes 前端动效/UI skill 的轻量吸收边界

## Objective

基于 Anime.js 官方 GitHub 与官网，评估其对用户前端工程/UI 动效工作流的净新增，而非默认落地到项目。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] Execute the smallest verifiable slice.
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| Official Anime.js README / docs / npm metadata review | done | README confirms CSS/SVG/DOM/Object coverage; docs confirm React scope cleanup, WAAPI 3KB-vs-10KB boundary, SVG/Text/Draggable modules |

## Proof Log

- 2026-05-20T00:24:28+08:00: Task created from local-brain control point.
- 2026-05-20T01:16:32+08:00: Verified Anime.js official README, documentation, and npm metadata; wrote boundary assessment to `/Users/charles/.hermes/kanban/workspaces/t_f28f5934/animejs-v4-hermes-ui-boundary-assessment.md`.
- 2026-05-20T01:16:32+08:00: Patched both `baseline-ui` skill copies to keep `motion/react` as default while allowing Anime.js v4 only for SVG/text/WAAPI/isolated draggable-procedural exceptions.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done — advisory evidence deposited; Anime.js v4 should be treated as an opt-in specialty layer rather than Hermes default animation stack.
- Evidence: official README/npm/docs review plus workspace report `/Users/charles/.hermes/kanban/workspaces/t_f28f5934/animejs-v4-hermes-ui-boundary-assessment.md`; skill boundary patch landed in both `baseline-ui` copies.
- Residual risk: if future product surfaces adopt Anime.js without reduced-motion/Safari/H5 verification or mix it into existing `motion/react` interaction surfaces, stack inconsistency and performance regressions can reappear.
