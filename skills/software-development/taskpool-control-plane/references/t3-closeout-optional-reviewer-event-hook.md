# T3 closeout optional-reviewer and event-hook pitfalls

When a T3 ratification round appears blocked by a provider such as Gemini, first compare the failure against `~/.hermes/config/quorum.yaml`:

- `required_models` are hard blockers.
- `optional_models` should produce warnings unless they create unresolved high-severity truth blockers.
- `consult_models.py evaluate_ratification()` and `brain_task_orchestrator.py ratification-gate` must agree on optional-reviewer semantics before lifecycle mutation.

If a `discussion_result.json` was produced by manually running `consult_models.py`, preserve target binding before calling `ratification-gate`:

- `task_id`
- `target_task_id`
- `target_task_path`
- `taskpool_binding.state_sha256`

For certified/review closeout transitions, beware event-hook churn: `HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1` disables multimodel spawn but not the whole dispatch tick. If the event hook reclaims the same target after `review`, use an auditable closeout path that preserves lifecycle gates and suppresses only hook/stream side effects, then record a runtime friction candidate for a first-class no-event-hook mode.
