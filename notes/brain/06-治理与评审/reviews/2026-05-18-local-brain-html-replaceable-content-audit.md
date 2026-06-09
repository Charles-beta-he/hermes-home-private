# 本地大脑 HTML 可替换/可增强内容审计

- generated_at: 2026-05-18T15:42:44+08:00
- brain: `/Users/charles/Documents/brain`
- markdown_files_scanned: 548
- html_files_found: 1
- candidate_threshold: score >= 12
- candidates_found: 153

## 结论边界

- 不建议用 HTML 替换任务池 canonical Markdown。Markdown 仍负责状态、diff、机器编辑、proof gate。
- 建议对高密度只读内容生成 HTML sidecar：仪表盘、矩阵、评审地图、研究报告、项目导航、PR review map。
- HTML 文件必须反链源 Markdown/JSON，并在源 Markdown evidence 中登记，避免双写漂移。

## 当前已有 HTML 文件

- `05-实践与项目/projects/agent-skill-learning/webapp-testing-playwright-evaluation-2026-05-13/fixtures/local-example.html`

## 优先级分组

### A. 仪表盘/矩阵：最适合生成 HTML sidecar

- count: 7

- score 24 | tables 53 | lines 153 | `07-仪表盘/Agent认知操作系统互补矩阵.md` — Agent 认知操作系统互补矩阵
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=53, dense_status/evidence, long=153l, high_value_path
- score 24 | tables 38 | lines 191 | `07-仪表盘/Agent Team并行任务池方案.md` — Agent Team 并行任务池方案
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=38, dense_status/evidence, long=191l, high_value_path
- score 22 | tables 35 | lines 80 | `07-仪表盘/Agent技能树路由矩阵.md` — Agent技能树路由矩阵
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=35, dense_status/evidence, high_value_path
- score 21 | tables 20 | lines 95 | `07-仪表盘/待完成任务运行态.md` — 待完成任务运行态
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=20, dense_status/evidence, high_value_path
- score 16 | tables 16 | lines 51 | `07-仪表盘/理论覆盖矩阵.md` — 理论覆盖矩阵
  - reasons: dashboard/matrix/overview, table_lines=16, dense_status/evidence, high_value_path
- score 15 | tables 38 | lines 57 | `07-仪表盘/技能生态健康度.md` — 技能生态健康度仪表盘
  - reasons: dashboard/matrix/overview, table_lines=38, high_value_path
- score 12 | tables 0 | lines 149 | `07-仪表盘/待完成任务控制台.md` — 待完成任务控制台
  - reasons: dashboard/matrix/overview, dense_status/evidence, long=149l, high_value_path

### B. 模板：适合新增 HTML 模板变体

- count: 2

- score 18 | tables 31 | lines 98 | `08-模板/项目工作记忆模板.md` — 项目工作记忆模板
  - reasons: dashboard/matrix/overview, table_lines=31, dense_status/evidence, high_value_path
- score 16 | tables 14 | lines 164 | `08-模板/mission-artifact-template.md` — Mission Artifact Template
  - reasons: HTML/artifact, table_lines=14, dense_status/evidence, long=164l, high_value_path

### C. 项目 Profile/Workpad：适合只读导航 HTML

- count: 3

- score 22 | tables 106 | lines 436 | `05-实践与项目/projects/uvisa-app-2.0/Workpad - uvisa-app-2.0.md` — Workpad - uvisa-app-2.0
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=106, dense_status/evidence, long=436l
- score 18 | tables 250 | lines 644 | `05-实践与项目/projects/uvisa-app-2.0/PROJECT-PROFILE-sanitized-reference.md` — UVISA 2.0 Sanitized Project Profile Reference
  - reasons: dashboard/matrix/overview, table_lines=250, dense_status/evidence, long=644l
- score 16 | tables 9 | lines 58 | `05-实践与项目/projects/hermes-local-brain/Project - Hermes Local Brain.md` — Project: Hermes Local Brain
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence

### D. Evidence/评估报告：适合研究报告 HTML

