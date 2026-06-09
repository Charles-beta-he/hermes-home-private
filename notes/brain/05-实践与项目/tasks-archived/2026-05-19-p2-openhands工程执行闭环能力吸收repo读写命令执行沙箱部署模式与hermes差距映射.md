---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["after:P1-A-self-proving-executor;before:CLI-Anything-repo-to-tool-adapter;parallel_with:OpenSpace-telemetry"]
created: 2026-05-19T14:07:02+08:00
updated: 2026-05-19T23:12:45+08:00
expires_at: 2026-06-18T14:07:02+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 将OpenHands的仓库读取/文件修改/命令执行/任务处理/多部署形态抽象为Hermes工程执行伙伴能力差距矩阵，并选出最小可验证集成片：沙箱命令执行+repo上下文+proof artifact
anti_drift_check: 不直接集成或安装OpenHands；先基于README与仓库结构提炼架构模式；必须保留Hermes现有任务池/权限/自证闭环红线；敏感执行必须走instruction_firewall和授权门禁
acceptance_evidence: "1) live repo inspection evidence: stars/forks/top-level/README; 2) Hermes gap matrix; 3) smallest integration slice design; 4) deterministic proof/selfcheck/tick pass; 5) no credentials leaked"
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: 外部高价值工程agent架构吸收，需要Claude/DeepSeek/MiMo等多模型对能力边界、安全沙箱和落地顺序做真实印证
expected_participants: ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"]
truth_gate: evidence_first_gap_mapping_then_bounded_slice
evidence_bundle: source:https://github.com/OpenHands/OpenHands;inspection:README+top-level;repo_stats:stars=74051,forks=9388,language=Python;summary:SDK+CLI+LocalGUI+Cloud+Enterprise
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2 evolution: high-value external reference architecture; requires evidence-first mapping before implementation"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json
multimodel_last_checked_at: 2026-05-19T21:27:26+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-p2-openhands工程执行闭环能力吸收repo读写命令执行沙箱部署模式与hermes差距映射-state.json
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
parallel_boundary: 只做参考架构吸收和Hermes能力映射；不clone全仓、不运行外部agent、不接入云账号、不修改生产凭据。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json"
  - proof:sha256:258ab657aba566bdea1e97d52d900ec9f192cac3e800906f9732cc11261b99fd
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json
concepts: ["OpenHands", "software-agent-sdk", "repo-read-write", "command-execution", "sandbox", "local-gui", "cloud", "enterprise-vpc", "kubernetes", "engineering-execution-loop"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - P2 OpenHands工程执行闭环能力吸收：repo读写命令执行沙箱部署模式与Hermes差距映射

## Objective

把OpenHands从代码生成器升级为工程执行伙伴的关键机制转译为Hermes local-brain任务池可落地能力，而不是泛泛调研。

## Acceptance Criteria

- [x] Observable source-intake result is recorded in Proof Log.
- [ ] Hermes gap matrix is produced from OpenHands README/top-level architecture.
- [ ] Smallest verifiable integration slice is selected and tied back to self-proving executor / instruction firewall gates.
- [ ] Multimodel review validates safety boundary before any implementation beyond analysis.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Inspect live source before taskpool intake.
- [x] Add classified task with capability_delta / anti_drift_check / acceptance_evidence / multimodel contract.
- [ ] Produce gap matrix and bounded implementation slice.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| GitHub API repo inspection | PASS | OpenHands/OpenHands exists; stars=74051, forks=9388, language=Python, default_branch=main |
| GitHub top-level contents inspection | PASS | `.agents`, `.openhands`, `openhands`, `frontend`, `openhands-ui`, `enterprise`, `containers`, `skills`, `tests`, `docker-compose.yml`, `config.template.toml` |
| README inspection | PASS | SDK, CLI, Local GUI REST API + React SPA, Cloud integrations/RBAC/collaboration, Enterprise VPC/Kubernetes |
| `brain_task_orchestrator.py add ... --json` | PASS | task id `2026-05-19-p2-openhands工程执行闭环能力吸收repo读写命令执行沙箱部署模式与hermes差距映射` |
| `HERMES_LOCAL_BRAIN_AUTORUN=1 brain_task_dispatch_tick.py --summary --print-always --no-state` | PASS | `/tmp/openhands-dispatch-tick.json`, status=OK, error_count=0 |

## Proof Log

- 2026-05-19T14:07:02+08:00: Task created from local-brain control point.
- 2026-05-19T14:08:00+08:00: Live source intake completed for `https://github.com/OpenHands/OpenHands`: repo exists, Python, stars=74051, forks=9388, default branch main.
- 2026-05-19T14:08:00+08:00: Architecture signals captured: SDK, CLI, Local GUI REST API + React SPA, Cloud integrations/RBAC/collaboration, Enterprise VPC/Kubernetes, enterprise/source-available boundary.
- 2026-05-19T14:08:00+08:00: Task classified as P2/evolution/local-brain with requires_multimodel=true; no clone/install/cloud login/external agent execution performed.
- 2026-05-19T14:09:00+08:00: Dispatch summary tick verified taskpool path remains healthy: status=OK, error_count=0.

## Blockers / Confusions

- None for intake. Multimodel ratification is required before using OpenHands as evidence for implementation-level changes.

## Final Handoff

- Status: Intake complete; pending gap matrix and bounded implementation slice.
- Evidence: `/tmp/openhands-task-add.json`, `/tmp/openhands-dispatch-tick.json`, plan entry in `/Users/charles/.hermes/hermes-agent/docs/private/autonomous-workflow-execution-plan.md`.
- Residual risk: README/top-level inspection is enough for intake classification, but not enough for implementation; next step must inspect deeper architecture docs/source before coding.

- 2026-05-19T21:22:04+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T21:22:04+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T21:27:26+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T21:27:26+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json

- 2026-05-19T23:12:45+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:258ab657aba566bdea1e97d52d900ec9f192cac3e800906f9732cc11261b99fd, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260519-132205-378727-p27488-ef2b2667-142b8ca2/discussion_result.json
