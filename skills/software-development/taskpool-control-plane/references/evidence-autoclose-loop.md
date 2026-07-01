# Evidence/autoclose loop for taskpool review gaps

Use when the user asks to start automatic taskpool closeout or says missing evidence should be supplemented automatically.

## Goal

Advance review/blocked/pending tasks through the normal governed gates:

- if evidence is missing, create or advance bounded evidence-repair work;
- if evidence is sufficient, let `auto-close-review` consume it;
- never bypass proof-check, lifecycle, permission, mission-envelope, or multimodel gates.

## Safe sequence

1. Baseline hard gates and escape state:

```bash
python3 ~/.hermes/scripts/envelope_bus.py stats
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py review-gap-scan --max-tasks 50 --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --max-tasks 50 --json
```

2. If `human_escape_triggered=true`, inspect post-ack `FAILED`/`BLOCKED` envelope rows read-only. Do not SQL-update/delete them. Ack only when the rows are reviewed terminal debt or their corresponding brain tasks have already been reconciled to `retry`/`review`/`done`/not-active:

```bash
python3 ~/.hermes/scripts/envelope_bus.py ack-escape 'reviewed post-ack terminal envelope failures <ids>; keep envelope audit records; unblock preclaim only'
```

3. Re-run `envelope_bus.py stats` and verify:

- `human_escape_triggered=false`
- `since_ack.failures=0`
- `since_ack.blocks=0`

4. Repair review gaps through the governed creator, not by forcing parents done:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py review-gap-scan --max-tasks 50 --authority autonomous-execution --actor hermes-auto-evidence --write --json
```

If this command times out, do not assume no side effect happened. It may already have created a `补证闭环` child and spawned a multimodel process. Immediately verify with `list --json` and `ps`/job state before retrying, to avoid duplicate children.

5. For each repair child or selected task, add only machine-readable evidence prefixes in YAML `evidence:`:

- `command:`
- `artifact:`
- `file:`
- `url:`
- `proof:`
- `classification:`
- `child-task:`

Put narrative in Proof Log / Final Handoff, not in YAML evidence.

6. Let closeout consume evidence through the normal gate:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 50 --authority autonomous-execution --actor hermes-auto-evidence --json
```

7. Re-verify:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
```

## Dynamic runner interpretation

- `human_escape_active_preclaim` means no claim/mutation happened; clear only via audited `ack-escape` when safe.
- `no_additional_boundary_safe_slots` with active running work means the runner is healthy but respecting concurrency/boundary caps.
- A cron `last_status=error` can lag a manual successful runner invocation; verify with a fresh direct `taskpool_dynamic_runner.py` run and process/list state before declaring the runner broken.

## Cron wiring pattern

For a durable evidence/autoclose loop, prefer a separate LLM cron with a self-contained prompt that:

- baselines `human_escape`, `selfcheck`, `proof-check`, `review-gap-scan`, and `blocked-resolve-step`;
- performs audited `ack-escape` only for reviewed terminal debt;
- creates review-gap children via `review-gap-scan --write`;
- supplements one bounded evidence tranche;
- runs `auto-close-review` rather than forcing `done`;
- emits output only when it took action or found a real blocker.

Tooling pitfall: `cronjob(action="run")` schedules the job for the scheduler's next tick; it may not execute immediately in the current turn. If immediate verification is required, use the Hermes CLI scheduler path (`hermes cron run <job_id>` followed by `hermes cron tick`) and then inspect `cronjob list` / process state. Bound long ticks because LLM cron jobs can legitimately exceed several minutes.

## Anti-conditions

Do not use this loop to:

- push/deploy/send external messages;
- enter secrets or credentials;
- delete data or rewrite envelope audit history;
- weaken proof-check/lifecycle/multimodel gates;
- mark review parents done just because a child was created;
- treat PASS_ADVISORY_ONLY as implementation proof.
