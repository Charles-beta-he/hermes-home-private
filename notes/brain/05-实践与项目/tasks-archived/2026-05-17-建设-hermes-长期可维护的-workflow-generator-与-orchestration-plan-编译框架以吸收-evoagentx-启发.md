---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T00:52:47+08:00
updated: 2026-05-17T08:51:14+08:00
expires_at: 2026-07-01T00:52:47+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 把 EvoAgentX 的 workflow generator 启发转成 Hermes 长期可维护的编排生成能力：从任务描述推导 delegate_task/pipeline 草案、并行边界、依赖顺序、权限与验证点，形成可审计可修改的 orchestration plan，而不是临时拼接调用序列。
anti_drift_check: 禁止只做从 prompt 到 delegate_task 的字符串模板器；必须建立可维护的 workflow/pipeline 中间表示、依赖与并行语义、authority 与验证点声明，并复用前序 execution_quality/skill 演化治理约束。禁止最小切片式“一次能跑就算完成”。
acceptance_evidence: workflow/pipeline 中间表示设计、自然语言到 orchestration plan 的编译规则、并行/依赖/authority/verification 语义、与 hermes-pipeline 或 delegate_task 的映射方案、与前序两项能力的衔接顺序。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T09:00:20+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-005114-176740-p14731-1bfba604-1930925e/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-建设-hermes-长期可维护的-workflow-generator-与-orchestration-plan-编译框架以吸收-evoagentx-启发-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:deepseek-v4-pro", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: serial-3-of-3:evoagentx-unlanded-evolution-closure
evidence:
  - proof:sha256:d686744da1cd4a6891ad8f6b02cff6874da90df7677c5aa8c558032b0e382c9b
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:0d44a4598456a51b8ffb95bc515eb8b1ae901b6b2f60330bdc309b6098d27c28
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:55dc3688bb15bce5ed4eb10972e3a8246743cfe24bf0fa8a0406564e38e87076
  - artifact:/Users/charles/.hermes/profiles/workflow/skills/autonomous-ai-agents/hermes-pipeline/references/orchestration-plan-compiler-ir.md
  - command:brain_task_orchestrator selfcheck rerun FAIL(pre-existing global profile debt)
  - command:brain_task_orchestrator proof-check --include-active rerun FAIL(pre-existing historical proof debt)
concepts: ["evoagentx", "workflow-generator", "delegate-task", "parallel-planning", "pipeline-generation", "orchestration-compiler"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 建设 Hermes 长期可维护的 workflow-generator 与 orchestration-plan 编译框架以吸收 EvoAgentX 启发

## Objective

基于 EvoAgentX 的 Workflow Generator 建议，为 Hermes 建设长期可维护的工作流生成框架：不是直接拼 delegate_task 调用，而是先定义可审计的 orchestration plan / pipeline IR，再从任务描述生成该计划，显式包含依赖、并行边界、权限层级、验证关卡与交付物闭环。此任务应在 execution_quality 基座与自动 skill 演化闭环方向明确后推进。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] 推进长期可维护主链方案并记录阶段性证据。
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | historical | Original lifecycle auto-closed this note as `done`, but frontmatter certification remained `not_certified`. |
| `HERMES_BRAIN_VAULT=/Users/charles/Documents/brain python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-dry-run --task /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-17-建设-hermes-长期可维护的-workflow-generator-与-orchestration-plan-编译框架以吸收-evoagentx-启发.md --json` | PASS/read-only | Artifact: `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/multimodel-dry-run.after.json`; returned `intervention_required: false` because the task is already `done`, therefore no fresh model round was executed from this command. |
| `HERMES_BRAIN_VAULT=/Users/charles/Documents/brain python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py selfcheck --json` | FAIL/global-pre-existing | Artifact: `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/selfcheck.after.json`; status `FAIL`, `task_count: 201`, `failure_count: 201`; failures are global taskpool profile-boundary debt, not this IR reference write. |
| `HERMES_BRAIN_VAULT=/Users/charles/Documents/brain python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py proof-check --include-active --json` | FAIL/global-pre-existing | Artifact: `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/proofcheck.after.json`; status `FAIL`, `checked_count: 201`, `failure_count: 172`; failures are historical unstructured/invalid proof hashes across older tasks. |
| `python3 -m py_compile /Users/charles/.hermes/scripts/brain_task_orchestrator.py /Users/charles/.hermes/scripts/brain_task_multimodel_loop_runner.py` | PASS | Syntax check passed after this note/reference patch. |
| `HOME=/Users/charles HERMES_BRAIN_VAULT=/Users/charles/Documents/brain python3 /Users/charles/.hermes/scripts/brainctl.py --json sync` | PASS | Artifact: `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/brainctl-sync-home.after.json`; `Sync complete: 0 pushed, 6 pulled`. |
| `HOME=/Users/charles HERMES_BRAIN_VAULT=/Users/charles/Documents/brain python3 /Users/charles/.hermes/scripts/brainctl.py --json reindex` | PASS | Artifact: `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/brainctl-reindex-home.after.json`; indexed 5565 blocks. |

