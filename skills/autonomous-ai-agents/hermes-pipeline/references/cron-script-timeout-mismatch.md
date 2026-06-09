# Cron Script Timeout vs Worker Timeout — The 120s Wall

Session: 2026-05-25 + 2026-05-26 envelope_executor cron timeout diagnosis

## The Problem

The cron system imposes a **120s script-level timeout** on `no_agent` (script-only) cron jobs.
But `envelope_executor.py run N` spawns `hermes chat -q --max-turns 30` workers that take
**300-600s each**. The cron kills the executor mid-run, leaving the RUNNING envelope as a ghost.

## Failure Cascade

```
cron fires envelope_executor_run_1.py (120s limit)
  → executor claims envelope: PENDING → RUNNING
  → executor spawns hermes chat -q (600s timeout)
  → 120s elapsed: cron kills executor process
  → hermes chat subprocess is also killed (child of executor)
  → envelope stays RUNNING (no cleanup ran)
  → next cron cycle: executor claims another envelope
  → repeat → ghost RUNNING envelopes accumulate
```

After N cycles: N orphaned RUNNING envelopes, each blocking the bus.

## Diagnosis

```bash
# 1. Check for orphaned workers (should be empty if cron killed them)
ps aux | grep 'hermes chat' | grep -v grep

# 2. Quick stats overview
cd ~/.hermes/scripts && python3 envelope_executor.py stats

# 3. Count ghost RUNNING envelopes
python3 -c "
from envelope_bus import list_by_status
running = list_by_status('RUNNING')
print(f'RUNNING: {len(running)}')
for e in running:
    print(f'  {e[\"id\"][:12]} {e.get(\"title\",\"?\")[:50]}')
"

# 4. If ps shows no workers but RUNNING > 0 → ghosts from killed cron runs
```

### Appetite-Aware Stale Detection

Not all RUNNING envelopes are ghosts — some may legitimately be running long tasks.
Check elapsed time vs `appetite_seconds` before resetting:

```python
import sqlite3, json
from pathlib import Path
from datetime import datetime

db = str(Path.home() / '.hermes' / 'state' / 'envelope_bus.db')
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, title, appetite_seconds, started_at, retry_count, max_retries FROM envelopes WHERE status = 'RUNNING'")
now = datetime.utcnow()
stale_ids = []
for row in cur.fetchall():
    d = dict(row)
    started = d.get('started_at', '')
    if started:
        st = datetime.strptime(started, '%Y-%m-%dT%H:%M:%SZ')
        elapsed = (now - st).total_seconds()
        is_stale = elapsed > d['appetite_seconds']
        if is_stale:
            stale_ids.append(d['id'])
        print(f"{'STALE' if is_stale else 'ACTIVE'}: {d['id'][:12]} | {d['title'][:50]} | elapsed={elapsed:.0f}s appetite={d['appetite_seconds']}s retry={d['retry_count']}/{d['max_retries']}")
    else:
        print(f"NO_START: {d['id'][:12]} | {d['title'][:50]}")
print(f"\n{len(stale_ids)} stale ghosts to reset")
conn.close()
```

**Key DB path**: `~/.hermes/state/envelope_bus.db` — NOT `~/.hermes/scripts/envelope_state.db` (stale/empty).

## Recovery: Batch Reset Ghost Envelopes

Only reset when `ps aux | grep 'hermes chat'` shows NO live workers.
If workers are still running, wait for them or kill them first.

```python
import sys, os, time
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
from envelope_bus import list_by_status, update_status

running = list_by_status('RUNNING')
now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
for e in running:
    update_status(e['id'], 'PENDING')
    print(f'Reset RUNNING→PENDING: {e["id"][:12]}')
print(f'Reset {len(running)} ghosts')
```

## Solutions

### Option A: Increase cron timeout (quick fix)

The cron `timeout` field needs to be ≥900s to accommodate one 600s worker + overhead.

For `no_agent` script cron jobs, the timeout is configured in the cron job itself.
Check current timeout: `hermes cron list` — look for `Timeout:` field.

