# Recover assignees stuck at `ON DISK=no`

Use when `hermes kanban assignees` shows a lane such as `brain-mirror` as `ON DISK=no`, `hermes kanban dispatch --dry-run --json` reports many `skipped_nonspawnable` tasks, and the board has accumulated ready work that never spawns.

## Fast diagnosis
- `hermes kanban assignees`
- `hermes kanban stats`
- `hermes kanban dispatch --dry-run --max 2 --json`
- `hermes kanban show <oldest-ready-task>` to confirm long-lived `ready` age and `assignee=<lane>`

Signal pattern:
- lane reports `ON DISK=no`
- ready tasks age for hours/days
- dry-run reports `skipped_nonspawnable` rather than proof-gate / governance warnings

## Recovery path used successfully
1. Create the missing profile on disk:
   - `hermes profile create brain-mirror --clone-from default --clone`
2. Re-check lane visibility:
   - `hermes kanban assignees`
   - expected: `brain-mirror` flips to `ON DISK=yes`
3. Re-check dispatchability:
   - `hermes kanban dispatch --dry-run --max 2 --json`
   - expected: old tasks are eligible to spawn instead of being listed under `skipped_nonspawnable`
4. Prove execution with a smoke task:
   - in this session `t_ac68d398` (`test-bridge-debug`) moved `ready -> running -> done`
   - worker wrote a smoke artifact under its workspace and completed normally
5. Prove full lane recovery with a delegate task:
   - in this session `t_c6a30191` completed after running `taskpool -> worker -> delegate_task`
   - completion summary confirmed two child agents finished and results were aggregated by the parent worker

## Important distinction
Creating the profile fixes spawnability only. If spawned workers still die immediately, check worker bootstrap separately (for example, disabled `kanban-worker` in config). The lane can be `ON DISK=yes` and still fail later during worker startup.

## Verification checklist
- `hermes kanban assignees` shows `ON DISK=yes`
- at least one pre-existing stalled task completes
- at least one delegate-bearing task completes
- `task_runs` contains `completed` outcome entries for the recovered lane