- count: 9

- score 22 | tables 44 | lines 350 | `05-实践与项目/projects/agent-skill-learning/superpowers-composable-evaluation-2026-05-13.md` — Superpowers 可组合开发流程与 TDD/brainstorming 适配评估（deterministic evidence slice）
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=44, dense_status/evidence, long=350l
- score 22 | tables 26 | lines 166 | `05-实践与项目/projects/agent-skill-learning/superpowers-composable-evaluation-2026-05-12.md` — Superpowers 可组合开发流程与 TDD/brainstorming 适配评估
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=26, dense_status/evidence, long=166l
- score 19 | tables 24 | lines 80 | `05-实践与项目/projects/agent-skill-learning/mcp-builder-evaluation-2026-05-13.md` — MCP Builder 四阶段 MCP Server 引导与 Hermes MCP skill 补强评估
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=24, dense_status/evidence
- score 19 | tables 24 | lines 64 | `05-实践与项目/projects/agent-skill-learning/ralph-loop-hook-evaluation-2026-05-13.md` — Ralph Loop Hook 防提前收工与 Hermes PUA/Loop 边界评估 — closeout report
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=24, dense_status/evidence
- score 19 | tables 21 | lines 107 | `05-实践与项目/projects/agent-skill-learning/planning-with-files-evaluation-2026-05-13.md` — Planning with Files — deterministic evidence slice (2026-05-13)
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=21, dense_status/evidence
- score 16 | tables 0 | lines 122 | `05-实践与项目/projects/hermes-self-improvement/evidence/taskpool-boundary-parallel/taskpool-boundary-parallel-advisory-20260510-165557.md` — Taskpool boundary + multi-agent parallel advisory
  - reasons: HTML/artifact, dashboard/matrix/overview, dense_status/evidence, long=122l, high_value_path
- score 14 | tables 23 | lines 84 | `05-实践与项目/projects/agent-skill-learning/skill-creator-evaluation-2026-05-13.md` — Skill Creator 官方元技能与 eval 测试框架适配评估
  - reasons: HTML/artifact, table_lines=23, dense_status/evidence
- score 14 | tables 13 | lines 147 | `05-实践与项目/projects/agent-skill-learning/webapp-testing-playwright-evaluation-2026-05-13.md` — Webapp Testing / Playwright 自动化与截图证据流水线评估
  - reasons: HTML/artifact, table_lines=13, dense_status/evidence, long=147l
- score 13 | tables 18 | lines 102 | `05-实践与项目/projects/agent-skill-learning/planning-with-files-evaluation-2026-05-11.md` — Planning with Files — Evidence-First Evaluation
  - reasons: HTML/artifact, table_lines=18, dense_status/evidence

### E. 治理/评审：适合 review map HTML

- count: 32

- score 22 | tables 27 | lines 118 | `06-治理与评审/reviews/2026-05-07-agent-cos-multimodel-selfcheck.md` — 2026-05-07 - Agent COS Multi-model Self-check Review
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=27, dense_status/evidence, high_value_path
- score 20 | tables 16 | lines 102 | `06-治理与评审/reviews/2026-05-08-openai-symphony-article-task-orchestration-review.md` — OpenAI Symphony 文章对本地大脑任务规划的补充评审
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=16, dense_status/evidence, high_value_path
- score 20 | tables 9 | lines 134 | `06-治理与评审/reviews/2026-05-07-resumable-multimodel-certification-multimodel-selfcheck.md` — 2026-05-07 Resumable Multi-Model Certification Multimodel Selfcheck
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence, long=134l, high_value_path
- score 18 | tables 9 | lines 69 | `06-治理与评审/技能生态/冲突检测与合并协议.md` — 冲突检测与合并协议
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence, high_value_path
- score 18 | tables 8 | lines 87 | `06-治理与评审/reviews/2026-05-08-local-brain-doc-function-closure-repair-review.md` — 本地大脑文档-功能闭环多模型修复记录
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=8, dense_status/evidence, high_value_path
- score 18 | tables 7 | lines 66 | `06-治理与评审/reviews/2026-05-06-hierarchy-rewrite-vs-overlay-review.md` — 2026-05-06 Hierarchy Rewrite vs Overlay Review
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=7, dense_status/evidence, high_value_path
- score 16 | tables 24 | lines 77 | `06-治理与评审/reviews/2026-05-06-multimodel-thinking-keypoint-coverage-review.md` — 多模型思考关键点覆盖复审
  - reasons: HTML/artifact, table_lines=24, dense_status/evidence, high_value_path
