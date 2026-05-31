Taskpool control plane: lifecycle_gate forbids advisory-only done; event-driven auto-claim; stale claims require reconcile --write; warning-only paths must still update counters; taskpool health SOP=dashboard→list→eligibility-check→reconcile→next→agent_team_controller status; Lark dedup key=lark_task_guid. §
§
UVISA GitHub: `feat/uvisa-2.0` 是远端目标/集成分支(长期分叉 main)；任务 PR 从 `origin/feat/uvisa-2.0` 新建工作分支，base=`feat/uvisa-2.0`，勿把它当 head。
§
UVISA通知中心分类链: DB type→appCategory()→前端normalizeCategory()→tab filter。入金/出金在"全部"可见但"交易"不可见→查(1)后端appCategory映射(2)DB type值(3)前端mock。PWA splash:白#FFF+蓝#1326FD。UVISA i18n gap: TransactionAggregationService timeline硬编码中文, failedReason未i18n, BizException detailMsg覆盖i18n。→codebase-intelligence/references/uvisa-i18n-audit.md。
§
任务池插拔化(05-29): TaskAdapter+TaskRegistry+TaskPipeline, adapters/(lark/brain/direct), observer.observe(task_id,event,detail)无step, preflight.check()旧API(title,desc)非spec, gates需pipeline设passed。→taskpool-control-plane skill。
§
外部框架评估SOP: 已沉淀为skill `external-framework-evaluation`。步骤:(1)架构提取(2)映射Hermes原语+gap(3)迁移价值评估(4)分阶段实施计划。含references/guardrails-evaluation-example.md完整示例。
§
Claude Code动态工作流(05-28): LLM编排(无DAG)+大规模并行(数百子agent)+对抗验证+长时运行。Hermes优势=状态机/证据脊柱/策略门控；差距=并行度/LLM分解/长时/对抗(加法性非矛盾)。分析: ~/Desktop/folder/claude-code-hermes-feature-mapping*.json。
§
统一任务池(v1.6.0)@~/hermes-edge-worker/: unified_task_pool.py(SSOT适配器)+edge_worker_executor.py(纯执行器)+unified_api.py(:9003)。三层:决策层(本地大脑SSOT)→执行层(Edge Worker)→API层。
§
JS pitfall: String(num) produces scientific notation for |num|<1e-7 (e.g. "1.234e-7"). URL params/any string context must use num.toFixed(precision) instead. Number("1.234e-7") parses back fine but intermediate display breaks.