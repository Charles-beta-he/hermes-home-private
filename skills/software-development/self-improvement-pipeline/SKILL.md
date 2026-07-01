---
name: self-improvement-pipeline
description: Use when the task falls under Self-Improvement Pipeline — 自进化优先调度层 (L0-L5).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - software
    - development
    - self
    - improvement
    - pipeline
    related_skills:
    - darwin-skill
    - design
    - devops
    - loop
    - mcp
    - p10
    - p7
    - p9
---

# Self-Improvement Pipeline — 自进化优先调度层 (L0-L5)

## Overview


> 自动挖取改进需求、按 bandit score 选最优路线、eval 准入门。
> 核心原则: **不重造轮子 — 用 Hermes 原生能力 (hooks/cron/sqlite/skills/config) 填补缺口。**

## When to Use

- The task falls under Self-Improvement Pipeline — 自进化优先调度层 (L0-L5)


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
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

### Architecture Alignment Gate — 自进化必须跟随总体架构方向

自进化不是随机堆功能或看到外部框架就照搬；每个 evolution 版本/任务必须声明它提升了总体架构的哪一层或哪条控制面。默认 north star 是：L0-L5+LX 多模型架构、local-brain taskpool、evidence-first、bounded autonomy、work/evolution 分道、fail-closed closeout。

每个自进化任务进入执行前必须回答并记录：
- `lane`: `work` / `evolution` / `advisory`；work 交付优先，不被 evolution 占用。
- `architecture_target`: L0/L1/L2/L3/L4/L5/LX/local-brain/skill-graph/provider-quota/taskpool 等。
- `capability_delta`: 具体能力提升，例如更准的路由、更低误报、更强证据门、更稳的 cron、更少 ghost signal。
- `anti_drift_check`: 是否违背现有总体方向；是否重复造轮子；是否绕过 evidence gate 或 fail-closed gate。
- `acceptance_evidence`: 测试/自检/usage-score/graph-check/ratification artifact，而不是“模型觉得更好”。

如果无法映射到总体架构方向，默认降级为 `advisory`，不得自动落地为 runtime 改动。

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

## Cron 时序链 (12 jobs, 已错开分钟)

```
00:05  每日健康度监控 (V函数)
00:10  自循环优化扫描
00:30  brain-hourly-sync (每小时 :30)
01:00  multi-brain-consult-models-nightly (Phase 6)
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

## Verification Checklist

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

### Manual trigger runbook (gateway/Telegram request)

Use when the user says “触发自进化 loop”, “run self-evolution now”, or asks to prove a self-improvement tick happened now rather than waiting for the nightly cron.

1. Locate the existing job and scripts before triggering:
   ```bash
   hermes cron list
   test -f ~/.hermes/scripts/self-improvement-pipeline.py
   test -f ~/.hermes/scripts/post-session-autopsy.py
   tail -5 ~/.hermes/logs/evolve.log
   ```
2. Trigger the scheduled self-evolution job by job id (usually the job named `双脑自进化 (Hermes→ClaudeCode→落地→Eval)`):
   ```bash
   hermes cron run <job_id>
   ```
   If using the Hermes cronjob tool, `run` may only move `next_run_at` to “now”. Wait for the scheduler, then re-list until `last_run_at` changes and `last_status=ok`; do not treat `next_run_at` movement alone as proof of execution.
3. Run the deterministic local pipeline as additional evidence and to force fresh signals/action-plan artifacts:
   ```bash
   python3 ~/.hermes/scripts/post-session-autopsy.py --recent 10 --write
   python3 ~/.hermes/scripts/self-improvement-pipeline.py --write --auto-exec
   python3 ~/.hermes/scripts/self-improvement-pipeline.py --preview
   ```
   `--auto-exec` can legitimately record a `kept` evolution closure while saying `No high-ROI actions to execute`; that means the loop generated/updated the queue but did not apply a risky patch.
4. Verify operational health after the tick:
   ```bash
   python3 ~/.hermes/scripts/usage-score.py
   python3 ~/.hermes/scripts/cron-health-quarantine.py
   python3 ~/.hermes/scripts/cron-missed-run-guard.py
   python3 ~/.hermes/scripts/self-test.py
   ```
   Healthy closure target: cron bad_count=0, missed_count=0, self-test all pass. Usage grade can be B if known non-blocking components such as ensemble/ratification corpus are intentionally empty; report the components rather than inflating the grade.
5. If the loop wrote auditable artifacts, commit only scoped evidence files (no push unless explicitly asked):
   ```bash
   cd ~/.hermes
   git add -- logs/evolve.log notes/improvement-action-plan.json notes/improvement-signals.jsonl
   git diff --cached --check
   git diff --cached --unified=0 -- logs/evolve.log notes/improvement-action-plan.json notes/improvement-signals.jsonl  # scan added lines for secrets
   git commit -m "chore(evolve): trigger self-improvement loop"
   git status --short -- logs/evolve.log notes/improvement-action-plan.json notes/improvement-signals.jsonl
   ```
- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side-effects were verified by read-back or direct inspection.
- [ ] The final result still matches the trigger and acceptance shape of this skill.
## Post-trigger audit: distinguish “ran” from “evolved”

Use this when a user asks to analyze a just-triggered self-evolution loop, especially after manual `hermes cron run <self-evolve-job>` or `self-improvement-pipeline.py --write --auto-exec`.

Core class of issue: a self-evolution tick can execute successfully and still fail to produce useful evolution. Treat scheduler success, queue generation, action execution, and performance improvement as separate facts.

Audit checklist:

```bash
# 1. Prove scheduler/script completion only
hermes cron list | grep -A12 -B2 'self-improvement\|自进化\|双脑'

