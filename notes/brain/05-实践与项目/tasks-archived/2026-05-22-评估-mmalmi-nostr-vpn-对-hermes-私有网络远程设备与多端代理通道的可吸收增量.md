---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: private-device-connectivity
dependency_order: ["1) 读取 mmalmi/nostr-vpn README、docs/protocol.md、docs/EXPERIMENTS.md、release/平台支持说明并确认 GitHub 只是 mirror/canonical repo 在 git.iris.to -> 2) 提取 Nostr discovery、FIPS data plane、participant allowlist、invite/import、exit-node、WireGuard upstream、MagicDNS、doctor bundle 等机制 -> 3) 对比 Hermes/Rokid/本地脑/外控设备在私有网络、NAT 穿透、远程诊断、可审计连接上的需求 -> 4) 风险评估：VPN/路由权限、密钥与邀请泄露、出口节点滥用、系统服务权限、移动端尚在 hardening -> 5) 输出 adopt/defer/reject 决策和最小无害评估方案，不直接改生产网络"]
created: 2026-05-22T12:41:33+08:00
updated: 2026-05-22T12:50:27+08:00
expires_at: 2026-06-12T12:41:33+08:00
project: hermes-agent
architecture_target: LX
capability_delta: 可能为 Hermes 提供去中心化私有 mesh、NAT 穿透、受邀设备 allowlist、远程诊断 doctor bundle、MagicDNS、出口节点和移动/桌面多端连接参考；长期可用于 Rokid/手机/Mac/家庭设备之间的可审计私有通道设计。
anti_drift_check: 不得把该项目当作普通 VPN 直接安装到生产机器；不得修改本机路由、系统服务、WireGuard/utun/NetworkExtension 或出口节点配置；不得生成/上传真实 Nostr 私钥、邀请链接或设备身份；评估阶段只能做文档/源码/架构审查和无特权 dry-run。
acceptance_evidence: 产出 evidence-first 评估文档，包含 GitHub mirror 与 canonical repo 关系、Star/Fork/Release/License/平台支持、协议与数据面机制、Hermes/Rokid/本地脑可迁移点、明确拒绝/需门禁能力、安全风险与权限边界、最小无害 PoC 条件、验证命令和回滚条件。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: VPN/私有 mesh/远程设备通道影响网络安全和外控权限，需要安全、网络、设备代理多视角审查，避免因工具吸引力直接引入高权限链路。
expected_participants: ["network-security-reviewer", "external-control-reviewer", "rokid-assistant-architect"]
truth_gate: repo-evidence-and-network-safety-boundary-present
evidence_bundle: "User request: add https://github.com/mmalmi/nostr-vpn. Browser verification 2026-05-22: repo public, Star 555, Fork 45, Issues 10, PRs 4, master branch, 70 tags, latest commit fc95430 about 7 hours ago, 843 commits, MIT license. README says GitHub is a mirror; canonical repository is git.iris.to htree://npub1xdhnr9mrv47kkrn95k6cwecearydeh8e895990n3acntwvmgk2dsdeeycm/nostr-vpn. Overview: Rust workspace for Tailscale-style private mesh VPN built around a FIPS-backed data plane; includes nvpn CLI/daemon, Nostr discovery, participant allowlists, NAT helpers, MagicDNS, exit node, WireGuard upstream, native macOS/Linux/Windows/Android/iOS shells, Umbrel and StartOS packages."
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "Pre-add triage: P2 evolution. 项目与 Hermes 长期多端私有连接、Rokid 入口、远程设备可达性相关，但涉及 VPN/路由/密钥/出口节点权限，先做安全架构评估，不进入直接安装。"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260522-044702-640740-p69654-3eb2905c-d2d2f0e7/discussion_result.json
multimodel_last_checked_at: 2026-05-22T12:54:13+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260522-044702-640740-p69654-3eb2905c-d2d2f0e7/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-22-评估-mmalmi-nostr-vpn-对-hermes-私有网络远程设备与多端代理通道的可吸收增量-state.json
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
parallel_boundary: 可与普通资讯/代码阅读并行；不得与生产网络、Rokid 外控、gateway、Telegram 投递或系统 VPN/路由配置改动并行；任何需要 tunnel interface/root/NetworkExtension 的动作必须另建任务并人工确认。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-044141-400215-p65375-5d822cab-99ac8151/discussion_result.json"
  - proof:sha256:9e9b9e347e26b78aceab7c58fa714b1361fcc9aa0c971e31bd47c70e3e17b5a3
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-044141-400215-p65375-5d822cab-99ac8151/discussion_result.json
concepts: ["nostr-vpn", "nvpn", "Nostr", "VPN", "WireGuard", "FIPS", "mesh-network", "remote-device", "Rokid", "private-connectivity"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#333"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 评估 mmalmi/nostr-vpn 对 Hermes 私有网络、远程设备与多端代理通道的可吸收增量

## Objective

判断 mmalmi/nostr-vpn 是否值得进入 Hermes 长期私有连接/远程设备/多端代理技术雷达，重点评估其基于 Nostr discovery 的 Tailscale-style 私有 mesh VPN、FIPS 数据面、WireGuard upstream/exit-node 与多平台原生 shell 对 Hermes/Rokid 入口和本地脑远程可达性的价值。

## Acceptance Criteria

- [ ] Task note exists with capability_delta/anti_drift_check/acceptance_evidence; first execution is a safety-first repo/protocol evaluation only, with no privileged VPN install or route changes.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-22T12:41:33+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-22T12:41:41+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-22T12:41:41+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-22T12:50:07+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-044141-400215-p65375-5d822cab-99ac8151/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T12:50:07+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-044141-400215-p65375-5d822cab-99ac8151/discussion_result.json

- 2026-05-22T12:50:27+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:9e9b9e347e26b78aceab7c58fa714b1361fcc9aa0c971e31bd47c70e3e17b5a3, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-044141-400215-p65375-5d822cab-99ac8151/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-044141-400215-p65375-5d822cab-99ac8151/discussion_result.json

- 2026-05-22T12:54:13+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-044702-640740-p69654-3eb2905c-d2d2f0e7/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
