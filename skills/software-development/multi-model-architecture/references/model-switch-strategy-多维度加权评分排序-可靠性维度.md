# Model Switch Strategy (多维度加权评分排序 + 可靠性维度)

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-architecture/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Model Switch Strategy (多维度加权评分排序 + 可靠性维度)

agent/model_health.py 中的 `score_provider()` + `get_best_provider()` — 当 provider 遇到 rate limit 时，动态选择最佳替代。

```
评分公式 (5 维度, sum=1.0):
  score = health(0.35) + capability(0.25) + reliability(0.20) + cost(0.10) + latency(0.10)

权重变更历史:
  v1: health=0.40, capability=0.30, cost=0.20, latency=0.10 (4维)
  v2: health=0.35, capability=0.25, reliability=0.20, cost=0.10, latency=0.10 (5维, 加入幻觉维度)

Provider Profiles (PROVIDER_PROFILES dict):
  openai-codex  cost_tier=1  caps=code,reasoning,chat,codegen,tool_calling,structured_output  reliability=0.90
  anthropic     cost_tier=2  caps=reasoning,code,chat,analysis,long_context                   reliability=0.95
  xiaomi        cost_tier=0  caps=chat,code,speed,cost_efficiency                              reliability=0.75
  deepseek      cost_tier=0  caps=code,reasoning,cost_efficiency                               reliability=0.60 (V4 幻觉较重)

健康评分: CLOSED→1.0, HALF_OPEN→0.5, OPEN/DISABLED→0.0 (短路返回0)
能力评分: task_type → required_caps 匹配率 (code/reasoning/chat/default)
可靠性评分: static baseline from PROVIDER_PROFILES + dynamic hallucination adjustment
  get_dynamic_reliability(): baseline * (1 - hallucination_rate * 2)
  hallucination_rate = hallucination_count / success_count
  hallucination_rate=0 → baseline, 0.1 → baseline*0.8, 0.5 → 0
成本评分: cost_tier 0→1.0, 1→0.65, 2→0.30 (降权到 0.10 避免便宜但幻觉重的模型受益)
延迟评分: <500ms→1.0, <2s→0.5, <5s→0.25, >5s→0.1, unknown→0.7

记录幻觉:
  monitor.record_hallucination("deepseek") → hallucination_count++ → reliability 动态下降
  用途: multi-model cross-check 发现输出不准确时调用
```

任务类型对评分的影响 (实测数据, 全健康时):
  default:   openai-codex(0.915) > xiaomi(0.837) > deepseek(0.723) > anthropic(0.807)
  code:      openai-codex 最强 (codegen+tool_calling 独有)
  reasoning: anthropic 反超 (analysis+reasoning 独有, reliability 最高)
  chat:      xiaomi 登顶 (cost=0 最便宜, 3/3 caps 全中)
  DeepSeek:  reliability=0.60 拉低分数, 排名从并列第2降至第4

动态降级流程 (run_agent.py _try_activate_fallback):
1. 先走静态 fallback_chain，跳过 OPEN/DISABLED
2. 静态 chain 穷尽 → get_best_provider() 从已知 provider 动态选择
3. 排除当前 provider，按综合评分选最优
4. 注入为 synthetic fallback entry 继续降级

/health 命令:
  /health          → 健康状态表 (circuit/err_rate/latency)
  /health scores   → 评分排序表 (score/health/cap/cost/lat)
  /health reset X  → 手动重置 provider

测试: 11/11 passed (7 原有 + 4 新增: scoring/get_best/latency/task_type)
