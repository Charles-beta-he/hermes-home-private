# LX: Model Health Monitor (电路断路器 + 评分策略) — Phase 1+2+3 完成

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-architecture/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## LX: Model Health Monitor (电路断路器 + 评分策略) — Phase 1+2+3 完成

agent/model_health.py — 基于电路断路器的 provider 健康追踪，FailoverReason-aware 恢复策略。已全栈集成。

```
4 状态电路断路器:
  CLOSED    → 正常使用
  OPEN      → 跳过 provider
  HALF_OPEN → 允许 1 个探测请求 (锁定防并发)
  DISABLED  → 永久失败 (auth/billing), 需手动 reset

触发条件:
  连续失败 >= 3  → 立即开路 (failure_threshold 可配)
  错误率 >= 40%  → 滑窗20次, 最低5次后才计算
  延迟尖峰 > 3x  → 告警 (不触发断路)

FailoverReason-aware 恢复策略 (agent/error_classifier.py 15类):
  rate_limit     60s base, 2x backoff, cap 3600s (优先用 Retry-After header)
  server_error   30s base, 2x backoff, cap 600s
  overloaded     30s base, 2x backoff, cap 600s
  timeout        15s base, 2x backoff, cap 120s
  auth/billing   → DISABLED (不自动恢复)

紧急模式: 全部 provider 挂掉 → 强制 least-recently-failed 进入探测

持久化:
  rate_limits/model_health_state.json  (快速加载, 每30s刷新)
  logs/model-health.jsonl              (审计日志)
  状态 >1h 未更新 → 自动重置为 fresh

线程安全: threading.Lock + atomic write (tmpfile+rename, 同 nous_rate_guard.py)

7/7 + 4/4 测试通过 (tests/test_model_health.py, 共 11 tests)

Phase 2 集成点 (全部完成):
  ✅ run_agent.py:10371  record_success (API 成功后, latency_ms=api_duration*1000)
  ✅ run_agent.py:11433  record_failure (FailoverReason 分类后, 带 reason)
  ✅ run_agent.py:6969   _try_activate_fallback 循环跳过 OPEN/DISABLED provider
  ✅ run_agent.py:7186   _restore_primary_runtime 检查 primary 健康, 不恢复降级 provider
  ✅ config.yaml:7       model_health 配置段 (9 参数)
  ✅ commands.py:176     /health 命令注册 (Info 类别)
  ✅ cli.py:6251+7146    /health 处理: 无参=健康表, reset <provider>=手动重置

Phase 3 集成点 (评分策略 + 可靠性维度, 全部完成):
  ✅ agent/model_health.py  score_provider() + get_best_provider() + get_provider_scores()
  ✅ agent/model_health.py  record_hallucination() + get_dynamic_reliability() (幻觉追踪)
  ✅ run_agent.py:6980   _try_activate_fallback 动态降级 (静态穷尽后 get_best_provider)
  ✅ cli.py:7170         /health scores 子命令 (评分排序表)
  ✅ tests/test_model_health.py  4 新增测试 (scoring/get_best/latency/task_type)

配置 (config.yaml):
  model_health:
    enabled: true
    failure_threshold: 3
    error_rate_threshold: 0.4
    min_calls_for_rate_check: 5
    latency_spike_threshold: 3.0
    recovery_timeout: 60
    max_recovery_timeout: 3600
    window_size: 20
    flush_interval: 30

多模型设计验证: MiMo(主设计) → Claude Code(8条验证, 全AMEND无REJECT) → 合并
Claude 关键修正: 遵循 nous_rate_guard.py 模式, 集成 FailoverReason, all_open 紧急模式, 探测锁
```