For `hermes cron edit` (if supported): set timeout=1200.
For `cronjob(action='update')`: the timeout is embedded in the cron wrapper, not the
hermes cron API. The actual fix is in the cron wrapper script (`envelope_executor_run_1.py`).

Current wrapper pattern:
```python
# envelope_executor_run_1.py
import os, sys
os.execv(sys.executable, [sys.executable, str(target)] + ['run', '1'])
```

The 120s timeout comes from the cron system's default for script-only jobs, not from
the wrapper itself. Fix: configure the cron job's timeout field explicitly.

### Option B: Async executor pattern (structural fix)

Instead of blocking on `hermes chat -q`, spawn workers in detached background processes:

```python
def run_async(envelope):
    """Spawn worker, don't wait for it. Check results next cycle."""
    worker_script = f"""
import subprocess, sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/scripts'))
from envelope_bus import update_status
cmd = ['hermes', 'chat', '-q', prompt, '--max-turns', '30']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if 'PROOF_JSON' in r.stdout:
    update_status('{envelope["id"]}', 'DONE')
else:
    update_status('{envelope["id"]}', 'FAILED', error='missing_proof')
"""
    # Detach: nohup + redirect so cron can exit immediately
    subprocess.Popen(['nohup', 'python3', '-c', worker_script],
                     stdout=open('/dev/null'), stderr=subprocess.STDOUT,
                     start_new_session=True)
```

Trade-off: loses the synchronous error path, but the cron job finishes in <5s.

### Option C: Claim-only cron (recommended for agent_team_controller)

For `agent_team_controller.py`, separate claim-cycle (fast) from execute-cycle (slow):

```python
# Run claim-cycle in cron (10s), execute-cycle as background process
argv = [sys.executable, target, 'claim-cycle', '--max-claims', '3', '--wall-budget-seconds', '15']
```

This doesn't apply directly to `envelope_executor.py` (which is already executor-only),
but the principle is the same: fast operations in cron, slow operations in background.

## Gotchas

### `timeout` wrapper + SIGTERM handler = empty output

The executor registers a SIGTERM handler that kills the worker process group and raises
`SystemExit(128 + signum)`. When you wrap the executor with the `timeout` CLI utility:

```bash
timeout 100 python3 envelope_executor.py run 1  # BAD: empty output
```

The `timeout` command sends SIGTERM when the deadline hits, which triggers the executor's
shutdown handler, which kills the worker and exits **before printing the JSON result**.
You get empty output with exit code 0 — looks like success but nothing happened.

Instead, use the terminal tool's built-in timeout which reports `[Command timed out after Ns]`:

```python
# From execute_code
r = terminal("python3 envelope_executor.py run 1", timeout=120)
# r['exit_code'] == 124 on timeout, output contains the timeout message
```

Or use `subprocess.run(cmd, timeout=N)` which raises `TimeoutExpired` (the executor
catches this and retries).

### Three consecutive timeouts = report, don't retry blindly

If the executor times out 3 times in a row (120s, 300s, 120s), the problem is structural
— the worker timeout (600s) exceeds any reasonable cron window. Don't keep retrying.
Instead:
1. Reset stale RUNNING ghosts (appetite-aware, see above)
2. Report the architecture mismatch to the user
3. Suggest Option A/B/C above

## Prevention

1. **Always check `ps aux | grep hermes` before resetting ghosts** — killing a live worker
   mid-task loses its progress.
2. **Set cron timeout ≥ max(worker_timeout) × expected_envelope_count** — for 1 envelope
   per cycle with 600s workers, need ≥900s cron timeout.
3. **Monitor ghost accumulation** — if `RUNNING > 0` and `ps` shows no workers, ghosts are
   building up. Add a guard to the executor that checks for and resets stale RUNNING envelopes
   at the start of each run.

## Related

- `references/envelope-executor-missing-link.md` — executor architecture and stuck RUNNING recovery
- `references/envelope-bus-escape-triage.md` — escape mechanism (separate from timeout ghosts)
- `taskpool-control-plane/references/cycle-timeout-diagnostics.md` — same pattern for agent_team_controller
