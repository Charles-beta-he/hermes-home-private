---
name: multi-model-architecture
description: Use when the task falls under Multi-Model Architecture — 多模型全栈架构.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - software
    - development
    - multi
    - model
    - architecture
    related_skills:
    - claude-code
    - incremental-implementation
    - loop
    - multi-model-thinking
    - p10-architecture-self-check
    - plan
    - router
---

# Multi-Model Architecture — 多模型全栈架构

## Overview


> L0: 模型追踪 → L1: 模型路由 → L2: Agent协议 → L3: 投票 → L4: 互相印证 → L5: 多脑自进化
> 双脑模式: self-describe → Claude Code -p 设计 → Hermes 落地 → eval gate

## When to Use

- The task falls under Multi-Model Architecture — 多模型全栈架构
- Don't use for: requests that do not need the task falls under Multi-Model Architecture — 多模型全栈架构; choose a more specific child skill or a broader routing skill that actually matches the task.
## 架构总览

```
L0: Model Traceability    record-trace.sh → route_outcomes.model_chain
L1: Model Router           ε-greedy + pricing-aware + task_tier 过滤 + select_pair
L2: Agent Protocol         agent_protocol.py v2.0.0 (可导入模块+symlink, OTel链式关联chain_id/span_id, ProtocolError/try_wrap, 灵活extract, envelope,persistence,v1→v2迁移, 新verdict:pending/skipped/timeout)
L3: Ensemble Vote          majority / weighted / arbiter (execute=True实际调用模型；必须从 pricing.models 解析 provider 并传 hermes chat --provider，避免模型名走默认 provider)
L4: Cross-Verification     cross-patch / consensus-check / consensus-plans (全protocol_emit)
L5: Multi-Brain Evolution  consult_models.py v3 (读quorum.yaml, protocol_emit, TICK_DIR清理, per-planner timeout)
LX: Model Health Monitor   agent/model_health.py — 电路断路器 + FailoverReason-aware 恢复 + 评分排序 (详见下方)
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

任务分层: T0(MiMo quick) T1(Codex/gpt-5.5 + DeepSeek) T2(Codex + DeepSeek + Claude arbiter) T3(Claude lead + Codex + DeepSeek, MiMo fallback)
用户命令: /quick /verify /3v /arch /budget

## OpenAI Codex / gpt-5.5 接入策略

Codex 已作为 OpenAI provider 接入，当前 default model 为 `gpt-5.5`，provider 为 `openai-codex`。订阅口径: **ChatGPT Plus $20/月**（含 Codex seat），边际 token 成本在 pricing 表中按 0 计，subject to `unlimited_subject_to_abuse_protection`。Plus plan: 无限制核心聊天, 2+座位按年计费, SSO/MFA, 数据不用于训练。

推荐职责分层：
- `gpt-5.5` / Codex: codegen 主力、cross-patch producer、T1/T2 实施型 planner、可做 reviewer。
- MiMo: 低成本日常推理、T0 quick、Claude skip 时的备用多样性。
- DeepSeek: 低成本独立 reviewer / sanity check / T1-T2 第二意见。(Key 已生效，可直接调用)
- Claude Opus/Sonnet: P10 架构、关键仲裁、T3 lead；预算不足时降级到 DeepSeek/MiMo。

配置落点：
- `~/.hermes/config.yaml`: `pricing.models.gpt-5.5` provider=`openai-codex`, input/output=0, candidate_groups=[chat, codegen, reviewer, hard_reasoning]。
- `~/.hermes/config.yaml`: `verification.cross_patch.producer_model=gpt-5.5`。
- `~/.hermes/config/quorum.yaml`: Phase 1 actual fan-out 已启用；T1=[gpt-5.5, mimo-v2.5-pro, deepseek-v4-pro]（DeepSeek key 已生效），T2=[gpt-5.5, mimo-v2.5-pro, claude-opus-4-7, deepseek-v4-pro]，T3=[claude-opus-4-7, gpt-5.5, deepseek-v4-pro, mimo-v2.5-pro]。

## L4.5: Evidence-First Truth Gate (consult_models.py v3)

Multi-model consensus is not factual truth. `consult_models.py` now separates model agreement from orchestrator-owned evidence:

- `build_state()` accepts `claims` and `evidence`, and marks `state_owner=main_orchestrator`.
- `build_evidence_bundle()` normalizes claims/evidence and computes per-claim grounding.
- `evaluate_truth_gate()` returns `truth_status`, `can_certify_truth`, unsupported and contradicted claim IDs.
- Planner prompts include `evidence_bundle` and `truth_assessment`; models must emit `evidence_requests` instead of pretending they verified tool facts.
- Ratification fails closed when severity>=3 claims are unsupported or contradicted.
- SPL remains opt-in (`HERMES_MULTI_BRAIN_USE_SPL=1`) so compression cannot silently drop orchestrator state.

CLI pattern:
```bash
python3 ~/.hermes/scripts/consult_models.py state 'question' \
  --claim '{"id":"C-001","text":"self-test is green","severity":4}' \
  --evidence-json '{"id":"E-001","type":"command","summary":"self-test output","supports":["C-001"]}' \
  --out /tmp/mm-state.json
