# Manual-review multi-model packet — 2026-05-27

Ask: classify each completed learning task as final-landed / partial-stage / reject-watch / reopen-needed; produce user-approval recommendations.

## 1. 审计-hermes-内置技能体系并优化开箱即用基础能力
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-审计-hermes-内置技能体系并优化开箱即用基础能力.md
- priority/status/updated: P2 / done / 2026-05-14T14:50:22+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, has implementation/test signal
- acceptance: built-in skills 对照清单、缺口清单、优化项与落地证据。
- evidence snippets:
  - L5: status: done
  - L7: created: 2026-05-14T00:27:57+08:00
  - L8: updated: 2026-05-14T14:50:22+08:00
  - L11: architecture_target: skill-graph
  - L13: anti_drift_check: 必须对照现有 skills/umbrella/reference 体系、触发条件与维护路径逐项审计。
  - L14: acceptance_evidence: built-in skills 对照清单、缺口清单、优化项与落地证据。
- risk/follow-up snippets:
  - L72: | brain_task_orchestrator list | pending | |
  - L86: - Residual risk:
  - L90: - 2026-05-14T13:08:00+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

## 2. 对预算耗尽后的-grace-call-continuation-new-session-resume-机制做多模型分析并完善方案
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-对预算耗尽后的-grace-call-continuation-new-session-resume-机制做多模型分析并完善方案.md
- priority/status/updated: P1 / done / 2026-05-19T18:41:26+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, has implementation/test signal
- acceptance: 多模型分析结论、现状与目标架构对照、continuation packet 结构方案、/new 续跑接入点设计、风险与回退策略、必要实现补丁或任务拆解。
- evidence snippets:
  - L5: status: done
  - L7: created: 2026-05-14T01:16:41+08:00
  - L8: updated: 2026-05-19T18:41:26+08:00
  - L14: acceptance_evidence: 多模型分析结论、现状与目标架构对照、continuation packet 结构方案、/new 续跑接入点设计、风险与回退策略、必要实现补丁或任务拆解。
  - L20: completion_gate: ratification-or-selfcheck-review-done
  - L21: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L74: | brain_task_orchestrator list | pending | |
  - L88: - Residual risk:
  - L90: - 2026-05-14T01:37:38+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff
  - L104: - 2026-05-19T11:11:12+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evid
  - L106: - 2026-05-19T18:41:24+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

## 3. p2-吸收-anthropic-founders-playbook-的-ai-原生组织阶段框架到-hermes-单人公司-多agent运营画像
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-p2-吸收-anthropic-founders-playbook-的-ai-原生组织阶段框架到-hermes-单人公司-多agent运营画像.md
- priority/status/updated: P2 / done / 2026-05-20T00:19:35+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording
- acceptance: 核验英文 PDF/官方说明，抽取四阶段机制，映射到 Hermes 当前能力矩阵、任务池优先级、角色/预算/验收治理，并形成可执行 follow-up 顺序。
- evidence snippets:
  - L5: status: done
  - L7: created: 2026-05-20T00:16:39+08:00
  - L8: updated: 2026-05-20T00:19:35+08:00
  - L14: acceptance_evidence: 核验英文 PDF/官方说明，抽取四阶段机制，映射到 Hermes 当前能力矩阵、任务池优先级、角色/预算/验收治理，并形成可执行 follow-up 顺序。
  - L20: completion_gate: ratification-or-selfcheck-review-done
  - L21: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L14: acceptance_evidence: 核验英文 PDF/官方说明，抽取四阶段机制，映射到 Hermes 当前能力矩阵、任务池优先级、角色/预算/验收治理，并形成可执行 follow-up 顺序。
  - L70: | brain_task_orchestrator list | pending | |
  - L84: - Residual risk:
  - L86: - 2026-05-20T00:16:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 4. p1-吸收-ai-编码后置-ci-cd-向内嵌连续验证与预合并层迁移的架构范式
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-p1-吸收-ai-编码后置-ci-cd-向内嵌连续验证与预合并层迁移的架构范式.md
- priority/status/updated: P1 / done / 2026-05-20T00:26:26+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals
- acceptance: 产出当前 Hermes 验证链路缺口图、预合并层/连续验证状态机、冲突与回滚治理边界、可验证落地顺序与 selfcheck/测试证据。
- evidence snippets:
  - L5: status: done
  - L7: created: 2026-05-20T00:13:38+08:00
  - L8: updated: 2026-05-20T00:26:26+08:00
  - L14: acceptance_evidence: 产出当前 Hermes 验证链路缺口图、预合并层/连续验证状态机、冲突与回滚治理边界、可验证落地顺序与 selfcheck/测试证据。
  - L20: completion_gate: ratification-or-selfcheck-review-done
  - L21: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L70: | brain_task_orchestrator list | pending | |
  - L84: - Residual risk:
  - L86: - 2026-05-20T00:13:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 5. p2-为每日日报补充-trendradar-多平台热点-rss-mcp-源质量评估与接入边界
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-p2-为每日日报补充-trendradar-多平台热点-rss-mcp-源质量评估与接入边界.md
- priority/status/updated: P2 / done / 2026-05-20T00:26:26+08:00
- deterministic_preclass: likely-landed
- signals: has implementation/test signal
- acceptance: 核验 sansan0/TrendRadar repo README/部署方式/MCP/RSS/通知能力，给出日报接入字段、质量门槛、去重策略、缓存/回退和验证方案。
- evidence snippets:
  - L5: status: done
  - L7: created: 2026-05-20T00:24:28+08:00
  - L8: updated: 2026-05-20T00:26:26+08:00
  - L14: acceptance_evidence: 核验 sansan0/TrendRadar repo README/部署方式/MCP/RSS/通知能力，给出日报接入字段、质量门槛、去重策略、缓存/回退和验证方案。
  - L20: completion_gate: ratification-or-selfcheck-review-done
  - L21: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L56: | brain_task_orchestrator list | pending | |
  - L70: - Residual risk:
  - L72: - 2026-05-20T00:26:25+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

