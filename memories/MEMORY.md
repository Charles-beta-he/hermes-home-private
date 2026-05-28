关键教训: 删前grep+build; 改后test+build; Lark先分类→基础设施扫描→杠杆点分析→执行；横切必须基础设施化；重复要求=继续落地/验证/补测；方案判定按用户目标/长期稳定架构，所有人类模糊描述含提示词都先目标校准。
§
Hermes: 私库`Charles-beta-he/hermes-agent-private`, upstream官方；稳定线`private/main`；SOP在`docs/private/`；norm治理见`hermes norms`/`agent/norm_governance.py`/`agent/norm_write_guard.py`。
§
UVISA: FE `/Users/charles/Desktop/folder/work/uvisa-app-2.0`, Admin `/Users/charles/Desktop/folder/work/uvisa-admin`, BE `/Users/charles/Desktop/folder/work/uvisa-backend`; 原型仅参照不可改；UI任务先pull；Railway `uvisa-test`; BE openjdk@21；Admin凭据在Keychain；C端线上验收优先复用既有登录/session态，不默认查Railway验证码。
§
任务池evolution需capability_delta/anti_drift/evidence；Lark安全设置重定向URL=:8765/callback是OAuth/免登，不证明bot事件回调；MCP Task OAuth若用:3010须同app注册。
§
Hermes MCP RPC 统一经 `_mcp_rpc_call(..., timeout)` 管理超时，安全网 30s；`post-update-check.py --fix` 可修复相关补丁漂移。
§
任务池+Kanban: brain markdown/kanban.db可不同步；覆盖率诊断`python3 ~/.hermes/scripts/kanban_coverage.py --json`，v_state用spawnability-aware分数。taskpool默认parallel,max_agents=3,autorun走--parallel-autorun并按claimed/running boundary去重。
§
多模型: 关键词“多模型式思考”表示应调用真实外部多模型思考，不是单模型多角度模拟；除非用户明确说“不要外调/内部思考”。“多模型式分析”仍按上下文判断。requires_multimodel仅标记。
§
brainctl=`python3 ~/.hermes/scripts/brainctl.py`; put `--json` before subcmd. HTML sidecars use `html build|status|refresh|watch|graph`; refresh script regenerates graph too.
§
Agent COS dashboard: `~/Documents/brain/07-仪表盘/Agent认知操作系统互补矩阵.md`; selfcheck script: `~/.hermes/scripts/agent_systems_engineering_control_plane_selfcheck.py`.
§
多模型canonical IDs: claude-opus-4-7, gpt-5.5, deepseek-v4-pro, mimo-v2.5-pro；Claude Max/Code走`claude-code`/`claude` CLI，`anthropic`是独立额度。路由tiers必须匹配canonical IDs。
§
任务池event hook: task_added默认智能路由auto。P2 evolution/高优先级/cert reasons/显式requires启用多模型，并用--multimodel-task限定新增任务；P3 advisory等轻任务不跑模型；hook内auto-close不嵌套触发cert。
§
personal-hermes-brain备份profiles/scripts/skills；overlay在`~/.hermes/brains`；runtime/personal归hermes-core。dev=工程打通脑：为其他脑补功能/打通/测试/交付后交还。
§
Rokid: 入口脑>适配器>L0快答/L1意图板/L2升级/外控门。SSE ACK 8.5s。Metis API认证用令牌header；写入API返回10001系统异常(查询正常)，可能平台bug或rejected态限制。烟盒MW#25359231
§
Bambu/X2D: 单台有遥测/控制+持续制造语义即可升独立manufacturing脑；external-control管物理动作/凭据/确认/幂等/审计；制造脑管材料/切片/G-code/状态/诊断并提交action_request。