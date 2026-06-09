---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T00:52:31+08:00
updated: 2026-05-20T20:58:34+08:00
expires_at: 2026-07-01T00:52:31+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 在已有 curator/skill_manage/多模型 ratification 基础上，建设长期可维护的自动 skill 演化闭环：失败归因、patch 候选生成、审阅/认证、应用、回滚与审计链全流程治理，不以单次 auto-patch 演示为目标。
anti_drift_check: 禁止只做一个 demo 级 auto-patch；必须依赖 execution_quality 基座，并明确失败分类、补丁安全边界、回滚机制、审计留痕与与 curator 的职责分层。禁止把 skill 自动演化做成隐式不可追踪魔法。
acceptance_evidence: 自动 skill 演化状态机、失败归因模型、patch 候选与 ratification 接口、apply/rollback 审计方案、与前序 execution-quality 基座的依赖关系、可继续派发的实现顺序。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-20T21:02:52+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260520-125451-154246-p76539-19840840-70538c31/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-建设-hermes-长期可维护的自动-skill-演化与-prompt-治理闭环以落地-evoagentx-agent-evolver-建议-state.json
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
parallel_boundary: serial-2-of-3:evoagentx-unlanded-evolution-closure
evidence:
  - proof:sha256:b13046c94f42e30bae67b0c29b6ac1b03e35137d0de7c619278d0b37558bc5fc
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:4cce0e8708e68f055f7334ed1ee37d61d27f9550c8e85acfd89d27fe86ba13fa
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:91f7573fdaed9304582bcbabce82442d7774da428108bd28bf227470c254f398
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - proof:sha256:4fb9969dfe3a57987c73a03658cb34e7e18479a976a2f33d05f2ce923d8e9ed2
  - proof:sha256:7e847a15da6abc18ab3e8124fb0873e66ac4390af33331c125c00f68dd747e1b
  - command:selfcheck_auto_skill_evolution_prompt_governance PASS; artifact:/Users/charles/.hermes/kanban/workspaces/t_951b8cf9/auto_skill_evolution_governance_selfcheck.json
  - file:/Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/references/auto-skill-evolution-prompt-governance.md
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260520-125054-801236-p72737-0ee2155d-af0ec455/discussion_result.json"
  - proof:sha256:42b7386b1582e3c3a33dc1794f7fbb004da43acf5637e2301d27bed369f5982e