## 6. p2-二次吸收-cli-anything-cli-hub-的工具注册表与软件-agent-native-适配机制
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-20-p2-二次吸收-cli-anything-cli-hub-的工具注册表与软件-agent-native-适配机制.md
- priority/status/updated: P2 / done / 2026-05-20T00:47:57+08:00
- deterministic_preclass: likely-landed
- signals: has implementation/test signal
- acceptance: 核验 HKUDS/CLI-Anything 与 clianything.cc/CLI-Hub，明确相对现有 scaffold 的净新增、权限模型、安装审查、工具注册/撤销流程与可验证试点。
- evidence snippets:
  - L5: status: done
  - L7: created: 2026-05-20T00:24:28+08:00
  - L8: updated: 2026-05-20T00:47:57+08:00
  - L13: anti_drift_check: 禁止重复已完成的 CLI Anything 安全 adapter scaffold；本任务只做 second-pass registry/hub/agent-native 软件适配增量，不重写旧任务结论。
  - L14: acceptance_evidence: 核验 HKUDS/CLI-Anything 与 clianything.cc/CLI-Hub，明确相对现有 scaffold 的净新增、权限模型、安装审查、工具注册/撤销流程与可验证试点。
  - L20: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L56: | brain_task_orchestrator list | pending | |
  - L70: - Residual risk:
  - L72: - 2026-05-20T00:47:56+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

## 7. implement-agentmemory-isolated-mcp-compatibility-spike-for-hermes-temporary-prof
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-21-implement-agentmemory-isolated-mcp-compatibility-spike-for-hermes-temporary-prof.md
- priority/status/updated: P2 / done / 2026-05-21T20:45:12+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording, has implementation/test signal
- acceptance: 临时 profile 配置片段、AgentMemory health 输出、MCP tools/list 证据、最小 remember/recall 或 read-only 查询证据、清理记录、失败/降级原因。
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-21T20:29:35+08:00
  - L10: updated: 2026-05-21T20:45:12+08:00
  - L16: acceptance_evidence: 临时 profile 配置片段、AgentMemory health 输出、MCP tools/list 证据、最小 remember/recall 或 read-only 查询证据、清理记录、失败/降级原因。
  - L27: completion_gate: ratification-or-selfcheck-review-done
  - L28: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L14: capability_delta: 在不修改默认 Hermes 配置的前提下，用临时 profile/隔离数据目录验证 AgentMemory MCP/server 可达性、工具枚举、health、只读 recall 与受控写入回滚，为后续共享记忆服务接入提供证据。
  - L51: - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - L83: | brain_task_orchestrator list | pending | |
  - L97: - Residual risk:
  - L99: - 2026-05-21T20:29:42+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 8. add-agentmemory-governance-selfcheck-for-server-auth-storage-retention-and-index
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-21-add-agentmemory-governance-selfcheck-for-server-auth-storage-retention-and-index.md
- priority/status/updated: P2 / done / 2026-05-21T22:17:06+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording, has implementation/test signal
- acceptance: selfcheck 规则或脚本设计、启用/未启用/不健康三态样例、auth/storage/retention/index 检查输出、proof-check/selfcheck 通过。
- evidence snippets:
  - L5: status: done
  - L8: dependency_order: ["depends on retrieval bridge and consolidation design -> 1 define selfcheck probes -> 2 implement default-off checks -> 3 verify healthy/unavailable/misconfigured outputs -> 4 integrate post-update or control-plane evidence"]
  - L9: created: 2026-05-21T20:38:37+08:00
  - L10: updated: 2026-05-21T22:17:06+08:00
  - L16: acceptance_evidence: selfcheck 规则或脚本设计、启用/未启用/不健康三态样例、auth/storage/retention/index 检查输出、proof-check/selfcheck 通过。
  - L27: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L50: - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - L82: | brain_task_orchestrator list | pending | |
  - L96: - Residual risk:
  - L98: - 2026-05-21T20:38:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim
  - L106: - 2026-05-21T20:44:08+08:00: Lifecycle transition `review` -> `pending` by `hermes-agent`. Force: true. Reason: User asked to add AgentMemory evolution improvements to taskpool; queued work items are not completed implementation. Evidence: command: brain_task_orchestrator transit

