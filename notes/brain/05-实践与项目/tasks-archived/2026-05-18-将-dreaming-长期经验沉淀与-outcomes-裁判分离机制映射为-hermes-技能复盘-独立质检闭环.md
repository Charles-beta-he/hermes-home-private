---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: "P1: 直接影响 Hermes 长期技能沉淀、任务验收、执行Agent/评估Agent分离与 proof gate 可靠性"
dependency_order: ["1) 梳理现有 skill_manage/复盘/任务池 proof gate；2) 定义 Dreaming=对话复盘到纯文本操作手册的触发条件与输出格式；3) 定义 Outcomes=独立上下文 evaluator 打回标准；4) 选一个任务闭环试跑并沉淀技能补丁"]
created: 2026-05-18T19:46:30+08:00
updated: 2026-05-19T21:12:08+08:00
expires_at: 2026-06-17T19:46:30+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 把“单次记忆”升级为可审计的长期技能沉淀；把执行与验收从同上下文自评升级为独立裁判窗口按预设标准打回。
anti_drift_check: 不要写成 Anthropic 新闻复述或泛泛 AGI 趋势；必须落到 Hermes 可实现的 skill 生成门槛、复盘输入、evaluator rubric、打回/重试状态流与 proof log 字段。
acceptance_evidence: 产出当前 Hermes 缺口图、Dreaming 输出模板、Outcomes 评估清单、至少一个现有 skill 或任务池验收流程的补丁建议，并给出可验证试跑证据。
workflow_contract: control_plane_evolution; independent_evaluator_required_for_high_risk_closure; no raw memory ghosts
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: "用户输入: Dreaming 自动复盘海量对话提炼纯文本操作手册、Harvey 任务完成率提升6倍；Outcomes 建立运动员-裁判员分离，Wisedocs 文件审查时间缩短50%。"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest triage: 用户提供 Harvey 6x/Wisedocs 50% 案例与机制描述；该机制直连 Hermes 记忆-技能-评估闭环，判定 P1，需要执行阶段 evidence-first，必要时真实多模型审查 evaluator rubric"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-19T00:46:31+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260518-163653-175535-p47380-f8e40627-f8f638a9/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-将-dreaming-长期经验沉淀与-outcomes-裁判分离机制映射为-hermes-技能复盘-独立质检闭环-state.json
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
parallel_boundary: 可先独立产出机制设计；若涉及自动写 skill 或自动打回任务，必须串行接在 proof gate/权限审计之后。
evidence:
  - proof:Dreaming/Outcomes Hermes mapping evidence tranche landed 2026-05-19; includes current-gap map, Dreaming output template, Outcomes evaluator rubric, patched hermes-agent reference, and bounded fail-closed handoff.
  - artifact:/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/references/dreaming-outcomes-skill-review-and-evaluator.md
  - classification:bounded_tranche_not_done
  - proof:sha256:bdda6c689d7d191af597001e0b4d320e1e00bf7df4a15eaf80e48838b720b868
  - command:py_compile_taskpool PASS
  - proof:sha256:d262e0b90036028d395232c160c38909d9d8d6ff48569c9319567c02adb16ab6
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - proof:sha256:106c2bfe77a1f7a413afceac5ef8fa158e8382a511e0f5596c88c9471fef536a
  - proof:sha256:25b1b15bab59a5a85fbcf11367c88e452cd8920ea7166b72e962b10974cfacc3