python3 ~/.hermes/scripts/consult_models.py run /tmp/mm-state.json --tier T3 --quorum 4 --discussion --max-rounds 2 --keep
```

Verification:
- `python3 ~/.hermes/scripts/test_consult_models_integration.py` includes evidence/truth-gate regression tests.
- `python3 ~/.hermes/scripts/self-test.py` validates `schemas/evidence-bundle.schema.json`.

## L5: Multi-Brain Evolution

consult-models.sh + consensus-plans.py + quorum.yaml

Plan Schema v1: patch id = sha1(file|op|body) — 确定性, 跨模型可比较
4层语义 consensus: L1 诊断 (0.4) L2 patch overlap (0.3) L3 参数 (0.2) L4 置信度 (0.1)
合并: 交集优先→多数补充→少数仲裁
4阶段: Phase 0 shadow → Phase 1 N=2 → Phase 2 N=3 → Phase 3 steady

### Fan-out Certification Semantics (P1 quorum hardening)

For any tier claiming multi-model validation, `min_quorum` is the certification threshold, not merely a best-effort hint.

Current hardened rule:
```yaml
T1:
  quorum: 3
  min_quorum: 2  # T1 must not certify from a single planner
  planners: [gpt-5.5, mimo-v2.5-pro, deepseek-v4-pro]
  diversity: provider
```

`consult_models.py` should expose a structured `fanout_certification` object in `merged_plan.json`, `discussion_result.json`, phase events, and final output:

```python
def fanout_certification_status(success_count: int, planner_count: int, min_quorum: int, fail_count: int = 0) -> dict:
    if success_count <= 0:
        return {"status": "all_failed", "certified": False, ...}
    if success_count < min_quorum:
        return {"status": "degraded_not_certified", "certified": False, ...}
    return {"status": "fanout_quorum_met", "certified": True, ...}