## 9. experience-ratchet-repo-replay-baseline-source-freshness-matrix
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-baseline-source-freshness-matrix.md
- priority/status/updated: P2 / done / 2026-05-23T15:52:41+08:00
- deterministic_preclass: likely-reject-or-supersede
- signals: has not_certified/advisory/ratification-pending signals, has implementation/test signal, has rejection/supersede signal
- acceptance: Updated docs/private/experience-ratchet-repo-replay-matrix.md with repo metadata/freshness rows and no direct core/memory mutation.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T15:43:35+08:00
  - L10: updated: 2026-05-23T15:52:41+08:00
  - L15: anti_drift_check: No ExperienceAtom may be promoted from a stale task summary alone; every row must cite canonical repo, checked commit/freshness, local artifact, and redaction status.
  - L16: acceptance_evidence: Updated docs/private/experience-ratchet-repo-replay-matrix.md with repo metadata/freshness rows and no direct core/memory mutation.
  - L27: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L79: | brain_task_orchestrator list | pending | |
  - L93: - Residual risk:
  - L95: - 2026-05-23T15:43:43+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 10. experience-ratchet-repo-replay-agentmemory-atom-extraction
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-agentmemory-atom-extraction.md
- priority/status/updated: P2 / done / 2026-05-23T16:22:00+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, has implementation/test signal
- acceptance: Validated/normalized ExperienceAtom JSON files for shared memory server boundary, hook-driven capture lifecycle, supersession/versioning, and retention/privacy.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T15:45:35+08:00
  - L10: updated: 2026-05-23T16:22:00+08:00
  - L15: anti_drift_check: Must cite agentmemory gap artifact and repo commit/freshness; no direct AgentMemory integration, no memory writes, no plugin enablement.
  - L16: acceptance_evidence: Validated/normalized ExperienceAtom JSON files for shared memory server boundary, hook-driven capture lifecycle, supersession/versioning, and retention/privacy.
  - L27: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L81: | brain_task_orchestrator list | pending | |
  - L95: - Residual risk:
  - L97: - 2026-05-23T15:45:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 11. experience-ratchet-repo-replay-bytebot-atom-extraction
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-bytebot-atom-extraction.md
- priority/status/updated: P2 / done / 2026-05-23T16:24:29+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording
- acceptance: Validated/normalized ExperienceAtom JSON files for external-control boundary, takeover state, NEEDS_HELP/NEEDS_REVIEW, and security red lines.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T15:47:36+08:00
  - L10: updated: 2026-05-23T16:24:29+08:00
  - L16: acceptance_evidence: Validated/normalized ExperienceAtom JSON files for external-control boundary, takeover state, NEEDS_HELP/NEEDS_REVIEW, and security red lines.
  - L27: completion_gate: ratification-or-selfcheck-review-done
  - L28: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L82: | brain_task_orchestrator list | pending | |
  - L96: - Residual risk:
  - L98: - 2026-05-23T15:47:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 12. experience-ratchet-repo-replay-karpathy-skills-atom-extraction
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-karpathy-skills-atom-extraction.md
- priority/status/updated: P2 / done / 2026-05-23T16:24:30+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording
- acceptance: Validated/normalized atoms for Think Before Coding, Simplicity First, Surgical Changes, and no speculative abstraction with falsifiers and boundaries.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T16:00:48+08:00
  - L10: updated: 2026-05-23T16:24:30+08:00
  - L14: capability_delta: Extract coding-behavior ExperienceAtoms from Karpathy Skills with applicability/anti-conditions for Hermes development behavior.
  - L16: acceptance_evidence: Validated/normalized atoms for Think Before Coding, Simplicity First, Surgical Changes, and no speculative abstraction with falsifiers and boundaries.
  - L27: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L82: | brain_task_orchestrator list | pending | |
  - L96: - Residual risk:
  - L98: - 2026-05-23T16:00:56+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 13. experience-ratchet-repo-replay-openclaw-wrong-source-supersede-atom
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-openclaw-wrong-source-supersede-atom.md
- priority/status/updated: P2 / done / 2026-05-23T16:24:30+08:00
- deterministic_preclass: likely-reject-or-supersede
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording, has rejection/supersede signal
- acceptance: Validated/normalized ExperienceAtom JSON showing wrong-source hypothesis superseded by corrected Karpathy Skills analysis with falsifier and rollback lesson.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T15:49:08+08:00
  - L10: updated: 2026-05-23T16:24:30+08:00
  - L14: capability_delta: Turn the historical OpenClaw/Garden Skills wrong-source correction into a reusable revoke/supersede ExperienceAtom pattern.
  - L15: anti_drift_check: Do not resurrect the superseded source as valid evidence for Karpathy Skills; preserve it only as correction/audit evidence.
  - L16: acceptance_evidence: Validated/normalized ExperienceAtom JSON showing wrong-source hypothesis superseded by corrected Karpathy Skills analysis with falsifier and rollback lesson.
