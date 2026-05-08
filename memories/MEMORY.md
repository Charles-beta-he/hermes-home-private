UI skills installed: taste-skill, impeccable, ui-ux-pro-max, ui-skills(baseline-ui/accessibility/metadata/motion).
§
关键教训: 删除文件前必须 grep 全项目残留引用 + 跑 pnpm build。改文件后要同时跑 test + build 验证。
§
L3-C MCP提案: git_operations→已安装 mcp-git-server.py (6 tools)。http_requests/pkg_manager/python_packages/file_searching→已驳回(工具覆盖或terminal足够)。
§
L2=agent_protocol.py v2.0.0 (可导入模块+symlink, OTel链式关联chain_id/span_id, protocol_messages持久化, ProtocolError异常, try_wrap安全包装, 灵活extract, v1→v2迁移, TypedDict子结构, envelope块, 新verdict: pending/skipped/timeout)。cross-patch.py/ensemble-vote.py已集成。
§
uvisa-app: /Users/charles/Desktop/folder/work/uvisa-app。React19+TS+Zustand；已落地服务/store/i18n/dark/PWA/Sentry/auth。原型同步 workflow 在 react-architecture-migration skill；导航链接修补最易漏。
§
Gateway 配置陷阱: config.yaml 的 platforms 必须顶层；PlatformConfig 用 token 非 bot_token；.env TELEGRAM_BOT_TOKEN 可启用；崩溃后清 gateway.pid/lock。
§
L0-L5+LX架构: trace→bandit router→agent_protocol v2→ensemble-vote→cross-patch/consensus→consult_models v3；LX=model_health电路断路器+model_quota。quorum: T1含DeepSeek, T2/T3 quorum=4。MCP timeout 用 _mcp_rpc_call(lock+wait_for)+_run_on_mcp_loop safety-net。
§
关键教训: bash script 中 `set -euo pipefail` 时禁止 `grep -q` 在管道里 — -q 匹配后立即退出不读 stdin, 发 SIGPIPE(141) 给上游, pipefail 取 max → 整个 if 判 false。改用 `grep ... > /dev/null 2>&1`。
§
consult_models.py 多脑默认是文本评审而非独立工具 Agent；真实性需 orchestrator evidence_bundle/truth_gate 支撑，其他模型用 evidence_requests 请求证据。
§
Skill Graphs 2.0 已落地为 Level 0 审计门: `~/.hermes/scripts/skill-steward.py --graph-check --json` 严格模式 cycle/depth/type violation exit 2，`--warn-only` 可写 `skills/steward/skill-graph-report.json`。当前生产图已治理到 cycles=0、depth_max=4，仍先审计不改 runtime loader。
§
Active brain vault: `/Users/charles/Documents/brain`; iCloud duplicate `/Users/charles/Documents/文稿 - charles的MacBook Pro/brain` symlinks back to canonical. brainctl/sync scripts in `~/.hermes/scripts/`.
§
Agent COS/control-plane brain landing: canonical dashboard `~/Documents/brain/07-仪表盘/Agent认知操作系统互补矩阵.md`; systems-engineering overlay now includes `Agent技能树路由矩阵`, `项目工作记忆模板`, `前端闭环验收标准`, and self-check `~/.hermes/scripts/agent_systems_engineering_control_plane_selfcheck.py` (PASS).