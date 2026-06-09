# Cycle Timeout Diagnostics

Diagnose `agent_team_controller.py cycle` hangs without waiting for the full timeout.

## Quick Triage (no waiting)

The cycle has two phases: **claim-cycle** (fast, ~10s) and **execute-cycle** (hangs on LLM subprocesses). The data layer is always accessible even when the cycle is stuck.

### Step 1: Check status (instant)

```bash
cd ~/.hermes/scripts && python3 agent_team_controller.py status 2>&1
```

Returns immediately with: `disabled`, `applied_n`, `dispatchable_tasks`, `conflict_groups`, `envelope_stats` (total, by_status, timeouts, human_escape_triggered).

Key fields:
- `disabled: true` → kill switch active, check `AGENT_TEAM_DISABLED` env or `state/agent_team_disabled` file
- `human_escape_triggered: true` → 2+ consecutive blocks or 3+ crashes, needs ack
- `envelope_stats.by_status.PENDING` → tasks waiting for execute-cycle
- `envelope_stats.by_status.RUNNING` → tasks currently being worked

### Step 2: Verify orchestrator is responsive (instant)

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json 2>&1 | head -20
```

Returns in 60-90s (scans 300+ task .md files; see `brain-orchestrator-subprocess-timeout.md`). If this hangs beyond 120s, the issue is in the orchestrator, not the cycle.

### Step 3: Run claim-cycle standalone (~10s)

```bash
cd ~/.hermes/scripts && timeout 30 python3 -u agent_team_controller.py claim-cycle --max-claims 1 --wall-budget-seconds 10 2>&1
```

If this works → claim phase is healthy, the hang is in execute-cycle.
If this hangs → check `brain_task_orchestrator.py claim` subprocess.

### Step 4: Query envelope bus directly (instant)

```python
cd ~/.hermes/scripts && python3 -c "
from envelope_bus import stats, list_by_status
print('Stats:', stats())
pending = list_by_status('PENDING')
print(f'PENDING: {len(pending)}')
for e in pending[:3]:
    print(f'  {e[\"id\"]}: assignee={e.get(\"assignee\",\"?\")}')