```

Required semantics:
- `success_count == 0` → `all_failed`, `certified=false`
- `success_count < min_quorum` → `degraded_not_certified`, `certified=false`
- `success_count >= min_quorum` → `fanout_quorum_met`, `certified=true`

Pitfall: T1 with three planners and `min_quorum: 1` lets a single successful model masquerade as multi-model certification. Tests should explicitly assert `T1 min_quorum >= 2` and `fanout_certification_status(success_count=1, planner_count=3, min_quorum=2)` returns `degraded_not_certified`.

## Claude Budget

日 250K/周 800K token 上限, 60% warn 95% block
多脑模式: <$5 排除 Claude, <$20 排除 opus, arbiter $5 独立池

## 双模型架构评分工作流 (Claude Code + Codex)

触发: 用户要求"测试 Claude Code 对架构评分 / 双模型评分 / 盯 Claude token 消耗 / PUA loop 评分"。

### 单次评分

流程:
1. 生成脱敏 state: `/tmp/hermes-<topic>-score-state.json` (2-3KB, 用正则脱敏 api_key/token/password/secret)
2. Claude Code 只读评分:
   ```bash
   cat /tmp/hermes-<topic>-score-state.json | claude -p 'You are Claude Code acting as an external P10 architecture reviewer. Score ... Output ONLY valid JSON ...' \
     --output-format json --max-turns 1 --allowedTools "" > /tmp/claude-<topic>-score.json
   ```
3. 解析: `json.loads(result)` 直接得到 JSON (无需 fence 解析)
4. 报告落盘到 `~/.hermes/notes/`

### PUA Loop 迭代评分

当目标是"评分过 N"时:
1. 建立基线 → 分析最低维度
2. 每轮: fix → self-test → state → Claude Code 评分
3. 若未达标: 让 Claude Code 设计下一轮 fix (双脑模式):
   ```bash
   cat state.json | claude -p 'Design a concrete fix plan. Output JSON with plan[].{id, file, change, test, impact}' \
     --output-format json --max-turns 1 --allowedTools ""
   ```
4. 按 plan 逐个实施 → 验证 → 重新评分
5. 重复直至达标或穷尽

关键经验:
- test_coverage 最敏感: 跨 patch 只有 2 个测试会被严厉扣分 (78→90 需要 10+ 测试)
- model_diversity 需要真正不同的 auth 路径, 不只是 config 列表
- safety 看重 "fail closed + 测试证明": 必须有 rollback 测试
- state 2-3KB 最优; 6KB+ 拉低评分质量
- 评分成本 ~$0.25-0.30/轮; 设计方案 ~$0.27/轮; 5 轮总计 ~$1.66

## Pricing

pricing.py: 多模型时间感知；Codex/gpt-5.5 Plus 订阅边际成本=0但受滥用防护；MiMo off-peak 0.8x；TTS 3免费 (auto-expire)

## 关键 Pitfalls

Detailed `关键 Pitfalls` guidance moved to `references/关键-pitfalls.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
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

3. agent_protocol seq counter: per-chain 非 per-(chain,agent) — 否则不同 agent 在同一 chain 中 seq 均为 1
4. agent_protocol envelope.chain_id: auto-gen 时必须写入 envelope，不能只在 explicitly passed 时写入

## LX-Q: Model Quota Monitor (实时额度可观测性 + quota gate) — 已落地

Detailed `LX-Q: Model Quota Monitor (实时额度可观测性 + quota gate) — 已落地` guidance moved to `references/lx-q-model-quota-monitor-实时额度可观测性-quota-gate-已落地.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## LX: Model Health Monitor (电路断路器 + 评分策略) — Phase 1+2+3 完成

Detailed `LX: Model Health Monitor (电路断路器 + 评分策略) — Phase 1+2+3 完成` guidance moved to `references/lx-model-health-monitor-电路断路器-评分策略-phase-1-2-3-完成.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Model Switch Strategy (多维度加权评分排序 + 可靠性维度)

