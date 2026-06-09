# Brain–Kanban Dual-Store Desync

## Problem

Brain markdown files (`~/Documents/brain/05-实践与项目/tasks/*.md`) and `~/.hermes/kanban.db` are **independent stores**. The dashboard reads from both. Cleaning one does NOT clean the other.

### Observed failure mode
1. User/archiver clears brain task files (bulk archive to `已归档/`)
2. Dashboard still shows `review=1, blocked=1` because kanban.db has stale entries
3. kanban.db accumulates 100+ zombie tasks across `blocked`, `pending`, `running`, `ready`, `splitting` statuses

### Detection
```bash
# kanban.db status distribution
sqlite3 ~/.hermes/kanban.db "SELECT status, count(*) FROM tasks GROUP BY status ORDER BY status"

# Compare with brain task count
ls ~/Documents/brain/05-实践与项目/tasks/*.md 2>/dev/null | wc -l

# Dashboard reads from both — if brain is clean but dashboard shows active tasks, kanban.db is stale
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write --json
```

## Bulk Cleanup Procedure

### Step 1: Archive all non-done/non-archived tasks in kanban.db
```sql
UPDATE tasks SET status='archived' WHERE status NOT IN ('done','archived');
```

### Step 2: Verify
```sql
SELECT status, count(*) FROM tasks GROUP BY status;
-- Should show only 'done' and 'archived'
```

### Step 3: Regenerate dashboard
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write --json
```

### Step 4: Run selfcheck
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

## kanban.db Corruption Recovery

### Symptom
```
Error: stepping, database disk image is malformed (11)
```

### Recovery procedure
```bash
# 1. Backup
cp ~/.hermes/kanban.db ~/.hermes/kanban.db.bak

# 2. Dump (works even on corrupt db)
sqlite3 ~/.hermes/kanban.db.bak ".dump" > /tmp/kanban_dump.sql

# 3. Fix statuses in dump file (Python)
python3 << 'PYEOF'
import sqlite3, os

with open('/tmp/kanban_dump.sql') as f:
    dump = f.read()

lines = dump.split('\n')
fixed = []
for line in lines:
    if 'INSERT INTO tasks' in line:
        for bad in ['running','blocked','pending','ready','splitting','retry','claimed','review','proposed']:
            if f"'{bad}'" in line:
                line = line.replace(f"'{bad}'", "'archived'", 1)
                break
    fixed.append(line)

with open('/tmp/kanban_fixed.sql', 'w') as f:
    f.write('\n'.join(fixed))

# 4. Recreate
db_path = os.path.expanduser('~/.hermes/kanban.db')
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
conn.executescript('\n'.join(fixed))
conn.close()

# 5. Verify
conn = sqlite3.connect(db_path)
cur = conn.execute("SELECT status, count(*) FROM tasks GROUP BY status ORDER BY status")
for row in cur:
    print(f'{row[0]}: {row[1]}')
conn.close()
PYEOF
```

### Key pitfall
The dump includes `CREATE TABLE` + `INSERT` statements. The Python fixer must only replace status strings inside `INSERT INTO tasks` lines, not arbitrary occurrences in titles or body text. The `for bad in ...` + `if f"'{bad}'" in line` check prevents false replacements.

## Brain markdown ↔ kanban.db status mapping

| Brain status | kanban.db status | Notes |
|---|---|---|
| `pending` | `pending` | Normalized |
| `running` | `running` | Active work |
| `blocked` | `blocked` or `ready` | kanban may diverge! |
| `done` | `done` or `archived` | kanban may already archive |
| `retry` | `retry` | Auto-retry state |
| `splitting` | `splitting` | Decomposition in progress |
| `review` | `review` | Awaiting closeout |

**Critical rule:** Brain frontmatter `status: blocked` ≠ kanban.db `status`. Always check both stores when diagnosing task state. See also `references/kanban-db-operations.md` for schema and common queries.

## Prevention

When doing bulk brain task cleanup (archiving task files), always also clean kanban.db:
1. Archive brain files → `已归档/`
2. `UPDATE tasks SET status='archived' WHERE status NOT IN ('done','archived')` in kanban.db
3. Regenerate dashboard
4. Run selfcheck

The two stores should be treated as a unit — never clean just one.
