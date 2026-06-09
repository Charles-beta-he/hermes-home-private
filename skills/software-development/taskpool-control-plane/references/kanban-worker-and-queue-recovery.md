# Kanban worker bootstrap and queue recovery

Durable patterns validated in session:

1. If `hermes kanban assignees` shows an assignee with `ON DISK=no`, the lane may be historically populated but non-spawnable. Recover by creating the missing profile, typically cloning from `default`:
   - `hermes profile create brain-mirror --clone-from default --clone`
   Then verify with:
   - `hermes kanban assignees`
   - `hermes kanban dispatch --dry-run --max 2 --json`

2. If worker runs crash immediately and logs show `Unknown skill(s): kanban-worker`, do not stop at copying files. Check whether `kanban-worker` is explicitly disabled in `~/.hermes/config.yaml` under `skills.disabled`. Removing it restores runtime resolution.

3. Runtime verification for the fix can be done inside Hermes source tree with:
   - import `scan_skill_commands` and `build_preloaded_skills_prompt`
   - confirm `/kanban-worker` is visible and `missing == []`

4. Large blocked backlogs are not necessarily control-plane failures. First classify blocked reasons from latest `task_runs.summary` / `error`:
   - `Iteration budget exhausted` => safe candidate for batch `hermes kanban unblock ...`
   - `review-required:` => keep blocked pending human verification
   - missing external source / prototype / comment text => keep blocked until the source is available

5. After batch unblocking budget-exhausted tasks, verify that the lane is genuinely healthy:
   - `hermes kanban dispatch --max N --json`
   - inspect `tasks.status` counts
   - verify all `running` tasks still have live worker PIDs via `ps`

6. When a lane is repaired, expect queue state to shift from `blocked` to `ready` to `running`. Judge success by real worker activity and completion records, not by dry-run alone.
