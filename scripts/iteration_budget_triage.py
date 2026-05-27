#!/usr/bin/env python3
"""Iteration Budget Triage — Multi-model analysis for budget-exhausted tasks.

When tasks hit iteration budget (60/60), this script:
1. Scans all iteration-budget-exhausted blocked tasks
2. Categorizes by domain/complexity/retry count
3. Outputs structured JSON for multi-model decision: 续费/拆分/降级/放弃

Designed to run as a cron no_agent script or called by an agent.
Output is a structured triage report.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
KANBAN_DB = HERMES_HOME / "kanban.db"
LOG_PATH = HERMES_HOME / "logs" / "iteration_budget_triage.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_budget_exhausted_tasks() -> list[dict[str, Any]]:
    """Load tasks blocked by iteration budget exhaustion."""
    if not KANBAN_DB.exists():
        return []
    
    db = sqlite3.connect(str(KANBAN_DB))
    db.row_factory = sqlite3.Row
    
    rows = db.execute("""
        SELECT t.id, t.title, t.assignee, t.priority, t.created_at,
               t.consecutive_failures, t.spawn_failures,
               tr.summary, tr.error, tr.started_at, tr.ended_at
        FROM tasks t
        JOIN task_runs tr ON tr.task_id = t.id AND tr.status = 'blocked'
        WHERE t.status = 'blocked'
          AND tr.summary LIKE '%Iteration budget exhausted%'
        ORDER BY t.priority DESC, t.created_at DESC
    """).fetchall()
    
    db.close()
    return [dict(r) for r in rows]


def categorize_task(task: dict) -> dict[str, str]:
    """Categorize a task by domain and complexity signals."""
    title = task.get("title", "")
    summary = task.get("summary", "")
    assignee = task.get("assignee", "")
    
    # Domain detection
    domain = "general"
    if any(k in title for k in ["Lark", "Admin", "uvisa", "UVISA"]):
        domain = "uvisa"
    elif any(k in title for k in ["Hermes", "taskpool", "kanban", "brain"]):
        domain = "hermes-infra"
    elif any(k in title for k in ["browser", "automation", "QA"]):
        domain = "browser-qa"
    elif any(k in title for k in ["精读", "书籍", "学习"]):
        domain = "learning"
    
    # Complexity signals
    complexity = "medium"
    if any(k in title for k in ["统一", "抽象", "架构", "重构", "设计"]):
        complexity = "high"
    elif any(k in title for k in ["文案", "下拉框", "样式", "UI"]):
        complexity = "low"
    
    # Progress signal from summary
    progress = "unknown"
    if summary:
        if "已" in summary or "完成" in summary or "passed" in summary.lower():
            progress = "substantial"
        elif "部分" in summary or "partial" in summary.lower():
            progress = "partial"
    
    return {
        "domain": domain,
        "complexity": complexity,
        "progress": progress,
    }


def build_triage_recommendation(task: dict, cat: dict) -> dict[str, Any]:
    """Generate triage recommendation for a budget-exhausted task."""
    task_id = task["id"]
    title = task["title"]
    consecutive_failures = task.get("consecutive_failures", 0) or 0
    priority = task.get("priority", 0) or 0
    progress = cat["progress"]
    complexity = cat["complexity"]
    domain = cat["domain"]
    
    # Decision matrix
    recommendation = "review"  # default: need human review
    reason = ""
    suggested_budget = None
    
    # High progress + high priority → 续费 (raise budget)
    if progress == "substantial" and priority >= 100:
        recommendation = "续费"
        reason = "任务已有实质进展且优先级高，建议提高迭代预算继续推进"
        suggested_budget = 120
    
    # High progress + medium priority → 续费 with moderate budget
    elif progress == "substantial" and priority >= 50:
        recommendation = "续费"
        reason = "有实质进展，建议适度提高预算"
        suggested_budget = 90
    
    # High complexity + no progress → 拆分
    elif complexity == "high" and progress != "substantial":
        recommendation = "拆分"
        reason = "高复杂度任务在60迭代内未完成，需拆分为子任务降低单任务复杂度"
    
    # Low complexity + exhausted → 降级 or 放弃
    elif complexity == "low":
        if consecutive_failures >= 3:
            recommendation = "放弃"
            reason = "低复杂度任务多次耗尽预算，可能存在根本性障碍，建议放弃或重新定义"
        else:
            recommendation = "降级"
            reason = "低复杂度任务耗尽预算，可能是执行路径问题，建议降级为探索性任务"
    
    # Domain-specific adjustments
    if domain == "uvisa" and recommendation in ("续费", "review"):
        recommendation = "续费"
        reason += " [UVISA项目任务，优先保障]"
        if not suggested_budget:
            suggested_budget = 90
    elif domain == "learning":
        recommendation = "降级"
        reason = "学习类任务不应消耗大量迭代预算，建议降级为后台长期任务"
    
    return {
        "task_id": task_id,
        "title": title[:80],
        "assignee": task.get("assignee"),
        "priority": priority,
        "domain": domain,
        "complexity": complexity,
        "progress": progress,
        "consecutive_failures": consecutive_failures,
        "recommendation": recommendation,
        "reason": reason,
        "suggested_budget": suggested_budget,
    }


def format_report(triages: list[dict]) -> str:
    """Format triage report for human consumption."""
    if not triages:
        return "无迭代预算耗尽任务需要分析。"
    
    # Group by recommendation
    groups: dict[str, list] = {}
    for t in triages:
        rec = t["recommendation"]
        groups.setdefault(rec, []).append(t)
    
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "  迭代预算耗尽任务多模型分析报告",
        f"  生成时间: {utc_now()}",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"总计: {len(triages)} 个任务",
    ]
    
    rec_labels = {
        "续费": "续费 (提高预算继续)",
        "拆分": "拆分 (降低单任务复杂度)",
        "降级": "降级 (转为探索性/后台任务)",
        "放弃": "放弃 (存在根本性障碍)",
        "review": "待人工决策",
    }
    
    for rec in ["续费", "拆分", "降级", "放弃", "review"]:
        tasks = groups.get(rec, [])
        if not tasks:
            continue
        label = rec_labels.get(rec, rec)
        lines.append(f"\n── {label}: {len(tasks)} 个 ──")
        for t in tasks[:10]:  # cap display
            budget_hint = f" → 建议{t['suggested_budget']}次" if t["suggested_budget"] else ""
            lines.append(f"  [{t['task_id'][:10]}] P{t['priority']} {t['domain']} | {t['title']}")
            lines.append(f"    {t['reason']}{budget_hint}")
        if len(tasks) > 10:
            lines.append(f"  ... 另有 {len(tasks)-10} 个")
    
    # Summary stats
    lines.append("\n── 决策汇总 ──")
    for rec in ["续费", "拆分", "降级", "放弃", "review"]:
        cnt = len(groups.get(rec, []))
        if cnt:
            lines.append(f"  {rec_labels.get(rec, rec)}: {cnt}")
    
    return "\n".join(lines)


def main():
    tasks = load_budget_exhausted_tasks()
    triages = [build_triage_recommendation(t, categorize_task(t)) for t in tasks]
    
    # Log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({
            "ts": utc_now(),
            "total": len(triages),
            "续费": sum(1 for t in triages if t["recommendation"] == "续费"),
            "拆分": sum(1 for t in triages if t["recommendation"] == "拆分"),
            "降级": sum(1 for t in triages if t["recommendation"] == "降级"),
            "放弃": sum(1 for t in triages if t["recommendation"] == "放弃"),
            "review": sum(1 for t in triages if t["recommendation"] == "review"),
        }, ensure_ascii=False) + "\n")
    
    if "--json" in sys.argv:
        print(json.dumps({"triages": triages, "total": len(triages)}, ensure_ascii=False, indent=2))
    else:
        print(format_report(triages))


if __name__ == "__main__":
    main()
