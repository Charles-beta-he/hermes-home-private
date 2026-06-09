# Problem Pattern Registry — Cross-Session Knowledge Transfer

## Problem

Hermes sessions are isolated. When Session A discovers and solves an infrastructure problem, Session B re-discovers it from scratch, wasting compute and time.

Real examples:
- kanban.db corruption: discovered 9:00, fixed 11:30 (2.5h wasted)
- Codex credentials missing: 99 worker crashes over 2 hours
- Priority mode wrong: blocked task dispatch for 17 days
- Task duplicates: 53 duplicates accumulated over 3 days

## Architecture

### Tier 1: Known Issues List (immediate)
```
~/.hermes/KNOWN_ISSUES.md
```
Flat markdown with 4 columns: issue name, detect command, severity, fix command.
`hermes status` or session-startup checks this and prints warnings.

### Tier 2: Cron Health Check (1 week)
```
~/.hermes/scripts/health-check.sh → cron every 4h
```
Checks known issues, writes results to `~/.hermes/logs/health-check.jsonl`.
Detect-and-report only — no auto-fix.

### Tier 3: Structured Registry (when issues > 10)
```json
// ~/.hermes/state/problem-patterns.json
{
  "patterns": [
    {
      "id": "kanban-db-corrupt",
      "detect_command": "sqlite3 ~/.hermes/kanban.db 'PRAGMA integrity_check;' | grep -v ok",
      "severity": "critical",
      "fix_command": "sqlite3 ~/.hermes/kanban.db 'REINDEX; PRAGMA integrity_check;'",
      "last_seen": "2026-05-29",
      "fix_count": 1,
      "ttl_days": 90
    }
  ]
}
```

## Design Principles (3-model consensus)

1. **Detect-and-report over auto-fix** — all 3 review models independently concluded auto-fix is dangerous. The 17-day priority mode block proves it.
2. **Phased complexity** — start with markdown, upgrade to JSON only when patterns exceed 10.
3. **Human judgment required** — print the fix command, let the human decide.
4. **Two-phase pattern registration** — sessions write candidates to `~/.hermes/state/pattern-candidates.json`, cron validates before promoting to active registry.
5. **Atomic writes** — write to .tmp then os.replace() for all shared state files.
6. **Oscillation detection** — track recent fixes, halt if same 2 patterns alternate 3+ times.

## Implementation Safety

- **Lock file**: `~/.hermes/state/health-check.lock` with flock(LOCK_EX|LOCK_NB) to prevent concurrent runs
- **Daily attempt cap**: max 3 fix attempts per pattern per day, then escalate to alert-only
- **Audit trail**: JSONL log at `~/.hermes/logs/problem-registry-actions.jsonl`
- **FD awareness**: health-check script must close inherited FDs and set conservative rlimit
- **Pattern aging**: auto-archive patterns not triggered in 90 days

## Integration Points

- Session startup: load KNOWN_ISSUES.md, check and print
- Cron: run health-check.sh every 4 hours
- Session end: write new problem candidates (not direct registry writes)
- `hermes status`: show health-check summary

## Pitfalls

- NEVER auto-fix without human confirmation — contradicts evidence-first principle
- NEVER allow direct session writes to production registry — use candidate queue
- NEVER use shell=True for untrusted pattern commands — injection risk
- If health-check itself fails (FD exhaustion), emit single line to stderr and exit
