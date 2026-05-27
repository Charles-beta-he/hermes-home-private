#!/usr/bin/env python3
"""Auth-Blocked Telegram Notifier — Scan credential-missing tasks and notify.

When tasks are blocked due to missing credentials/auth, this script:
1. Scans kanban for auth-blocked and credential-missing tasks
2. Deduplicates against recent notifications (avoid spam)
3. Outputs notification text for Telegram delivery

Designed to run as a cron no_agent script.
Non-empty stdout = message to deliver; empty = silent.
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
STATE_FILE = HERMES_HOME / "state" / "auth_blocked_notify_state.json"
LOG_PATH = HERMES_HOME / "logs" / "auth_blocked_notifier.jsonl"

# Notification cooldown: don't re-notify same task within this window
COOLDOWN_HOURS = 24


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def load_state() -> dict[str, float]:
    """Load last notification timestamps per task."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict[str, float]):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_auth_blocked_tasks() -> list[dict[str, Any]]:
    """Load tasks blocked due to auth/credential issues."""
    if not KANBAN_DB.exists():
        return []
    
    db = sqlite3.connect(str(KANBAN_DB))
    db.row_factory = sqlite3.Row
    
    # Find blocked tasks where the most recent run indicates auth/credential issues
    rows = db.execute("""
        SELECT t.id, t.title, t.assignee, t.priority, t.created_at,
               tr.summary, tr.error
        FROM tasks t
        JOIN task_runs tr ON tr.task_id = t.id AND tr.status = 'blocked'
        WHERE t.status = 'blocked'
          AND (
            tr.summary LIKE '%auth-required%'
            OR tr.summary LIKE '%credentials%'
            OR tr.summary LIKE '%登录凭证%'
            OR tr.summary LIKE '%登录态%'
            OR tr.summary LIKE '%admin 登录%'
            OR tr.summary LIKE '%OTP-log access%'
            OR tr.summary LIKE '%authenticated admin%'
            OR tr.summary LIKE '%GitHub credentials%'
            OR tr.summary LIKE '%凭据%'
          )
        ORDER BY t.priority DESC, t.created_at DESC
    """).fetchall()
    
    db.close()
    return [dict(r) for r in rows]


def extract_credential_need(task: dict) -> str:
    """Extract what credential is needed from the summary."""
    summary = task.get("summary", "") or ""
    title = task.get("title", "") or ""
    combined = summary + " " + title
    
    if "Railway" in combined and ("OTP" in combined or "admin" in combined):
        return "Railway admin 登录态"
    elif "GitHub" in combined and "credentials" in combined.lower():
        return "GitHub credentials"
    elif "admin" in combined.lower() and ("登录" in combined or "auth" in combined.lower()):
        return "UVISA Admin 登录凭证"
    elif "OTP" in combined:
        return "OTP 验证访问"
    else:
        return "认证凭证"


def format_notification(new_tasks: list[dict]) -> str:
    """Format Telegram notification for auth-blocked tasks."""
    if not new_tasks:
        return ""
    
    lines = [
        "🔐 任务池凭证缺失通知",
        "",
        f"以下 {len(new_tasks)} 个任务因缺少凭证/认证而阻塞：",
    ]
    
    for t in new_tasks:
        cred = extract_credential_need(t)
        prio = t.get("priority", 0) or 0
        lines.append(f"")
        lines.append(f"📋 [{t['id'][:10]}] P{prio}")
        lines.append(f"   {t['title'][:65]}")
        lines.append(f"   需要: {cred}")
    
    lines.append("")
    lines.append("───")
    lines.append("请提供相应凭证后回复「续费 <task_id>」解除阻塞。")
    
    return "\n".join(lines)


def main():
    now = utc_ts()
    state = load_state()
    
    tasks = load_auth_blocked_tasks()
    if not tasks:
        # Clean stale state entries
        state = {k: v for k, v in state.items() if now - v < 86400 * 7}
        save_state(state)
        # Silent exit — no notification needed
        return
    
    # Filter: only notify for tasks not recently notified
    cooldown_secs = COOLDOWN_HOURS * 3600
    new_tasks = []
    for t in tasks:
        tid = t["id"]
        last_notified = state.get(tid, 0)
        if now - last_notified > cooldown_secs:
            new_tasks.append(t)
    
    if not new_tasks:
        # All recently notified — silent
        return
    
    # Update state
    for t in new_tasks:
        state[t["id"]] = now
    save_state(state)
    
    # Log
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps({
            "ts": utc_now(),
            "total_auth_blocked": len(tasks),
            "new_notifications": len(new_tasks),
            "task_ids": [t["id"] for t in new_tasks],
        }, ensure_ascii=False) + "\n")
    
    # Output notification text (will be delivered by cron)
    notification = format_notification(new_tasks)
    if notification:
        print(notification)


if __name__ == "__main__":
    main()