- risk/follow-up snippets:
  - L81: | brain_task_orchestrator list | pending | |
  - L95: - Residual risk:
  - L97: - 2026-05-23T15:49:17+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 14. experience-ratchet-repo-replay-hermes-upstream-ratchet-atom-extraction
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-hermes-upstream-ratchet-atom-extraction.md
- priority/status/updated: P2 / done / 2026-05-23T16:24:30+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording, has implementation/test signal
- acceptance: Validated/normalized atoms for no-agent cron silence, semantic review packet, fail-closed certification gate, and private overlay ratchet governance.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T16:14:19+08:00
  - L10: updated: 2026-05-23T16:24:30+08:00
  - L15: anti_drift_check: Must cite committed scripts/docs and verification evidence; do not use this task to auto-promote private/main or alter upstream sync policy.
  - L16: acceptance_evidence: Validated/normalized atoms for no-agent cron silence, semantic review packet, fail-closed certification gate, and private overlay ratchet governance.
  - L27: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L82: | brain_task_orchestrator list | pending | |
  - L96: - Residual risk:
  - L98: - 2026-05-23T16:14:27+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 15. experience-ratchet-repo-replay-rag-anything-atom-extraction
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-rag-anything-atom-extraction.md
- priority/status/updated: P2 / done / 2026-05-23T16:24:30+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording
- acceptance: Validated/normalized atoms for structured parsing before semantic insertion, multimodal decomposition, modality-aware retrieval, and resilience callbacks.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T16:06:20+08:00
  - L10: updated: 2026-05-23T16:24:30+08:00
  - L16: acceptance_evidence: Validated/normalized atoms for structured parsing before semantic insertion, multimodal decomposition, modality-aware retrieval, and resilience callbacks.
  - L27: completion_gate: ratification-or-selfcheck-review-done
  - L28: lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
- risk/follow-up snippets:
  - L82: | brain_task_orchestrator list | pending | |
  - L96: - Residual risk:
  - L98: - 2026-05-23T16:06:28+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 16. experience-ratchet-repo-replay-cross-repo-consensus-synthesis
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-experience-ratchet-repo-replay-cross-repo-consensus-synthesis.md
- priority/status/updated: P2 / done / 2026-05-23T16:25:07+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording
- acceptance: MemoryMaze relations plus proposal artifacts under ~/.hermes/experience-ratchet/proposals/; report lists promoted_candidate vs normalized-only vs deprecated/revoked atoms.
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T15:53:26+08:00
  - L10: updated: 2026-05-23T16:25:07+08:00
  - L15: anti_drift_check: Must wait for repo-level atoms; multi-model agreement is not truth; no direct memory/skill/profile/taskpool/core mutation.
  - L16: acceptance_evidence: MemoryMaze relations plus proposal artifacts under ~/.hermes/experience-ratchet/proposals/; report lists promoted_candidate vs normalized-only vs deprecated/revoked atoms.
  - L27: completion_gate: ratification-or-selfcheck-review-done