- score 16 | tables 0 | lines 201 | `06-治理与评审/reviews/2026-05-08-local-brain-residue-repair-multimodel-review.md` — Review - 本地大脑残留与闭环修复流程
  - reasons: HTML/artifact, dashboard/matrix/overview, dense_status/evidence, long=201l, high_value_path
- score 16 | tables 0 | lines 226 | `06-治理与评审/reviews/2026-05-12-keypoint-coverage-ratchet-engineering-review.md` — 关键点覆盖棘轮：工程实现/测试评审
  - reasons: HTML/artifact, dashboard/matrix/overview, dense_status/evidence, long=226l, high_value_path
- score 16 | tables 0 | lines 183 | `06-治理与评审/reviews/2026-05-09-pua-loop-agent-frameworks-and-idle-runner-round1.md` — 2026-05-09 PUA-loop Round 1 — Agent-S / Agent-Reach / idle-runner 全线推进
  - reasons: HTML/artifact, dashboard/matrix/overview, dense_status/evidence, long=183l, high_value_path

### F. 任务 Markdown：通常不替换 canonical，仅可生成 task-brief HTML

- count: 50

- score 22 | tables 52 | lines 228 | `05-实践与项目/tasks/_temporarily_removed_lark_tasks/20260513-204908/2026-05-12-uvisa-online-ui-regression-batch-closed-lark.md` — Task - UVISA 线上 UI 回归测试（覆盖 2026-05-12 已闭 Lark 批次）
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=52, dense_status/evidence, long=228l
- score 20 | tables 15 | lines 193 | `05-实践与项目/tasks/2026-05-10-增强本地任务池任务边界与多agent并行处理.md` — Task - 增强本地任务池任务边界与多Agent并行处理
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=15, dense_status/evidence, long=193l
- score 19 | tables 11 | lines 177 | `05-实践与项目/tasks/2026-05-17-分析外部仓库-galaxy-s10-billd-desk-的任务池价值与落地优先级.md` — Task - 分析外部仓库 galaxy-s10/billd-desk 的任务池价值与落地优先级
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=11, dense_status/evidence, long=177l
- score 19 | tables 11 | lines 155 | `05-实践与项目/tasks/2026-05-10-mission方法论p0任务池-mission-envelope-schema--selfcheck-fail-closed.md` — Task - Mission方法论P0：任务池 Mission Envelope schema + selfcheck fail-closed
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=11, dense_status/evidence, long=155l
- score 19 | tables 10 | lines 121 | `05-实践与项目/tasks/2026-05-08-多模型分析-panniantong-agent-reach-并给出-hermes-优化方案.md` — Task - 多模型分析 Panniantong/Agent-Reach 并给出 Hermes 优化方案
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=10, dense_status/evidence, long=121l
- score 19 | tables 10 | lines 193 | `05-实践与项目/tasks/2026-05-10-多模型分析-agent-development-kit-图片并将-hermes-优化方案落地.md` — Task - 多模型分析 Agent Development Kit 图片并将 Hermes 优化方案落地
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=10, dense_status/evidence, long=193l
- score 18 | tables 15 | lines 119 | `05-实践与项目/tasks/2026-05-06-local-brain-empty-directory-audit.md` — 2026-05-06 本地大脑空白目录审计
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=15, dense_status/evidence
- score 18 | tables 9 | lines 129 | `05-实践与项目/tasks/2026-05-10-mission方法论p2proof-gated-auto-claim-and-handoff-mission-runner-集成.md` — Task - Mission方法论P2：proof-gated auto-claim-and-handoff Mission runner 集成
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence, long=129l
- score 18 | tables 9 | lines 151 | `05-实践与项目/tasks/2026-05-10-mission方法论p1local-first-mission-artifacts-与知识图谱沉淀.md` — Task - Mission方法论P1：local-first Mission artifacts 与知识图谱沉淀
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence, long=151l
- score 18 | tables 9 | lines 131 | `05-实践与项目/tasks/2026-05-10-mission方法论p1mission-dag-分解路由与-dashboard-进度视图.md` — Task - Mission方法论P1：Mission DAG 分解、路由与 Dashboard 进度视图
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence, long=131l

