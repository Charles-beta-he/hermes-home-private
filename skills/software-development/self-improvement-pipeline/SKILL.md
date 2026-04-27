---
name: self-improvement-pipeline
description: "自进化管线 — L0-L5 完整架构。自动挖取需求、按 bandit score 选最优路线、eval harness 准入、灰度放量。全部基于 Hermes 原生能力构建。触发词：'自进化', '自进化管线', '自优化 pipeline', 'self-improvement pipeline', '改进信号', 'autopsy', 'evolution baseline', 'l0-l5', '自进化架构'。"
license: MIT
---

# Self-Improvement Pipeline — 自进化优先调度层 (L0-L5)

> 自动挖取改进需求、按 bandit score 选最优路线、eval 准入门。
> 核心原则: **不重造轮子 — 用 Hermes 原生能力 (hooks/cron/sqlite/skills/config) 填补缺口。**

## Architecture

```
L0 执行层:  拉源 → triage → router(选skill) → exec → verify
L1 观测层:  shell hook 自动写入 trace → route_outcomes SQLite
L2 短环层:  router skill (多臂老虎机, e-greedy 90/10)
            score = pass_rate - 0.1*cost - 0.01*duration/60
L3 中环层:  离线分析: 路线全灭检测 + 工具模式挖掘 + skill 退化修复
L4 准入门:  eval-harness — 85条基线, 三维比较(pass_rate/cost/duration), 5%阈值
L5 灰度层:  config.yaml canary_ratio + skills-staging/ 目录
```

## Double-Brain 模式 (Hermes ↔ Claude Code)

> Hermes 是执行体 (24/7), Claude Code 是架构师 (强规划)。通过结构化 JSON 通道互通。

### 核心数据流

```
Hermes (执行体)                    Claude Code (架构师)
  │                                      │
  ├─ self-describe.sh → state.json       │
  │  (summary <8K + details file)        │
  │                                      │
  │             state.json ──────────────┤
  │                                      ├─ claude -p --skills plan,architect,critic
  │                                      │   retry×3 with schema feedback
  │    JSON plan (5 steps max) ←─────────┤
  │                                      │
  ├─ apply-plan.sh                       │
  │  drain in-flight → snapshot → apply  │
  │                                      │
  ├─ eval-after-apply.sh                 │
  │  baseline(7d) vs new(1h) →           │
  │  delta < -5%→rollback                │
  │  3连败→暂停cron                      │
  │                                      │
  └─ evolve.log (append-only)            │
```

### 4 个关键补丁 (实战发现, 必须外加)

| # | 补丁 | 触发条件 | 动作 |
|---|------|---------|------|
| 1 | **Degradation path** | claude -p 失败或不可用 | 降级到 self-improvement-pipeline.py 本地规划, 标记 degraded=true |
| 2 | **Retry-with-feedback** | JSON plan schema 不合规 | 注入具体错误信息 (哪个字段缺了), 重试最多 3 次 |
| 3 | **Summary mode** | state.json 超 8K tokens | 输出 summary (<8K) + details_pointer (文件系统), 非原始 dump |
| 4 | **Drain phase** | apply 时 inflight tasks 未完成 | 拒收新 task → wait max 600s → 超时则 abort |

降级模式 key 设计:
- degraded=true → eval 不计入 baseline (不污染统计)
- 3 次连续 degraded → 告警人审 (claude -p 装出问题)
- 降级时 consult-claude.sh 自动 fallback, 调用栈透明

Schema retry feedback 示例:
```
FEEDBACK from previous attempt 1:
- missing 'steps' array
- steps missing required field 'expected_gain'
- step risk must be 'low' or 'med', not 'high'
Re-output JSON plan. Fix ALL of the above errors.
```

Drain 实现关键:
```bash
hermes config set scheduler.accept_new false  # 立即拒新
sleep 30                                        # 给 inflight 缓冲
while [ $(sessions_running) -gt 0 ] && [ $waited -lt 600 ]; do
    sleep 5; waited+=5
done
[ $waited -ge 600 ] && { echo "ABORT: drain timeout"; exit 1; }
# ... apply changes ...
hermes config set scheduler.accept_new true   # 恢复
```

### 终止条件 (写死在编排 skill 中)

