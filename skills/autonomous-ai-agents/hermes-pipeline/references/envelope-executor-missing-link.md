# Envelope Executor — The Missing Link

Session: 2026-05-10 Full auto-trigger chain implementation
Problem: pipeline_tick creates PENDING envelopes but nothing consumes them

## The Gap

The hermes-pipeline skill documents the flow: collector → confirmer → executor → validator → reporter.
But in practice, the `executor` step was missing — pipeline_tick created PENDING envelopes
and they just accumulated without being consumed.

## The Fix: envelope_executor.py

A dedicated script that:
1. Reads PENDING envelopes from envelope_bus
2. Claims them (PENDING → RUNNING)
3. Delegates to `hermes chat -q` workers
4. Detects budget exhaustion (Iteration budget reached)
5. Saves checkpoints for continuation (via task_continuation.py)
6. Reports DONE/BLOCKED/FAILED status back to envelope_bus

```python
def delegate_to_worker(envelope):
    prompt = f"Execute this task and output PROOF_JSON on last line.\nTASK: {title}"
    
    # Check for continuation context
    if brain_id:
        can_cont, count = can_continue(brain_id)
        if count > 0:
            prompt = build_continuation_context(brain_id, prompt)
    
    cmd = ['hermes', 'chat', '-q', prompt, '--model', 'mimo-v2.5-pro',
           '--provider', 'xiaomi', '--quiet', '--max-turns', '30']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    # Detect budget exhaustion
    exhausted, signal = detect_budget_exhausted(r.stdout)
    if exhausted:
        save_checkpoint(brain_id, r.stdout)
        update_status(eid, 'PENDING')  # Re-queue for continuation
        return {'status': 'continuation_pending'}
    
    # Check for proof
    if 'PROOF_JSON' in r.stdout:
        update_status(eid, 'DONE')
        return {'status': 'done'}
```

## Cron Setup

```python
cronjob(action='create', name='envelope-executor-cycle',
        schedule='every 30m', script='envelope_executor.py run 1',
        prompt='Run envelope_executor.py run 1. If processed=0, silent.')
```

## Full Auto-Trigger Chain

```
orchestrator.list → pipeline_tick(create PENDING) → envelope_executor(claim→delegate) → kanban_bridge(mirror)
```

All connected via cron:
- pipeline-tick-hourly: creates envelopes
- envelope-executor-cycle (30m): consumes envelopes
- brain-kanban-bridge-sync (2h): mirrors to Kanban
- v-state-hourly: health monitoring

## Troubleshooting

### Diagnose without running: `stats` subcommand
The `stats` subcommand returns envelope bus state instantly (no hermes chat delegation):
```bash
python3 ~/.hermes/scripts/envelope_executor.py stats
```
Returns total, by_status breakdown, timeouts, human_escape state. Always run `stats` first to understand the bus before attempting `run`.

### "Script not found" from cron — transient PATH issue
If cron reports `Script not found: /path/to/envelope_executor.py run 1` but the script exists:
- The cron wrapper may have parsed the full string (script + args) as the script path
- Or the cron shell environment lacked the correct PATH
- Verify with `hermes cron list` — the `Script:` field should show `envelope_executor.py run 1`
- Usually transient; next cron cycle resolves. If persistent, check cron shell env.

### Long execution: run in background with notify_on_complete
`envelope_executor.py run N` delegates to `hermes chat -q` per envelope (up to 600s each).
The agent terminal has a 60-300s timeout, so synchronous execution will kill the process mid-run.
**Pattern:** Run in background, poll for completion:
```
terminal(command="python3 ~/.hermes/scripts/envelope_executor.py run 1",
         background=True, notify_on_complete=True, timeout=600)
# Then poll: process(action='poll', session_id=...) or process(action='wait', timeout=60)
```

### Stuck RUNNING envelopes
If `stats` shows RUNNING > 0 for extended periods:
- The worker subprocess likely crashed or timed out without cleanup
- Check trace: `python3 -c "from envelope_bus import get; print(get('eid')['trace'])"`
- Manual reset: `python3 -c "from envelope_bus import update_status; update_status('eid', 'PENDING')"`
- Or let human_escape trigger (2 blocks OR 3 crashes auto-pauses pipeline)

## File Locations

| File | Path | Purpose |
|------|------|---------|
| envelope_bus.py | `~/.hermes/scripts/envelope_bus.py` | Bus module (import, not run) |
| envelope_executor.py | `~/.hermes/scripts/envelope_executor.py` | Executor CLI (`stats`, `run N`, `ack`) |
| envelope_bus.db | `~/.hermes/state/envelope_bus.db` | **Actual SQLite state** (NOT scripts/) |
| envelope_escape_ack.json | `~/.hermes/state/envelope_escape_ack.json` | Last human ack record |

**Pitfall**: `~/.hermes/scripts/envelope_state.db` is a stale/empty file — do NOT query it. The real DB is at `~/.hermes/state/envelope_bus.db`.

