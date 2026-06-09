# Health Check Pattern

Reusable pattern for infrastructure health monitoring in Hermes.

## Components

### 1. Known Issues Registry (`~/.hermes/KNOWN_ISSUES.md`)

Markdown file with structured issue entries:

```markdown
## Issue 1: Kanban DB Integrity

- **Severity**: CRITICAL
- **Symptom**: `integrity_check returned 'wrong # of entries in index'`
- **Detect**: `sqlite3 ~/.hermes/kanban.db "PRAGMA integrity_check;" | grep -v ok`
- **Fix**: `sqlite3 ~/.hermes/kanban.db "REINDEX; PRAGMA integrity_check;"`
- **Last seen**: 2026-05-29
- **Fix count**: 2
```

### 2. Health Check Script (`~/.hermes/scripts/health-check.py`)

Python script that:
- Reads known issues from KNOWN_ISSUES.md (or hardcoded issue list)
- Runs detect commands for each issue
- Outputs: interactive (human-readable), --json (machine-readable), --log (audit trail)
- **Detect-only, no auto-fix** — human decides

Usage:
```bash
python3 ~/.hermes/scripts/health-check.py          # interactive
python3 ~/.hermes/scripts/health-check.py --json    # machine-readable
python3 ~/.hermes/scripts/health-check.py --log     # append to audit log
```

### 3. Audit Log (`~/.hermes/logs/health-check.jsonl`)

JSONL format, one entry per detection:
```json
{"ts": "2026-05-29T08:07:00Z", "action": "DETECTED", "pattern_id": "kanban-db-integrity", "severity": "CRITICAL", "detail": "wrong # of entries in index"}
```

### 4. Cron Job

Schedule: every 4h. Deliver: local (only notify on issues).

```
Schedule: every 4h
Model: mimo-v2.5-pro (cost-efficient)
Prompt: Run health-check.py --json, report issues if any, [SILENT] if all OK
```

## Design Decisions

- **Detect-only**: Never auto-fix infrastructure issues. Human must decide.
- **Threshold tuning**: Start with aggressive thresholds (100KB file size), tune up for false positives (moved to 500KB for legitimately large files).
- **Severity levels**: CRITICAL = blocks core function, HIGH = degrades function, MEDIUM = cosmetic/efficiency.
- **Audit log**: Append-only JSONL for trend analysis. Don't rotate — keep history.

## Pitfalls

- **File size threshold false positives**: Legitimately large files (811 lines of proof log) can exceed 100KB. Start at 500KB threshold for task file bloat detection. Tune after first run.
- **Detect command timeout**: Some detect commands (sqlite3 on large DBs) can hang. Always use subprocess timeout (30s).
- **Cron job silent failure**: Health check cron should use `[SILENT]` pattern when all OK — don't spam user with "all clear" messages.
- **Audit log rotation**: Don't rotate — keep history for trend analysis. JSONL format is append-safe.

## Adding New Issues

1. Add entry to `~/.hermes/KNOWN_ISSUES.md`
2. Add detection logic to `health-check.py` ISSUES list
3. Test: `python3 ~/.hermes/scripts/health-check.py --json`
4. Verify the detect command returns "OK" when healthy, non-OK when broken
