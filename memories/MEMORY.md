UI技能已安装(13个): taste-skill(高品位), impeccable(设计语言), ui-ux-pro-max(UIUX设计+6个子skill), ui-skills(4个: baseline-ui/fixing-accessibility/fixing-metadata/fixing-motion-performance)。
§
关键教训: 删除文件前必须 grep 全项目残留引用 + 跑 pnpm build。改文件后要同时跑 test + build 验证。
§
L3-C MCP提案: git_operations→已安装 mcp-git-server.py (6 tools)。http_requests/pkg_manager/python_packages/file_searching→已驳回(工具覆盖或terminal足够)。
§
L2=agent_protocol.py v2.0.0 (可导入模块+symlink, OTel链式关联chain_id/span_id, protocol_messages持久化, ProtocolError异常, try_wrap安全包装, 灵活extract, v1→v2迁移, TypedDict子结构, envelope块, 新verdict: pending/skipped/timeout)。cross-patch.py/ensemble-vote.py已集成。
§
uvisa-app: /Users/charles/Desktop/folder/work/uvisa-app。React19+TS+Zustand；已落地服务/store/i18n/dark/PWA/Sentry/auth。原型同步 workflow 在 react-architecture-migration skill；导航链接修补最易漏。
§
Gateway 平台配置陷阱: config.yaml 中 platforms: 必须在顶层,不能放在 gateway.platforms: 下 (gateway/config.py line 539 读 yaml_cfg.get("platforms"))。PlatformConfig.from_dict() 用 token 而非 bot_token。替代方案: .env 中设 TELEGRAM_BOT_TOKEN 会通过 _apply_env_overrides 自动启用。调试: 用 Python 直接 load_gateway_config() 验证配置,hermes gateway run -v 看详细日志。gateway.pid/gateway.lock 崩溃后可能有残留 PID。
§
L0-L5+LX架构: trace→bandit router→agent_protocol v2→ensemble-vote→cross-patch/consensus→consult_models v3；LX=model_health电路断路器+model_quota。quorum: T1含DeepSeek, T2/T3 quorum=4。MCP timeout 用 _mcp_rpc_call(lock+wait_for)+_run_on_mcp_loop safety-net。
§
关键教训: bash script 中 `set -euo pipefail` 时禁止 `grep -q` 在管道里 — -q 匹配后立即退出不读 stdin, 发 SIGPIPE(141) 给上游, pipefail 取 max → 整个 if 判 false。改用 `grep ... > /dev/null 2>&1`。