---
name: p10-architecture-self-check
description: "P10 架构自检流水线 — 全栈健康度评估、风险分析、P9任务编制。触发词: 'p10 自检', 'p10 self-check', '架构健康检查', 'architecture health check'。"
license: MIT
---

# P10 Architecture Self-Check — 全栈架构自检

> 季度/事件驱动的全栈架构健康度评估。从参考模型偏差检测到 P9 任务编制。
> 核心原则: 先读模型 → 查健康 → 深挖 → 输出战略 → 委托执行 → Claude Code 外脑验证。

## 触发条件

- 用户说 "p10 自检架构"
- 季度 review（按 timescale-separation 每季度）
- V̇ < -0.05 连续 2 次
- 新类型任务首次出现且现有模型不适用

## 执行序列 (6 步)

### Step 1: 加载参考模型

```
skill_view("p10", file_path="references/reference-model.md")
skill_view("p10", file_path="references/p10-protocol.md")
skill_view("p10", file_path="references/stability-margin.md")
skill_view("p10", file_path="references/timescale-separation.md")
```

### Step 2: 运行健康快照

```bash
# 一体化健康评分 V(t) — 包含 self-test + route + cron + memory
bash ~/.hermes/scripts/p10-health.sh
# JSON 模式:
bash ~/.hermes/scripts/p10-health.sh --json

# 路线分数 (多口径: overall/real_only/synthetic_only/main)
python3 ~/.hermes/scripts/route_store.py summary
python3 ~/.hermes/scripts/route_store.py scores --view main
python3 ~/.hermes/scripts/route_store.py stats  # 四口径 JSON

# Eval 状态
python3 ~/.hermes/scripts/eval-harness.py --status

# Cron 状态 (优先用 cronjob 工具, 其次 jobs.json)
# cronjob(action='list')  # ← 从 Hermes 内调用
# 或者:
python3 -c "
import json, os
p=os.path.expanduser('~/.hermes/cron/jobs.json')
with open(p) as f: data=json.load(f)
for j in (data.get('jobs',data) if isinstance(data,dict) else data):
    print(j.get('name','?'), 'last_run:', j.get('last_run_at','null') or 'null')
"

# Evolve 日志
tail -20 ~/.hermes/logs/evolve.log
```

### Step 3: 深挖审计

```bash
# Skill 膨胀（原始文件数）
find ~/.hermes/skills -name 'SKILL.md' | wc -l

# Skill 治理健康（有效技能数 / alias 去重 / 相似度 / 供应链）
python3 ~/.hermes/scripts/skill-steward.py
# 重点读：
# - 总技能数（不含别名）
# - test coverage
# - 同名冲突
# - 内容重叠 → 建议合并
# - related_skills 覆盖率
# - 供应链安全扫描

# Orphan 检测: 用 Python 扫描所有 SKILL.md 的 skill_view 引用
# 输出未被引用的 skill 列表

# Cron 健康: 检查 last_run_at 全 null 的 job
cat ~/.hermes/cron/jobs.json | python3 -c "..."

# Canary 状态
grep canary_ratio ~/.hermes/config.yaml
ls -la ~/.hermes/skills-staging/
```

### Step 4: 输出 P10 战略文档

按 P10 协议输出五部分：
1. **当前状态 V(t)** — 关键指标 + 判定
2. **Top-5 风险** — P0→P2 分级, 证据 + 缓解
3. **架构审查** — 五维度 (代码架构/技术栈/可扩展性/开发体验/质量基线)
4. **决策记录** — 为什么选 A 不选 B
5. **P9 编制** — 任务分解, 不写 Prompt

写出战略文档: `~/.hermes/notes/p10-strategy-YYYY-MM-DD.md`

### Step 5: Claude Code 外脑验证

```bash
bash ~/.hermes/scripts/self-describe.sh
bash ~/.hermes/scripts/consult-claude.sh
```

读取 `/tmp/hermes-plan.json`, 评估每个 step:
- 拒绝新 cron (避免膨胀)
- 检查是否已有相同配置
- 接受低风险 config_set 和代码修复

### Step 6: P9 执行 → P10 验证

按 `p9` 协议拆解任务, 执行, 然后 P10 层最终验证。

## 常见问题与修复

### Cron 全部未执行 (last_run_at 全 null)

