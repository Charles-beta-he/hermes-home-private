---
type: task
lane: advisory
layer: L3
status: done
priority: P3
priority_layer: "P3: 媒体能力有潜在价值，但当前 GitHub 地址 depalash/OmniVoiceStudio 404，需先验证来源真实性与维护状态"
dependency_order: ["1) 验证 canonical repo/包名/许可证；2) 若存在，检查本地依赖/GPU/语言覆盖与安全边界；3) 与现有 text_to_speech/媒体技能对比；4) 决定是否创建实施任务"]
created: 2026-05-18T19:46:39+08:00
updated: 2026-05-20T20:39:25+08:00
expires_at: 2026-06-17T19:46:39+08:00
project: hermes-agent
architecture_target: LX
capability_delta: 若项目真实可靠，可为 Hermes 增加本地语音克隆和视频配音评估入口，降低对 ElevenLabs 等外部服务依赖。
anti_drift_check: 不要在源码未验证前安装或宣传646语言/3秒克隆等能力；不得引入未审计模型权重或隐私风险。先做来源验证与许可证/安全审查。
acceptance_evidence: 给出 canonical URL 或确认不可用；若可用，补充 README/许可证/安装成本/隐私风险/与现有 TTS 工具差距；若不可用，关闭为无效来源并记录证据。
workflow_contract: source_validation_before_adoption; media_tool_safety_review
audit_closeout: fail_closed_reject
source_decision: "reject: github.com/depalash/OmniVoiceStudio GitHub API 404; GitHub repository search total_count=0; no canonical source found."
landing_decision: "defer/no-landing: 不创建 Hermes 媒体工具、skill 或安装任务；如未来用户提供新的 canonical URL，再作为全新 source-validation 任务重开。"
verification_evidence: "2026-05-20T20:39:25+08:00: urllib GitHub API check /repos/depalash/OmniVoiceStudio => HTTP 404; /search/repositories?q=OmniVoiceStudio+in:name,description => total_count=0."
stop_condition: "停止条件已触发：canonical source 不存在/不可验证；不得安装依赖、下载模型权重、宣传 646 语言或 3 秒克隆能力，也不得要求用户上传私密音频/视频试跑。"
license_boundary: "license unavailable because canonical repo is absent; no adoption until an auditable license file is verified from a canonical upstream."
privacy_boundary: "voice cloning/dubbing 涉及私密声纹与视频内容；无 verified local code/model provenance 前 fail-closed，不处理用户私密媒体。"
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: "用户输入: OmniVoiceStudio 支持646种语言、本地语音克隆与视频配音、3秒音频零样本克隆、GitHub=github.com/depalash/OmniVoiceStudio；本次 API 检查该 repo 404，search 无命中。"
required_authority: dispatch-hint
max_authority: budget-handoff
permission_tier: dispatch-hint
write_surfaces: ["taskpool", "brain"]
completion_gate: advisory-evidence-review-done
lane_semantics: "research/advisory: evidence deposition; no execution closeout without promotion"
multimodel_triage_result: "pre-ingest evidence pass: 用户给出的 github.com/depalash/OmniVoiceStudio 经 GitHub API 返回 404，GitHub search 未命中；判定为 P3 source-validation，不进入实现队列"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-19T23:16:21+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-151246-217201-p81496-0b236221-e28eda92/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-验证-omnivoicestudio-本地语音克隆-视频配音项目真实性并评估是否纳入-hermes-媒体工作流-state.json
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
parallel_boundary: 可与其他外部资料吸收任务并行；任何安装/试跑必须等待来源与许可证验证完成。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-151246-217201-p81496-0b236221-e28eda92/discussion_result.json"
  - proof:sha256:70ca61090813464187c6e43cdec5b8b3b629adb4794cbca0b68c4108520756fa
concepts: ["OmniVoiceStudio", "voice cloning", "dubbing", "local TTS", "ElevenLabs alternative", "media workflow"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract"]
multimodel_certification_reasons: []
---

# Task - 验证 OmniVoiceStudio 本地语音克隆/视频配音项目真实性并评估是否纳入 Hermes 媒体工作流

## Objective

验证用户提到的 OmniVoiceStudio 是否为真实可用的开源 ElevenLabs 替代品，并判断是否值得进入 Hermes 媒体/语音工作流。

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

- 2026-05-18T19:46:39+08:00: Task created from local-brain control point.
- 2026-05-20T20:39:25+08:00: Second-pass media closeout: canonical source validation rerun. `https://api.github.com/repos/depalash/OmniVoiceStudio` returned HTTP 404 and GitHub repository search for `OmniVoiceStudio in:name,description` returned `total_count=0`. Decision: reject/fail-closed; no Hermes media landing until a new canonical URL and license are supplied.

## Blockers / Confusions

- None.

## Final Handoff

- Status: reject / fail-closed. The candidate is not adopted, not monitored as an implementation task, and not promoted into Hermes media workflows.
- Evidence: user-provided URL `github.com/depalash/OmniVoiceStudio` remains unavailable via GitHub API 404; GitHub repo search has zero matches as of 2026-05-20T20:39:25+08:00.
- Landing: none. No skill/tool/config/model download task should be created from this source. If a future canonical upstream appears, start over with source/license/privacy validation before any install or demo.
- Stop-condition: canonical source absent or license unavailable; stop before installation, model weight download, capability claims, or private media handling.
- Residual risk: the project may exist under a different name or private/deleted upstream, but that is insufficient for adoption; require a verifiable canonical URL and license before reopening.

- 2026-05-19T04:08:00+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-195849-712021-p18768-6cb8aaba-18588191/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T04:47:22+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-203841-729677-p30979-c2a47731-4c9bd273/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T06:07:49+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-215930-329373-p52544-236f5ac2-0278c8c0/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T06:46:49+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-223913-141974-p64122-ea73c9ce-7ca32314/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T23:12:45+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T23:12:45+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T23:16:21+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-151246-217201-p81496-0b236221-e28eda92/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T23:16:21+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-151246-217201-p81496-0b236221-e28eda92/discussion_result.json

- 2026-05-19T23:18:49+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:70ca61090813464187c6e43cdec5b8b3b629adb4794cbca0b68c4108520756fa, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-151246-217201-p81496-0b236221-e28eda92/discussion_result.json
