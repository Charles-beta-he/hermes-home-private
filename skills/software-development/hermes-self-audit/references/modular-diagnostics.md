# Modular Self-Diagnostic System

## Architecture

Registry-driven, parallel-executing, 3-tier auto-fix diagnostic system.

### Runner (`runner.py`)

Core design principles:
- **Hot-reload**: Registry re-read every run — add checks without restart
- **Parallel execution**: ThreadPoolExecutor(4) for concurrent checks
- **3 output modes**: terminal (human), JSON (machine), status (one-liner)
- **Trend tracking**: JSONL history at `~/.hermes/logs/diagnostics-history.jsonl`
- **Degradation detection**: Compares current score against rolling average

### Registry (`check-registry.json`)

Each check entry:
```json
{
  "id": "kanban-db-integrity",
  "name": "Kanban DB Integrity",
  "description": "Checks SQLite integrity of kanban.db",
  "category": "data",
  "check_type": "sqlite",
  "check_command": "/path/to/checks/kanban-integrity.py",
  "source_type": "python_fn",
  "severity": "critical",
  "weight": 1.0,
  "enabled": true,
  "timeout": 30,
  "auto_fix": {
    "command": "/path/to/fixes/reindex-kanban.py",
    "tier": "safe",
    "description": "Reindex kanban.db",
    "requires_confirmation": false
  }
}
```

Key fields:
- `source_type`: `python_fn` (Python module with `check()` function), `shell_cmd` (exit code), `subprocess_json` (JSON output)
- `severity`: `critical` (score capped at 40 if fails), `high`, `medium`, `low`
- `auto_fix.tier`: `safe` (auto-apply), `moderate` (needs `--confirm`), `dangerous` (never auto), `none`

### Check Scripts (`checks/`)

Each script must expose a `check()` function returning:
```python
{"ok": bool, "detail": str, "metrics": dict}
```

### Fix Scripts (`fixes/`)

Each script must expose a `fix()` function returning:
```python
{"success": bool, "detail": str, "snapshot": str}  # snapshot = backup path
```

### Score Calculation

- Weighted by `weight × severity_multiplier`
- Critical failures cap score at 40
- Severity multipliers: critical=3, high=2, medium=1, low=0.5
- Exit codes: 0 (>=80), 1 (50-79), 2 (<50)

### Cron Integration

Schedule: every 4h. Prompt instructs runner to use `--json`, report only if score < 80.

## Adding New Checks

1. Write script in `checks/` with `check()` function
2. Add entry to `check-registry.json`
3. Test: `python3 runner.py` — verify check appears
4. Optional: write fix script in `fixes/` with `fix()` function

## Pitfalls

- **Python 3.9 compatibility**: macOS system Python is 3.9. Do NOT use `X | Y` union syntax (3.10+), `list[dict]` generics (3.9+), or `match` statements (3.10+). Use `Optional[X]`, `List[Dict]`, `if/elif`.
- **Rotated log files**: Log rotation creates `.rotated-*` files that can be GB-sized. The `log-file-size` check excludes these. Periodically clean: `find ~/.hermes/logs/ -name '*.rotated*' -delete`.
- **Cron health false positives**: `hermes cron list --json` may not be valid JSON. Use plain `hermes cron list` and count string occurrences instead.
- **Registry hot-reload**: Runner reads registry fresh each run. No need to restart anything after editing `check-registry.json`.
- **Auto-fix snapshots**: All fix scripts must create backups before modifying files. The `snapshot` field in the return value is the backup path.

## Extending

To add a new check category (e.g., network, MCP servers):
1. Create check script in `checks/`
2. Add registry entry with appropriate severity/weight
3. Optionally create matching fix script
4. Update this reference if the category is novel