排查顺序:
```
1. hermes cron status            → 看 scheduler 状态
2. grep cron_mode config.yaml    → 必须是 approve (不是 deny)
3. hermes gateway status         → 必须 running
4. hermes gateway install        → 安装 launchd/systemd 服务
5. hermes cron tick              → 手动触发 (会跑全部到期 job, 可能超时)
```

根因组合:
- `cron_mode: deny` → 改为 `approve`
- Gateway 未安装 → `hermes gateway install`
- Gateway 已安装但未启动 → `hermes gateway start`

### 路由名截断/空值

检查 `~/.hermes/agent-hooks/record-trace.sh` 的 route 字段:
```python
# ❌ 原代码: route 硬编码空值
'route': '',

# ✅ 修复: 使用工具名作为路由标识
'route': 'hook:' + d.get('tool_name', 'unknown'),
```

注意: bash heredoc 内嵌 Python -c 不能用 f-string（引号冲突），用字符串拼接。

### 合成 trace 污染观测数据

当观测数据被人工生成的 trace 主导时，eval gate 失去意义。

检测:
```bash
python3 ~/.hermes/scripts/route_store.py summary
# 看 "Real: N traces | Synthetic: M traces" 比例
```

修复流程:
```bash
# 1. 加列
sqlite3 ~/.hermes/route_outcomes.db "ALTER TABLE route_outcomes ADD COLUMN is_synthetic INTEGER DEFAULT 0"

# 2. 更新 route_store.py: append() + CLI --synthetic flag + summary 显示 split

# 3. 回填标签
sqlite3 ~/.hermes/route_outcomes.db "UPDATE route_outcomes SET is_synthetic=1 WHERE route='' OR route='planner-'"

# 4. 未来 trace: hook 写入 is_synthetic=0，手动生成设 is_synthetic=1
```

### Cron 踩踏 (全部在 minute=0)

症状: 所有 11+ cron job 在同一分钟触发 → API rate limit + 并发竞争。

检测:
```bash
# 读 jobs.json，解析 schedule 字段，构建 24h 热力图
python3 -c "
import json
with open('$HOME/.hermes/cron/jobs.json') as f:
    jobs = json.load(f)['jobs']
hours = {h: 0 for h in range(24)}
for j in jobs:
    expr = j['schedule']['expr'] if isinstance(j['schedule'], dict) else j['schedule']
    parts = expr.split()
    h_field = parts[1] if len(parts) >= 5 else '*'
    # parse */N, comma, single values
# 找出 count>=3 的小时 → stampede
"
```

修复:
```bash
# 错开高频小时的 minute 偏移
hermes cron edit <job_id> --schedule "5 0 * * *"    # 从 0 → 5
hermes cron edit <job_id> --schedule "10 0 * * *"   # 从 0 → 10
hermes cron edit <job_id> --schedule "30 * * * *"   # hourly → minute=30
# 重型 job 从 hourly 降为 6h: "0 */6 * * *"
```

### Cron 新增但 `last_run_at` 仍是 null

不要立刻判定 scheduler 坏了。先分两类：

1. **高频 job (≤6h)**: 跨过 2+ 轮应执行窗口仍无 last_run_at → 真正故障
2. **日频 job (每天一次)**: 可能尚未到首次触发时间 — next_run_at 在今晚/明早, last_run_at null 属正常

验证方法:
```bash
# 通过 cronjob 工具获取 (推荐, 可看到完整 last_run_at)
# cronjob(action='list')

# 或解析 jobs.json
python3 -c "
import json, os
p=os.path.expanduser('~/.hermes/cron/jobs.json')
with open(p) as f: data=json.load(f)
for j in (data.get('jobs',data) if isinstance(data,dict) else data):
    last = j.get('last_run_at','null') or 'null'
    nxt = j.get('next_run_at','?')
    name = j.get('name','?')
    print(f'{name:40s} last={str(last)[:19]}  next={str(nxt)[:19]}')
"
```

判断: 3 个高频 job (脑同步/健康监控/canary) 有 recent last_run_at → scheduler 活着。日频 job null → 等待轮次即可。

### Raw skill count 与 effective skill count 不一致

`find ~/.hermes/skills -name 'SKILL.md'` 给的是**原始文件数**，会把 alias stub 也算进去。

治理决策（Dunbar 阈值、冲突数、系统多样性）应以 `skill-steward.py` 的 **总技能数（不含别名）** 为准。

示例:
- raw SKILL.md: 197
- effective skills (excluding aliases): 181

结论:
- P10 报告里两者都可写，但**风险判断用 effective count**。

