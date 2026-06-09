---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: codebase-knowledge-graph
dependency_order: ["1) 核验 safishamsi/graphify GitHub 与 raw README/pyproject/SECURITY 元信息，确认默认分支 v8、PyPI 包 graphifyy、CLI graphify -> 2) 阅读 README/docs/graphify 源码中的 install/hermes/MCP/hook/global/prs/query/export 路径，列出写入面与权限面 -> 3) 提取 tree-sitter 多语言、GraphRAG、MCP stdio、PR impact、callflow、global graph、watch/update 的机制证据 -> 4) 对比 Hermes 现有 code-intel.py/search_files/taskpool evidence/browser-harness 验证链路，识别互补点而非替代真相 -> 5) 安全评估 URL ingest、LLM 后端、凭据/私有代码外传、git hook、graphify-out 提交、MCP 访问路径、prompt injection -> 6) 设计隔离临时目录 PoC 与清理命令，输出 adopt/defer/reject 和是否需要独立 Hermes skill/adapter。"]
created: 2026-05-22T13:52:04+08:00
updated: 2026-05-22T14:01:55+08:00
expires_at: 2026-06-12T13:52:04+08:00
project: hermes-agent
architecture_target: LX
capability_delta: 可能为 Hermes 提供本地代码/数据库/基础设施/文档的一体化知识图谱、GraphRAG 查询、PR impact/冲突分析、callflow HTML、全局跨项目 graph、MCP stdio 查询与 Hermes skill 安装参考；长期可吸收到 codebase-intelligence、taskpool evidence、Lark/项目验收、multi-brain 项目导航与变更影响分析。
anti_drift_check: 不得直接在现有 Hermes/Claude/Codex 生产配置执行 graphify install 或 graphify hermes install；不得安装 git hooks、MCP server、watcher、global graph 或提交 graphify-out/；不得把 GitHub stars/营销语当作能力事实；不得把 graph 输出当作唯一真相，必须与 search_files/read_file/测试证据交叉验证；任何 URL/video/PDF ingest 需避免凭据、内网 URL、隐私材料与大文件外传。
acceptance_evidence: 产出 evidence-first 评估文档，包含 GitHub repo 元信息、PyPI/package 名称 graphifyy 与命令 graphify、Stars/Forks/Issues/Tags/Commit/License/Security、安装/卸载/写入面、Hermes 平台 skill 支持证据、MCP stdio server、tree-sitter 语言覆盖、GraphRAG/query/path/explain、PR dashboard/impact、hook/watch/global graph/callflow 能力、隐私/SSRF/路径/XSS/prompt-injection 安全边界、与 Hermes codebase-intelligence/taskpool 的可吸收点、最小无害 PoC 和回滚条件。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: 本地代码知识图谱会影响 Hermes 项目理解、证据链、MCP 权限和隐私边界，需要架构、安全、codebase-intelligence 多视角审查，避免用 graph 输出替代源代码真相或污染现有 agent 配置。
expected_participants: ["codebase-intelligence-architect", "dev-environment-security-reviewer", "taskpool-evidence-reviewer"]
truth_gate: repo-evidence-install-surface-privacy-boundary-and-poC-plan-present
evidence_bundle: "User request 2026-05-22: 分析并添加任务池 https://github.com/safishamsi/graphify. Browser verification 2026-05-22: public repo safishamsi/graphify; title says AI coding assistant skill for Claude Code, Codex, OpenCode, Cursor, Gemini CLI and more; turns folders of code, SQL schemas, R scripts, shell scripts, docs, papers, images, or videos into queryable knowledge graph; app code + database schema + infrastructure in one graph. Observed branch v8, Stars 50.9k, Forks 5.5k, Issues 104, PRs 172, 9 branches, 112 tags, latest commit 076e6b7 about 2 days ago, 511 commits, MIT license, SECURITY.md present. Raw pyproject check: package name graphifyy version 0.8.14, CLI script graphify, Python >=3.10, dependencies include networkx/datasketch/rapidfuzz/tree-sitter and many tree-sitter language grammars; optional extras include mcp, neo4j, pdf, watch, svg, leiden, office, video, LLM backends. README mentions Hermes install platform, MCP stdio server, query/path/explain, PR dashboard, hook install, global graph, callflow HTML. SECURITY says local dev tool, no network calls during graph analysis except explicit ingest; mitigations for SSRF, path traversal, XSS, prompt injection, symlink traversal."
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "Pre-add triage: P2 evolution. Graphify 与 Hermes codebase-intelligence、多脑项目导航、taskpool evidence 和 PR impact 分析高度相关，且仓库明确支持 Hermes 平台；但涉及安装 skill、MCP stdio、git hook、watcher、URL/video/PDF ingest 与可能的代码/隐私外传，先做安全架构与写入面评估，不直接集成。"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260522-055510-264113-p5383-860012d9-50ca44f3/discussion_result.json
multimodel_last_checked_at: 2026-05-22T14:01:55+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260522-055510-264113-p5383-860012d9-50ca44f3/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-22-评估-safishamsi-graphify-对-hermes-代码知识图谱多脑项目导航与-taskpool-evidence-的可吸收增量-state.json
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
parallel_boundary: 可与文档/源码静态审查、隔离临时目录 dry-run 并行；不得与 Hermes/Claude/Codex 生产 skill 安装、MCP 注册、git hook 安装、watcher 启动、global graph 写入、真实项目 graphify-out 提交并行；任何对真实 work 项目或 ~/.hermes 的安装/写入必须另建任务并人工确认。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-055212-317483-p3636-e5feb0c7-78dbc09b/discussion_result.json"
  - proof:sha256:68314b6f4386703434ed0ffc23b7b7fd74bdcd89873bbc3e2fdb80f9ad338586
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-055510-264113-p5383-860012d9-50ca44f3/discussion_result.json
concepts: ["graphify", "graphifyy", "knowledge-graph", "GraphRAG", "tree-sitter", "codebase-intelligence", "MCP", "Claude Code", "Codex", "Hermes", "PR-impact", "callflow", "global-graph"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#347"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 评估 safishamsi/graphify 对 Hermes 代码知识图谱、多脑项目导航与 taskpool evidence 的可吸收增量

## Objective

判断 safishamsi/graphify 是否值得进入 Hermes codebase-intelligence、多脑项目导航与 taskpool evidence 技术雷达，重点评估其本地代码/文档/数据库/基础设施知识图谱、GraphRAG 查询、MCP stdio、PR impact、callflow/global graph 与 Hermes 平台 skill 对长期项目理解和变更影响分析的可吸收增量。

## Acceptance Criteria

- [ ] Task note exists with capability_delta/anti_drift_check/acceptance_evidence; first execution is safety-first repo/install-surface/privacy-boundary evaluation only, with no production Hermes/Claude/Codex config mutation.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-22T13:52:04+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-22T13:52:12+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-22T13:52:12+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-22T14:00:11+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-055212-317483-p3636-e5feb0c7-78dbc09b/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T14:00:11+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-055212-317483-p3636-e5feb0c7-78dbc09b/discussion_result.json

- 2026-05-22T14:01:55+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260522-055510-264113-p5383-860012d9-50ca44f3/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-22T14:01:55+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:68314b6f4386703434ed0ffc23b7b7fd74bdcd89873bbc3e2fdb80f9ad338586, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260522-055212-317483-p3636-e5feb0c7-78dbc09b/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260522-055510-264113-p5383-860012d9-50ca44f3/discussion_result.json
