---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-14T01:42:54+08:00
updated: 2026-05-19T20:07:42+08:00
expires_at: 2026-06-13T01:42:54+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 让任务在 add 入池时即完成优先级分层、依赖关系、执行顺序、parallel boundary 与多模型 triage 结果写入，提升 taskpool 独立性、可调度性与可审计性。
anti_drift_check: 必须优先复用现有 workflow_contract、frontmatter 字段、priority/multimodel 路由与 orchestrator 能力；避免新增平行任务模型或只在入池后补录治理信息。
acceptance_evidence: 现状与目标 add 流程对照、必填字段清单、创建期校验/默认策略、多模型 triage 接入点、依赖/顺序/并行边界写入方案、派生视图刷新策略、历史任务是否需要回填的评估结论、必要补丁或后续拆解任务。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260513-205020-930639-p32882-edd3e449-505cd106/discussion_result.json
multimodel_last_checked_at: 2026-05-14T04:53:15+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260513-205020-930639-p32882-edd3e449-505cd106/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-14-补齐-brain-task-orchestrator-add-流程并在创建时强制写入优先级分层依赖顺序与多模型-triage-结果-state.json
multimodel_last_failures: []
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - proof:sha256:d79d644d325b7e8236fbee5fb541c0afadbc8ee2990cc981c5e737a1e4609ab6
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:c3b8a815718e59a06be850501165cf363c07cd2b32bfcf418b3dcb806be4a1bc
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:f8135dd2f9961f0a1918cfc76494fa95c1a1920f913e412d7c2de26c484ce3e2
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260513-205020-930639-p32882-edd3e449-505cd106/discussion_result.json
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - artifact:/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json
  - proof:sha256:60d867cd2593a2839e50ffdea47894e9fa2acda8ee96a446ed10a3495384787d
concepts: ["taskpool", "brain-task-orchestrator", "pre-ingest-triage", "dependency-ordering", "parallel-boundary", "multimodel-routing"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 补齐 brain_task_orchestrator add 流程并在创建时强制写入优先级分层依赖顺序与多模型 triage 结果

## Objective

补齐 brain_task_orchestrator add 流程，使任务创建时就跑完优先级与依赖治理，而不是入池后再补分析与排序。

## Acceptance Criteria

- [x] 明确 add 流程应强制采集和写入的字段；形成创建期前置 triage 与依赖顺序写入方案；明确完成时默认刷新派生视图；历史任务是否全量回填需单独评估，不与 add 流程改造强绑定；必要时补充脚本实现或拆解后续子任务。

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] Execute the smallest verifiable slice.
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| isolated `brain_task_orchestrator.py add` without priority/dependency/triage metadata | PASS (fail-closed) | `/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json` records nonzero exit and `task creation requires explicit priority/dependency/triage metadata` |
| isolated `brain_task_orchestrator.py add` with `--priority-layer P1 --dependency-order 1,2 --multimodel-triage-result ... --parallel-boundary evolution:taskpool` | PASS | Artifact read-back confirms creation-time frontmatter contains `priority_layer`, `dependency_order`, `multimodel_triage_result`, and `parallel_boundary` |
| derived view refresh after add | PASS | Artifact confirms isolated `任务池-排序.md`, dashboard, and control-center files were generated |

## Proof Log

- 2026-05-14T01:42:54+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status: review; real-chain add-flow evidence is present, but not auto-closed to done by this cron tranche.
- Evidence: `/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json`.
- Residual risk: historical task reopen was caused by generic py_compile/hash closeout; current tranche supplies task-specific command/read-back evidence. Any final `review -> done` close should rely on this artifact plus the existing multimodel certification gate, not generic proof hashes alone.

- 2026-05-14T04:50:20+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-14T04:50:20+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-14T04:50:20+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:c3b8a815718e59a06be850501165cf363c07cd2b32bfcf418b3dcb806be4a1bc, command:py_compile_taskpool PASS

- 2026-05-14T04:52:41+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260513-205020-590910-p32863-b927e75a-3dc8fab1/discussion_result.json`. Failures: []

- 2026-05-14T04:53:15+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260513-205020-754224-p32873-8a2f8218-5c070b3e/discussion_result.json`. Failures: []

- 2026-05-14T04:53:15+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260513-205020-930639-p32882-edd3e449-505cd106/discussion_result.json`. Failures: []

- 2026-05-14T05:05:07+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:f8135dd2f9961f0a1918cfc76494fa95c1a1920f913e412d7c2de26c484ce3e2, proof:sha256:c3b8a815718e59a06be850501165cf363c07cd2b32bfcf418b3dcb806be4a1bc, command:py_compile_taskpool PASS, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260513-205020-930639-p32882-edd3e449-505cd106/discussion_result.json

- 2026-05-19T11:11:13+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T20:05:10+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-follow-through`. Reason: follow_through_bounded_evidence_tranche_claim Evidence: artifact:/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json

- 2026-05-19T20:05:10+08:00: Lifecycle transition `claimed` -> `running` by `hermes-follow-through`. Reason: follow_through_bounded_evidence_tranche_running Evidence: artifact:/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json

- 2026-05-19T20:05:10+08:00: Lifecycle transition `running` -> `review` by `hermes-follow-through`. Reason: real_chain_add_flow_evidence_ready_for_review_not_auto_done Evidence: artifact:/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json

- 2026-05-19T20:07:42+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:60d867cd2593a2839e50ffdea47894e9fa2acda8ee96a446ed10a3495384787d, proof:sha256:d79d644d325b7e8236fbee5fb541c0afadbc8ee2990cc981c5e737a1e4609ab6, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:c3b8a815718e59a06be850501165cf363c07cd2b32bfcf418b3dcb806be4a1bc, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:f8135dd2f9961f0a1918cfc76494fa95c1a1920f913e412d7c2de26c484ce3e2, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260513-205020-930639-p32882-edd3e449-505cd106/discussion_result.json, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, artifact:/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json

## Second-pass Evidence Backfill (2026-05-20)

- Source: 2026-05-19 prior audit classed this as `extract_to_brain_or_skill` with missing `source,landing`; see `/Users/charles/Documents/brain/06-治理与评审/reviews/2026-05-19-prior-external-analysis-quality-audit.md` lines 50-51. The task note later records closeout-audit reopening and a 2026-05-19 follow-through tranche.
- Decision: absorbed / done after real-chain follow-through. Adopted rule: taskpool add must capture priority tier, dependency order, and multi-model triage result at creation time; raw external intake should be governed before formal task creation.
- Landing: `/Users/charles/.hermes/scripts/brain_task_orchestrator.py`; skill/reference `/Users/charles/.hermes/profiles/hermes-core/skills/autonomous-ai-agents/hermes-agent/references/taskpool-pre-ingest-triage.md`; evidence artifact `/Users/charles/.hermes/state/taskpool-evidence/preadd-triage-add-flow-20260519-200457.json`.
- Verification: lifecycle log records follow-through running/review at 2026-05-19T20:05 with `real_chain_add_flow_evidence_ready_for_review_not_auto_done`, then review→done at 2026-05-19T20:07 with the evidence artifact above plus py_compile and proof hashes. Current second-pass path check confirms the orchestrator script, triage reference, and evidence artifact exist.
- Stop-condition / boundary: do not bulk-add external repos/articles as uniform P2 raw intake unless explicitly requested as raw capture. If add/create times out, verify existing task files/sorted pool before retrying to avoid duplicate artifacts; taskpool queue independence depends on this pre-ingest triage remaining upstream of formal creation.