Detailed `Model Switch Strategy (多维度加权评分排序 + 可靠性维度)` guidance moved to `references/model-switch-strategy-多维度加权评分排序-可靠性维度.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## SPL (Structured Protocol Language) — Token 优化通讯协议

agent/spl.py (1025行) — 用结构化 JSON 替代自然语言 prompt，减少多模型通讯 token 开销。

5 大压缩技术:
  ① 头部压缩: {"hdr":{"role":"vr","op":"vf"}} 替代 "You are a second brain..."
  ② 上下文哈希: {"ctx":{"ref":"sha256:abc123"}} 替代重复发送完整 state
  ③ 响应模板: {"rsp":{"schema":"v1","fields":["verdict","reasoning"]}} 替代 300 词格式描述
  ④ 缩写字典: pl=planner, vr=validator, A=agree, R=reject, rl=rate_limit (40+ 术语)
  ⑤ 分层上下文: T0(50tok) T1(200tok) T2(400tok)

API:
  SPLEncoder().encode_planner_call(model, state, tier, state_hash)
  SPLEncoder().encode_vote_call(task, model)
  SPLEncoder().encode_arbiter_call(model, task, verdicts)
  SPLDecoder().decode(spl_msg)
  spl_prompt_for_model(model, question, tier)
  SPLTier.T0 / SPLTier.T1 / SPLTier.T2

Token 节省:
  Planner fan-out: ~1700tok → ~760tok (56%)
  Vote batch:      ~320tok  → ~300tok (6%)
  Compaction:      ~570tok  → ~120tok (79%)
  典型 session:    ~2602tok → ~1177tok (55%)

集成 (已完成):
  ✅ consult_models.py — planner call 前尝试 SPL 编码, 失败回退自然语言
  ✅ ensemble-vote.py  — vote call 前尝试 SPL 编码, 失败回退自然语言

## Claude 访问方式变更 / 当前口径

当前 `consult_models.py` 对 Claude 模型优先走 Claude Code CLI，而不是 Hermes Anthropic adapter：
  当前: `claude -p prompt --model <claude-model> --max-turns 1 --output-format json`
  fallback: 非 Claude / 无 `claude` CLI 时才走 `hermes chat -q ... --provider <provider>`；DeepSeek 仍走 direct API fallback。

原因: Claude Code CLI 使用用户 Claude Max/OAuth session，能避开部分本地 Hermes Anthropic adapter 的 provider/model misroute；同时与“Claude Code 作为多脑 P10 设计/仲裁参与者”的实际决策路径一致。

验证口径:
  - `claude --version` + `claude auth status --text` 确认 CLI/auth。
  - `printf 'ping' | claude -p 'Reply exactly: CLAUDE_CODE_OK' --max-turns 1 --allowedTools ""` 确认 Claude Code print mode 可用。
  - `consult_models.py run <state> --tier T3 --quorum 1 --keep` 后检查 `tick-*/plans/claude-*.json.meta.adapter == "claude-code"`。
  - Discussion/ratification 路径可直接通过 `call_discussion_model('claude-opus-4-7', ...)` 或完整 `--discussion` tick 验证；只有 planner fan-out 不等于完整认证。

双脑工作流中的 Claude Code 调用 (Step 2) 仍用 `claude -p` (需要完整 Claude Code 能力)

## DeepSeek V4 幻觉验证 (2026-04-28)

基础测试 (3题): HTTP 429/RFC 6585 ✅, Python flatten ✅, 概率 2/5 ✅
进阶测试 (7题): 多跳推理 ✅, 逻辑谬误 ✅, 代码调试陷阱 ✅, 认知偏差 ✅, Python版本 ✅, 2024大选 ✅, JSON输出 ✅
总计 10/10 通过

结论: 基础+进阶任务表现正常, 但保持 reliability=0.60 (用户反馈实际使用中幻觉较重)
幻觉高发区: 长上下文窗口、工具调用链、项目级代码生成 (难以用单题测试覆盖)

## 关联脚本

model-router.py pricing.py claude-budget-tracker.py cross-patch.py
consensus-plans.py consensus-check.py agent-protocol.py ensemble-vote.py
consult-models.sh record-trace.sh route_store.py backfill-model-traces.py
self-describe.sh config/quorum.yaml
model-usage.py skill-audit.py model-diversity-monitor.py   (NEW: 运维工具)
agent/model_health.py tests/test_model_health.py           (NEW: 电路断路器+评分策略)
agent/spl.py                                                (NEW: SPL 通讯协议)

## Round 1 硬化 (2026-04-27)

1. cross-patch.py `apply_file_patches` 增加唯一命中检查：`before.count(original)` 必须等于 1，否则报 ambiguous conflict。
2. `cross-patch.py run --apply` 默认要求 `--verify`；无 verify 时 fail closed 返回 `rejected`。可显式 `--force-no-verify` 覆盖。
3. Producer prompt 新增 `patch_id` 字段（sha1(file+original+suggested)）。Reviewer prompt 新增 `approved_patch_ids`。run_cross_patch_actual 用 approved_patch_ids 做交叉验证。
4. 默认 reviewer 不再硬编码，改为 `_select_reviewer_via_router()` 调用 model-router select-pair 动态选择 diverse reviewer。
5. self-test.py 从 24 tests 扩展到 39 tests。

## Round 2-3 (2026-04-27)

6. test_ensemble_vote_integration.py: 6 tests (majority/unanimous/split/weighted/single voter)
7. test_consult_models_integration.py: 6 tests (provider resolution, quorum config, T1 diversity)
8. model-router.py `_model_available()`: preflight provider check, 不可用 provider 自动从候选过滤
9. cross-patch.py: per-run cost cap (max_cost_per_run_usd), cost tracking (latency_ms)
10. cross-patch.py: fuzzy whitespace fallback (exact miss + normalized match → hint)

## Round 4 (2026-04-27, Claude Code 设计方案)

11. test_cross_patch_safety.py: 5 tests (非唯一匹配/apply guard/verify pass/rollback/cost tracking)
12. pricing.py: promo TTL 7 天告警 (PROMO_EXPIRING_SOON logging)
13. model-router.py: `_log_unavailable_provider()` → state/unavailable_providers.jsonl

## Round 5 (2026-04-27, 最终 91 分)

14. _model_available 三层检查: shell env → .env file → Claude CLI auth
15. 正确识别 3 个活跃 provider: openai-codex (OAuth), xiaomi (.env API key), anthropic (Claude CLI)
16. self-test: 44/44 passed, V(t)=0.9682 Grade A

## Round 6 (2026-04-28, 多模型架构系统审计 + 修复)

Detailed `Round 6 (2026-04-28, 多模型架构系统审计 + 修复)` guidance moved to `references/round-6-2026-04-28-多模型架构系统审计-修复.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## PUA Loop 评分迭代工作流 (78→91 in 5 rounds)

