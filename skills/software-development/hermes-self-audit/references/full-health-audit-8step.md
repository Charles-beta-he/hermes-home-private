# Full Health Audit — 8-Step Pattern

When the user asks for "根因排查", "全面健康检查", or "infrastructure health audit", run this 8-step procedure:

## Step 1: state.db Cleanup
```bash
# Check current size
ls -lh ~/.hermes/state.db ~/.hermes/state.db-wal

# Backup before cleanup
cp ~/.hermes/state.db ~/.hermes/state.db.bak.$(date +%Y%m%d)

# Clean old sessions (3-day TTL)
python3 ~/.hermes/scripts/hermes-cleanup.py --session-ttl 3

# VACUUM to reclaim space
sqlite3 ~/.hermes/state.db "VACUUM;"

# WAL checkpoint
sqlite3 ~/.hermes/state.db "PRAGMA wal_checkpoint(TRUNCATE);"

# Verify integrity
sqlite3 ~/.hermes/state.db "PRAGMA integrity_check;"
```

## Step 2: Memory Compression
```bash
# Check current size
wc -m ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md

# Limits: MEMORY.md=2200, USER.md=1375
# Target: 80% headroom (MEMORY=1760, USER=1100)

# Backup before editing
cp ~/.hermes/memories/MEMORY.md ~/.hermes/memories/MEMORY.md.bak.$(date +%Y%m%d)
cp ~/.hermes/memories/USER.md ~/.hermes/memories/USER.md.bak.$(date +%Y%m%d)
```

Compression rules:
1. Merge entries with same domain
2. Move procedural knowledge to skills
3. Drop entries with <1 reference in last 10 sessions
4. Use § as entry separator, avoid full sentences

## Step 3: Source Leak Detection
```bash
# Check for .hermes inside the source repo
find ~/.hermes/hermes-agent -name ".hermes" -type d 2>/dev/null

# If found, move contents to proper location, then remove
# Also check for plans/ files in wrong location
ls ~/.hermes/hermes-agent/.hermes/ 2>/dev/null
```

## Step 4: Kanban Cleanup
```bash
# Find corrupt/backup kanban files
find ~/.hermes -name "kanban.db.corrupt.*.bak" -o -name "kanban.db.bak.*"

# Move to backups with date-based naming
mkdir -p ~/.hermes/backups/kanban-corrupt-$(date +%Y%m%d)
mv ~/.hermes/kanban.db.corrupt.*.bak ~/.hermes/backups/kanban-corrupt-$(date +%Y%m%d)/
```

## Step 5: Selfcheck Fix
```bash
# Run hook registry selfcheck
python3 ~/.hermes/scripts/hermes_hook_registry_selfcheck.py

# Common issues:
# - "shell hook missing": script path doesn't exist
# - "shell hook not executable": needs chmod +x
# - "command missing": hook registered without command
# - python3 interpreter resolution bug (see hermes-storage-governance pitfall #6)

# Fix permissions
chmod +x ~/.hermes/scripts/auth_blocked_notifier.py
chmod +x ~/.hermes/scripts/iteration_budget_triage.py
```

## Step 6: Git Cleanup
```bash
cd ~/.hermes/hermes-agent

# Create backup branch
git branch backup/pre-cleanup-$(date +%Y%m%d-%H%M%S)

# Check stash
git stash list --max-count=5

# Stage and commit pending changes
git add -A
git commit -m "chore: workspace cleanup $(date +%Y%m%d)"
```

## Step 7: Cron Recovery
```bash
# Check paused jobs
python3 -c "
import json
with open('/Users/charles/.hermes/cron/jobs.json') as f:
    data = json.load(f)
for j in data['jobs']:
    if j.get('state') == 'paused':
        print(f'{j[\"name\"]}  last_status={j.get(\"last_status\",\"?\")}')
"

# Resume non-deprecated paused jobs
# Keep deprecated ones (e.g., rokid-related) paused
```

## Step 8: Profile Bootstrap
```bash
# Check existing profiles
ls ~/.hermes/profiles/

# Create .env for each profile if missing
# Example: ~/.hermes/profiles/personal/.env
# HERMES_HOME=/Users/charles/.hermes
# HERMES_GATEWAY=<gateway_url>
```

## Final Verification
```bash
echo "=== 最终验证 ==="
echo "1. state.db:"; ls -lh ~/.hermes/state.db ~/.hermes/state.db-wal
sqlite3 ~/.hermes/state.db "PRAGMA integrity_check;"
echo "2. Memory:"; wc -m ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md
echo "3. Source leak:"; ls ~/.hermes/hermes-agent/.hermes/ 2>&1 || echo "CLEAN"
echo "4. Selfcheck:"; python3 ~/.hermes/scripts/hermes_hook_registry_selfcheck.py
echo "5. Git:"; cd ~/.hermes/hermes-agent && git status --short --branch
echo "6. Cron:"; python3 -c "import json; d=json.load(open('/Users/charles/.hermes/cron/jobs.json')); print(f'Total: {len(d[\"jobs\"])}, Paused: {len([j for j in d[\"jobs\"] if j.get(\"state\")==\"paused\"])}')"
```

## Backup Files Created
- `~/.hermes/state.db.bak.YYYYMMDD`
- `~/.hermes/memories/MEMORY.md.bak.YYYYMMDD`
- `~/.hermes/memories/USER.md.bak.YYYYMMDD`
- `~/.hermes/backups/kanban-corrupt-YYYYMMDD/`
- Git branch: `backup/pre-cleanup-YYYYMMDD-HHMMSS`
