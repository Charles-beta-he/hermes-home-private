#!/usr/bin/env python3
"""Cron/no_agent wrapper for parallel local-brain autorun summaries.

Explicit opt-in counterpart to brain_task_dispatch_summary_tick.py. It keeps the
same compact summary shape, but asks the dispatch tick to claim a
parallel_boundary-deduped non-conflicting batch after safe gates pass.

Important: a human-escape pause is a deliberate safety state, not a cron script
failure. In that state this wrapper emits a structured report and exits 0 so the
scheduler does not keep reclassifying a fail-closed pause as broken automation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

HERMES = Path.home() / ".hermes"
SCRIPTS = HERMES / "scripts"
TICK = SCRIPTS / "brain_task_dispatch_tick.py"
AGENT_TEAM = SCRIPTS / "agent_team_controller.py"


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_json(cmd: list[str], timeout: int = 120) -> Dict[str, Any]:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if proc.returncode != 0:
        return {
            "status": "ERROR",
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-2000:],
        }
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"status": "ERROR", "returncode": proc.returncode, "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:], "parse_error": "json_decode"}
    return data if isinstance(data, dict) else {"status": "OK", "value": data}


def human_escape_report(status: Dict[str, Any]) -> Dict[str, Any] | None:
    envelope = status.get("envelope_stats") or {}
    info = envelope.get("escape_info") or {}
    if not envelope.get("human_escape_triggered"):
        return None
    return {
        "schema": "taskpool_autorun_summary_preflight_v1",
        "ts": utc(),
        "status": "SKIP",
        "reason": "SAFETY_PAUSE_POST_ACK_FAILURES",
        "safety": "human_escape is fail-closed by design; no parallel autorun attempted",
        "blocks_what": ["parallel_autorun_preclaim"],
        "dispatchable_tasks": status.get("dispatchable_tasks"),
        "conflict_groups": status.get("conflict_groups") or {},
        "live_workers": 0,
        "human_escape": {
            "triggered": True,
            "since_ack": info.get("since_ack"),
            "historical": info.get("historical"),
            "ack": info.get("ack"),
        },
        "next_action": "review/quarantine post-ack envelope failures or explicitly acknowledge the safety pause; cron wrapper exits 0 to avoid false broken-job health",
    }


def main() -> int:
    os.environ.setdefault("HERMES_LOCAL_BRAIN_AUTORUN", "1")
    status = run_json([sys.executable, str(AGENT_TEAM), "status", "--json"], timeout=120)
    report = human_escape_report(status)
    if report is not None:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    proc = subprocess.run([sys.executable, str(TICK), "--summary", "--parallel-autorun", "--archive-handoffs"])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