# 2. Prove local queue/action-plan generation
python3 ~/.hermes/scripts/post-session-autopsy.py --recent 10 --write
python3 ~/.hermes/scripts/self-improvement-pipeline.py --write --auto-exec
cat ~/.hermes/notes/improvement-action-plan.json

tail -5 ~/.hermes/logs/evolve.log

# 3. Prove operational health separately
python3 ~/.hermes/scripts/usage-score.py
python3 ~/.hermes/scripts/cron-health-quarantine.py
python3 ~/.hermes/scripts/cron-missed-run-guard.py
python3 ~/.hermes/scripts/self-test.py
```

Interpretation rules:
- `last_status=ok` means the cron script completed; it is not proof that a useful improvement happened.
- `eval_result=kept` in `evolve.log` may only mean the priority queue had items. Check whether any item was actionable/executed.
- If `baseline/new/delta` are constant zeros, do not claim measured improvement. Report this as an observability/verifier gap.
- A HIGH item can be skipped if `roi < actionable_threshold` (currently `roi >= 2.0 and impact >= 4`). This is a triage/gating design issue, not automatically a runtime failure.
- `fix_tool_config` should not auto-edit config based on vague failure aggregates. First generate read-only diagnostics: exact tool, error signature, count, first/last seen, stale status, and current operational health.
- Usage grade can be B even when runtime is green if ensemble/ratification corpus components are missing. Separate `operational_health_grade` from `evidence_readiness_grade` in reports.

Recommended low-risk next implementation slice after this audit:
1. Add action-state ledger fields to closure events: `generated_count`, `actionable_count`, `executed_count`, `pending_review_count`, `skipped_below_threshold_count`, `top_item_roi`, `top_item_impact`, `skipped_reason`, `useful_evolution`.
2. Add read-only `tool-failure-diagnostic-<ts>.json` generation for `fix_tool_config` rather than changing config or thresholds first.
3. Improve autopsy aggregation from detail strings to structured `tool_name`, `error_signature`, `exit_code`, `count`, `first_seen`, `last_seen`, `stale_status`, `suppression_reason`.

When landing this slice, treat it as a governance-code change and close the loop with TDD + evidence-first ratification:
1. Add/extend regression tests before or alongside implementation:
   - `scripts/test_self_improvement_pipeline.py` for action-state ledger and read-only diagnostic schema.
   - `scripts/test_post_session_autopsy.py` for structured `tool_name + error_signature + exit_code` aggregation.
   - `scripts/test_usage_score.py` for `semantic_grades.operational_health` vs `evidence_readiness`, and for certified `tick-*/discussion_result.json` artifacts counting as ratification corpus when `status` is certified, truth gate allows certification, and 2+ models participated.
   - `scripts/test_consult_models_integration.py` for grounding aliases such as `claims_supported` / `supported_claim_ids` and raw unlinked evidence -> `needs_link_review`.
   - `scripts/test_ensemble_vote_integration.py` for executed ensemble votes persisting `execute=true`; without this log field, `usage-score.py` will continue reporting `ensemble_executed` missing even after real model calls.
2. Run deterministic gates before multi-model ratification:
   ```bash
   cd ~/.hermes
   python3 -m py_compile scripts/self-improvement-pipeline.py scripts/post-session-autopsy.py scripts/consult_models.py scripts/usage-score.py scripts/self-test.py
   python3 -m unittest scripts/test_self_improvement_pipeline.py scripts/test_post_session_autopsy.py scripts/test_consult_models_integration.py scripts/test_usage_score.py -v
   python3 scripts/usage-score.py
   python3 scripts/self-improvement-pipeline.py --write --auto-exec
   python3 scripts/cron-health-quarantine.py
   python3 scripts/cron-missed-run-guard.py
   python3 scripts/self-test.py
   ```
   Run `usage-score.py` before `self-improvement-pipeline.py --write --auto-exec` so the diagnostic can include fresh `semantic_grades` health context.
3. Build a `consult_models.py` evidence-first state for acceptance, not just a prose summary. Put each acceptance assertion in `state.claims` and deterministic outputs/diff summaries in `state.evidence` using explicit `claims_supported` links. Locally verify `build_evidence_bundle(state)` and `evaluate_truth_gate(bundle)` report `verified_claim_count == claim_count`, `truth_status=grounded`, and no `unsupported` / `needs_link_review` high-severity claims before running T3.
4. Full multi-model acceptance requires the ratification artifact, not just truth-gate precheck:
   ```bash
   python3 scripts/consult_models.py run /tmp/<state>.json --tier T3 --quorum 4 --discussion --max-rounds 5 --keep --timeout 180
   ```
   If the command times out after planner fan-out or lacks `discussion_result.json`, report weak consensus / not fully ratified and inspect the tick directory rather than claiming certification.
5. Before committing, stage only scoped scripts/tests/runtime evidence, run `git diff --cached --check`, scan staged added lines for secret-like patterns, verify `git diff --cached --name-only`, then local commit only; do not push unless explicitly asked.

## Pitfalls (实战发现)

Detailed `Pitfalls (实战发现)` guidance moved to `references/pitfalls-实战发现.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
