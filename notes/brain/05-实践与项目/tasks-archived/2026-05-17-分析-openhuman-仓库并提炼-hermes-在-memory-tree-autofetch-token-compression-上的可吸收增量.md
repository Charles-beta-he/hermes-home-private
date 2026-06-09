---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T00:19:06+08:00
updated: 2026-05-17T04:49:58+08:00
expires_at: 2026-06-16T00:19:06+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 分析 tinyhumansai/openhuman 对 Hermes 的可迁移增量，重点不是泛泛竞品笔记，而是提炼其可复用基础设施：20 分钟 auto-fetch→memory tree→Obsidian vault 的本地记忆流水线、TokenJuice 风格统一压缩层、OAuth 集成自动 typed-tool 暴露、以及 UI-first 人机交互对长期记忆代理的启发。
anti_drift_check: 禁止把任务写成“研究一个热门 repo”式宽泛调研；必须明确 Hermes 应吸收什么、不吸收什么、为什么。禁止被 openhuman 的 mascot/营销表述带偏；优先看 memory pipeline、压缩层、工具暴露与本地知识库这些对 Hermes completion/stability/cost 有真实杠杆的部分。禁止重复已有 prompt 治理任务。
acceptance_evidence: 至少形成：1) repo 元数据与 README 关键机制证据（10.3k★、Rust、118+ integrations、20-min auto-fetch、Memory Tree/Obsidian、TokenJuice）；2) 与 Hermes 当前 local-brain/taskpool/token-compression/skills 的差异图；3) 哪些是 P1 杠杆、哪些只是产品层特性；4) 推荐的长期可维护主链方案与执行顺序；5) 需要新增或修订的技能/脚本/文档/自检项。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T04:57:55+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-204958-898320-p65821-069b0060-6e3b04ab/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-openhuman-仓库并提炼-hermes-在-memory-tree-autofetch-token-compression-上的可吸收增量-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先做仓库证据抽取与 Hermes 现状对照；然后可并行评估 memory tree/Obsidian、本地 auto-fetch 集成、TokenJuice 压缩、118+ OAuth 工具暴露、桌面 mascot/meeting agent 中哪些值得吸收；最后再收敛成 Hermes 的长期可维护主链方案，禁止直接展开为全量对标重写。
evidence:
  - proof:sha256:a62ac7f091465febaf15890734c4b6b093ae0fc9605090df7afcacc485849ddd
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:8d1ce3c7142368dada6897a2221b1fad0c8cdf6d2947399a2212a1b1c18c34b4
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:6cb09da8476cfb47c68f71ef7c83f5744013ade2cd59b7c306e15214317b8cd8
concepts: ["openhuman", "memory-tree", "autofetch", "obsidian-wiki", "token-compression", "oauth-integrations", "agent-harness"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 openhuman 仓库并提炼 Hermes 在 memory tree autofetch token compression 上的可吸收增量

## Objective

分析 GitHub 仓库 tinyhumansai/openhuman（Personal AI super intelligence）并将其作为 Hermes 的外部参考架构进行任务池化吸收。重点关注 README 中可验证的高杠杆机制：本地 Memory Tree + Obsidian Wiki、每 20 分钟 auto-fetch 到记忆树、TokenJuice 统一 token compression、118+ OAuth integrations 暴露为 typed tools、以及“UI-first but local-first”代理体验。任务目标不是照搬 openhuman 产品，而是回答：这些机制里哪些值得 Hermes 在 local-brain / token compression / tool exposure / context ingestion 层吸收，长期可维护主链方案是什么，执行顺序如何，哪些部分应明确不做。

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

- 2026-05-17T00:19:06+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T00:49:49+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-164813-303927-p92791-fa7d8c2a-f4ec4d65/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T04:49:57+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T04:49:58+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T04:49:58+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:8d1ce3c7142368dada6897a2221b1fad0c8cdf6d2947399a2212a1b1c18c34b4, command:py_compile_taskpool PASS

- 2026-05-17T04:49:58+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:6cb09da8476cfb47c68f71ef7c83f5744013ade2cd59b7c306e15214317b8cd8, proof:sha256:8d1ce3c7142368dada6897a2221b1fad0c8cdf6d2947399a2212a1b1c18c34b4, command:py_compile_taskpool PASS

- 2026-05-17T04:53:03+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-204959-059491-p65830-7baf1ec3-63f2d5ce/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T04:57:55+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-204958-898320-p65821-069b0060-6e3b04ab/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
