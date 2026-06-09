# Background review → taskpool suggest/enqueue semantics

Use this when discussing or modifying the post-conversation `background_review.taskpool` integration.

## Semantics

`background_review.taskpool.enabled: true` with `mode: suggest` does **not** add tasks to the local-brain taskpool.

Suggest mode only:
- inspects the bg-review snapshot after a conversation,
- extracts structured task candidates when the review model sees durable follow-up work,
- writes those candidates into the bg-review JSON status and HTML report,
- does not call `brain_task_orchestrator.py add`,
- does not claim/execute taskpool items,
- does not trigger multimodel certification or autorun.

`mode: enqueue` is the side-effecting mode. Only enqueue mode should call taskpool add, and it must pass intelligent-routing metadata such as priority layer, dependency order, evidence bundle, truth gate, requires-multimodel, and expected participants.

## User-facing explanation pattern

When the user asks whether conversation content is being assigned to the taskpool, answer clearly:
- No, not in suggest mode.
- Conversation text is not dumped into the taskpool.
- At most, bg-review abstracts durable follow-up work into structured candidates.
- Candidates are visible in `hermes bg-review --json` and the HTML report.
- Real taskpool mutation requires explicit `mode: enqueue`.

## Safety guardrails before enabling enqueue

Before recommending or enabling enqueue:
1. Observe candidate quality in suggest mode first.
2. Add or verify dedupe/cooldown/max-candidates controls.
3. Avoid enqueueing vague one-off conversation fragments.
4. Keep bg-review lightweight; complex execution belongs to taskpool after routing.
5. Treat multimodel flags as certification contracts, not casual labels.

## Taskpool stall interpretation

If the user reports low concurrency or stuck taskpool after suggest mode is enabled, first verify whether any task is dispatchable. Low apparent concurrency often means `dispatchable_count=0`, not a worker-limit problem.

Useful checks:
- `brain_task_orchestrator.py dashboard --json`
- `brain_task_orchestrator.py next --json`
- `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents N --json`
- `brain_task_orchestrator.py eligibility-check --json`
- `brain_task_orchestrator.py autorun-runner --json`
- `brain_task_orchestrator.py selfcheck --json`

Interpretation:
- `active_count=0`, `next=null`, `dispatchable=false`, or `no_dispatchable_task` means there is no work to parallelize.
- Do not tune concurrency until a concrete dispatchable task exists.
- A selfcheck warning like a large autorun handoff backlog may explain sluggish inspection and should be treated as cleanup work, not proof that suggest mode is mutating the pool.