"
```

### Step 5: Check for blocking processes

```bash
ps aux | grep -E 'agent_team_controller|brain_task_orchestrator|claude -p|hermes chat' | grep -v grep
```

If you see `claude -p` or `hermes chat -q` processes → execute-cycle workers are running and blocking the parent process.

## Root Cause

`execute_cycle()` → `delegate_to_worker()` → spawns `hermes chat -q` or `claude -p` subprocesses with:
- Code tasks: 600s timeout, GPT-5.5 via openai-codex, max_turns=30
- Analysis tasks: 300s timeout, MiMo-v2.5-pro via xiaomi, max_turns=15
- Multi-model verification: 4 models × 90s = ~360s sequential

With N=3 sequential workers: up to 1800s+ per cycle. The cron job's 120s timeout always expires first.

## Why Status/Claim Work But Cycle Doesn't

| Command | Typical time | Why |
|---------|-------------|-----|
| `status` | <1s | Pure Python, no subprocesses |
| `brain_task_orchestrator list --json` | 60-90s | Scans 300+ .md files, slow on Xcode Python 3.9; use timeout≥120 (see `brain-orchestrator-subprocess-timeout.md`) |
| `claim-cycle` | ~10s | Orchestrator claim calls only, no LLM |
| `execute-cycle` | 300-1800s+ | Spawns LLM workers that do real work |
| `cycle` (full) | ∞ (hangs) | claim + execute, cron kills at 120s |

## Solutions

### Option A: Claim-only cron (recommended)

Change the cron script to run claim-cycle only:

```python
# In agent_team_controller_cycle.py, replace:
argv = [sys.executable, str(target)] + ['cycle']
# With:
argv = [sys.executable, str(target)] + ['claim-cycle', '--max-claims', '3', '--wall-budget-seconds', '15']
```

Then run execute-cycle separately as a long-lived process or with a 1200s+ timeout.

### Option B: Increase cron timeout

Set the cron job timeout to 1200s+ and accept ≤1 task per cron run. Use `cronjob(action='update', ...)` to adjust.

### Option C: Background execution

Use `terminal(background=True, notify_on_complete=True)` for the execute phase so it doesn't block the cron process.

## Confirmed Live Data

### claim-cycle output shape (verified 2026-05-28)

```json
{
  "status": "ok",
  "mode": "claim-only",
  "n_info": {
    "applied_n": 3,
    "raw_n": 3,
    "candidate_n": null,
    "candidate_count": 0,
    "smoothing_active": false,
    "formula": "min(ceil(48/7), 18, 3)"
  },
  "conflict_groups": 18,
  "total_dispatchable": 48,
  "tasks_claimed": 3,
  "claimed": [
    {"task_id": "...", "title": "...", "envelope_id": "...", "conflict_group": "boundary:...", "priority": "P2", "worker_result": "enqueued"}
  ],
  "claim_errors": [],
  "deferred_groups": 15,
  "safety": "claim-cycle only claims and enqueues; execution is delegated to execute-cycle"
}
```

Key: `n_info.formula` shows the dynamic-N formula evaluated live. When `smoothing_active: false`, N is applied immediately (no 2-cycle delay). `deferred_groups` = conflict groups that couldn't be scheduled this cycle.

### envelope_bus stats() output shape (verified 2026-05-28)

```json
{
  "total": 416,
  "by_status": {"BLOCKED": 6, "DONE": 88, "FAILED": 98, "PENDING": 64, "RUNNING": 2, "SKIPPED": 158},
  "timeouts": 2,
  "human_escape_triggered": false,
  "escape_info": {
    "blocks": 0,
    "failures": 1,
    "since_ack": {"blocks": 0, "failures": 1, "invalid_timestamps": 0},
    "historical": {"blocks": 6, "failures": 98, "invalid_timestamps": 0},
    "ack": {"status": "ok", "acked_at": "2026-05-28T08:55:27Z", "acked_by": "human", "reason": "post-observation recovery: fixed UTC Z ack-age parsing in taskpool_dynamic_runner.py to prevent immediate 24x scale-up; hold deterministic min cap and resume via hooks only after clean window"}
  }
}
```

Key: `escape_info.ack.reason` often explains the *last fix* that enabled recovery — read it to understand what was patched. `since_ack` vs `historical` separates post-fix failures from pre-fix ones.

### Active PENDING accumulation (confirmed 2026-05-28)

Observed: 64 PENDING + 2 RUNNING with 48 dispatchable, 18 conflict groups. This confirms the cron-timeout pattern is actively occurring — claim-cycle enqueues but execute-cycle can't drain fast enough.

### execute-cycle wall-budget pitfall (confirmed 2026-05-28)

`execute-cycle --wall-budget-seconds 30` timed out at 45s (exit_code 124) even though it should return within 30s. This means `execute_cycle()` may hang before reaching the wall-budget check loop, possibly in `human_escape_check()` or `list_by_status('PENDING')` when the envelope bus is under load. Use `timeout` wrapper as safety net regardless of wall-budget setting.

### Long-lived worker processes (confirmed 2026-05-28)

Worker PID 15085 (batch `parallel-20260528182521-3`) was alive for 6.5+ hours processing 3 book-reading tasks. `ps aux | grep PID` is the definitive check for whether workers are still alive or orphaned. The job file at `state/taskpool-workers/jobs/<job_id>.json` contains the full command, batch_id, and task_ids for forensic analysis.

### Quick isolation script (confirmed 2026-05-28)

When the full `cycle` times out, isolate the failure in <45s:

```bash
cd ~/.hermes/scripts && timeout 30 python3 -c "
import sys, json
sys.path.insert(0, '.')
from agent_team_controller import claim_cycle
r = claim_cycle(max_claims=3, wall_budget_seconds=10)
print(json.dumps(r, indent=2, ensure_ascii=False))
" 2>&1
```

If this returns `status: ok` with `tasks_claimed > 0`, the claim phase is healthy. The hang is in execute-cycle. Check worker PIDs next:

```bash
python3 -c "
import json, os, glob
jobs = sorted(glob.glob(os.path.expanduser('~/.hermes/state/taskpool-workers/jobs/*.json')))
for jf in jobs[-5:]:
    with open(jf) as f:
        d = json.load(f)
    pid = d.get('pid', 0)
    alive = False
    try: os.kill(pid, 0); alive = True
    except: pass
    print(f'{os.path.basename(jf)}: PID={pid} alive={alive} tasks={len(d.get(\"task_ids\",[]))}')
