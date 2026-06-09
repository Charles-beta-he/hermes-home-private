---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-14T01:36:41+08:00
updated: 2026-05-19T19:10:12+08:00
expires_at: 2026-06-13T01:36:41+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 将预算耗尽后的 grace call 从普通总结升级为结构化 continuation packet 生成器，为新 session 续跑提供稳定、可机读、可复用的接力材料。
anti_drift_check: 必须基于当前 _handle_max_iterations、tools stripped final summary、上下文压缩与真实消息结构设计，避免引入与现有 summary 路径并行冲突的新机制。
acceptance_evidence: continuation packet 字段设计、与当前 grace call 总结路径差异分析、注入样例、失败/降级策略、必要实现补丁或接口变更。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-14T01:50:43+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260513-174310-966372-p45778-0ea0fdd0-a186faeb/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-14-为-hermes-设计-grace-call-输出结构化-continuation-packet-机制-state.json
multimodel_last_failures: []
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - proof:sha256:c90ddb9f0fc410a63d82b3d19fff6e66772a8385d60d750e651f14eaa11a8826
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:cd56ee89cfae563231169ede3d3a54badf855f9fccfcba2995327735180c2dcc
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:cacbd806629b629e19f0c826c23fd84d7d20e59ea77c1a9ed6a5a19bb762d35f
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260513-174311-169248-p45788-890a09c2-1ab51b5b/discussion_result.json
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
concepts: ["grace-call", "continuation-packet", "iteration-budget", "resume-brief", "structured-summary"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 Hermes 设计 grace call 输出结构化 continuation packet 机制

## Objective

把预算耗尽时的 grace call 产物设计成适合自动续跑的结构化 continuation packet，而不是松散自然语言总结。

## Acceptance Criteria

- [x] 明确 packet schema、生成时机、与现有总结路径的兼容关系、最小实现方案与风险控制。

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Confirm the historical design intent against the landed continuation control-plane surfaces.
- [x] Backfill source / decision / landing / verification / stop-condition with current evidence.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| Historical design artifact present | pass | `/Users/charles/.hermes/kanban/workspaces/t_cb60fb30/grace-call-continuation-new-session-resume-analysis.md` |
| Continuation packet schema landed | pass | `/Users/charles/.hermes/hermes-agent/agent/continuation.py` |
| Conversation auto-relay uses canonical packet writer | pass | `/Users/charles/.hermes/hermes-agent/agent/conversation_loop.py` |
| Architecture record names landed control-plane slice | pass | `/Users/charles/.hermes/hermes-agent/docs/adr/2026-05-18-continuation-control-plane.md` |
| Kanban fail-honest boundary still enforced | pass | `/Users/charles/.hermes/hermes-agent/tests/run_agent/test_run_agent.py` |

## Proof Log

- 2026-05-14T01:36:41+08:00: Task created from local-brain control point.

- 2026-05-19T19:10:12+08:00: Historical evidence debt backfilled from the landed continuation control-plane implementation. Source artifact: `/Users/charles/.hermes/kanban/workspaces/t_cb60fb30/grace-call-continuation-new-session-resume-analysis.md`. Current landing confirmed in `/Users/charles/.hermes/hermes-agent/agent/continuation.py`, `/Users/charles/.hermes/hermes-agent/agent/conversation_loop.py`, and `/Users/charles/.hermes/hermes-agent/docs/adr/2026-05-18-continuation-control-plane.md`.

## Blockers / Confusions

- None.

## Final Handoff

- Status: absorbed and closed honestly. The original design intent no longer lives as a standalone grace-call-only mechanism; it has been folded into Hermes's landed continuation control plane.
- Source:
  - Historical design-analysis artifact: `/Users/charles/.hermes/kanban/workspaces/t_cb60fb30/grace-call-continuation-new-session-resume-analysis.md`
  - Current landed implementation: `/Users/charles/.hermes/hermes-agent/agent/continuation.py`, `/Users/charles/.hermes/hermes-agent/agent/conversation_loop.py`
  - Current architecture record: `/Users/charles/.hermes/hermes-agent/docs/adr/2026-05-18-continuation-control-plane.md`
- Decision:
  - Hermes did not keep grace-call output as a loose natural-language summary or a taskpool-only side format. The durable decision was to promote it into a shared continuation packet schema (`hermes_continuation_packet_v1`) with compatibility copies for legacy relay debugging.
  - Kanban workers remain fail-honest on iteration exhaustion; automatic successor behavior is not implied by this note and still requires an explicit continuation contract.
- Landing:
  - Packet schema and storage helpers: `/Users/charles/.hermes/hermes-agent/agent/continuation.py`
  - Conversation auto-relay packet writing: `/Users/charles/.hermes/hermes-agent/agent/conversation_loop.py`
  - Architecture rationale and rollout boundary: `/Users/charles/.hermes/hermes-agent/docs/adr/2026-05-18-continuation-control-plane.md`
  - Anti-fragmentation guard: `/Users/charles/.hermes/scripts/post-update-check.py`
- Verification:
  - Relay packet regression: `/Users/charles/.hermes/hermes-agent/tests/run_agent/test_auto_relay_continuation.py`
  - Kanban block regression: `/Users/charles/.hermes/hermes-agent/tests/run_agent/test_run_agent.py`
  - Architecture status recorded as `landed-minimum-viable-control-plane`: `/Users/charles/.hermes/hermes-agent/docs/adr/2026-05-18-continuation-control-plane.md`
- Stop-condition:
  - This historical task should not be reopened merely because later slices are still pending. Evidence debt is resolved once the note points to the landed continuation control-plane surfaces above.
  - Remaining work belongs to follow-up continuation surfaces (`delegate_task`, `cron`, `bg-review`, `gateway`) and possible future kanban continuation contracts, not to this closed note.
- Residual risk:
  - The minimum landed slice intentionally does not yet expand continuation behavior for every runtime surface.
  - Gateway/taskpool/cron-wide successor semantics still need later bounded follow-ups rather than being silently inferred from this note.

- 2026-05-14T01:43:10+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-14T01:43:10+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-14T01:43:10+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:cd56ee89cfae563231169ede3d3a54badf855f9fccfcba2995327735180c2dcc, command:py_compile_taskpool PASS

- 2026-05-14T01:46:37+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260513-174311-368437-p45796-8c718072-d5a3de45/discussion_result.json`. Failures: []

- 2026-05-14T01:46:39+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260513-174311-169248-p45788-890a09c2-1ab51b5b/discussion_result.json`. Failures: []

- 2026-05-14T01:49:50+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:cacbd806629b629e19f0c826c23fd84d7d20e59ea77c1a9ed6a5a19bb762d35f, proof:sha256:cd56ee89cfae563231169ede3d3a54badf855f9fccfcba2995327735180c2dcc, command:py_compile_taskpool PASS, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260513-174311-169248-p45788-890a09c2-1ab51b5b/discussion_result.json

- 2026-05-14T01:50:43+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260513-174310-966372-p45778-0ea0fdd0-a186faeb/discussion_result.json`. Failures: []

- 2026-05-19T11:11:10+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T18:44:57+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

## Second-pass Evidence Backfill (2026-05-20)

- Source: 2026-05-19 prior audit classed this task as `extract_to_brain_or_skill` with missing `source,landing`; see `/Users/charles/Documents/brain/06-治理与评审/reviews/2026-05-19-prior-external-analysis-quality-audit.md` lines 46-47. The note itself also records a 2026-05-19 closeout audit reopening because earlier evidence was py_compile/hash/multimodel-only or lacked task-type-specific real-chain acceptance.
- Decision: partially absorbed. The structure is now represented by Hermes continuation-control-plane artifacts, but this historical task should not be treated as fully closed for every runtime surface until real-chain successor semantics are separately accepted.
- Landing: `/Users/charles/.hermes/hermes-agent/agent/continuation.py`; `/Users/charles/.hermes/hermes-agent/docs/adr/2026-05-18-continuation-control-plane.md`; `/Users/charles/.hermes/hermes-agent/tests/agent/test_continuation.py`; `/Users/charles/.hermes/hermes-agent/tests/run_agent/test_auto_relay_continuation.py`; `/Users/charles/.hermes/profiles/hermes-core/skills/autonomous-ai-agents/hermes-agent/references/continuation-control-plane.md`; backfill artifact `/Users/charles/.hermes/kanban/workspaces/t_ced7cbb0/grace-call-continuation-packet-backfill.md`.
- Verification: current second-pass path check confirms the continuation module, ADR, tests, skill reference, and backfill artifact exist. Historical Proof Log still only proves the earlier minimum slice (`py_compile_taskpool`, hashes, multimodel ratification), so the reopened state remains honest.
- Stop-condition / reopen reason: keep reopened/pending until a bounded real-chain task proves the intended runtime surface (conversation grace call, delegation relay, taskpool/cron/gateway successor behavior as applicable) with task-type-specific acceptance. Do not infer global continuation semantics from config names or a single py_compile/hash proof.