### G. Hermes notes/长期方案：适合架构地图 HTML

- count: 20

- score 23 | tables 22 | lines 138 | `99-hermes-notes/evolution/2026-05-06-evidence-first-skill-graphs.md` — Evolution Event: Evidence-First Multi-Brain + Skill Graphs 2.0
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=22, dense_status/evidence, long=138l, high_value_path
- score 22 | tables 127 | lines 273 | `99-hermes-notes/engineering-cybernetics/AGENT-EVOLUTION-PLAN.md` — Agent 控制论进化计划 — 融合钱学森工程控制论
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=127, dense_status/evidence, long=273l
- score 22 | tables 39 | lines 163 | `99-hermes-notes/engineering-cybernetics/AGENT-EVOLUTION-HANDBOOK.md` — Agent 自我进化系统手册
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=39, dense_status/evidence, long=163l
- score 21 | tables 24 | lines 391 | `99-hermes-notes/evolution/2026-05-09-hermes-v013-update-fusion-plan.md` — Evolution Advisory: Hermes v0.13/update 新增功能与现有体系融合方案
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=24, dense_status/evidence, long=391l
- score 20 | tables 18 | lines 205 | `99-hermes-notes/evolution/2026-05-06-symphony-obsidian-local-brain.md` — Evolution Event: Symphony → Obsidian Local Brain Control Plane
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=18, dense_status/evidence, long=205l
- score 18 | tables 98 | lines 317 | `99-hermes-notes/cross-disciplinary-agent-mapping.md` — 跨学科理论 × Agent 进化 — 全景分析与配对评级
  - reasons: dashboard/matrix/overview, table_lines=98, dense_status/evidence, long=317l
- score 15 | tables 15 | lines 131 | `99-hermes-notes/private-branch-upgrade-strategy.md` — Hermes Private Branch Upgrade Strategy
  - reasons: HTML/artifact, table_lines=15, dense_status/evidence, long=131l
- score 15 | tables 15 | lines 124 | `99-hermes-notes/evolution/2026-05-06-multimodel-local-brain-category-landing.md` — Evolution Event: Multi-model Thinking → Local Brain Category Landing
  - reasons: HTML/artifact, table_lines=15, dense_status/evidence, long=124l
- score 14 | tables 22 | lines 87 | `99-hermes-notes/hermes-private-evolution-manifesto.md` — Hermes Private Evolution Manifesto
  - reasons: HTML/artifact, table_lines=22, dense_status/evidence
- score 14 | tables 13 | lines 54 | `99-hermes-notes/reports/FINAL-STATUS-REPORT.md` — Agent Evolution System — 最终状态报告
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=13

### H. 其他候选

- count: 30

- score 19 | tables 21 | lines 86 | `05-实践与项目/实践方案/08-理论到影响全架构传播矩阵.md` — 08 - 理论到影响全架构传播矩阵
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=21, dense_status/evidence
- score 18 | tables 36 | lines 138 | `03-理论与元认知/复杂巨系统理论与Hermes优化方案.md` — 复杂巨系统理论 × Hermes Agent 优化方案
  - reasons: dashboard/matrix/overview, table_lines=36, dense_status/evidence, long=138l