## Proof Log

- 2026-05-17T00:52:47+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T04:52:54+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-204959-572288-p65853-16b172fe-360e93b0/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T08:51:13+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T08:51:13+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T08:51:13+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:0d44a4598456a51b8ffb95bc515eb8b1ae901b6b2f60330bdc309b6098d27c28, command:py_compile_taskpool PASS

- 2026-05-17T08:51:14+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:55dc3688bb15bce5ed4eb10972e3a8246743cfe24bf0fa8a0406564e38e87076, proof:sha256:0d44a4598456a51b8ffb95bc515eb8b1ae901b6b2f60330bdc309b6098d27c28, command:py_compile_taskpool PASS

- 2026-05-17T08:55:18+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-005114-042152-p14722-51fee56d-a4ea9a43/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-20T20:48:33+08:00: Bounded follow-up evidence chain added for Workflow Generator -> Hermes orchestration-plan compiler. Source: `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-16-evoagentx-分析-Hermes优化建议.md`. Decision: land the EvoAgentX workflow-generator idea as a typed `hermes_orchestration_plan_v1` IR, not as a prompt-to-`delegate_task` string template. Landing path: `/Users/charles/.hermes/profiles/workflow/skills/autonomous-ai-agents/hermes-pipeline/references/orchestration-plan-compiler-ir.md` plus index pointer in `hermes-pipeline/SKILL.md`. Verification artifacts: `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/selfcheck.before.json`, `/Users/charles/.hermes/kanban/workspaces/t_fbef3018/proofcheck.before.json`; deterministic checks show pre-existing global taskpool debt, so this note remains `multimodel_status: not_certified`. Stop-condition: do not claim full certification or core implementation until a fresh certification round reaches PASS/LOOP_DONE or a reviewer explicitly accepts the deterministic-only evidence.

## Orchestration Plan Compiler Evidence Chain

### Source

- Primary source: `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-16-evoagentx-分析-Hermes优化建议.md` second-pass backfill.
- Historical target: this task note, which was auto-closed as `done` while frontmatter still said `multimodel_status: not_certified`.
- Skill/reference landing target: `hermes-pipeline` reference `/Users/charles/.hermes/profiles/workflow/skills/autonomous-ai-agents/hermes-pipeline/references/orchestration-plan-compiler-ir.md`.

### Decision

Adopt `hermes_orchestration_plan_v1` as the durable intermediate representation for workflow generation. The compiler must first produce a reviewable plan with explicit source anchors, nodes, edges, parallel groups, authority tiers, verification gates, and handoff/stop policies. Direct prompt-to-`delegate_task` string generation is rejected because it cannot encode durable dependencies, authority, or certification boundaries.

### IR semantics

- Fields: `source`, `intent`, `nodes[]`, `edges[]`, `parallel_groups[]`, `authority`, `verification`, `handoff`.
- Dependency: a node is runnable only after predecessor outputs and node-level verification pass; fan-in passes artifact handles/summaries, not raw child transcripts.
- Parallel: parallel nodes require non-conflicting write surfaces or explicit conflict groups; unknown safety means serial fallback.
- Authority: choose the lowest sufficient tier (`read_only`, `workspace_write`, `project_write`, `external_side_effect`, `human_only`) and fail closed when write scope or approval authority is unclear.
- Verification: every executable node needs a deterministic command, read-back artifact, browser/runtime proof, ratification artifact, or human review gate.

### Mapping boundary

- `delegate_task`: short-lived bounded subwork inside the parent session only; no durable ownership transfer and no long-running guarantee.
- `kanban_create`: durable follow-up, cross-agent handoff, review-required work, or anything that must survive parent-session interruption.
- `hermes-pipeline`: repeated envelope workflows with collector/confirmer/executor/validator/reporter stages.
- `cronjob`: recurring execution only when the prompt is self-contained, bounded, and non-recursive.

### Stop-condition

This bounded follow-up stops after source, decision, landing path, verification artifacts, and unresolved certification gate are explicit. Because this task remains `multimodel_status: not_certified` and current taskpool proof/selfcheck are globally failing, the correct terminal state for the Kanban follow-up is review/blocked rather than false completion.
