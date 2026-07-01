# Multimodel Certification Loop Handoff Pitfalls

Use when operating taskpool closeout/certification handoffs where a task is blocked by multimodel ratification and repeated `multimodel-intervention-step` attempts.

## Durable lessons

1. Do not treat a successful advisory/dry-run plan as lifecycle authority. `T2_advisory` or dry-run output can diagnose next steps, but it cannot authorize `review`, `certified`, or `done`.
2. Repeated T3 failures may trigger economy/throttle behavior that downgrades future dry-run plans to `T2_advisory`. Once that happens, stop trying to close the task and inspect the certification runtime or provider output first.
3. If a canonical multimodel step claims a task and then terminates without a JSON completion artifact, repair the lifecycle to a safe blocked state before doing anything else.
4. When intentionally moving a task to `blocked` to stop a runaway multimodel loop, disable event-hook multimodel spawning for that transition:

```bash
HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1 \
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition TASK_ID \
  --to blocked \
  --actor dev-closure-certification-controller \
  --authority autonomous-execution \
  --reason 'stop multimodel route; leave blocked pending certification repair' \
  --evidence 'command:...; artifact:/absolute/path/to/intervention.md' \
  --force \
  --json
```

Without this env guard, the transition event hook can immediately re-route the same task back into `hermes-multimodel` (`blocked -> claimed -> running`), hiding the intended blocked state.

## Applicability

- Applies to taskpool control-plane operations, certification/ratification handoffs, and dev-closure closeout adapters.
- Especially relevant when the user authorizes full progression but canonical gates still require certification PASS before closeout.

## Anti-conditions

- Do not use the env guard to bypass normal certification. It is only for stabilizing a task after a failed or runaway multimodel attempt.
- Do not force `done` from `blocked`, `pending`, or `running`; close through `review`/`certified` only after the ratification gate PASSes.
- Do not record provider credential failures as durable tool defects. Capture only the recovery/control-plane pattern.