- score 18 | tables 18 | lines 115 | `01-系统与偏好/system/Hermes Local Brain Memory Hierarchy.md` — Hermes Local Brain Memory Hierarchy
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=18, dense_status/evidence
- score 17 | tables 11 | lines 72 | `05-实践与项目/projects/cybernetic-multimodel-intervention/P10 - Long-term Strategy.md` — P10 - Long-term Strategy: Cybernetic Multi-model Intervention
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=11, dense_status/evidence
- score 16 | tables 36 | lines 82 | `05-实践与项目/实践方案/07-关键点多模型介入路由矩阵.md` — 07 - 关键点多模型介入路由矩阵
  - reasons: dashboard/matrix/overview, table_lines=36, dense_status/evidence
- score 16 | tables 21 | lines 169 | `05-实践与项目/missions/2026-05-10-mission-local-first-artifacts-kg.md` — Mission: Mission方法论P1 — local-first Mission artifacts 与知识图谱沉淀
  - reasons: HTML/artifact, table_lines=21, dense_status/evidence, long=169l
- score 16 | tables 9 | lines 56 | `05-实践与项目/projects/agent-systems-engineering-control-plane/Project - Agent系统工程控制面.md` — Project - Agent系统工程控制面
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=9, dense_status/evidence
- score 16 | tables 8 | lines 65 | `05-实践与项目/projects/symphony-inspired-local-task-orchestrator/Project - Symphony-inspired Local Task Orchestrator.md` — Project - Symphony-inspired Local Task Orchestrator
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=8, dense_status/evidence
- score 16 | tables 8 | lines 64 | `05-实践与项目/projects/symphony-inspired-local-task-orchestrator/P10 - Long-term Strategy.md` — P10 - Long-term Strategy
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=8, dense_status/evidence
- score 16 | tables 7 | lines 118 | `05-实践与项目/实践方案/11-Symphony-inspired本地任务编排Playbook.md` — Symphony-inspired 本地任务编排 Playbook
  - reasons: HTML/artifact, dashboard/matrix/overview, table_lines=7, dense_status/evidence

## Top 30 全局候选

