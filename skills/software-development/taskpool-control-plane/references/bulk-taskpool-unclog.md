# Bulk Taskpool Unclog — When the Pool is Congested, Not Stalled

Use this when the pool has dispatchable work but systemic congestion prevents it:
- many stale `claimed` tasks from parallel workers that exited without releasing
- blocked tasks stuck in `PASS_ADVISORY_ONLY` + `CONTINUE_LOOP` that need multimodel retry
- review tasks stranded because they lack project evidence (test/build/browser/curl/commit)

This is different from the single-task bounded advance (`full-pool-advance-bounded-loop.md`). That handles "advance one task carefully." This handles "the pool itself is clogged with 20+ stuck items."

## Three-phase unclog sequence

### Phase 1: Release stale claims in bulk

Identify all tasks stuck in `claimed` by stale workers:

```bash
cd ~/Documents/brain/05-实践与项目/tasks
grep -l '^status: claimed' *.md
```

Release them all back to `pending`:

```python
# In execute_code for efficiency
for tid in task_ids:
    terminal(f"python3 ~/.hermes/scripts/brain_task_orchestrator.py transition '{tid}' "
             f"--to pending --actor hermes --authority claim-and-handoff "
             f"--reason bulk_stale_claim_release --force --json 2>&1", timeout=30)
```

Verify: `claimed` count drops to near zero.

### Phase 2: Unblock blocked tasks for retry

Check blocked tasks and their multimodel state:

```bash
for f in $(grep -l '^status: blocked' *.md); do
  grep -E '^(multimodel_last_gate_status|multimodel_last_decision):' "$f"
done
```

Release blocked tasks to `pending` so dispatch can re-evaluate them:

```python
for tid in blocked_ids:
    terminal(f"python3 ~/.hermes/scripts/brain_task_orchestrator.py transition '{tid}' "
             f"--to pending --actor hermes --authority claim-and-handoff "
             f"--reason retry_multimodel_unblock --force --json 2>&1", timeout=30)
```

### Phase 3: Requeue review tasks lacking evidence

Check review tasks for project evidence gaps:

```bash
# auto-close-review will reject tasks without test/build/browser/curl/commit evidence
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 50 --json
```

The skipped tasks have `failures: ["project-evidence-review-done requires test/build/browser/curl/commit/project-verification evidence"]`. Requeue them to `pending`:

```python
for tid in review_ids:
    terminal(f"python3 ~/.hermes/scripts/brain_task_orchestrator.py transition '{tid}' "
             f"--to pending --actor hermes --authority claim-and-handoff "
             f"--reason review_evidence_gap_requeue --force --json 2>&1", timeout=30)
```

### Final: Dispatch tick to re-activate the pool

```bash
HERMES_LOCAL_BRAIN_AUTORUN=1 HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 \
  python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --parallel-autorun --no-state --max-agents 24
```

Verify with:
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
```

Expected outcome: `dispatchable` jumps from ~1 to ~18+, `blocked` and `review` drop to 0.

## Valid transition authorities

`brain_task_orchestrator.py transition --authority` accepts an enum. **Invalid values fail silently** — the task stays in its current status with no error message.

| Authority | Use case |
|---|---|
| `read` | Read-only inspection |
| `dry-run` | Simulate transition without writing |
| `dispatch-hint` | Advisory routing suggestion |
| `claim-and-handoff` | Release stale claims, requeue stuck tasks |
| `budget-handoff` | Context-budget-driven release |
| `autonomous-execution` | Full autonomous pipeline |
| `yolo-execution` | Skip safety gates |

**Pitfall**: Do not invent free-form authority names like `stale-claim-cleanup`. argparse accepts them without error but the transition silently does nothing. Always use one of the values above.

## Dispatch tick flags reference

| Flag / Env | Effect |
|---|---|
| `HERMES_LOCAL_BRAIN_AUTORUN=1` | Enable autorun execution mode |
| `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1` | Enable multimodel intervention |
| `--parallel-autorun` | Dispatch multiple tasks in parallel |
| `--max-agents N` | Cap concurrent workers (use 24 for full capacity) |
| `--no-state` | Skip state file read (faster, stateless) |
| `--summary` | Concise output instead of full JSON |
| `--print-always` | Always emit full JSON payload |

Note: `multimodel-intervention-step` can take >120s when it runs real external model discussions. This is expected, not a failure. Run it in background or with generous timeout.

## When to use which unclog pattern

| Symptom | Pattern |
|---|---|
| Pool has 0 running, many claimed but stale | Phase 1 (bulk claim release) |
| Many blocked PASS_ADVISORY_ONLY tasks | Phase 2 (unblock for retry) |
| Many review tasks auto-close-review rejects | Phase 3 (evidence gap requeue) |
| All three above (congested pool) | Full three-phase sequence |
| Single task stuck, need careful evidence | `full-pool-advance-bounded-loop.md` |
| Pool has no dispatchable tasks at all | `no-running-final-drain-and-policy-boundary.md` |

## Pitfalls

- Do not call `multimodel-intervention-step` inline with 30s timeout — it needs 120s+ or background execution.
- `auto-close-review` only checks structured evidence fields, not body text. A task with "pytest passed" in its body but no `evidence:` entry will still be rejected.
- After bulk unclog, the dispatch tick will auto-claim many tasks. Don't assume claimed=11 is a problem — it means dispatch is actively working.
- Review tasks requeued to pending will re-enter the full pipeline (multimodel discussion → project execution → review). If they lack clear acceptance criteria, they may cycle back to review without evidence again.
