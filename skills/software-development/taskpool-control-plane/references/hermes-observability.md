---
name: hermes-observability
description: "Use when building monitoring dashboards, task progress tracking, metrics visualization, or operational observability for Hermes or any task-pool/worker system. Covers data big screens (数据大屏), step-level execution progress, health score trending, and alert panels."
triggers:
  - dashboard
  - monitoring
  - task progress
  - metrics visualization
  - data big screen
  - 数据大屏
  - task execution visibility
  - observability
  - health score
---

# Hermes Observability

Dashboards, metrics, and step-level task progress tracking for Hermes (or any agent/task-pool system).

## Core Insight

Task status (pending/running/done/blocked) is **not enough**. Users need to see:
- **What step** a running task is on (e.g., "implementing fix" step 3/5)
- **What happened** at each step (results, errors, durations)
- **Live heartbeats** — what the task is doing right now
- **Aggregate flow metrics** — throughput, WIP, cycle time, flow efficiency

Status machine = state. Step timeline = progress. Both are needed.

## Architecture

```
Worker executes task
  ↓ calls task_progress.py to log each step
  ↓ writes ~/.hermes/task-progress/<task_id>.jsonl
  ↓
dashboard-data.py aggregates all task progress + system metrics
  ↓ generates dashboard-data.json
  ↓
dashboard.html renders:
  - KPI cards (throughput, WIP, cycle time, flow efficiency)
  - Status distribution bar chart
  - Alert panel (auto-generated from thresholds)
  - Task progress timeline (step-level with heartbeats)
  - Lifecycle health (ingestion → dispatch → execution → verification → completion)
  - Trend charts
```

## Tools (already created)

| File | Purpose |
|------|---------|
| `~/.hermes/scripts/task_progress.py` | Step-level progress tracker (CLI) |
| `~/.hermes/diagnostics/dashboard.html` | Data big screen (self-contained HTML) |
| `~/.hermes/diagnostics/dashboard-data.py` | Data aggregator for dashboard |

## task_progress.py Usage

```bash
TP="python3 ~/.hermes/scripts/task_progress.py"

# Step lifecycle
$TP start <task_id> "step name" --step "1/5"
$TP heartbeat <task_id> "step name" "what I'm doing now..."
$TP done <task_id> "step name" --result "summary" --duration 3.2
$TP fail <task_id> "step name" --error "error message"
$TP completed <task_id> "overall summary"

# Queries
$TP active              # all tasks with recent activity
$TP show <task_id>      # full step timeline for one task
$TP dashboard           # JSON for dashboard consumption
```

## Dashboard Data Model

Each task has a step timeline:
```json
{
  "task_id": "uvisa-6906ef6e",
  "title": "消息通知中心交易类型区分",
  "project": "uvisa-app-2.0",
  "progress": "5/5",
  "status": "done|running|failed",
  "steps": [
    { "name": "拉取代码", "status": "done", "duration_s": 2.3, "result": "git pull OK" },
    { "name": "实现修复", "status": "running", "heartbeat_msg": "editing Vue file" },
    { "name": "构建", "status": "failed", "error": "TS error in App.tsx:42" }
  ]
}
```

Step statuses: `done` (green ✓), `running` (blue ▶ pulse), `failed` (red ✗), `pending` (gray ○).

## Dashboard Layout (1920×1080)

```
┌─────────────────────────────────────────────────────┐
│  ⬡ Hermes Agent · 任务监控大屏       Health: 80/100 │
├──────────┬──────────┬──────────┬────────────────────┤
│ 吞吐量   │ WIP      │ 周期时间 │ 流效率             │
├──────────┴──────────┼──────────┴────────────────────┤
│ 状态分布 (bar chart) │ ⚠️ 告警 (auto-threshold)      │
├─────────────────────┴───────────────────────────────┤
│ 📋 任务执行进度（步骤级时间线）                        │
│  ┌─────────────────────────────────────────────┐    │
│  │ task title              ▶ 执行中 3/5        │    │
│  │ ████████████████░░░░░░░░░░░░░░░ 60%        │    │
│  │ ● step 1 ✓ 2.3s                           │    │
│  │ ● step 2 ✓ 5.1s                           │    │
│  │ ● step 3 ▶ heartbeat: editing file...      │    │
│  └─────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│ 生命周期: 摄取✅ 派发❌ 执行❌ 验证⏸️ 完成❌ 监控✅    │
├──────────────────────┬──────────────────────────────┤
│ Health Score 趋势    │ 项目分布                      │
└──────────────────────┴──────────────────────────────┘
```

## Task Workflow Templates

Different task types have different step sequences:

**UVISA Bug Fix**: 拉取代码 → 读取原型 → 实现修复 → 运行测试 → 浏览器验证
**Hermes 改进**: 调研 → 设计 → 实现 → 自检
**研究任务**: 搜索 → 阅读 → 分析 → 输出报告
**Deploy**: build → test → migrate → deploy → verify

Workers should define their step sequence upfront (e.g., as a const) and call `task_progress.py` at each step boundary.

## Alert Thresholds

| Metric | WARNING | CRITICAL |
|--------|---------|----------|
| Health Score | <70 | <50 |
| Throughput | <1/day | =0 |
| Blocked tasks | >20 | >40 |
| Running stale (>12h) | >5 | >15 |
| Flow efficiency | <20% | <5% |

## Pitfalls

- **Don't just track status, track steps.** A task stuck in "running" for 19h with no step data is invisible. Always emit step_start/done/fail.
- **Heartbeats matter for long steps.** If a step takes >30s, emit heartbeats so the dashboard shows "what it's doing now" not just "still on step 3".
- **Dashboard HTML is self-contained.** No npm, no build step, no external deps. Just open in browser. Keep it that way.
- **Data freshness vs performance.** dashboard-data.py runs all data collectors sequentially. If it gets slow (>5s), parallelize with asyncio or threading.
- **task_progress.py is additive.** It writes append-only JSONL. No database, no migrations. Safe to call from any worker/process.