### 同名 Skill 多副本 ≠ 可直接合并

`find ~/.hermes/skills -name 'SKILL.md'` 可能显示同一 skill 名在多个目录:
- impeccable: 12 副本 (.cursor/, .claude/, .gemini/, .trae/ 等)
- pua/pua-en/pua-ja: 各 4 副本 (root + pua/skills/ + pua/codex/ + pua/codebuddy/)

**先 diff 再决策**: `diff -q root/SKILL.md pua/skills/X/SKILL.md`
- IDENTICAL → 可 symlink 或删除副本
- DIFFER → 故意平台变体，不可安全合并 (需上游库收敛)

### Memory 去重判定: Ghost 识别口诀

读取 `~/.hermes/memories/MEMORY.md` 时，逐条问:
- **Will this fact still be true in 10 sessions?**
- 时变数字 (92 traces, PID 50599, 3kept) → ❌ ghost
- 完成式状态 (Week1→0.85, P0已解) → ❌ ghost  
- 日限定条目 (首次运行今03:00) → ❌ ghost
- 项目约定、工具清单、关键教训 → ✅ durable
- 环境事实 (路径、部署方式) → ✅ durable


配置阈值:
```yaml
# ~/.hermes/config.yaml
hermes:
  evolve:
    min_traces: 30           # 不足 30 traces 拒绝决策
    min_traces_for_action: 30
    min_traces_for_eval: 20
```

验证 trace 量达标:
```bash
python3 ~/.hermes/scripts/route_store.py summary
# 确认 Total >= 30
```

## 输出物

- `~/.hermes/notes/p10-strategy-YYYY-MM-DD.md` — 战略文档
- Memory 更新: 淘汰旧条目, 写入当前状态
- 最终报告: 任务完成度矩阵 + V 变化
- `~/.hermes/logs/health-history.jsonl` — V(t) 历史记录 (由 p10-health.sh 自动追加)

## 核心工具速查

| 工具 | 用途 | 关键命令 |
|------|------|----------|
| `p10-health.sh` | 一体化 V(t) 健康评分 | `bash ~/.hermes/scripts/p10-health.sh [--json]` |
| `route_store.py v2` | 四口径 trace 统计 | `python3 ~/.hermes/scripts/route_store.py stats` → views: overall/real_only/synthetic_only/main |
| `route_store.py v2` | Main 口径评分 | `python3 ~/.hermes/scripts/route_store.py scores --view main` |
| `self-test.py` | 组件完整性检查 | `python3 ~/.hermes/scripts/self-test.py` (隔离DB, 不污染生产) |
| `eval-harness.py` | Eval gate 状态 | `python3 ~/.hermes/scripts/eval-harness.py --status` |

### V(t) 评分公式

```
V(t) = 0.25 × self_test_pass
     + 0.30 × main_pass_rate_7d    (排除 blank/planner- 路由)
     + 0.15 × cron_health          (最近24h运行比例)
     + 0.20 × real_ratio           (1 - synthetic_ratio)
     + 0.10 × gateway_running

Grade: A(≥0.90) B(≥0.75) C(≥0.60) D(<0.60)
```

### route_store.py 四口径

- **overall**: 全部 traces, 含 blank + planner- 污染
- **real_only**: is_synthetic=0 的真实施行
- **synthetic_only**: is_synthetic=1 的合成 traces
- **main**: 排除 blank("") + planner- 路由的净化口径 → **决策用此**

## Pitfalls

1. **`hermes cron tick` 超时**: 会跑所有到期 job, 11 jobs × 60s = 660s。用 `hermes cron status` 确认调度器在线后等自动触发，不必手跑 tick。
2. **patch 工具转义引号**: `patch(mode='replace')` 会把 `"` 转义为 `\"`。在 bash heredoc 场景下改用字符串拼接避免引号问题。
3. **Memory 2,200 字符上限**: P10 自检结果需合并为一条。优先删除 "已完成" 条目腾空间。
4. **self-describe.sh 数据滞后**: 刚修改的 config 可能未反映在 state.json 中。P10 验证时直接用 `hermes cron status` 等实时命令，不要依赖 state.json。

## Related

- `p10` — CTO 战略层协议
- `self-improvement-pipeline` — L0-L5 自进化架构
- `self-evolve-via-claude` — 双脑进化流程
- `stuck-diagnosis` — 卡顿排查（含 cron 调试模式）
- `skill-ecosystem-governance` — Skill 生态治理