触发: 用户要求"PUA loop 直至 Claude Code 评分过 90"。

流程:
1. 建立基线评分 (Claude Code --max-turns 1 --allowedTools "")
2. 分析最低维度 → 聚焦修复
3. 每轮: 修复 → self-test → 更新 state (2-3KB) → Claude Code 评分
4. 若 <90: 让 Claude Code 设计下一轮 fix plan (双脑模式)
5. 重复直至 ≥90

关键经验:
- Claude Code 评分对 test_coverage 最敏感: 跨 patch 只有 2 个测试会被严厉扣分
- model_diversity 需要真正不同的 auth 路径 (OAuth/API key/CLI session), 不只是 config 列表
- 安全维度看重"fail closed + 测试证明": --apply requires --verify 必须有测试覆盖 rollback
- state.json 2-3KB 最优; 6KB+ 会拉低评分质量
- Claude Code 评分成本 ~$0.25-0.30/轮; 设计方案 ~$0.27/轮

## Provider 可用性三层检查

`_model_available()` 必须检查三层, 不能只看 shell env:
1. `os.environ.get(env_var)` — shell 环境变量
2. `~/.hermes/.env` 文件解析 — hermes 启动时加载
3. CLI 工具认证 — `shutil.which("claude")` 检测 Claude CLI session

已知 provider auth 路径:
- openai-codex: OAuth device code (hermes auth)
- xiaomi: API key in .env
- anthropic: Claude CLI session (独立于 ANTHROPIC_API_KEY)
- openrouter: OPENROUTER_API_KEY (当前未设置 → 自动过滤)

## Verification Checklist
- [x] self-test 44/44
- [x] test_cross_patch_safety 19/19 (原有5 + Phase 4.5 selector mock 14)
- [x] eval-harness classify_infra_failure: 5 类全部已验证 (ok/timeout/auth/unavailable/dry_run)
- [x] eval-harness baseline: 85/85 prompts 已填充 (DeepSeek API, pass_rate=100%, keyword_hit=93.2%)
- [x] Phase 6 cron registered: multi-brain-consult-models-nightly (01:00 daily)
- [x] Claude Code 严格评分 91/100 (2026-04-27, 5轮 PUA loop: 78→86→86→89→91)
- [ ] model_stats total = stats.overall total (口径一致)
- [ ] main view = 0 synthetic (纯 real-only)
- [ ] model-router candidates 全, pricing 加载
- [ ] Claude budget ok, 日 250K/周 800K
- [ ] consensus exact/dissent 双向通过 (确定性 patch ID)
- [ ] cross-patch merge (高置信应用, 低置信拒绝)
- [ ] promotion 有效期内/外双场景验证
- [ ] V(t) > 0.8, V̇ > 0

## 关联 Skill

- multi-model-thinking: 多模型思考协议 (设计→验证→合并，避免单模型盲信)
- p10-architecture-self-check: P10 架构自检
- incremental-implementation: 增量实施策略

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
