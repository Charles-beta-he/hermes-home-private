# LX-Q: Model Quota Monitor (实时额度可观测性 + quota gate) — 已落地

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-architecture/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## LX-Q: Model Quota Monitor (实时额度可观测性 + quota gate) — 已落地

`~/.hermes/scripts/model_quota.py` — provider quota snapshot 统一层。核心原则：exact / estimated / unobservable 必须分开，unknown 不等于额度充足；但 unknown/unobservable 默认允许路由，只有 `status=exhausted` 做 hard gate。

能力：
- `snapshot_from_headers()` 解析 OpenAI/Anthropic 风格 rate-limit headers：remaining tokens / requests / reset。
- `default_snapshot()` 对订阅/OAuth provider（如 `openai-codex`）标记 `status=unobservable`, `quota_type=subscription_cap`，不伪造剩余额度。
- `record_call()` 持久化到 `state/model_quota_state.json`，审计日志写 `logs/model-quota.jsonl`。
- `probe_deepseek_balance()` 支持 DeepSeek `/user/balance` 余额端点（低频、非 token 调用）。
- CLI：
  - `python3 ~/.hermes/scripts/model_quota.py status --model gpt-5.5 --model claude-opus-4-7`
  - `python3 ~/.hermes/scripts/model_quota.py probe --deepseek --json`

集成点：
- `consult_models.py`：fan-out 前 `filter_planners_by_quota()`，把 `model_quota_snapshot` 与 `skipped_due_to_quota` 注入 state.budget、merged_plan、discussion_result、protocol event；`status --quota` 展示 T0-T3 quota。
- `model-router.py`：`_quota_filter_candidates()` 在 availability 之后 hard-gate exhausted candidates，decision 输出 `quota_exhausted_candidates` 与 `quota_snapshot`；`status --quota` 展示路由候选额度。
- `self-test.py`：新增 `model_quota.py compiles`、`model_quota tests (4/4)`、`model-router quota tests (1/1)`，总 self-test 47/47。

Pitfalls：
1. 不要让模型自己报告额度；额度只能来自 headers / balance endpoint / local tracker / error inference。
2. 不要把 `unknown` 当 `ok`；输出必须保留 observability/source/confidence。
3. 测试中 `model_quota` 会被多个模块 import，`HERMES_HOME` 是 import-time constant；隔离测试需从 `sys.modules` pop 掉旧 `model_quota` 后再导入 router。
4. 传入的 partial quota snapshot 必须 merge `default_snapshot()` 补全 schema，否则输出会缺 `observability` 等字段。
5. `agent/model_health.py` 测试不要用真实 `~/.hermes`: 持久化的 `rate_limits/model_health_state.json` 会让 fresh monitor 从 `HALF_OPEN` 等状态开始。运行相关测试用 `TMP=$(mktemp -d); HERMES_HOME="$TMP" python -m pytest tests/test_model_health.py ...; rm -rf "$TMP"`。

验证：
- `python3 -m unittest test_model_quota.py test_consult_models_integration.py test_model_router_quota.py -v` → 16/16 passed。
- `python3 ~/.hermes/scripts/self-test.py` → 47/47 passed。
- `bash ~/.hermes/scripts/p10-health.sh` → V(t)=0.951 Grade A。