"
```

If a worker PID is alive, the execute-cycle spawned it and the cron killed the parent before the worker finished. The worker itself may still be doing useful work — don't kill it.

### Envelope bus full snapshot (confirmed 2026-05-28 19:37 UTC)

```json
{"total": 425, "by_status": {"DONE": 88, "FAILED": 99, "PENDING": 58, "RUNNING": 4, "SKIPPED": 170, "BLOCKED": 6}, "timeouts": 4, "human_escape_triggered": false}
```

Pattern: 58 PENDING + 4 RUNNING confirms active claim-then-stuck cycle. Each cron run claims 2-3 new tasks but execute-phase can't drain them within 120s.

## Diagnostic Signals

### PENDING accumulation pattern

If `status` shows many PENDING envelopes (e.g., 40+) with few RUNNING:
- claim-cycle is adding envelopes faster than execute-cycle drains them
- This is the classic cron-timeout symptom: each cron run claims new tasks but the execute phase times out before finishing any
- Fix: switch to claim-only cron (Option A above)

### High FAILED count with low DONE

If FAILED >> DONE (e.g., 98 FAILED vs 88 DONE):
- Workers are crashing or timing out more often than succeeding
- Check `envelope_stats.timeouts` — if >0, workers are hitting their wall budget
- Check human_escape state: `envelope_stats.human_escape_triggered`

### 2 RUNNING stuck

If exactly 2 envelopes show RUNNING for extended periods:
- Two workers were spawned by the last execute-cycle but the cron timed out before they returned
- The workers may still be running (check `ps aux | grep 'hermes chat\|claude -p'`)
- Or they crashed without the controller cleaning up (orphaned RUNNING state)

## Recovery Actions

### Clear stale PENDING envelopes

If PENDING envelopes are accumulating but never consumed:

```bash
cd ~/.hermes/scripts && python3 -c "
from envelope_bus import list_by_status, update_status
pending = [e for e in list_by_status('PENDING') if 'agent-team-' in str(e.get('assignee',''))]
print(f'Found {len(pending)} stale PENDING agent-team envelopes')
for e in pending:
    update_status(e['id'], 'SKIPPED', error='manual_cleanup_stale_pending')
    print(f'  Skipped: {e[\"id\"]}')
"
```

### Reset human escape

If human_escape_triggered is true:

```bash
cd ~/.hermes/scripts && python3 -c "
from envelope_bus import human_escape_check
# The escape check reads failure/block counts since last ack
# Ack resets the counter
import json, urllib.request
req = urllib.request.Request('http://localhost:3456/ack', method='POST')
"
```

Or manually: `python3 agent_team_controller.py enable` to clear kill switch, then ack the escape via the gateway.

### Force-release stuck claims

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition TASK_ID --to pending --actor hermes --reason manual_claim_cleanup --force --json
```

## See Also

- `agent-team-parallel.md` — Architecture, safety rules, scaling strategy
- `envelope-bus-escape-triage.md` — Human escape mechanism details
