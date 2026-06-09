# Worker Timeout Infrastructure Cascade Diagnosis

> When ALL workers in a dispatch window timeout or fail, the root cause is almost always infrastructure, not the task. This reference covers the diagnostic methodology and known failure patterns.

## Diagnostic Methodology

### Step 1: Time-window error scan

```bash
# Replace timestamps with your dispatch window
grep -a "2026-05-28 19:3[7-9]\|2026-05-28 19:[4-5]\|2026-05-28 20:\|2026-05-28 21:0[0-5]" \
  ~/.hermes/logs/errors.log 2>/dev/null | python3 -c "
import sys, re
from collections import Counter
errors = Counter()
for line in sys.stdin:
    if 'MCP server' in line and 'failed' in line:
        errors['MCP server connection failure'] += 1
    elif 'Codex stream: SDK parse_response crashed' in line:
        errors['Codex SDK null response crash'] += 1
    elif 'Path not found' in line or 'File not found' in line:
        errors['Path/File not found'] += 1
    elif 'Access denied' in line:
        errors['Access denied (outside allowed dirs)'] += 1
    elif 'missing on disk' in line:
        errors['Workspace missing on disk'] += 1
    elif 'Could not find a match' in line:
        errors['Skill patch match failure'] += 1
    elif 'timed out' in line:
        errors['Timeout'] += 1
    elif 'Connection closed' in line:
        errors['Connection closed'] += 1
    elif 'fatal:' in line:
        errors['Git fatal error'] += 1

print('Error distribution:')
for err, count in errors.most_common():
    print(f'  {count:3d}x  {err}')
print(f'  Total: {sum(errors.values())}')
"
```

### Step 2: Classify failure mode

| Pattern | Diagnosis | Action |
|---|---|---|
| SDK crashes > 50 | Provider instability | Switch provider or add circuit breaker |
| MCP failures > 10 | MCP server down | Disable MCP git or fix server |
| Path/File not found > 5 | Workspace setup race | Check worktree creation ordering |
| Mixed infra errors | Cascade failure | Fix highest-count error first |
| Zero infra errors | Task genuinely too hard | Increase timeout or simplify task |

### Step 3: Check if timeout was consumed by infra overhead

```python
# 600s timeout breakdown (typical cascade):
# - MCP git reconnect: 3 retries × (1+2+4)s = 7s per worker
# - Codex SDK crash loop: 150 crashes × ~2-3s each = 300-450s
# - Workspace rebuild/path search: 100-200s
# - Actual task execution: ~0s (never reached)
```

If infra overhead > 80% of timeout, the task didn't actually fail — the infrastructure did.

## Known Failure Patterns

### Pattern 1: Codex SDK Null Response Crash

**Symptom:** `Codex stream: SDK parse_response crashed on null response.output`
**Provider:** openai-codex (GPT-5.5)
**Frequency:** Can reach 150+ crashes in a 90-minute window across parallel workers
**Root cause:** GPT-5.5 backend returns null response.output; SDK doesn't handle gracefully
**Impact:** Each crash wastes a tool call cycle + ~2-3s; 150 crashes = 300-450s wasted

**Mitigation:** Add circuit breaker — after N consecutive null responses, fail the worker fast rather than letting it retry until timeout.

### Pattern 2: MCP Git Server Connection Failure

**Symptom:** `MCP server 'git' initial connection failed (attempt 1/3) ... giving up`
**Frequency:** Each worker hits 3 retries (1+2+4s = 7s wasted); parallel workers double it
**Root cause:** MCP git server process not running or incompatible with worker environment
**Impact:** 7-14s per dispatch + continued retries throughout execution

**Mitigation:** Disable MCP git in worker profiles or use lazy init. Workers can use terminal `git` commands instead.

### Pattern 3: Worktree Path Race Condition

**Symptom:**
- `Path not found: /tmp/agent-team-.../uvisa-app-2.0`
- `LocalEnvironment cwd '...' is missing on disk; falling back to parent`
- `fatal: '...' does not appear to be a git repository`

**Root cause:** Parallel workers creating worktrees from the same parent repo; directory not visible to sibling worker process at query time
**Impact:** Workers waste 100-200s trying to find/recreate workspace

**Mitigation:** Serial worktree creation with verification, or pre-create all worktrees before spawning workers.

### Pattern 4: Access Denied on Workspace Paths

**Symptom:** `Access denied - path outside allowed directories: /Users/charles/...`
**Root cause:** MCP filesystem tool's allowed_directories doesn't include the tmp workspace path
**Impact:** Worker can't read/write task-specific files

**Mitigation:** Ensure worker spawn includes tmp workspace in MCP filesystem allowed paths.

## Decision Tree

```
Worker timeout detected
├─ Check errors.log time window
│  ├─ Infra errors > 10 → Infrastructure cascade (fix infra, re-run)
│  │  ├─ SDK crashes dominant → Switch provider or circuit-break
│  │  ├─ MCP failures dominant → Disable MCP git or fix server
│  │  ├─ Path errors dominant → Fix worktree creation ordering
│  │  └─ Mixed → Fix highest-count first, re-run
│  └─ Infra errors ≤ 10 → Task-level failure
│     ├─ max_iterations_reached → Task too complex, simplify
│     ├─ OOM/crash → Reduce memory footprint
│     └─ Block reason present → Human decision needed
```

## Quick Commands

```bash
# Count errors in last 2 hours
grep -c "WARNING\|ERROR" ~/.hermes/logs/errors.log

# Check MCP server status
hermes mcp status 2>/dev/null || echo "no mcp status command"

# Check worker workspace state
ls -la /tmp/agent-team-$(date +%Y-%m-%d)-*/ 2>/dev/null

# Check git worktree state
git worktree list 2>/dev/null

# Check active worker processes
ps aux | grep "hermes.*worker\|hermes.*team" | grep -v grep
```
