# 补充模式: 多模型基础设施自检 (Multi-Model Infrastructure Self-Check)

Extracted from `/Users/charles/.hermes/skills/p10-architecture-self-check/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## 补充模式: 多模型基础设施自检 (Multi-Model Infrastructure Self-Check)

当需要对 L0-L5 多模型架构做健康审计时，使用以下检查流程。触发词: "多模型自检", "multi-model self-check", "多模型架构修复", "circuit breaker 检查"。

### 七维检查清单

1. **Quorum 截断**: quorum.yaml 中 T2/T3 的 quorum < planners 数量 → 某些模型永远被截断
   ```bash
   python3 ~/.hermes/scripts/consult_models.py status
   # 检查每个 tier: quorum vs len(planners)
   ```

2. **Cold Start 死循环**: model-router 中某模型 0 traces → score=None → exploit 跳过 → 永远 0 traces
   ```bash
   sqlite3 ~/.hermes/route_outcomes.db "SELECT model_chain, COUNT(*) FROM route_outcomes WHERE model_chain != '' GROUP BY model_chain ORDER BY 2 DESC"
   # 任何 quorum.yaml 中列出的模型, 0 调用 = cold start 死循环
   ```

3. **Stale Circuit Breaker**: model_health_state.json 中 circuit=open 但 recent_outcomes 全 true
   ```bash
   python3 -c "
   import json, time
   with open('$HOME/.hermes/rate_limits/model_health_state.json') as f:
       state = json.load(f)
   now = time.time()
   for name, info in state.get('providers', {}).items():
       c = info.get('circuit', 'unknown')
       recent = info.get('recent_outcomes', [])
       sr = sum(1 for x in recent if x) / len(recent) if recent else 0
       opened = info.get('opened_at', 0)
       timeout = info.get('recovery_timeout', 60)
       if c in ('open','half_open') and (now-opened) > timeout and sr > 0.7:
           print(f'STALE: {name} — {c}, success={sr:.0%}, stale={now-opened:.0f}s')
   "
   ```

4. **Gateway 误报**: macOS pgrep -f 不能匹配完整路径 → health 脚本报 down 但 gateway 实际在跑
   ```bash
   # 不能只靠 pgrep -f, 必须同时检查 ps aux
   pgrep -f "hermes.*gateway" || ps aux | grep -q "[h]ermes.*gateway"
   ```

5. **Model Diversity**: 单模型占比 >90% = 多模型印证机制名存实亡
   ```bash
   python3 ~/.hermes/scripts/model-diversity-monitor.py
   ```

6. **Memory 膨胀**: >2200 chars → 需压缩, 先删"已完成"条目
   ```bash
   # 用 memory(action='remove') 逐条清理
   ```

7. **Provider 可用性三层检查**: 只查 shell env 会漏掉 .env 和 CLI session
   ```bash
   python3 ~/.hermes/scripts/model-router.py probe
   ```

### 冷启动修复模式

当某模型 0 traces 陷入死循环时:

1. **Quorum 修复**: 确保模型在 T1/T2/T3 planners 列表中, 且 quorum >= len(planners)
2. **评分预热**: 在 model-router.py score_model() 中加入冷启动 bonus:
   ```python
   # Bonus decays linearly: 0 traces → +0.25, min_traces → +0
   if count < min_traces:
       warmup_bonus = 0.25 * (1.0 - count / max(min_traces, 1))
       base += warmup_bonus
   ```
3. **验证**: `for i in $(seq 1 100); do model-router.py select; done | sort | uniq -c`

### Stale Circuit 修复模式

```python
# 读取 state → 检测 stale → 修复 → 写回
for name, info in state['providers'].items():
    if circuit in ('open','half_open') and time_in_state > recovery_timeout and success_rate > 0.7:
        info['circuit'] = 'closed'
        info['consecutive_failures'] = 0
        info['opened_at'] = 0.0
        info['probe_in_progress'] = False
