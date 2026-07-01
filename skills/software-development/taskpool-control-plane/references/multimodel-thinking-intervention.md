# Multi-model thinking intervention vs routing

Use this reference when operating taskpool drain loops, multimodel intervention jobs, or blocked/review closeout that mentions “multi-model intervention”.

## Durable distinction

Multi-model intervention means multi-model thinking: target-bound discussion, critique, prioritization, and certification over the task’s evidence bundle.

It does **not** mean that the models are merely choosing a routing strategy, nor that a “multi-model smart routing方案” can substitute for the discussion/ratification artifact.

Routing is only the selector:

- decide whether a task needs multi-model thought;
- choose the target task id;
- choose advisory vs certification tier;
- choose safe background execution timing.

The intervention body is the thinking loop:

1. Build a target-bound evidence state for the exact task.
2. Run `consult_models.py ... --discussion` with the appropriate tier/quorum.
3. Preserve the `discussion_result.json` artifact.
4. Run `ratification-gate` against that artifact and task id.
5. Write back only gate-backed advisory/certification evidence.

## Correct taskpool drain behavior

When a drain loop sees `multimodel_intervention.intervention_required=true`, it should trigger the thinking path, not only report or debate routing. Preferred shape:

```bash
HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 \
python3 ~/.hermes/scripts/brain_task_orchestrator.py \
  multimodel-intervention-step --task "$TASK_ID" --background --json
```

Use `--task` whenever the selector has a specific candidate. Avoid global unscoped selection unless intentionally operating the top-priority multimodel queue.

## Safety boundaries

- Advisory-only discussion may consume weak signals, but it must not authorize `done`.
- Certification closeout still requires `ratification-gate` PASS / LOOP_DONE plus normal proof/completion gates.
- Do not force `done` from route metadata, model agreement text, or a skipped multimodel job.
- If provider/quorum/circuit-breaker issues prevent discussion, record an intervention packet or retry plan; do not reframe routing as completion.

## Verification checklist

- `multimodel-intervention-dry-run --task <id> --json` shows a `run_discussion_command` containing `consult_models.py run ... --discussion`.
- `multimodel-intervention-step --task <id> --background --json` creates a durable job under `~/.hermes/state/taskpool-multimodel/jobs/`.
- `multimodel-intervention-jobs --json` readback shows the target task id, recommended tier, advisory_only flag, log path, and state path.
- The task note receives discussion/gate evidence before any review->done attempt.
