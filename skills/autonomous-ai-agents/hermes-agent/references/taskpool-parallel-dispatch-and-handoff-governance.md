# Taskpool Parallel Dispatch and Handoff Backlog Governance

Use this reference when Hermes taskpool feels stuck, serial, or laggy, especially when the user asks why async taskpool work is not continuing after a conversation.

## Durable lesson

Low apparent concurrency is often not caused by `max_parallel_agents`; first check whether there are any dispatchable tasks. A healthy parallel dispatcher with zero dispatchable tasks will correctly select zero agents.

## Control-plane entrypoint

Primary tick script:

```bash
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --no-state
```

Parallel autorun entrypoint:

```bash
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --parallel-autorun --max-agents 3 --print-always --no-state
```

Handoff backlog cleanup (current checkout note):

`brain_task_dispatch_tick.py` may not expose `--archive-handoffs` on every installed Hermes version. Check help first:

```bash
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --help
```

If `--archive-handoffs` is unavailable, do not invent the flag. Either leave the selfcheck warning visible, or perform a separate audited manual archive that moves old handoff files into an archive directory while keeping the newest handoffs for traceability.

## Runtime config

Keep dispatch behavior config-driven. `max_parallel_agents` is the conservative floor; in parallel mode the tick can raise the effective cap up to `dynamic_max_parallel_agents` after a read-only boundary dry-run, so Lark/work bursts use their existing `parallel_boundary` / `parallel_group` / `conflict_group` classification instead of being pinned to 3.

```yaml
taskpool:
  dispatch_mode: parallel
  max_parallel_agents: 3
  dynamic_max_parallel_agents: 24
  handoff_archive_threshold: 100
  handoff_archive_keep: 50
```

The tick script should read these values dynamically so tuning does not require code edits. In summaries, check `taskpool_runtime.configured_max_parallel_agents`, `dynamic_max_parallel_agents`, `max_parallel_agents`, and `parallel_cap_source` to distinguish the floor from the effective cap.

## Expected summary fields

A useful tick summary should expose:

- `taskpool_runtime`
  - `dispatch_mode`
  - `max_parallel_agents`
  - whether parallel dispatch was requested
- `parallel_dispatch`
  - dry-run command used
  - `dispatchable`
  - `selected_count`
  - selected tasks / lanes
  - boundary gates
- `handoff_backlog`
  - checked directories
  - counts
  - archive threshold / keep count
  - whether archive was requested
- `evidence_spine`
  - proof/selfcheck/boundary status
  - counts by status and lane

## Handoff directories

Check both current autorun handoff surfaces:

- `~/.hermes/state/autorun/auto_run_handoffs`
- `~/.hermes/state/autorun/parallel_handoffs`

Prefer archive over deletion. Move old files into an archive area so the audit chain survives.

## Debugging sequence

1. Run the summary tick read-only.
2. Inspect `evidence_spine.summary.counts.dispatchable` and `parallel_dispatch.selected_count`.
3. If both are zero, do not blame concurrency. Diagnose why no tasks are eligible:
   - no pending/review/claimed work
   - lane priority preemption
   - kill switch
   - blocked status
   - failed boundary gate
4. If dispatchable tasks exist but selected count is zero, inspect boundary gates and priority mode.
5. If selected count is positive but execution stalls, inspect handoff files and autorun/worker logs.
6. If handoff count exceeds threshold, run with `--archive-handoffs`.
7. Only after eligibility and backlog are understood should you tune `max_parallel_agents`.

## Pitfalls

- `active_count: 0` and `dispatchable: 0` means the parallel dispatcher has nothing to do; increasing max agents will not help.
- Keep tick script high-cohesion and standalone. It should remain usable as a single read-only summary probe and as a controlled autorun entrypoint.
- `background_review.taskpool.mode: suggest` is non-mutating; it records candidates/status but does not enqueue tasks. Do not count it as taskpool load unless mode is `enqueue`.
- Distinguish taskpool continuation from conversation auto-relay. Taskpool dispatch is ledger/handoff driven; auto-relay is conversation-loop recursion after budget/tool exhaustion.
