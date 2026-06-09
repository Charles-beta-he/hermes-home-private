---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: voice-agent-safety-and-capability
dependency_order: ["1) 读取 microsoft/VibeVoice README/模型卡/许可证/安全说明并确认当前源码与权重边界 -> 2) 记录 TTS 源码因深度伪造风险下架、仅保留权重的事实与影响 -> 3) 对比 Hermes 现有 TTS/voice-memo/Rokid 入口需求，分离可吸收能力与禁止接入能力 -> 4) 设计 consent/watermark/audit/fail-closed 安全边界 -> 5) 输出 adopt/defer/reject 决策与最小可验证 PoC 条件"]
created: 2026-05-22T11:49:20+08:00
updated: 2026-05-22T11:59:52+08:00
expires_at: 2026-06-12T11:49:20+08:00
project: hermes-agent
architecture_target: LX
capability_delta: 可能提升 Hermes 在长文本/多说话人/自然对话式 TTS、Rokid 语音反馈、媒体生成工作流中的表达能力；同时要求建立模型权重使用、身份同意、音频水印、审计留痕、禁止仿冒真人等安全约束。
anti_drift_check: 不得因为项目高 Star 就直接集成或下载运行权重；不得绕过其 TTS 源码下架背景；不得实现真人仿声/身份冒充/无同意语音克隆；任何 PoC 必须使用自有或明确授权声音，并默认不对外发布生成音频。
acceptance_evidence: 产出一份 evidence-first 评估文档，包含 GitHub repo 现状、Star/Fork/源码-权重边界、TTS 源码下架与深度伪造风险证据、许可证/模型权重限制、与 Hermes 当前 TTS 工具链差距、可吸收/拒绝项、安全门禁、是否进入 PoC 的决策；若进入 PoC，需给出最小无害测试样例与回滚条件。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: 语音生成与深度伪造风险涉及安全、伦理、产品边界和技术可行性，采用多模型审查避免被 Star 数或单一模型乐观判断带偏。
expected_participants: ["voice-stack-reviewer", "security-reviewer", "rokid-assistant-architect"]
truth_gate: repo-evidence-and-safety-boundary-present
evidence_bundle: "User request: add github.com/microsoft/VibeVoice; user notes 31k stars and TTS source removed due to deepfake risk, weights retained. Browser verification 2026-05-22: https://github.com/microsoft/VibeVoice is public, page shows Open-Source Frontier Voice AI, Star 47.3k, Fork 5.3k, Issues 116, PRs 44, latest commit 303b283 two weeks ago, directories include finetuning-asr, vibevoice, vllm_plugin."
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "Pre-add triage: P2 evolution. Repo 热度高且与语音个人助理/Rokid 长线相关，但 TTS 源码因 deepfake 风险下架，主任务应是安全评估与能力雷达，不是立即接入。"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260522-034928-749017-p36341-352acba6-725e101c/discussion_result.json
multimodel_last_checked_at: 2026-05-22T12:00:09+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260522-034928-749017-p36341-352acba6-725e101c/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-22-评估-microsoft-vibevoice-对-hermes-rokid-语音能力的可吸收增量与深度伪造安全边界-state.json
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
parallel_boundary: 可与普通日报/资讯整理并行；不得与生产 TTS、Rokid 外控、Telegram 自动发音频链路改动并行；不得在未完成风险评估前下载或执行模型权重。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-035254-965647-p38544-3e5db9ec-07f1e69a/discussion_result.json"
  - proof:sha256:d01ef3c3a625e50ee5ed8f6367d8132defb6c0ce317a6ccea1c76bd740d0b0f7
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-035254-965647-p38544-3e5db9ec-07f1e69a/discussion_result.json
concepts: ["VibeVoice", "TTS", "voice-ai", "deepfake-risk", "Rokid", "local-assistant", "media-workflow", "safety-governance"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#324"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 评估 microsoft/VibeVoice 对 Hermes/Rokid 语音能力的可吸收增量与深度伪造安全边界

## Objective

判断 microsoft/VibeVoice 是否值得进入 Hermes 长期语音/个人助理/Rokid 入口技术雷达，并在不放大深度伪造风险的前提下提炼可吸收的 TTS/对话语音能力、部署约束和治理边界。

## Acceptance Criteria

- [ ] Task note exists with capability_delta/anti_drift_check/acceptance_evidence and appears in taskpool as pending/proposed; first execution produces safety-first evaluation before any model execution.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-22T11:49:20+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-22T11:49:28+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-22T11:49:28+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-22T11:59:52+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-035254-965647-p38544-3e5db9ec-07f1e69a/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T11:59:52+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-035254-965647-p38544-3e5db9ec-07f1e69a/discussion_result.json

- 2026-05-22T11:59:52+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:d01ef3c3a625e50ee5ed8f6367d8132defb6c0ce317a6ccea1c76bd740d0b0f7, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-035254-965647-p38544-3e5db9ec-07f1e69a/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-035254-965647-p38544-3e5db9ec-07f1e69a/discussion_result.json

- 2026-05-22T12:00:09+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-034928-749017-p36341-352acba6-725e101c/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