concepts: ["evoagentx", "agent-evolver", "auto-prompt-optimization", "skill-evolution", "background-review", "multimodel-ratification"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#6"
---

# Task - 建设 Hermes 长期可维护的自动 skill 演化与 prompt 治理闭环以落地 EvoAgentX Agent Evolver 建议

## Objective

承接 EvoAgentX 的 Agent Evolver 思路，把 Hermes 当前“手动 patch skill”为主的机制升级为长期可维护的自动 skill 演化闭环：基于前序 execution_quality 与证据回写结果，对低分或失败 skill 进行归因、生成 patch 候选、交由多模型认证、再受控应用并保留回滚能力。该任务依赖 execution-quality 评估反馈基座完成后再推进。

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

- 2026-05-17T00:52:31+08:00: Task created from local-brain control point.

## 2026-05-20 bounded evidence-chain closeout

### Source

- Upstream source: EvoAgentX Agent Evolver / automatic evolution loop idea, captured in `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-16-evoagentx-分析-Hermes优化建议.md` lines 77-79: execution -> evaluation -> optimization -> re-execution, with Hermes missing the automatic optimization leg.
- Local source: this task note previously had `multimodel_status: not_certified` while lifecycle auto-close moved it to `done` using hash/py_compile evidence only; see Proof Log 2026-05-17/2026-05-19 lifecycle entries.
- Governance source: parent kanban `t_449ac7c5` bounded this follow-up to the unfinished `自动 skill 演化与 prompt 治理闭环`, not a fresh EvoAgentX repository review.

### Decision

- Decision 1: Keep this note as the taskpool evidence spine for the auto skill/prompt evolution lane; do not overwrite it with a generic repo summary.
- Decision 2: Land reusable operating rules in workflow skill reference `/Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/references/auto-skill-evolution-prompt-governance.md`, and link that reference from `hermes-workflow-orchestrator/SKILL.md` under Recent operational references.
- Decision 3: Treat the current closeout as `selfcheck-only` evidence, not certification authority. Because `multimodel_status` remains `not_certified`, this note is moved back to `status: review` and must not be auto-closed as done until a target-bound certification artifact or explicit reviewer approval exists.

### Landing path

- Task evidence spine: `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-17-建设-hermes-长期可维护的自动-skill-演化与-prompt-治理闭环以落地-evoagentx-agent-evolver-建议.md`.
- Reusable workflow reference: `/Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/references/auto-skill-evolution-prompt-governance.md`.
- Skill routing/index surface: `/Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/SKILL.md`.

### State machine boundary

Executable boundary: `failure_attribution -> patch_candidate -> ratification -> apply_or_rollback -> audit_trail`.

1. `failure_attribution`: classify the trigger before editing. Valid classes: `trigger_routing`, `control_flow`, `verification_gap`, `stale_command`, `overbroad_memory`, `project_specific_rule`, `code_bug`, `insufficient_evidence`. Output must name source artifact, claim, owning surface, and negative-space boundary.
2. `patch_candidate`: create a bounded candidate with `candidate_id`, `source`, `attribution`, `landing_path`, `change_summary`, `verification`, `rollback`, and `stop_condition`. Candidate must be reviewable without reading an entire repo.
3. `ratification`: declare authority as `selfcheck-only`, `advisory`, or `certification`. Multi-model ratification is required for routing, prompt-governance policy, taskpool authority, auto-close behavior, or cross-brain contracts. Advisory-only or not_certified cannot close to done.
4. `apply_or_rollback`: apply via the narrowest tool; read back the changed artifact; run parser/compile/selfcheck gates; rollback immediately if verification fails.
5. `audit_trail`: write source, decision, landing path, verification, stop condition, authority level, and rollback result to the task note and reusable reference when applicable.

### Verification commands / artifacts

- `read_file /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-17-建设-hermes-长期可维护的自动-skill-演化与-prompt-治理闭环以落地-evoagentx-agent-evolver-建议.md`: confirmed original status was `done` but frontmatter remained `multimodel_status: not_certified` and Proof Log evidence was hash/py_compile-heavy.
- `write_file /Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/references/auto-skill-evolution-prompt-governance.md`: landed reusable state-machine/reference contract.
- `patch /Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/SKILL.md`: linked the new reference from Recent operational references.
- `python3 /Users/charles/.hermes/kanban/workspaces/t_951b8cf9/auto_skill_evolution_governance_selfcheck.py`: `PASS`; artifact `/Users/charles/.hermes/kanban/workspaces/t_951b8cf9/auto_skill_evolution_governance_selfcheck.json`; this proves required anchors and state-machine labels exist, not that multi-model certification passed.
- `HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py list --include-done --json`: target task now appears as `status: review`, `multimodel_status: not_certified`, `multimodel_last_gate_status: FAIL`; this is the intended non-fake-close state.
- `HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py proof-check --json`: rerun after evidence write; broad gate returned `FAIL` due an unrelated sibling workflow-generator note with unstructured `reference:` evidence, not due this auto-skill note. This task therefore remains review/not_certified.
- `HOME=/Users/charles python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`: rerun after evidence write; broad gate returned `FAIL` because the taskpool has pre-existing `project_profile_missing` boundary violations across historical tasks, including this note's project profile. This is outside this bounded follow-up's scope and reinforces review/not_certified rather than done.

### Stop condition

- Stop auto-closing this task as done while `multimodel_status: not_certified` remains in frontmatter.
- Stop treating `proof:sha256` or `command:py_compile_taskpool PASS` as sufficient evidence for a prompt/skill governance capability.
- Stop broadening global skill prompts for project-specific facts; those belong in project profiles or task notes.
- Stop applying any auto-evolution patch without rollback and audit trail.
- Stop at `review` if deterministic selfcheck passes but no target-bound multi-model certification or human approval exists.

## Blockers / Confusions

- None.

## Final Handoff

- Status: `review` / `not_certified`; deterministic selfcheck passed, but no target-bound multi-model certification was produced in this bounded pass.
- Evidence: task note contains Source / Decision / Landing path / Verification / Stop condition; reusable workflow reference is linked from hermes-workflow-orchestrator; selfcheck artifact is `/Users/charles/.hermes/kanban/workspaces/t_951b8cf9/auto_skill_evolution_governance_selfcheck.json`.
- Residual risk: broad taskpool `proof-check` and `selfcheck` still fail for unrelated/pre-existing pool issues, so this note must not be considered done until target-bound certification or human review approves the selfcheck-only closeout.

- 2026-05-17T02:10:05+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-180820-265973-p25282-c9847667-0c376571/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T02:50:20+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T02:50:20+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T02:50:21+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:4cce0e8708e68f055f7334ed1ee37d61d27f9550c8e85acfd89d27fe86ba13fa, command:py_compile_taskpool PASS

- 2026-05-17T02:50:21+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:91f7573fdaed9304582bcbabce82442d7774da428108bd28bf227470c254f398, proof:sha256:4cce0e8708e68f055f7334ed1ee37d61d27f9550c8e85acfd89d27fe86ba13fa, command:py_compile_taskpool PASS

- 2026-05-17T02:54:08+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-185021-166467-p42319-16f84715-226f518c/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T02:59:08+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-185021-288115-p42325-53feb745-b1f2d489/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-19T11:11:14+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T21:40:38+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T21:40:38+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T21:40:38+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:4fb9969dfe3a57987c73a03658cb34e7e18479a976a2f33d05f2ce923d8e9ed2, command:py_compile_taskpool PASS

- 2026-05-19T21:40:38+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:7e847a15da6abc18ab3e8124fb0873e66ac4390af33331c125c00f68dd747e1b, proof:sha256:b13046c94f42e30bae67b0c29b6ac1b03e35137d0de7c619278d0b37558bc5fc, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:4cce0e8708e68f055f7334ed1ee37d61d27f9550c8e85acfd89d27fe86ba13fa, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:91f7573fdaed9304582bcbabce82442d7774da428108bd28bf227470c254f398, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:4fb9969dfe3a57987c73a03658cb34e7e18479a976a2f33d05f2ce923d8e9ed2

- 2026-05-20T20:50:54+08:00: Lifecycle transition `review` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-20T20:50:54+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-20T20:58:33+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260520-125054-801236-p72737-0ee2155d-af0ec455/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-20T20:58:33+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260520-125054-801236-p72737-0ee2155d-af0ec455/discussion_result.json

- 2026-05-20T20:58:34+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:42b7386b1582e3c3a33dc1794f7fbb004da43acf5637e2301d27bed369f5982e, proof:sha256:b13046c94f42e30bae67b0c29b6ac1b03e35137d0de7c619278d0b37558bc5fc, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:4cce0e8708e68f055f7334ed1ee37d61d27f9550c8e85acfd89d27fe86ba13fa, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:91f7573fdaed9304582bcbabce82442d7774da428108bd28bf227470c254f398, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:4fb9969dfe3a57987c73a03658cb34e7e18479a976a2f33d05f2ce923d8e9ed2, proof:sha256:7e847a15da6abc18ab3e8124fb0873e66ac4390af33331c125c00f68dd747e1b, command:selfcheck_auto_skill_evolution_prompt_governance PASS; artifact:/Users/charles/.hermes/kanban/workspaces/t_951b8cf9/auto_skill_evolution_governance_selfcheck.json, file:/Users/charles/.hermes/profiles/workflow/skills/software-development/hermes-workflow-orchestrator/references/auto-skill-evolution-prompt-governance.md, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260520-125054-801236-p72737-0ee2155d-af0ec455/discussion_result.json

- 2026-05-20T21:02:52+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260520-125451-154246-p76539-19840840-70538c31/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