```

### 多模型思考修复流程

当自检发现多个问题时, 使用多模型思考协议生成修复方案:

1. 准备 state.json (问题列表 + 约束 + 验收标准)
2. 三模型并行: GPT-5.5(工程方案) + DeepSeek(红队) + MiMo(极简审查)
3. Claude 交叉质疑 → 合成最终方案
4. 按依赖顺序执行修复
5. self-test 验证 44/44 保持

### 本地大脑 × 多模型自动化 readiness 审计补充

当用户问“多模型分析自检架构与本地大脑中未自动化的部分”或类似问题时，不要只读 `p10-health` 的 A 分。必须同时区分：核心健康、readiness-gated advisory、fully certified autonomous execution。

最小证据采集：
```bash
bash ~/.hermes/scripts/p10-health.sh --json
python3 ~/.hermes/scripts/self-test.py
python3 ~/.hermes/scripts/consult_models.py status
python3 ~/.hermes/scripts/model-router.py probe
python3 ~/.hermes/scripts/model-diversity-monitor.py --json
python3 ~/.hermes/scripts/model-router.py readiness --json
python3 ~/.hermes/scripts/brainctl.py --json status
python3 ~/.hermes/scripts/brainctl.py --json validate --write-dashboard
python3 ~/.hermes/scripts/local_brain_exhaustive_audit.py --sample-limit 50
python3 ~/.hermes/scripts/local_brain_main_hierarchy_migration_selfcheck.py --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --json
python3 ~/.hermes/scripts/brain_task_idle_runner.py --json --write-state
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --no-state
```

判定规则：
- `p10-health` A + `self-test` PASS 只证明核心健康，不证明自治执行可认证。
- `model-diversity-monitor gate_failed=true` 或 `model-router readiness ok=false` 时，T2/T3 只能输出 `readiness-gated advisory` / `not_certified_for_autonomous_execution`，即使 quorum.yaml 配了 4 个模型。
- `brainctl validate passed=false`、`local_brain_exhaustive_audit stop_gate_pass=false`、或主层级 selfcheck FAIL 时，禁止把本地大脑任务自动 promotion/done；只允许检测、dashboard 标红、修复建议。
- `brain_task_multimodel_loop_runner --dry-run` PASS 只证明 verifier 可验证合成 artifact；未拿到真实 `discussion_result.json` 前，不得称生产级多模型闭环。
- `local-brain-task-dispatch-safe-tick` 若 cron `last_status=error` 但手动运行 exit=0/空输出，优先查 `~/.hermes/cron/jobs.json` 的 `last_error`、`~/.hermes/logs/brain_task_dispatch_tick.jsonl`、以及 no_agent/空输出语义；常见根因包括 cron runtime `[Errno 24] Too many open files`，不是任务池逻辑失败。
- 任务池 `eligibility mode=deny`、`allowlist_empty`、`autorun_disabled`、`kill_switch=true` 通常是正确 fail-closed 姿态，不要当 bug 修成自动执行。

多模型 consult 超时处理：
- 如果 `consult_models.py run ... --discussion` timeout，先按 state 内容/问题文本/`state_hash` 找目标 tick，不要盲目使用最新 tick（可能已有别的并发任务生成更新 tick）。
- 只有 fan-out + `merged_plan.json` 而缺 `discussion_result.json` 时，报告为 weak consensus / not certified；读取 `discussion/round_*/round_summary.json` 提取 unresolved issue ledger。
- 若 round summary 显示 `certification_intent=implementation_required` 但 `patches=[]` 或 severity>=3 unresolved，必须保持 `not_certified`，不能把“问题被证实”升级为“方案已认证”。

输出优先级模板：
- P0：堵假认证/假健康（diversity gate blocker、brain validate/audit stop gate、dispatch cron 可观测性）。
- P1：补真实闭环（certify-only real consult artifact、proof hash 固定路径、resume/timeout verifier、router diversity enforcement）。
- P2：保持 fail-closed 自动推进（idle-runner 只读、autorun 需 allowlist+kill-switch+budget+proof+lease）。

### macOS Pitfalls

- `pgrep -f` 不能匹配 Python 进程的完整路径 → 用 `ps aux | grep` 回退
- `grep -q "a\|b"` 在 macOS BRE 中 `\|` 行为不一致 → 用 `grep -E "a|b"` 或拆两行
- `cat -A` 不存在 → 用 `od -c` 检查字节