- risk/follow-up snippets:
  - L83: | brain_task_orchestrator list | pending | |
  - L97: - Residual risk:
  - L99: - 2026-05-23T15:53:34+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 17. add-negative-space-evals-for-karpathy-style-hermes-coding-guardrails
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-add-negative-space-evals-for-karpathy-style-hermes-coding-guardrails.md
- priority/status/updated: P1 / done / 2026-05-23T18:18:11+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, has implementation/test signal
- acceptance: "command: pytest/eval command output plus fixtures showing positive and negative routing cases."
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T18:04:15+08:00
  - L10: updated: 2026-05-23T18:18:11+08:00
  - L13: architecture_target: skill-graph
  - L16: acceptance_evidence: "command: pytest/eval command output plus fixtures showing positive and negative routing cases."
  - L22: evidence_bundle: /tmp/andrej-karpathy-skills-hermes-adoption-state.json
- risk/follow-up snippets:
  - L15: anti_drift_check: Include cases where simple typo fixes stay lightweight, broad migrations are not blocked, and low-ambiguity tasks do not trigger unnecessary questions.
  - L79: | brain_task_orchestrator list | pending | |
  - L93: - Residual risk:
  - L95: - 2026-05-23T18:04:23+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

## 18. convert-andrej-karpathy-skills-examplesmd-into-optional-hermes-coding-behavior-e
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-23-convert-andrej-karpathy-skills-examplesmd-into-optional-hermes-coding-behavior-e.md
- priority/status/updated: P2 / done / 2026-05-23T18:24:33+08:00
- deterministic_preclass: partial-landed-needs-scope-check
- signals: has not_certified/advisory/ratification-pending signals, contains prototype/candidate/follow-up wording, has implementation/test signal
- acceptance: "command: eval fixture/read-back showing at least four behavior classes and expected outcomes."
- evidence snippets:
  - L5: status: done
  - L9: created: 2026-05-23T18:05:51+08:00
  - L10: updated: 2026-05-23T18:24:33+08:00
  - L13: architecture_target: skill-graph
  - L16: acceptance_evidence: "command: eval fixture/read-back showing at least four behavior classes and expected outcomes."
  - L22: evidence_bundle: /tmp/andrej-karpathy-skills-hermes-adoption-state.json
- risk/follow-up snippets:
  - L81: | brain_task_orchestrator list | pending | |
  - L95: - Residual risk:
  - L97: - 2026-05-23T18:18:11+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

## 19. Long-task management governance for Hermes taskpool handoff and evaluator closure
- file: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-25-吸收长任务管理四原则到-hermes-任务池交接与评价治理.md
- priority/status/updated: P2 / done / 2026-05-26T01:02:18+08:00
- deterministic_preclass: likely-stage-only
- signals: has not_certified/advisory/ratification-pending signals
- acceptance: 产出当前 Hermes 长任务链路对照表；明确 Checkpoint/Progress/Git 三类状态接力落点；定义 Handoff Artifact 必备字段与可执行包验收；补齐 Evaluator 看 diff/证据的独立验收 rubric；给出最小可落地 patch/skill/reference/任务模板更新与验证命令。 ["任务输出必须包含 Handoff Artifact 字段规范、Evaluator 验收 rubric、以及最小验证命令或 proof-gate。"]
- evidence snippets:
  - L5: status: done
  - L8: dependency_order: ["1) 审计现有 continuation/taskpool/handoff/proof-gate 表面; 2) 设计四原则到字段/模板/skill 的映射; 3) 落地最小控制面或模板补丁; 4) 用 evaluator rubric 独立验收 diff 与证据"]
  - L9: created: 2026-05-25T19:08:12+08:00
  - L10: updated: 2026-05-26T01:02:18+08:00
  - L16: acceptance_evidence: 产出当前 Hermes 长任务链路对照表；明确 Checkpoint/Progress/Git 三类状态接力落点；定义 Handoff Artifact 必备字段与可执行包验收；补齐 Evaluator 看 diff/证据的独立验收 rubric；给出最小可落地 patch/skill/reference/任务模板更新与验证命令。
  - L19: multimodel_reason: P2 evolution task touching Hermes taskpool/handoff/evaluator lifecycle gates; needs real external-model certification before done to avoid self-approved governance changes.
- risk/follow-up snippets:
  - L39: checkpoint_states: ["task_created", "multimodel_certified", "pending_execution_evidence"]
  - L98: | brain_task_orchestrator list | pending | |
  - L112: - Residual risk:
  - L114: - 2026-05-25T19:08:39+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim
