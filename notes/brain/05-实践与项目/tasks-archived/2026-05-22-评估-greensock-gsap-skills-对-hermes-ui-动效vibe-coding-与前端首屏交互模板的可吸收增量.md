---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: frontend-animation-agent-skills
dependency_order: ["1) GitHub 搜索 GSAP-AI-Skills/gsap ai skills，确认官方候选 greensock/gsap-skills 并记录弱相关仓库 -> 2) 读取 README/AGENTS/skills/*/.claude-plugin/.cursor-plugin/examples，提取安装方式、写入面、技能目录、React/ScrollTrigger/performance 规则 -> 3) 对照 Hermes baseline-ui 与 fixing-motion-performance，形成可接受动画边界：transform/opacity、cleanup、reduced-motion、移动端性能、ScrollTrigger refresh/kill -> 4) 分析电影级滚动/Apple 风格动效在个人项目首屏的最小可迁移模板，限定为隔离 demo 而非生产引入 -> 5) 评估 license、供应链、agent prompt 注入/过度动画、bundle 体积、可访问性、SEO/首屏性能风险 -> 6) 输出 adopt/defer/reject 与是否创建 Hermes 内部 GSAP motion skill/profile 的建议。"]
created: 2026-05-22T14:09:41+08:00
updated: 2026-05-22T14:25:53+08:00
expires_at: 2026-06-12T14:09:41+08:00
project: hermes-agent
architecture_target: LX
capability_delta: 可能为 Hermes/work 前端项目提供官方 GSAP Agent Skills、动画生成提示词、React/Vue/Svelte/vanilla 使用规范、ScrollTrigger/Flip/SplitText 等高级动效模式、性能与清理规则；长期可吸收到 UI 动效评审、首屏交互模板、Vibe Coding 动画验收、browser-harness 性能/视觉验证与设计系统 motion guidelines。
anti_drift_check: 不得直接把 npx skills add、Claude/Cursor plugin 或技能文件安装到生产 agent 配置；不得在真实项目首屏直接引入复杂 GSAP/ScrollTrigger/ScrollSmoother 动效；不得以营销文案替代官方 repo/skill 内容；不得违背 Hermes UI 基线：不丢功能、不降性能、尊重 prefers-reduced-motion、动画优先 transform/opacity、避免大面积 blur/filter/layout/scrollY 驱动；任何应用到 work 项目必须另建隔离 PoC 并做桌面/移动 browser-harness 验证。
acceptance_evidence: 产出 evidence-first 评估文档，包含 GitHub 搜索 GSAP-AI-Skills 的官方仓库选择依据、greensock/gsap-skills 元信息、Stars/Forks/Issues/Commit/License、README 安装入口与支持 agent、skills 目录清单、Claude/Cursor plugin 写入面、核心 skills 内容与示例、Apple 风格/电影级滚动可实现路径、与 Hermes baseline-ui/fixing-motion-performance 的一致性检查、最小无害 PoC、验收指标和回滚条件。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: 前端动效能力会影响 Hermes/work 项目的设计系统、性能、可访问性、AI coding agent 行为和用户作品集交付质量，需要前端架构、motion 性能、agent skill 安全多视角审查。
expected_participants: ["frontend-motion-architect", "ui-performance-reviewer", "agent-skill-security-reviewer"]
truth_gate: official-github-repo-evidence-install-surface-motion-boundary-and-poc-plan-present
evidence_bundle: "User request 2026-05-22: 分析添加任务池：GSAP AI Skills 开启 Vibe Coding 动画新时代，并要求 GitHub 搜索 GSAP-AI-Skills、参考 51CTO 技术解析。 GitHub API search verification 2026-05-22: query GSAP-AI-Skills returned top repo greensock/gsap-skills; query gsap ai skills also returned greensock/gsap-skills as top candidate. Repo metadata: greensock/gsap-skills, description Official AI skills for GSAP teaching AI coding agents correct GSAP usage including best practices, patterns, plugins; Stars 3810, Forks 247, open issues 0, subscribers 20, default branch main, pushed 2026-04-21T23:47:09Z, updated 2026-05-22T06:07:29Z, license MIT. README states official AI skills for GSAP, Agent Skills format, works with skills CLI for Cursor/Claude Code/Codex/Windsurf/Copilot/40+ agents; install npx skills add https://github.com/greensock/gsap-skills; Claude Code marketplace add greensock/gsap-skills; Cursor remote rule greensock/gsap-skills. Skills listed: gsap-core, gsap-timeline, gsap-scrolltrigger, gsap-plugins, gsap-utils, gsap-react, gsap-performance, gsap-frameworks. Repo contains .claude-plugin, .cursor-plugin, AGENTS.md, examples for vanilla/react/vue/nuxt. README risk level says LOW, but Hermes evaluation still treats agent skill installation and production animation changes as gated."
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "Pre-add triage: P2 evolution. 官方 GSAP Agent Skills 与用户前端强项、Vibe Coding、首屏动效、AI 编码助手提示词高度相关；但动效容易引入性能、可访问性和设计一致性退化，且涉及安装 agent skills/plugin，先做官方 repo 证据与 UI/motion 边界评估，不直接安装或改项目。"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json
multimodel_last_checked_at: 2026-05-22T14:16:29+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-22-评估-greensock-gsap-skills-对-hermes-ui-动效vibe-coding-与前端首屏交互模板的可吸收增量-state.json
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
parallel_boundary: 可与文档/源码静态审查、隔离动画 demo 设计并行；不得与生产 Claude/Cursor/Codex skill 安装、真实 work 项目 GSAP 引入、首屏动效改造、全局 agent prompt 配置并行；任何项目落地必须另建任务并做桌面 1280px 与移动 375px browser-harness 验证。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json"
  - proof:sha256:6a98b92a15374388653764f9dd336be3895e91a3cc34948f56a9a5c5e751c630
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json
concepts: ["GSAP", "gsap-skills", "greensock", "Agent Skills", "animation", "ScrollTrigger", "ScrollSmoother", "Flip", "SplitText", "React", "Vue", "Svelte", "Cursor", "Claude Code", "Codex", "Copilot", "vibe-coding", "frontend-motion", "Apple-style-scroll", "cinematic-scroll"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#357"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - 评估 greensock/gsap-skills 对 Hermes UI 动效、Vibe Coding 与前端首屏交互模板的可吸收增量

## Objective

判断 greensock/gsap-skills 是否值得进入 Hermes UI/motion、Vibe Coding、前端作品集首屏交互与 agent skill 技术雷达，重点评估官方 GSAP AI Skills 对 AI 生成专业级滚动/Apple 风格/电影级动效的提示词质量、实现规范、性能/可访问性边界与可迁移模板。

## Acceptance Criteria

- [ ] Task note exists with capability_delta/anti_drift_check/acceptance_evidence; first execution is official repo/install-surface/motion-boundary evaluation only, with no production agent skill installation or project animation change.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-22T14:09:41+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-22T14:09:49+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-22T14:09:49+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-22T14:16:29+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T14:16:29+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json

- 2026-05-22T14:25:53+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:6a98b92a15374388653764f9dd336be3895e91a3cc34948f56a9a5c5e751c630, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-060949-457051-p13552-cdb12d37-be624748/discussion_result.json
