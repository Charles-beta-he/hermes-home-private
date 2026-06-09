# Kanban worker disabled in config → worker bootstrap crash

Use this when a real Kanban/taskpool dispatch spawns a worker process, but the task immediately crashes and `hermes kanban log <task>` shows `Unknown skill(s): kanban-worker)` or `Unknown skill(s): kanban-worker`.

## Symptom pattern
- `hermes kanban dispatch --dry-run --json` says the task is spawnable.
- Real `hermes kanban dispatch --max 1 --json` creates a run and records `spawned {pid: ...}`.
- The run quickly flips to `crashed` with `pid ... not alive`.
- `hermes kanban log <task>` shows `Unknown skill(s): kanban-worker`.

## Durable root cause
The worker bootstrap path preloads `kanban-worker`. Hermes skill discovery respects the active profile's disabled-skill config, so a copied/bundled `kanban-worker` file is still invisible if `~/.hermes/config.yaml` lists it under `skills.disabled`.

## Verification steps
1. Confirm the task is truly spawnable, not just blocked by profile absence:
   - `hermes kanban dispatch --dry-run --max 1 --json`
2. Inspect the blocked/crashed task:
   - `hermes kanban show <task_id>`
   - `hermes kanban runs <task_id>`
   - `hermes kanban log <task_id>`
3. Check whether runtime skill loading can resolve the worker skill:
   - `python3 - <<'PY'
import sys
sys.path.insert(0, '/Users/charles/.hermes/hermes-agent')
from agent.skill_commands import scan_skill_commands, build_preloaded_skills_prompt
skills = scan_skill_commands()
print('/kanban-worker' in skills)
prompt, loaded, missing = build_preloaded_skills_prompt(['kanban-worker'], task_id='debug')
print('loaded', loaded)
print('missing', missing)
PY`
4. Inspect `~/.hermes/config.yaml` for `skills.disabled:` containing `kanban-worker`.

## Fix
Remove `kanban-worker` from `skills.disabled` in `~/.hermes/config.yaml`, then re-run the runtime check above. Only after runtime resolution succeeds should you unblock and redispatch the task.

## Runtime verification
- Do not stop at file-presence checks such as `~/.hermes/skills/devops/kanban-worker/SKILL.md` existing.
- Confirm the runtime loader now resolves the skill; a reliable probe is importing `agent.skill_commands` and checking that `build_preloaded_skills_prompt(['kanban-worker'], ...)` returns `loaded=['kanban-worker']` and `missing=[]`.
- If the task auto-blocked after repeated crashes, unblock it and re-dispatch so you can prove the repair with a longer-lived run and a completed `task_runs` row.

## Field notes
- Merely copying the skill file is insufficient when the active config still disables the skill.
- Fix lane spawnability (`ON DISK=yes`) and worker bootstrap (`kanban-worker` enabled) as separate layers; the first gets you a PID, the second gets you actual task execution.

## Important distinction
Do not stop at "the file exists under ~/.hermes/skills". The runtime loader can still hide the skill if the active profile marks it disabled.

## Evidence from the acceptance run
In the larger-chain acceptance task:
- runs 1–3 crashed quickly with `pid ... not alive`
- logs showed `Unknown skill(s): kanban-worker`
- after removing `kanban-worker` from `skills.disabled`, run 4 completed and the task reached `done`
- that successful run executed a real `taskpool -> worker -> delegate_task(2 subagents) -> complete` chain