| 条件 | 动作 |
|------|------|
| 自描述失败 | abort, 写错误日志, 跳过本轮 |
| plan schema 3 次校验失败 | 降级路径 (#1) |
| snapshot 备份失败 | abort (不允许无网执行) |
| 3 次连续 eval reject | 暂停 evolve cron, 人等审 |
| 3 次连续 degraded | 告警人审 (claude -p 装出问题) |

## Cron 时序链 (11 jobs, 已错开分钟)

```
00:05  每日健康度监控 (V函数)
00:10  自循环优化扫描
00:30  brain-hourly-sync (每小时 :30)
02:00  夜间自主进化审计
02:15  skill-steward-daily-audit
03:00  双脑自进化 ← 核心: describe → consult → apply → eval
04:15  Sun snapshot-GC + evolve.log月归档
05:00  */6h 自进化健康监控告警 (错开至 :05)
09:00 Mon 每周失败模式分析
23:00  PA每日进化触发
*/6h   canary灰度评估 (降频 1h→6h, 省 75% 周期)
```

**关键教训**: 所有 job 默认 minute=0 导致整点踩踏 (00:00 曾有 5 job 并发)。
必须错开到 :05/:10/:15/:30。`hermes cron edit <id> --schedule "5 0 * * *"` 可改。

## 核心经验 (从实战中总结)

### 关于 Hermes 原生能力

| 设计需求 | Hermes 原生 | 实际方案 |
|---------|-------------|---------|
| 持久化 route outcomes | `hermes memory append --table` (不存在) | SQLite route_outcomes.db + WAL mode |
| 自定义 metrics 查询 | `hermes insights --metric` (只读固定指标) | route_store.py CLI (stats/scores/summary) |
| 实时 trace 写入 | shell hook (存在) | record-trace.sh, 需 hooks_auto_accept: true |
| 灰度放量 | config.yaml skills section (存在) | 扩展 skills.canary_ratio |
| 技能版本管理 | 无 staging 概念 | skills-staging/ 目录 + promote 脚本 |

### 采样率策略

Shell hook 接收所有匹配的工具调用, 需要采样避免数据爆炸:
- 启动阶段: 30% 足够训练 bandit
- 稳定阶段: 50% 提供充足统计置信度
- 采样通过 `$RANDOM % 100` 实现, 无需外部依赖

### hooks_auto_accept

非 TTY 环境 (cron/gateway) 必须设置为 true, 否则 hook 即使注册也无法执行:
```yaml
hooks_auto_accept: true
```

### SQLite WAL 模式

route_outcomes.db 被多个进程并发读写:
- shell hook (cron 或每次工具调用)
- route_store.py CLI 查询
- router skill 读取 scores
- WAL mode + synchronous=NORMAL 防止写锁阻塞读

## 脚本清单 (13 个)

| 脚本 | 层 | 位置 | 功能 |
|------|----|------|------|
| `route_store.py` | L1 | `~/.hermes/scripts/` | SQLite 存储 + bandit 评分 CLI |
| `post-session-autopsy.py` | L0 | `~/.hermes/scripts/` | 从 session JSON 挖改进信号 |
| `self-improvement-pipeline.py` | L0 | `~/.hermes/scripts/` | 聚合信号 + 优先级排序 |
| `eval-harness.py` | L4 | `~/.hermes/scripts/` | 85条基线, 三维比较, promote/reject |
| `self-test.py` | 测试 | `~/.hermes/scripts/` | 全组件自动验证 (24项) |
| `l3-route-collapse.py` | L3-B | `~/.hermes/scripts/` | 检测路线全灭 → 提案新 skill |
| `l3-tool-patterns.py` | L3-C | `~/.hermes/scripts/` | 挖掘重复 bash/API → 提案 MCP |
| `record-trace.sh` | L1 | `~/.hermes/agent-hooks/` | shell hook, 50% 采样写入 trace |

## Eval Baseline

位置: `~/.hermes/eval/`
- `baseline-prompts.json` — 85 条测试用例, 12 个 task_class
- `eval-baseline.json` — 基线版本 v2
- `promote-log.jsonl` — 所有 promote 记录

覆盖的 task_class:
feature.frontend(10) | feature.backend(10) | bugfix(5) | refactor(5)
research(5) | devops(5) | config(5) | planning(5)
code_review(5) | testing(5) | documentation(5) | security(5)
data(5) | general(10)

## Gray/Canny 配置

```yaml
# ~/.hermes/config.yaml
evolve:
  canary_ratio: 0.1    # 10% 流量走 staging skills
  canary_log: ~/.hermes/notes/canary-log.jsonl
  auto_approve:
    enabled: false       # 需 real≥50 + canary 7d clean 才能开启
    criteria:
      eval_delta_min: 0.02
      canary_clean_hours: 24
      max_risk_level: med
    guard:
      require_p0_free: true
      require_human: schema_changes,mcp_config,auth_changes
```

## MCP 提案自动审核流水线 (L3-C 实践经验)

当 L3-C 工具模式挖掘生成 MCP 提案后, 完整的审核流程:

```bash
# Step 1: 扫描所有 skill 中的 bash 模式
python3 ~/.hermes/scripts/l3-tool-patterns.py --threshold 15

# Step 2: 读取每份提案
cat ~/.hermes/mcp/proposals/mcp-proposal-*.md

# Step 3: 逐份评估 (三条标准):
#   a. 该模式是否有 Hermes 原生工具已覆盖? (例如 search_files 已存在 → 驳回)
#   b. 是否只是单行 shell 命令? (例如 npm install, pip install → 驳回, terminal 足够)
#   c. 是否值得 MCP 封装的复杂度? (高频 + 多 skills + 结构化操作 → 实施)

# Step 4: 对通过评估的: 编写 MCP server + 注册 config.yaml
# Step 5: 对驳回的: 写 ASSESSMENT.md 留存决策理由
```

### 实际审核案例 (本轮 5 份提案的决策)

| 提案 | 评估维度 | 决策 | 依据 |
|------|---------|------|------|
| git_operations (56x/11skills) | a=未覆盖, b=否(非单行), c=是(高频结构化) | ✅ 实施 | 6-tool MCP server |
| http_requests (38x/13skills) | a=已覆盖(web_search), c=否 | ❌ 驳回 | 重复造轮子 |
| package_manager (16x/11skills) | b=是(单行命令) | ❌ 驳回 | terminal 足够 |
| python_packages (53x/24skills) | b=是(单行命令) | ❌ 驳回 | terminal 足够 |
| file_searching (51x/20skills) | a=已覆盖(search_files) | ❌ 驳回 | 提案自身也说无需封装 |

评估原则:
- 数量多不等于值得 MCP。53 次 pip install 就是 53 个单行命令, MCP 封装反而增加延迟
- 真正需要 MCP 的是**结构性操作**(git commit 带多个参数, 状态检查)而非自动化无关的 shell 单行
- 实施前必须确认提案的 suggestion 是否合理

## Verification

```bash
# 全组件自测
python3 ~/.hermes/scripts/self-test.py

# 查看路线分数 (含 Real/Synthetic 分拆)
python3 ~/.hermes/scripts/route_store.py summary

# Cron 健康一键诊断
hermes cron status && hermes gateway status

# 检查系统健康
python3 ~/.hermes/scripts/eval-harness.py --status
python3 ~/.hermes/scripts/route_store.py summary

# 手动跑一次完整管线
python3 ~/.hermes/scripts/post-session-autopsy.py --recent 10 --write
python3 ~/.hermes/scripts/self-improvement-pipeline.py --write --auto-exec
```

## Pitfalls (实战发现)

1. **Shell hook 仅在非 TTY 需要 auto_accept**: cron/gateway 环境需要提前设置 hooks_auto_accept: true, 否则 hook 静默不执行
2. **SQLite lastrowid 在 Python 3.12+ 行为不同**: `conn.execute().lastrowid` 报错. 改用 `cursor = conn.execute(...); cursor.fetchone()[0]`
3. **YAML frontmatter 中 description 含引号/冒号会解析失败**: 避免在 SKILL.md 的 frontmatter description 中使用双引号、单引号或冒号
4. **工具失败检测误报**: 工具返回 JSON 含 "error": null 作为 key name. 必须解析 JSON 后判断 exit_code 而非正则匹配 raw string
5. **hook 的 matcher 正则影响性能**: 匹配范围过大会每工具调用触发, 消耗 5ms/hook. 用具体 tool_name 限制
6. **ε-greedy 的 ε 不宜超过 10%**: 过高探索导致服务品质波动, 过低导致策略锁死

7. **Cron 全部静默不执行 → 先查 cron_mode 而非进程**:
   - `hermes cron status` 显示 "Gateway is not running — cron jobs will NOT fire"
   - 根因 99% 是 `approvals.cron_mode: deny` (默认值), 不是 scheduler 故障
   - 修复: `cron_mode: approve` + `hermes gateway install` (macOS launchd) + `hermes gateway status` 验证
   - `hermes cron tick` 会同步跑所有到期 job, 11 个 job 超 60s 超时 — 不要用它调试

8. **合成 trace 必须先打标再写入 — 否则污染 eval gate**:
   - 生成合成 trace 提升样本量 → pass_rate 虚高 → eval gate 放行回归 → 恶性循环
   - 正确流程: ALTER TABLE 加 `is_synthetic` → route_store.py 支持 `--synthetic` flag → summary 显示 Real/Synthetic 分拆
   - eval gate 必须用 `min_real_traces` (默认 20) 而非 total traces
   - Claude Code 在 2026-04-26 审计中直接指认为 P0 风险

9. **route_outcomes schema 迁移必须同步更新 4 处**:
   - (a) SQL ALTER TABLE 加列
   - (b) `_ensure_schema()` 的 CREATE TABLE IF NOT EXISTS (新安装用)
   - (c) `append()` 的 INSERT 语句
   - (d) CLI `--synthetic` flag + `append` 传参
   - 遗漏任一处 → 静默失败, 无报错

10. **Auto-approve 标准应写为 config 而非代码判断**:
    - config.yaml `evolve.auto_approve` section: criteria (eval_delta_min, canary_clean_hours, max_risk_level) + guard (require_p0_free, require_human 白名单)
    - 启用前置条件: real_traces≥50, canary 7d clean, dry-run 复现历史决策
    - 当前 enabled=false — 避免过早自动化

## Related Skills

- `router` — 多臂老虎机路线选择器 (L2)
- `pro` — PUA Pro 自进化追踪 (依赖 evolution.md)
- `darwin-skill` — 单个 skill 优化
- `skill-ecosystem-governance` — 生态治理
- `loop` — 迭代执行
