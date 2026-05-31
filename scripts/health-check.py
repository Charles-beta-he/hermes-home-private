#!/usr/bin/env python3
"""
Hermes Infrastructure Health Check
Checks known issues from KNOWN_ISSUES.md and reports status.
Detect-only, no auto-fix. Human decides.

Usage:
  python3 ~/.hermes/scripts/health-check.sh          # interactive: print to terminal
  python3 ~/.hermes/scripts/health-check.sh --json    # machine-readable
  python3 ~/.hermes/scripts/health-check.sh --log     # append to audit log
"""
import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HERMES = HOME / ".hermes"
AUDIT_LOG = HERMES / "logs" / "health-check.jsonl"

ISSUES = [
    {
        "id": "kanban-db-integrity",
        "name": "Kanban DB Integrity",
        "severity": "CRITICAL",
        "detect": "sqlite3 {hermes}/kanban.db 'PRAGMA integrity_check;' 2>/dev/null | grep -qv ok && echo ISSUE || echo OK",
        "fix_hint": "sqlite3 ~/.hermes/kanban.db \"REINDEX; PRAGMA integrity_check;\"",
    },
    {
        "id": "codex-credentials",
        "name": "Codex Credentials",
        "severity": "CRITICAL",
        "detect": "hermes auth status openai-codex 2>&1 | grep -q 'logged out' && echo ISSUE || echo OK",
        "fix_hint": "hermes auth openai-codex  (manual, interactive)",
    },
    {
        "id": "priority-mode",
        "name": "Priority Mode",
        "severity": "HIGH",
        "detect": "python3 -c \"import json; d=json.load(open('{state}/taskpool_priority_mode.json')); print('OK' if d.get('mode')=='work-first' else 'ISSUE: '+d.get('mode','unknown'))\" 2>/dev/null || echo OK",
        "fix_hint": "python3 -c \"import json; json.dump({'mode':'work-first','reason':'manual fix'}, open('$HOME/.hermes/state/taskpool_priority_mode.json','w'), indent=2)\"",
    },
    {
        "id": "task-file-bloat",
        "name": "Task File Bloat",
        "severity": "MEDIUM",
        "detect": "count=$(find {brain}/05-实践与项目/tasks/ -name '*.md' -size +500k 2>/dev/null | wc -l | tr -d ' '); [ \"$count\" -gt 0 ] && echo ISSUE: $count files bloated || echo OK",
        "fix_hint": "Run frontmatter cleanup script to truncate escape-exploded fields",
    },
]


def run_detect(issue):
    """Run detection command, return (ok: bool, detail: str)."""
    cmd = issue["detect"].format(
        hermes=str(HERMES),
        state=str(HERMES / "state"),
        brain=str(HOME / "Documents" / "brain"),
    )
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = r.stdout.strip()
        if output == "OK":
            return True, "OK"
        else:
            return False, output or "check failed"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def audit(entry):
    """Append to audit log."""
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry["ts"] = datetime.now(timezone.utc).isoformat()
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    mode = "interactive"
    if "--json" in sys.argv:
        mode = "json"
    if "--log" in sys.argv:
        mode = "log"

    results = []
    issues_found = 0

    for issue in ISSUES:
        ok, detail = run_detect(issue)
        results.append({
            "id": issue["id"],
            "name": issue["name"],
            "severity": issue["severity"],
            "ok": ok,
            "detail": detail,
            "fix_hint": issue["fix_hint"] if not ok else None,
        })
        if not ok:
            issues_found += 1
            audit({
                "action": "DETECTED",
                "pattern_id": issue["id"],
                "severity": issue["severity"],
                "detail": detail,
            })

    if mode == "json":
        print(json.dumps({
            "status": "PASS" if issues_found == 0 else "FAIL",
            "issues_found": issues_found,
            "total_checked": len(ISSUES),
            "results": results,
        }, indent=2, ensure_ascii=False))
    elif mode == "log":
        if issues_found > 0:
            audit({
                "action": "RUN_COMPLETE",
                "issues_found": issues_found,
                "total_checked": len(ISSUES),
            })
    else:
        # Interactive mode
        if issues_found == 0:
            print("✅ All health checks passed")
        else:
            print(f"⚠️  {issues_found}/{len(ISSUES)} issues detected:\n")
            for r in results:
                if not r["ok"]:
                    print(f"  [{r['severity']}] {r['name']}: {r['detail']}")
                    print(f"    Fix: {r['fix_hint']}\n")

    return 1 if issues_found > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
