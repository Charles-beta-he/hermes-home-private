# Envelope Bus & Agent Team Controller — Escape Triage

## Subsystem overview

The **agent team controller** (`agent_team_controller.py`) is a parallel dispatch
system separate from `brain_task_orchestrator.py`. Both scripts live in
`~/.hermes/scripts/`:

```
~/.hermes/scripts/agent_team_controller.py
~/.hermes/scripts/envelope_bus.py
```

The controller's deps (`task_classifier.py`, `dynamic_n.py`, `task_continuation.py`,
`self_optimizing_verifier.py`) are also in `~/.hermes/scripts/`.

Note: `personal-hermes-brain` (`/Users/charles/Code/personal-hermes-brain/hermes/scripts/`)
contains `brain_task_orchestrator.py`, `brain_task_dispatch_tick.py`, and other
brain control-plane scripts — but NOT the envelope bus or agent team controller.
The envelope DB lives at `~/.hermes/state/envelope_bus.db` (older notes may mention `~/.hermes/scripts/envelope_state.db`; that path is stale and may contain no `envelopes` table).

The controller dispatches tasks via an **envelope bus** — a SQLite-backed queue
where each task gets an envelope with status lifecycle (`PENDING → CLAIMED →
RUNNING → DONE/FAILED/BLOCKED`).

## Escape mechanism

The controller has a **human escape** kill switch that halts all dispatch when
failure thresholds are exceeded. This is the primary safety mechanism.

### Thresholds

| Signal | Threshold | Trigger |
|--------|-----------|---------|
| BLOCKED envelopes (since ack) | ≥ 2 | Escape |
| FAILED envelopes (since ack) | ≥ 3 | Escape |

### Ack watermark

The escape system tracks a **human ack watermark** stored at:
```
~/.hermes/state/envelope_escape_ack.json
```

Format:
```json
{
  "acked_at": "2026-05-13T06:22:28Z",
  "acked_by": "human",
  "reason": "reviewed post-ack terminal FAILED envelopes; ..."
}
```

**Key behavior:** A human ack resets the *counter* but does NOT delete historical
FAILED/BLOCKED rows. The `_failure_counts()` function in `envelope_bus.py` filters
by `completed_at` or `updated_at` being *after* the ack timestamp. Tasks created
before the ack but completing after it still count as post-ack failures.

### Post-ack failure tracing

To find which envelopes re-triggered escape after an ack:

```python
import json, sys
sys.path.insert(0, '/Users/charles/.hermes/scripts')
conn = sqlite3.connect('/Users/charles/.hermes/state/envelope_bus.db')
rows = conn.execute(
    "SELECT id, title, created_at, completed_at, updated_at, error "
    "FROM envelopes WHERE status='FAILED' "
    "AND (coalesce(completed_at, updated_at) > '2026-05-13T06:22:28Z') "
    "ORDER BY created_at"
).fetchall()
```

Replace the timestamp with the `acked_at` value from `envelope_escape_ack.json`.

## Proof gate error types

When the controller marks an envelope FAILED, the `error` field indicates why:

| Error | Meaning |
|-------|---------|
| `missing_proof` | Worker completed but didn't produce a proof artifact |
| `invalid_proof` | Worker produced a proof artifact but it was malformed or failed validation |

Both are proof-gate discipline working correctly — the system refuses to mark
DONE without valid proof.

## Running the controller

```bash
# Run a dispatch cycle
python ~/.hermes/scripts/agent_team_controller.py cycle

# Get envelope bus stats
python ~/.hermes/scripts/envelope_bus.py stats

# Acknowledge escape to resume dispatch
python ~/.hermes/scripts/envelope_bus.py ack-escape "reason for re-enable"
```

### Cycle output interpretation

The `cycle` command returns JSON:
- `status: "idle"` — nothing to dispatch, all quiet
- `status: "tasks_claimed"` — N tasks were claimed; includes `conflict_groups`
- `status: "escaped"` — escape threshold hit; dispatch halted
- `status: "error"` — controller error

## Cron job context

This controller is monitored by a cron job that runs `agent_team_controller.py cycle`
and reports status. The cron prompt expects:
- `idle` → silent (no output)
- `tasks_claimed > 0` → report count and conflict groups
- `escaped` → ALERT with full diagnostics
- `error` → report error
- N changed (smoothing) → note scaling

## Fast triage for ESCAPED status

1. Run `envelope_bus.py stats` to see current counts and escape info.
2. Identify post-ack failures: query envelopes where `coalesce(completed_at, updated_at) > acked_at`.
3. Check the `error` field — `missing_proof` / `invalid_proof` means proof gate is working.
4. If failures are understood and acceptable, re-enable with `ack-escape`.
5. If failures indicate a systemic worker bug, fix the worker before re-enabling.

## Pitfalls

- The ack file uses `completed_at` OR `updated_at` for filtering — not `created_at`.
  A task created days before the ack can still trigger escape if it completes after.
- Historical FAILED rows (18 in the observed case) are preserved for audit and do
  NOT reset on ack. Only the *counter* resets.
- The controller and its deps all live in `~/.hermes/scripts/`. Don't look in
  `personal-hermes-brain` for envelope bus scripts — that repo has the brain
  control plane (`brain_task_orchestrator.py`, etc.) but not the agent team controller.
- `agent_team_controller.py` imports from `envelope_bus.py`, `task_classifier.py`,
  `dynamic_n.py`, `task_continuation.py`, and `self_optimizing_verifier.py` — all
  co-located in `~/.hermes/scripts/`.
- The envelope DB is `~/.hermes/state/envelope_bus.db`; `~/.hermes/scripts/envelope_state.db` is stale/incorrect for current controller triage.
