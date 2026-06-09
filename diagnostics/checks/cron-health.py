import json
import re
from pathlib import Path
from typing import Any, Dict, List

SAFETY_PAUSE_RE = re.compile(r"SAFETY_PAUSE_POST_ACK_FAILURES|human_escape_active_preclaim", re.I)
PROVIDER_RE = re.compile(r"Non-streaming API call timed out|Codex backend|Request timed out|Connection error|RateLimit|Too many requests", re.I)
DELIVERY_RE = re.compile(r"delivery error|Telegram send failed|send failed", re.I)
SCHEDULER_RE = re.compile(r"Script not found|missed its scheduled time|Fast-forwarding|idle for .*limit|Script timed out", re.I)


def _jobs(data: Any) -> List[Dict[str, Any]]:
    jobs = data.get("jobs", data) if isinstance(data, dict) else data
    return jobs if isinstance(jobs, list) else []


def classify(j: Dict[str, Any]) -> str:
    text = "\n".join(str(j.get(k) or "") for k in ("last_error", "last_delivery_error", "name", "id"))
    if SAFETY_PAUSE_RE.search(text):
        return "safety_pause"
    if DELIVERY_RE.search(text):
        # Prefer provider_generation when both are present: content did not finish.
        if PROVIDER_RE.search(str(j.get("last_error") or "")):
            return "provider_generation"
        return "delivery"
    if PROVIDER_RE.search(text):
        return "provider_generation"
    if SCHEDULER_RE.search(text):
        return "scheduler_runtime"
    return "job_error"


def check():
    try:
        jobs_path = Path.home() / ".hermes" / "cron" / "jobs.json"
        data = json.loads(jobs_path.read_text(encoding="utf-8"))
        active = [j for j in _jobs(data) if j.get("enabled", True)]
        errors = [j for j in active if j.get("last_status") == "error" or j.get("state") == "error"]
        by_class: Dict[str, int] = {}
        for j in errors:
            c = classify(j)
            by_class[c] = by_class.get(c, 0) + 1
        ok = not errors
        names = ", ".join(f"{j.get('name') or j.get('id') or 'unknown'}[{classify(j)}]" for j in errors[:5])
        detail = f"{len(errors)} error jobs in {len(active)} active jobs"
        if names:
            detail += f": {names}"
        if by_class:
            detail += f"; classes={by_class}"
        return {"ok": ok, "detail": detail,
                "metrics": {"error_count": len(errors), "total": len(active), "classes": by_class}}
    except Exception as e:
        return {"ok": False, "detail": str(e), "metrics": {}}
