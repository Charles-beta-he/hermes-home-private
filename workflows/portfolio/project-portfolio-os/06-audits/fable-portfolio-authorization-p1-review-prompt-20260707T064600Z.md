你是 Claude Fable 5。请复审用户“授权”后执行的 Portfolio P1 本地修复。只基于证据，不声称执行工具。

授权消费边界：只做本地可逆 metadata/readback/CLI contract 修复；未外发、未push/deploy、未改项目代码、未恢复 validated 状态，除非当前证据足够。

修复摘要：
- 给全部 project profiles 补 `portfolio_profile: true`，修复 Hermes CLI `hermes portfolio --json` 的 contract drift。
- 给 UVISA 补 `portfolio_code_guard`，保护 work-project code boundary。
- 给 work-project exemption 增加 reason + review_after=2026-08-07。
- semantic_audit 增加 exemption review date 检查和 evidence_freshness 字段。
- 创建 Hermes CLI strict verify 所需 Portfolio OS SSOT docs/status/receipt，内容声明为本地 metadata/operator-surface receipt，不声称生产部署。
- 对 control-console/router/self-extension 只附 readback，不恢复 previous validated 状态：
  - control-console: portfolio CLI readback green, 但仍需 actual desktop/runtime/browser/UI readback。
  - router: gpt-5.5 smoke pass, 但输出含 Hermes verification gate 未认证，故不恢复 validated。
  - self-extension: mission board readback显示 paused/ticks exhausted，故不恢复 active validated。

验证：
- hermes portfolio --json: ok true, profile_count=16, doctor errors=0 warnings=0
- hermes portfolio verify --json: ok true, errors=0 warnings=0
- portfolio_os_verify.py: ok true
- portfolio_semantic_audit.py --fail-on-warning: ok=True, coverage=100.0, dimensions=16, counts={'error': 0, 'warning': 0, 'info': 0}, findings=[]
- tests/hermes_cli/test_portfolio_os.py: 7 passed
- JSON readback: pass

Router smoke tail:
{"ts": "2026-07-07T06:39:30Z", "run_id": "77d146f4", "iteration": 1, "model": "gpt-5.5", "provider": "openai-codex", "ok": true, "duration_s": 14.985, "tokens_in": 17, "tokens_out": 24, "cost_usd": 1e-08, "route": "probe:smoke", "task_id": "smoke-77d146f4-1-gpt-5.5", "error": "session_id: 20260707_143918_7ba577", "output_preview": "ACK\n\n[Hermes verification gate] 门禁未认证：不能声明已完成/已验收；需要补充客观证据和独立 verifier vote 后再提升为 certified。"}
{"status": "pass", "models": 1, "passed": 1, "run_id": "77d146f4"}


Mission board excerpt:
[
  {
    "cron_installed": false,
    "direction": "ERG high-risk mission lifecycle smoke 20260630",
    "mission_id": "msn_20260630_140834_01dd4046",
    "needs_user": false,
    "next_step": "hermes mission resume msn_20260630_140834_01dd4046",
    "open_decision_id": null,
    "stage": "intake",
    "status": "paused",
    "ticks_max": 1,
    "ticks_used": 0
  },
  {
    "cron_installed": true,
    "direction": "Hermes 自身架构长期自推进：我只给高抽象方向；Hermes 负责研究、拆解、执行、验证、沉淀；遇到价值判断、权限升级、不可逆风险、外部副作用、证据不足或路线分歧时，生成 Human Intervention Packet 交给我选择后再继续。",
    "mission_id": "msn_20260610_120149_27c88cfc",
    "needs_user": false,
    "next_step": "hermes mission resume msn_20260610_120149_27c88cfc",
    "open_decision_id": null,
    "stage": "intake",
    "status": "paused",
    "ticks_max": 72,
    "ticks_used": 72
  }
]


请输出中文 800 字以内：
1. 系统审核
2. 架构审核
3. 多角度审核
4. 是否 PASS（限定域）
5. 是否正确没有恢复 validated 状态
6. 剩余边界。