Taskpool: lifecycle_gate forbids advisory-only done; event auto-claim; stale claims→reconcile --write; warning paths update counters; health SOP=dashboard→list→eligibility→reconcile→next→agent_team_controller; Lark dedup=lark_task_guid.
§
UVISA GitHub: 用户端远端目标分支已改为 `main`；任务 PR/工作分支默认从 `origin/main` 派生并以 `main` 为 base。
§
UVISA: 通知分类链 DB type→appCategory()→normalizeCategory()→tab；入/出金只在全部可见查BE映射/DB type/mock。PWA splash #FFF+#1326FD。i18n gaps见 codebase-intelligence refs/uvisa-i18n-audit.md。
§
Taskpool adapter facts: TaskAdapter+Registry+Pipeline; adapters lark/brain/direct; observer.observe(task_id,event,detail) no step; old preflight.check(title,desc); gates require pipeline passed. See taskpool-control-plane skill.
§
Claude Code动态工作流(05-28): LLM编排(无DAG)+大规模并行(数百子agent)+对抗验证+长时运行。Hermes优势=状态机/证据脊柱/策略门控；差距=并行度/LLM分解/长时/对抗(加法性非矛盾)。分析: ~/Desktop/folder/claude-code-hermes-feature-mapping*.json。
§
统一任务池(v1.6.0)@~/hermes-edge-worker/: unified_task_pool.py(SSOT适配器)+edge_worker_executor.py(纯执行器)+unified_api.py(:9003)。三层:决策层(本地大脑SSOT)→执行层(Edge Worker)→API层。
§
JS money: avoid Number/toFixed/floor; preserve API decimal strings and string-truncate/pad to currency precision. Tiny nums may stringify as scientific notation, so keep fixed decimal strings.
§
UVISA RN: repo `/Users/charles/Desktop/folder/work/uvisa-app-2.0-migration`, RN in `apps/mobile/`, PWA baseline in repo `src/` and `/Users/charles/Desktop/folder/work/uvisa-app-2.0`; never use standalone `/work/app` as target.
§
UVISA backend local verification should use JDK 21 (`JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`); Homebrew OpenJDK 26 triggers Lombok/Javac `TypeTag :: UNKNOWN` during Maven compile.