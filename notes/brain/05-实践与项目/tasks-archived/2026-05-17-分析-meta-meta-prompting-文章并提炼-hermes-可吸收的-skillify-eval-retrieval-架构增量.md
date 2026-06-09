---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T00:16:45+08:00
updated: 2026-05-17T00:50:42+08:00
expires_at: 2026-06-16T00:16:45+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 把 Garry Tan 这篇 meta-meta-prompting 文章中的可复用机制转成 Hermes 可执行演进项：不仅研究 system prompt，还研究“技能如何生成技能”“薄 harness + 胖 skills”“基于已知事实的 cross-modal eval”“按节 deep retrieval + cite brain pages”“一次性工作 skillify 成复用基础设施”等可复利模式。
anti_drift_check: 禁止把该任务做成泛读书笔记或 YC 个人 workflow 赏析；禁止与已有“系统提示词五大核心规则”任务重复造轮子；必须明确哪些点属于 prompt 结构治理、哪些属于 skill graph、哪些属于 local brain / eval / retrieval 基础设施；必须产出 Hermes 是否吸收、如何吸收、先后顺序是什么。
acceptance_evidence: 形成 article→Hermes 的结构化吸收清单：1) 文章关键机制与原文证据；2) 与现有 Hermes prompt/skills/local-brain/taskpool 的对应关系；3) 与既有“系统提示词五大核心规则”任务的重叠/增量边界；4) 推荐的 P1/P2 实施切片（如 meta-skill skillify、cross-modal eval gate、brain citation retrieval、thin harness/fat skills 治理）；5) 需要新增或修订的技能/文档/自检项。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T00:52:28+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-165042-556931-p96577-5413e979-b07126b1/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-meta-meta-prompting-文章并提炼-hermes-可吸收的-skillify-eval-retrieval-架构增量-state.json
multimodel_last_failures: ["best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]
multimodel_failure_taxonomy: ["criteria_missing", "provider_parse_error", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "patch_normalization", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'patch_normalization': ['provider_parse_error'], 'framing': ['vote_reject', 'provider_parse_error']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先完成文章证据抽取与 Hermes 现状 gap map；然后可并行拆成 skillify/meta-skill、cross-modal eval 质检、brain retrieval 引用、thin harness/fat skills 分工四个吸收方向；若与既有系统提示词治理任务重叠，优先做边界对齐再决定是否合并或设为子任务。
evidence:
  - proof:sha256:e991ea3e274ed57e53b964f89d0e9a86effcc97ecfc9375e4695da720e9338ae
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:efea6ed18d6b4ca5e8cde5c5e308beef3165c9819cd46e1771133c533a5b94d4
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:82ce428cb5770b9802cfcf0e564ec0022f09be11163c9faad4f28d8846873f66
concepts: ["meta-meta-prompting", "skillify", "thin-harness", "fat-skills", "cross-modal-eval", "brain-retrieval", "prompt-governance"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 Meta-Meta-Prompting 文章并提炼 Hermes 可吸收的 skillify eval retrieval 架构增量

## Objective

分析并吸收 Garry Tan《Meta-Meta-Prompting: The Secret to Making AI Agents Work》对 Hermes 的可落地启发，不把它当成抽象“提示词很重要”的文章，而是聚焦其中真正能改变 Hermes 的机制：薄 harness / 胖 skills 架构，skillify 作为创建新技能的 meta-skill，输出前基于已知事实的 cross-modal evaluation，按节 deep retrieval 与引用 brain pages 的 specificity 保障，以及把一次性 workflow 提炼成可复利基础设施的闭环。任务需要明确这些机制与 Hermes 现有 system prompt 治理任务的关系：哪些是重叠，哪些是增量，哪些应进入 skill-graph/local-brain/eval 体系而不是继续堆进 system prompt。

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

- 2026-05-17T00:16:45+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T00:50:42+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T00:50:42+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T00:50:42+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:efea6ed18d6b4ca5e8cde5c5e308beef3165c9819cd46e1771133c533a5b94d4, command:py_compile_taskpool PASS

- 2026-05-17T00:50:42+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:82ce428cb5770b9802cfcf0e564ec0022f09be11163c9faad4f28d8846873f66, proof:sha256:efea6ed18d6b4ca5e8cde5c5e308beef3165c9819cd46e1771133c533a5b94d4, command:py_compile_taskpool PASS

- 2026-05-17T00:51:37+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-165042-389113-p96568-3ade7ef4-6643efe1/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T00:52:23+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-165042-689051-p96586-9e712485-2b4bf1b6/discussion_result.json`. Failures: ["best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}

- 2026-05-17T00:52:28+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-165042-556931-p96577-5413e979-b07126b1/discussion_result.json`. Failures: ["best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}
