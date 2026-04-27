UI技能已安装(13个): taste-skill(高品位), impeccable(设计语言), ui-ux-pro-max(UIUX设计+6个子skill), ui-skills(4个: baseline-ui/fixing-accessibility/fixing-metadata/fixing-motion-performance)。
§
关键教训: 删除文件前必须 grep 全项目残留引用 + 跑 pnpm build。改文件后要同时跑 test + build 验证。
§
L0-L5自进化体系: route_outcomes(SQLite, is_synthetic列), record-trace hook(fix空路由→hook:toolname), bandit router, eval-harness(baseline/v2, staging 2 skills), canary(ratio=0.1, router入staging, 6h评估)。auto_approve已定义(enabled=false, 需real≥50+canary 7d)。双脑自进化: self-describe→consult-claude→apply-plan→eval-after-apply(自动回滚+3连败kill switch)。cron 03:00每天, 02:00审计互补。self-describe.sh v3已部署(main pass_rate等多口径, schema_version=3)。
§
L3-C MCP提案: git_operations→已安装 mcp-git-server.py (6 tools)。http_requests/pkg_manager/python_packages/file_searching→已驳回(工具覆盖或terminal足够)。
§
p10-health.sh已部署(~/.hermes/scripts/p10-health.sh): V(t)健康评分, 5维度加权(self_test×0.25 + main_pass_rate×0.30 + cron_health×0.15 + real_ratio×0.20 + gateway×0.10), 输出V̇(t)变化率, 历史记录到logs/health-history.jsonl。当前V=0.8157 Grade B。
§
全栈L0-L5: L0=model_chain捕获+backfill; L1=ε-greedy model-router(pricing-aware, 8模型, MiMo off-peak 0.8x); L2=agent-protocol.py v1.0.0; L3=ensemble-vote(majority/weighted/arbiter); L4=互相印证(cross-patch+consensus-check+adversarial); L5=多脑升级(consult-models.sh + consensus-plans.py 4层语义检测 + quorum.yaml Phase0 shadow)。Claude预算日250K保护, T0-T3任务分层。TTS免费路由。
§
项目: gomoku-react pnpm monorepo。教训: 删文件前grep+pnpm build。macOS脚本坑: head -n -1→sed '$d', 无timeout。