| Rank | Score | Tables | Lines | Type | Path |
|---:|---:|---:|---:|---|---|
| 1 | 24 | 53 | 153 | A. 仪表盘/矩阵 | `07-仪表盘/Agent认知操作系统互补矩阵.md` |
| 2 | 24 | 38 | 191 | A. 仪表盘/矩阵 | `07-仪表盘/Agent Team并行任务池方案.md` |
| 3 | 23 | 22 | 138 | G. Hermes notes/长期方案 | `99-hermes-notes/evolution/2026-05-06-evidence-first-skill-graphs.md` |
| 4 | 22 | 127 | 273 | G. Hermes notes/长期方案 | `99-hermes-notes/engineering-cybernetics/AGENT-EVOLUTION-PLAN.md` |
| 5 | 22 | 106 | 436 | C. 项目 Profile/Workpad | `05-实践与项目/projects/uvisa-app-2.0/Workpad - uvisa-app-2.0.md` |
| 6 | 22 | 52 | 228 | F. 任务 Markdown | `05-实践与项目/tasks/_temporarily_removed_lark_tasks/20260513-204908/2026-05-12-uvisa-online-ui-regression-batch-closed-lark.md` |
| 7 | 22 | 44 | 350 | D. Evidence/评估报告 | `05-实践与项目/projects/agent-skill-learning/superpowers-composable-evaluation-2026-05-13.md` |
| 8 | 22 | 39 | 163 | G. Hermes notes/长期方案 | `99-hermes-notes/engineering-cybernetics/AGENT-EVOLUTION-HANDBOOK.md` |
| 9 | 22 | 35 | 80 | A. 仪表盘/矩阵 | `07-仪表盘/Agent技能树路由矩阵.md` |
| 10 | 22 | 27 | 118 | E. 治理/评审 | `06-治理与评审/reviews/2026-05-07-agent-cos-multimodel-selfcheck.md` |
| 11 | 22 | 26 | 166 | D. Evidence/评估报告 | `05-实践与项目/projects/agent-skill-learning/superpowers-composable-evaluation-2026-05-12.md` |
| 12 | 21 | 24 | 391 | G. Hermes notes/长期方案 | `99-hermes-notes/evolution/2026-05-09-hermes-v013-update-fusion-plan.md` |
| 13 | 21 | 20 | 95 | A. 仪表盘/矩阵 | `07-仪表盘/待完成任务运行态.md` |
| 14 | 20 | 18 | 205 | G. Hermes notes/长期方案 | `99-hermes-notes/evolution/2026-05-06-symphony-obsidian-local-brain.md` |
| 15 | 20 | 16 | 102 | E. 治理/评审 | `06-治理与评审/reviews/2026-05-08-openai-symphony-article-task-orchestration-review.md` |
| 16 | 20 | 15 | 193 | F. 任务 Markdown | `05-实践与项目/tasks/2026-05-10-增强本地任务池任务边界与多agent并行处理.md` |
| 17 | 20 | 9 | 134 | E. 治理/评审 | `06-治理与评审/reviews/2026-05-07-resumable-multimodel-certification-multimodel-selfcheck.md` |
| 18 | 19 | 24 | 80 | D. Evidence/评估报告 | `05-实践与项目/projects/agent-skill-learning/mcp-builder-evaluation-2026-05-13.md` |
| 19 | 19 | 24 | 64 | D. Evidence/评估报告 | `05-实践与项目/projects/agent-skill-learning/ralph-loop-hook-evaluation-2026-05-13.md` |
| 20 | 19 | 21 | 107 | D. Evidence/评估报告 | `05-实践与项目/projects/agent-skill-learning/planning-with-files-evaluation-2026-05-13.md` |
| 21 | 19 | 21 | 86 | H. 其他候选 | `05-实践与项目/实践方案/08-理论到影响全架构传播矩阵.md` |
| 22 | 19 | 11 | 177 | F. 任务 Markdown | `05-实践与项目/tasks/2026-05-17-分析外部仓库-galaxy-s10-billd-desk-的任务池价值与落地优先级.md` |
| 23 | 19 | 11 | 155 | F. 任务 Markdown | `05-实践与项目/tasks/2026-05-10-mission方法论p0任务池-mission-envelope-schema--selfcheck-fail-closed.md` |
| 24 | 19 | 10 | 121 | F. 任务 Markdown | `05-实践与项目/tasks/2026-05-08-多模型分析-panniantong-agent-reach-并给出-hermes-优化方案.md` |
| 25 | 19 | 10 | 193 | F. 任务 Markdown | `05-实践与项目/tasks/2026-05-10-多模型分析-agent-development-kit-图片并将-hermes-优化方案落地.md` |
| 26 | 18 | 250 | 644 | C. 项目 Profile/Workpad | `05-实践与项目/projects/uvisa-app-2.0/PROJECT-PROFILE-sanitized-reference.md` |
| 27 | 18 | 98 | 317 | G. Hermes notes/长期方案 | `99-hermes-notes/cross-disciplinary-agent-mapping.md` |
| 28 | 18 | 36 | 138 | H. 其他候选 | `03-理论与元认知/复杂巨系统理论与Hermes优化方案.md` |
| 29 | 18 | 31 | 98 | B. 模板 | `08-模板/项目工作记忆模板.md` |
| 30 | 18 | 18 | 115 | H. 其他候选 | `01-系统与偏好/system/Hermes Local Brain Memory Hierarchy.md` |

## 建议落地顺序

1. 先做 `07-仪表盘/*` 的只读 HTML sidecar，收益最高、状态漂移风险低。
2. 再做 `06-治理与评审/reviews/*` 的 review-map HTML，用于快速看风险/证据/结论。
3. 再做项目 profile/workpad 的导航 HTML，但源数据仍保留 Markdown。
4. 最后才考虑任务级 HTML brief；任务状态禁止迁移到 HTML。