concepts: ["Dreaming", "Outcomes", "skill distillation", "evaluator agent", "long-term memory", "proof gate"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "evidence_bundle_contract", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - 将 Dreaming 长期经验沉淀与 Outcomes 裁判分离机制映射为 Hermes 技能复盘/独立质检闭环

## Objective

把用户提供的 Dreaming/Outcomes 机制转化为 Hermes 长期经验沉淀与独立评估闭环的架构任务，优先补齐技能复盘、纯文本操作手册、裁判Agent打回机制。

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

- 2026-05-18T19:46:30+08:00: Task created from local-brain control point.

## Dreaming/Outcomes Mapping Tranche — 2026-05-19T00:02:47+08:00

### Current Hermes gap map

| Surface | Current behavior observed | Gap against Dreaming/Outcomes | Bounded fix landed / next boundary |
|---|---|---|---|
| Memory | Durable facts can be saved, but session progress must stay out of memory | Dreaming-style distillation needs a strict memory-vs-skill split to avoid ghosts | Landed reference rule: procedures go to skills/references; progress stays in task proof logs |
| Skills | Skills can be patched and referenced, but triggers/rubrics vary by skill | Repeated experience needs a plain-text operating-manual template | Landed `hermes-agent` reference with trigger/precondition/steps/red-lines/evidence/retirement template |
| Taskpool proof | Task notes carry proof logs and structured evidence, but historical proof debt exists | Outcomes-style evaluator needs consistent required fields and independent rejection criteria | Added structured evidence entries for this tranche; historical proof debt remains separate |
| Lifecycle | Advisory multimodel PASS is visible but not closeout authority | Executor must not self-certify done from advisory-only evidence | This task remains bounded/not-done; release back to pending after evidence tranche |
| Worker handoff | Brain overlay contract is now visible in rows/prompts/handoffs | Worker needs evaluator rubric in addition to execution prompt | Reference defines evaluator rubric; next step is integrating it into closeout gate automation |

### Dreaming output template for Hermes

A post-run distillation should produce a short plain-text procedure with:

1. Trigger: when to use the procedure.
2. Preconditions: repo/path/config/authority checks.
3. Steps: exact commands/tool surfaces in order.
4. Red lines: what must not be mutated, leaked, claimed, or closed.
5. Evidence: tests, logs, file paths, proof rows.
6. Verification: how to prove it works now and next run.
7. Retirement: when upstream or a broader workflow absorbs it.

### Outcomes evaluator checklist

A separate evaluator context should reject lifecycle advancement unless:

- red lines were respected: no credentials, no raw runtime state in code repo, no fake done/review, no unapproved push;
- required task fields are present: `capability_delta`, `anti_drift_check`, `acceptance_evidence`, proof/evidence rows, residual risk;
- evidence is tool-backed, not asserted from memory;
- lifecycle is honest: partial advisory progress returns to `pending` or `review` instead of `done`;
- worker handoff contains context, commands, stop conditions, and exact boundary;
- skill/memory split is correct: procedures to skills, durable facts to memory, session progress to task notes only.

### Patch evidence

- Patched existing skill: `hermes-agent`.
- New reference artifact: `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/references/dreaming-outcomes-skill-review-and-evaluator.md`.
- The reference operationalizes Dreaming as procedure distillation and Outcomes as an independent evaluator gate for Hermes skill review/taskpool closeout.

### Fail-closed boundary

This tranche satisfies the task's first evidence requirement but does not close the task. Remaining closeout work:

1. wire this evaluator rubric into an automated taskpool closeout/evaluator command or background-review evaluator path;
2. run a separate evaluator context against a real completed task;
3. only then promote this task to review/done via lifecycle gate.

## Blockers / Confusions

- Historical `proof-check` debt still exists in unrelated older task evidence entries (`child-task:` / `child-axis:` shape). It should not block this bounded tranche, but it must be cleaned before treating proof spine as fully healthy.

## Final Handoff

- Status: bounded evidence tranche landed; keep `pending` after release, not ready for `done`.
- Evidence: gap map + Dreaming template + Outcomes evaluator checklist recorded above; `hermes-agent` reference artifact created at `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/references/dreaming-outcomes-skill-review-and-evaluator.md`.
- Residual risk: evaluator rubric is documented but not yet wired into an automated independent closeout gate; proof-check has unrelated historical structured-evidence debt.

- 2026-05-18T20:03:37+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-115325-116946-p89803-770b97a1-1cb0ac71/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T21:05:04+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-125329-365343-p16679-f59d6f6b-bdcd72b9/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T22:03:37+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-135330-304903-p94122-e8909cc7-845b238c/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T23:02:33+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-145417-279892-p57161-adb476ca-b67a266d/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T23:47:23+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

- 2026-05-18T23:48:19+08:00: Lifecycle transition `claimed` -> `pending` by `hermes-autorun`. Reason: bounded full-pool advance: handoff artifact emitted and verified brain overlay injection; releasing because no worker execution was performed

- 2026-05-18T23:57:20+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

- 2026-05-18T23:58:05+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Force: true. Reason: bounded_full_pool_advance_handoff_verified_release_no_worker_body

- 2026-05-19T00:00:07+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-154724-327795-p179-49807a31-5a91425a/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T00:01:08+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

- 2026-05-19T00:04:11+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Force: true. Reason: bounded_full_pool_advance_dreaming_outcomes_evidence_tranche_landed_not_closeout

- 2026-05-19T00:05:39+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-155510-326482-p9543-1b51e2d5-7af937e1/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T00:08:30+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-155720-893831-p15207-ab44b9b2-28161edc/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T00:34:02+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

- 2026-05-19T00:44:36+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Force: true. Reason: bounded_full_pool_advance_handoff_or_evidence_verified_release_no_worker_body

- 2026-05-19T00:46:31+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-163653-175535-p47380-f8e40627-f8f638a9/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T00:51:06+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T00:51:06+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T00:51:07+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:bdda6c689d7d191af597001e0b4d320e1e00bf7df4a15eaf80e48838b720b868, command:py_compile_taskpool PASS

- 2026-05-19T00:51:07+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:d262e0b90036028d395232c160c38909d9d8d6ff48569c9319567c02adb16ab6, proof:Dreaming/Outcomes Hermes mapping evidence tranche landed 2026-05-19; includes current-gap map, Dreaming output template, Outcomes evaluator rubric, patched hermes-agent reference, and bounded fail-closed handoff., artifact:/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/references/dreaming-outcomes-skill-review-and-evaluator.md, classification:bounded_tranche_not_done, proof:sha256:bdda6c689d7d191af597001e0b4d320e1e00bf7df4a15eaf80e48838b720b868, command:py_compile_taskpool PASS

- 2026-05-19T11:11:15+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T21:12:08+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T21:12:08+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T21:12:08+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:106c2bfe77a1f7a413afceac5ef8fa158e8382a511e0f5596c88c9471fef536a, command:py_compile_taskpool PASS

- 2026-05-19T21:12:08+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:25b1b15bab59a5a85fbcf11367c88e452cd8920ea7166b72e962b10974cfacc3, proof:Dreaming/Outcomes Hermes mapping evidence tranche landed 2026-05-19; includes current-gap map, Dreaming output template, Outcomes evaluator rubric, patched hermes-agent reference, and bounded fail-closed handoff., artifact:/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/references/dreaming-outcomes-skill-review-and-evaluator.md, classification:bounded_tranche_not_done, proof:sha256:bdda6c689d7d191af597001e0b4d320e1e00bf7df4a15eaf80e48838b720b868, command:py_compile_taskpool PASS, proof:sha256:d262e0b90036028d395232c160c38909d9d8d6ff48569c9319567c02adb16ab6, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:106c2bfe77a1f7a413afceac5ef8fa158e8382a511e0f5596c88c9471fef536a
