import json
from pathlib import Path


def check():
    try:
        jobs_path = Path.home() / ".hermes" / "cron" / "jobs.json"
        data = json.loads(jobs_path.read_text(encoding="utf-8"))
        jobs = data.get("jobs", [])
        active = [j for j in jobs if j.get("enabled", True)]
        errors = [j for j in active if j.get("last_status") == "error" or j.get("state") == "error"]
        ok = not errors
        names = ", ".join((j.get("name") or j.get("id") or "unknown") for j in errors[:5])
        detail = f"{len(errors)} error jobs in {len(active)} active jobs"
        if names:
            detail += f": {names}"
        return {"ok": ok, "detail": detail,
                "metrics": {"error_count": len(errors), "total": len(active)}}
    except Exception as e:
        return {"ok": False, "detail": str(e), "metrics": {}}
