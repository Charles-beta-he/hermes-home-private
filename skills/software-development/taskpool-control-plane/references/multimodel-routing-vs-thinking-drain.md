# Taskpool drain: multi-model routing intervention vs thinking intervention

Applicability: use when operating or modifying taskpool drain loops, dispatch ticks, blocked/review recovery, or multi-model intervention for Hermes taskpool tasks.

## Core distinction

Do not collapse all "multi-model intervention" into one thing. In taskpool operations there are at least two distinct intervention classes:

1. Multi-model routing-plan intervention
   - Purpose: decide the safest next control-plane route for a task or stalled pool state.
   - Typical choices: ordinary worker dispatch, multi-model thinking discussion, review auto-close, blocked-resolve/child progress, retry promotion, or stop-on-hard-gate.
   - Output: routing decision / risks / evidence-needed / rollback or stop boundary.
   - Side effects: advisory only; must not mark tasks done or bypass lifecycle/proof gates.
   - Good default tier: light/medium discussion such as T1 with a small quorum and short max-rounds, unless the routing decision itself is high risk.

2. Multi-model thinking / task-content intervention
   - Purpose: reason about the task substance: decomposition, critique, evidence quality, ranking, certification, unresolved axes.
   - Output: discussion artifact and ratification/advisory result.
   - Side effects: only through governed taskpool commands, e.g. `multimodel-intervention-step` followed by ratification/proof gates.
   - Typical tiers: T2 for advisory/architecture absorption; T3 for certification/ratification.

## Stage-to-model policy

Use different model mixes by purpose, not a single global model route:

- deterministic maintenance: no model calls. Examples: auto-close-review, blocked-resolve-step, retry promotion, boundary reclass, subtask sync.
- routing-plan review: multi-model, low-cost, short discussion; advisory only. Use it to choose the next path, not to complete the task.
- advisory thinking: T2-style discussion where the goal is critique, prioritization, or architecture/value judgment.
- certification / ratification: T3-style quorum discussion plus deterministic `ratification-gate`; model consensus alone is not enough.
- actual execution: worker/agent path; still governed by claim, resource ceiling, boundary isolation, proof, and review gates.

## Safe drain-loop order

When draining toward empty without bypassing gates:

1. Read taskpool state and active workers.
2. If alive workers exist, wait unless there is a verified stale/orphan claim path.
3. Run deterministic maintenance first: auto-close review, blocked-resolve, reconcile/retry promote, boundary reclass, review-gap scan, subtask sync.
4. Run dispatch/parallel autorun under resource and boundary gates.
5. If dispatch probe reports `multimodel_intervention.intervention_required`, first run a bounded multi-model routing-plan intervention for the selected task.
6. Then, if appropriate, run target-bound multi-model thinking via the governed command, e.g. `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 brain_task_orchestrator.py multimodel-intervention-step --task <task_id> --background --json`.
7. Never treat routing advice, advisory-only output, or a successful discussion as `done`. Done still requires the relevant lifecycle/proof/ratification gate.

## Pitfalls

- Pitfall: saying "multi-model intervention" when only routing is being discussed. Say whether it is routing-plan intervention or task-content thinking intervention.
- Pitfall: routing-plan intervention becomes a fake completion path. It must be advisory and evidence-producing only.
- Pitfall: using a high-tier certification quorum for every small routing question. This wastes model budget and can stall drain loops.
- Pitfall: starting broad multi-model work while ordinary workers are still active and healthy. Let execution finish unless the routing review is specifically needed to unblock.
- Pitfall: killing/restarting drain processes can emit exit code 143. If it was an intentional replacement after a logic correction, report it as SIGTERM from the operator action, not as a crash.

## Verification checklist

- `consult_models.py status` shows actual enabled tiers and planners; do not assume model names from memory.
- `multimodel-intervention-dry-run --json` shows recommended tier/advisory status and planned discussion command.
- Background multi-model jobs are checked with `multimodel-intervention-jobs --json`; `alive_count=0` means no current job, not that the system cannot trigger one.
- Drain logs should distinguish events, for example `multimodel_routing_plan_intervention` vs `multimodel_thinking_background_step`.
- A drain loop claim of completion requires fresh taskpool counts plus selfcheck/proof evidence, not just a running background process.
