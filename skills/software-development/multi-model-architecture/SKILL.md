---
name: multi-model-architecture
description: "多模型/多Agent 全栈架构 L0-L5 — 从模型追踪到多脑自进化。使用 Claude Code 作为架构设计伙伴, Hermes 负责实施。触发词: 多模型, 互相印证, cross-patch, 三模型验证, ensemble, consensus, 模型路由, pricing, 任务分层, 多脑, consult-models, dual-brain"
license: MIT
---

# Multi-Model Architecture — 多模型全栈架构

> L0: 模型追踪 → L1: 模型路由 → L2: Agent协议 → L3: 投票 → L4: 互相印证 → L5: 多脑自进化
> 双脑模式: self-describe → Claude Code -p 设计 → Hermes 落地 → eval gate

## 架构总览

```
L0: Model Traceability    record-trace.sh → route_outcomes.model_chain
L1: Model Router           ε-greedy + pricing-aware + task_tier 过滤 + select_pair
L2: Agent Protocol         agent-protocol.py v1.0.0 结构化通信
L3: Ensemble Vote          majority / weighted / arbiter
L4: Cross-Verification     cross-patch / consensus-check / adversarial / T0-T3分层
L5: Multi-Brain Evolution  N模型独立plan → 4层语义consensus → 交集合并 → apply
```

## 双脑设计→实施工作流 (最关键的模式)

```
Step 1: 采集状态
  写 /tmp/hermes-<topic>-state.json (紧凑 2-3KB, 含 existing_infra + constraints + question)
  
Step 2: Claude Code 设计
  cat state.json | claude -p '...' --output-format json --max-turns 20-25 --allowedTools "Read"
  关键: --output-format json 返回 wrapped 格式:
    {type: "result", result: "```json\n{actual_plan}\n```"}
  需反序列化: json.loads(response) → 从 result 字段提取 inner JSON

Step 3: 解析 plan
  python3 -c "import json,re; d=json.load(sys.stdin); r=d['result']
  m=re.search(r'```json\n(.*?)```', r, re.DOTALL); plan=json.loads(m.group(1))"

Step 4: 创建 todo → 实施 → self-test → health check → 保存 memory
Step 5: 循环直到 plan 中所有 steps 完成

Pitfalls:
  - state.json 不要 > 4KB (Claude 注意力分散)
  - --max-turns 设 20-25 (太少了设计不完整)
  - 不让 Claude 用 Bash/Write (只读 stdin, 设计 only)
```

## L0: Model Traceability

```bash
# record-trace.sh v3 捕获模型 (带 60s TTL 缓存)
MODEL_CACHE="/tmp/.hermes-model-cache"
export HERMES_TRACE_MODEL="$MODEL"
# backfill 历史数据 (不改 is_synthetic)
python3 backfill-model-traces.py
```

## L1: Model Router

model-router.py v2: cost-aware ε-greedy + task_tier + select_pair
score = pass_rate - λ_cost×effective_rate(now) - λ_time×avg_dur
冷启动 ε=1.0, min_traces=10 后降为 0.1

## L4: Cross-Verification

consensus-check.py: AST/JSON 归一化 → hash 比较
cross-patch.py (T2): Producer→Reviewer→Merger (min_patch_conf=0.7)

任务分层: T0(MiMo) T1(+DeepSeek) T2(+Claude arbiter) T3(Claude lead)
用户命令: /quick /verify /3v /arch /budget

## L5: Multi-Brain Evolution

consult-models.sh + consensus-plans.py + quorum.yaml

Plan Schema v1: patch id = sha1(file|op|body) — 确定性, 跨模型可比较
4层语义 consensus: L1 诊断 (0.4) L2 patch overlap (0.3) L3 参数 (0.2) L4 置信度 (0.1)
合并: 交集优先→多数补充→少数仲裁
4阶段: Phase 0 shadow → Phase 1 N=2 → Phase 2 N=3 → Phase 3 steady

## Claude Budget

日 250K/周 800K token 上限, 60% warn 95% block
多脑模式: <$5 排除 Claude, <$20 排除 opus, arbiter $5 独立池

## Pricing

pricing.py: 8模型时间感知, MiMo off-peak 0.8x, TTS 3免费 (auto-expire)

## 关键 Pitfalls

1. Patch ID 必须确定性: sha1(file|op|body), 不含 model_name
2. Claude -p JSON nesting: wrapper→result→fence→inner JSON (双反序列化)
3. state.json 紧凑 (2-3KB): >4KB 分散注意力
4. Provider diversity: select_pair 必须不同 provider
5. Backfill 不改 is_synthetic: 保护 real-only 口径
6. YAML 重复 key: 最后出现覆盖 → grep 重复项
7. Memory 满: 压缩/删除过时条目, 合并重复

## DeepSeek 特殊计费模式 (本次新增)

Promotion 模式: 限时折扣, 自动过期
```yaml
deepseek-v4-pro:
  promotion:
    active: true
    discount: 0.25           # 2.5折
    expires_at: "2026-05-05T15:59:00Z"   # 北京时间 23:59 = UTC 15:59
    promo_input: 0.20
    promo_output: 0.60
```
pricing.py effective_rate(): free > promotion > schedule > base (优先级)
过期自动恢复: datetime.isoformat → now < expires → 才生效

Cache hit: 全系列 1/10 (字段 cache_hit_input/cache_hit_output)
废弃别名: modes: {non_thinking: "deepseek-chat (deprecated)", thinking: "deepseek-reasoner"}

## 日常运维命令 (模型使用可见性)

  python3 model-usage.py              # 摘要 + 最近20条
  python3 model-usage.py --today      # 只看今天
  python3 model-usage.py --model mimo # 过滤
  python3 model-usage.py --cost       # 按花费排序
  python3 model-usage.py --timeline 50

  python3 skill-audit.py              # skill 生态审计 (未引用/stale/stub)
  python3 model-diversity-monitor.py  # per-pair 模型差异性 (趋同告警)
  python3 claude-budget-tracker.py status  # Claude 预算

## 关键 Bug 修复记录

1. main 口径未排除 synthetic: _aggregate() 漏传 synthetic=0
   → 219 main(real) vs 216 main(all) — 7条合成污染
   修复: main = _aggregate(where, params, synthetic=0, exclude_routes=...)

2. self-describe.sh state_hash: 须在 FULL_OUT 写入后计算
   SHA256=$(sha256sum "$FULL_OUT" | cut -d' ' -f1)

## 关联脚本

model-router.py pricing.py claude-budget-tracker.py cross-patch.py
consensus-plans.py consensus-check.py agent-protocol.py ensemble-vote.py
consult-models.sh record-trace.sh route_store.py backfill-model-traces.py
self-describe.sh config/quorum.yaml
model-usage.py skill-audit.py model-diversity-monitor.py   (NEW: 运维工具)

## 验证

- [ ] self-test 24/24
- [ ] model_stats total = stats.overall total (口径一致)
- [ ] main view = 0 synthetic (纯 real-only)
- [ ] model-router candidates 全, pricing 加载
- [ ] Claude budget ok, 日 250K/周 800K
- [ ] consensus exact/dissent 双向通过 (确定性 patch ID)
- [ ] cross-patch merge (高置信应用, 低置信拒绝)
- [ ] promotion 有效期内/外双场景验证
- [ ] V(t) > 0.8, V̇ > 0
