# Retry after human-escape release and empty async worker recovery

Use when retry tasks reappear immediately after a blocked/retry recovery pass, especially after `parallel-claim-and-handoff` or `brain_task_dispatch_tick.py --parallel-autorun`.

## Failure signature

Retry tasks may be created by the controller deliberately, not by a new task failure:

- lifecycle shows `claimed -> retry`;
- reason contains `event-driven worker blocked by human escape; claim released for retry`;
- `agent_team_controller.py status --json` previously showed `human_escape_triggered=true` with post-ack `failures >= 3` or `blocks >= 2`;
- task `next_attempt_at` is just the retry delay after safe claim release.

This is a safety release: the controller avoids leaving claims occupied when consume is blocked by envelope escape.

## Recovery sequence

1. Diagnose before promoting.
   - `brain_task_orchestrator.py list --json` and inspect retry lifecycle lines.
   - `agent_team_controller.py status --json` and confirm whether `human_escape_triggered` is now false.
   - If escape is still active, query/understand post-ack FAILED/BLOCKED envelopes before acking. Do not blindly promote.

2. If the only retry cause is historical human-escape release and escape is now clear (`since_ack.failures=0`, `since_ack.blocks=0`), force-promote:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK" \
  --to pending \
  --actor hermes-retry-recovery \
  --authority claim-and-handoff \
  --reason 'retry_recovery_after_human_escape_cleared; last retry was claim release while envelope human_escape was active; since_ack failures=0 blocks=0; preserve proof/multimodel gates' \
  --evidence 'command:agent_team_controller.py status human_escape_triggered=false since_ack_failures=0 since_ack_blocks=0' \
  --force --json
```

3. Dispatch with bounded parallel autorun:

```bash
HERMES_LOCAL_BRAIN_AUTORUN=1 \
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py \
  --print-always --parallel-autorun --max-agents 4 --no-state
```

4. Verify list + worker state:
   - `retry` count should drop;
   - selected tasks should move to `running` or remain `pending` when capacity is full;
   - `agent_team_controller.py worker-jobs --json` should show live jobs for running parallel tasks;
   - `selfcheck` and `proof-check` should remain PASS.

## Empty async worker / false running pattern

Sometimes a task remains `running` even though the async worker job already died and produced no log/proof:

- task status is `running` with a claim/run id;
- corresponding `agent_team_controller.py worker-jobs --json` entry has `alive=false`;
- job log exists but is size 0 or has no PROOF_JSON;
- no matching `hermes chat` worker process exists.

Do not leave this as active capacity. Align it back to `pending` with explicit evidence, then redispatch or start the proper specialized step:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK" \
  --to pending \
  --actor hermes-retry-recovery \
  --authority claim-and-handoff \
  --reason 'no_live_worker_for_running_claim; async job pid exited with empty log before proof; requeue pending instead of leaving false running' \
  --evidence 'command:agent_team_controller.py worker-jobs <job_id> alive=false log_size=0' \
  --evidence 'command:ps no matching hermes worker for task run id' \
  --force --json
```

For tasks whose next safe step is parent ratification rather than ordinary project work, explicitly start the multimodel step instead of relying on a stale claim:

```bash
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 \
python3 ~/.hermes/scripts/brain_task_orchestrator.py \
  multimodel-intervention-step --task "$TASK" --background --json
```

Then verify `multimodel-intervention-jobs --json` shows a live job for that task.

## Evidence hygiene pitfall

When adding repair evidence to task frontmatter, every evidence item must use a structured prefix accepted by proof-check. Avoid ad-hoc prefixes such as `repair:`. Use e.g.:

- `artifact:review-gap-repair child=<id> evidence_collected=<time>`
- `proof:deterministic-gate-refresh <time> selfcheck=PASS proof-check=PASS`
- `command:<exact command> PASS ...`
- `artifact:/absolute/path/to/proof.json`

If dispatch tick fails in `proof_check` after evidence supplementation, inspect the exact failure and normalize only the unstructured evidence line; do not weaken proof-check.

## Interpretation

- Retry after human escape is not proof that the task failed again; it is often a deliberate claim-release safety state.
- Clearing retry by force-promote is safe only after the underlying escape/failure condition is understood and cleared.
- A parent task moving from running to blocked after worker execution may be correct when the worker reports `blocked`; run `blocked-resolve-step` to create narrowed convergence children rather than forcing done.
