---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1 source inventory/security triage -> 2 compare with CUA/Agent-S -> 3 design Hermes safety wrapper/read-only spike -> 4 deterministic verification -> 5 optional multimodel certification before enabling mutating actions"]
created: 2026-05-21T20:24:01+08:00
updated: 2026-05-21T20:42:08+08:00
expires_at: 2026-06-20T20:24:01+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 Bytebot 的容器化 Linux 桌面、REST/MCP computer-use action space、任务状态机、takeover mode 与本地部署模式，提炼 Hermes 在 computer_use/browser-harness/external-control 方向的可吸收增量。
anti_drift_check: 先对照已有 CUA/Agent-S 分析，禁止把 Bytebot 写成重复的通用 GUI agent 调研；必须突出其净新增：产品化容器桌面、takeover action trace、任务 NEEDS_HELP/NEEDS_REVIEW 状态、REST+MCP 双面、默认安全风险(privileged/no auth)。任何执行必须只做隔离只读 spike，不直接控制宿主桌面或真实账号。
acceptance_evidence: Bytebot repo metadata、README/architecture/takeover/computer-use/source code 证据、Hermes gap matrix、吸收/拒绝项、安全门、临时 profile read-only spike 计划、任务池留痕与 proof/selfcheck 通过。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2: high-leverage desktop-agent reference for Hermes computer-use evolution; not urgent; requires safety/security gate before runtime adoption"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-21T20:27:11+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-122408-547387-p16387-56a00542-cfed78f5/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-analyze-bytebot-desktop-agent-repo-and-harden-hermes-computer-use-external-contr-state.json
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
parallel_boundary: 先完成源码/文档证据与安全风险清单；再评估 Hermes browser-harness/computer_use/external-control 边界；最后形成只读 spike 与后续可派发实现任务，禁止直接默认启用 Bytebot 或暴露 unauthenticated ports。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122408-547387-p16387-56a00542-cfed78f5/discussion_result.json"
  - proof:sha256:89fefc4d850ff4f9356649fd36bfd94ea586cafac31ad4170128bbee88c72b1f
concepts: ["bytebot", "computer-use", "desktop-agent", "external-control", "containerized-desktop", "takeover-mode"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#231"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - Analyze Bytebot desktop-agent repo and harden Hermes computer-use/external-control adoption boundary

## Objective

基于 https://github.com/bytebot-ai/bytebot 的真实源码，提炼 Hermes 可吸收的容器化桌面 agent / takeover trace / computer-use API 模式，并形成安全优先的落地顺序。

## Acceptance Criteria

- [x] Observable source-backed analysis exists at docs/private/bytebot-gap-analysis.md and task contains corrected evidence.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py list --json` | PASS | returned `status=OK` at 2026-05-21T20:31:27+08:00 |
| `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py proof-check --include-active --json` | PASS | returned `status=PASS` at 2026-05-21T20:31:27+08:00 |
| Bytebot source read-back | PASS | verified compose/docs/code paths under `/tmp/bytebot` for privileged desktop, unauthenticated localhost desktop API, takeover mode, computer-use actions, and task statuses |
| Hermes boundary read-back | PASS | verified `tools/computer_use/schema.py`, `tools/computer_use/tool.py`, `plugins/browser/browser_use/provider.py`, and `~/.hermes/scripts/external_control_gate.py` before updating the gap matrix |
| analysis artifact write | PASS | `/Users/charles/.hermes/hermes-agent/docs/private/bytebot-gap-analysis.md` now includes explicit Hermes boundary, gap matrix, read-only spike plan, and absorb/reject decision table |

## Proof Log

- 2026-05-21T20:24:01+08:00: Task created from local-brain control point.
- 2026-05-21T20:32:34+08:00: Re-read the Bytebot source clone plus the current Hermes computer-use/browser-use/external-control boundaries, then expanded `/Users/charles/.hermes/hermes-agent/docs/private/bytebot-gap-analysis.md` with an explicit Hermes↔Bytebot gap matrix, net-new value vs prior CUA/Agent-S analysis, a temporary-profile read-only spike plan, and a fail-closed absorb/reject boundary for future desktop-agent adoption.

## Blockers / Confusions

- None.

## Final Handoff

- Status: source-backed Bytebot analysis is now hardened to the actual Hermes adoption boundary; the artifact is ready for review as a P2 evolution brief, not an execution approval for mutating desktop control.
- Evidence: Bytebot source/doc refs in `/tmp/bytebot` (`docker/docker-compose.yml`, `docs/core-concepts/architecture.mdx`, `docs/guides/takeover-mode.mdx`, `docs/rest-api/computer-use.mdx`, `packages/bytebotd/src/computer-use/computer-use.service.ts`, `packages/bytebot-agent/prisma/schema.prisma`) plus Hermes boundary refs (`/Users/charles/.hermes/hermes-agent/tools/computer_use/schema.py`, `/Users/charles/.hermes/hermes-agent/tools/computer_use/tool.py`, `/Users/charles/.hermes/hermes-agent/plugins/browser/browser_use/provider.py`, `/Users/charles/.hermes/scripts/external_control_gate.py`) and the consolidated report `/Users/charles/.hermes/hermes-agent/docs/private/bytebot-gap-analysis.md`.
- Residual risk: no runtime spike was executed in this tranche; Bytebot still defaults to privileged container + unauthenticated localhost desktop API, so any follow-up must stay read-only/isolated until Hermes adds an authenticated adapter, audit wrapper, and screenshot retention policy.

- 2026-05-21T20:24:08+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T20:24:08+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T20:26:34+08:00: User supplied source URL `https://github.com/bytebot-ai/bytebot`. Cloned successfully to `/tmp/bytebot` at commit `3d37894ce07ef8d8b40adc7fd309ad96c2a71313`; GitHub API canonical `bytebot-ai/bytebot`, Apache-2.0. Source-backed analysis written to `/Users/charles/.hermes/hermes-agent/docs/private/bytebot-gap-analysis.md`. Key verified surfaces: `README.md`, `docs/core-concepts/architecture.mdx`, `docs/guides/takeover-mode.mdx`, `docs/rest-api/computer-use.mdx`, `docker/docker-compose.yml`, `packages/bytebotd/src/computer-use/*`, `packages/bytebotd/src/mcp/computer-use.tools.ts`, `packages/bytebot-agent/src/agent/*`, `packages/bytebot-agent/prisma/schema.prisma`.

- 2026-05-21T20:27:11+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-122408-547387-p16387-56a00542-cfed78f5/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:27:11+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122408-547387-p16387-56a00542-cfed78f5/discussion_result.json

- 2026-05-21T20:42:08+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:89fefc4d850ff4f9356649fd36bfd94ea586cafac31ad4170128bbee88c72b1f, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-122408-547387-p16387-56a00542-cfed78f5/discussion_result.json