## Diagnosing Human Escape (Escaped Pipeline)

When `stats` shows `human_escape_triggered: true`, the pipeline is **paused**. Diagnostic steps:

```bash
# 1. Check escape state
python3 ~/.hermes/scripts/envelope_executor.py stats

# 2. Query FAILED envelopes directly (the real DB)
python3 -c "
import sqlite3, json
conn = sqlite3.connect(str(Path.home() / '.hermes/state/envelope_bus.db'))
conn.row_factory = sqlite3.Row
for r in conn.execute('SELECT id, title, project, error, updated_at, retry_count FROM envelopes WHERE status=\"FAILED\" ORDER BY updated_at DESC LIMIT 5'):
    print(f'[{r[\"id\"]}] {r[\"title\"][:80]}  error={r[\"error\"]}  retries={r[\"retry_count\"]}')
"

# 3. Check last ack
cat ~/.hermes/state/envelope_escape_ack.json
```

### Common Escape Causes

| Failure Type | Meaning | Fix |
|-------------|---------|-----|
| `missing_proof` | Worker ran but didn't output PROOF_JSON | Fix worker prompt to include proof gate instructions |
| `invalid_proof` | Worker output malformed JSON | Worker needs better JSON formatting guidance |
| `timeout` | Worker exceeded 600s | Simplify task or increase appetite_seconds |
| HTTP 429/500 in `error` | API rate-limit or server error from the model provider | Retry later; if persistent, check provider quota or switch model. These are infrastructure failures, not proof gate failures. |
| `Appetite timeout after N retries` | Worker exceeded appetite_seconds on all retry attempts | Task too large for appetite budget; split task or increase `appetite_seconds` |

**Failure taxonomy for escape triage:** Not all FAILED envelopes are equal. Classify by root cause before ACKing:
1. **Proof gate** (`missing_proof`, `invalid_proof`) — worker behavior issue; fix worker prompt
2. **Infrastructure** (HTTP 429/500, API errors) — transient provider issue; ACK + retry may resolve
3. **Timeout** (appetite timeout, subprocess timeout) — task sizing issue; split or increase budget
4. **Stale** (ghost RUNNING from killed cron) — infrastructure; reset ghosts before ACKing

**Failure migration after ACK:** After ACKing one failure class, a *different* class can re-trigger escape within hours. This is NOT a regression — the fixed failures were masking the next bottleneck. Example: HTTP 429 failures dominate → ACK after patching → proof-gate failures emerge (workers now reach the proof validation step). Triage: classify post-ack failures; if they're a new type, they were previously masked. Fix the most common one, ACK, expect the next class to surface. Full pattern: see `references/escape-triggered-cron-alert-pattern.md`.

**Project-level clustering is the key diagnostic signal.** If all post-ack failures are in one project with the same error (e.g., 3× `hermes-skill-learning` + `missing_proof`), the problem is systematic worker behavior for that project. If failures are scattered across projects with different errors, it's likely infrastructure flakiness that an ACK + retry could resolve. See `taskpool-control-plane/references/envelope-bus-escape-triage-cli-patterns.md` for the SQL query pattern.

### Resuming After Escape

```bash
# Via CLI
python3 ~/.hermes/scripts/envelope_executor.py ack "reason text"

# Via Python
from envelope_bus import ack_escape
ack_escape("reviewed failures; resume pipeline")
```

### Escaped Pipeline in Cron

The cron prompt pattern `"If status=escaped, ALERT."` triggers a diagnostic report. The cron agent should:
1. Run `stats` to get bus state
2. Query FAILED envelopes from `~/.hermes/state/envelope_bus.db`
3. Report failure pattern + PENDING count + last ack date
4. Recommend: ack to resume, fix proof generation, or purge poisoned envelopes

## Pitfalls
- executor timeout should be 600s (10min) not 1800s (30min) — faster feedback
- PROOF_JSON detection should be fuzzy (check for string, not parse)
- continuation context must be injected BEFORE the prompt, not appended
- max_concurrent should be 1 by default — parallel execution via agent_team_controller
- **Never run `envelope_executor.py run` synchronously in agent terminal** — hermes chat -q subprocess takes up to 600s per envelope, exceeding terminal timeout. Always use `background=True, notify_on_complete=True`.
- **Use `stats` before `run`** — check bus state first (idle? stuck RUNNING? human escape?) to avoid wasting a 600s run cycle on an empty or broken bus.
- **DB is at `~/.hermes/state/envelope_bus.db`** — NOT `~/.hermes/scripts/envelope_state.db`. The scripts/ file is stale/empty. Always query state/ for diagnostics.
- **Escape ack JSON at `~/.hermes/state/envelope_escape_ack.json`** — contains `acked_at`, `acked_by`, `reason`. Use to determine how long pipeline has been paused.
