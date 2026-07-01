# Taskpool concurrency expansion certification

Use this when a user asks whether taskpool can support more parallel workers, or asks to certify a long-term concurrency expansion plan.

## Landing-zone classifier

- Reusable procedure / verification checklist: keep in this reference and the taskpool-control-plane skill.
- Concrete implementation work (adding gates, refactoring scheduler, changing config): create/advance a taskpool candidate; do not store it as a fake skill.
- Current machine counts, transient provider health, exact task IDs: evidence for the current run only; do not encode as durable truth.

## Core rule

Do not treat `max_agents` or `dynamic_max_parallel_agents` as the real answer. Concurrency is safe only when all effective-capacity inputs agree:

```text
effective_concurrency = min(
  machine_slots,
  provider_slots,
  boundary_safe_slots,
  proof_gate_slots,
  review_capacity_slots,
  dynamic_ceiling,
  human_policy_cap
)
```

If any of these inputs is stale, unobservable, or below the requested concurrency, certify only a guard/metrics slice — not a concurrency raise.

## Evidence sequence

1. Read current runtime/config:
   - `~/.hermes/config.yaml` taskpool section.
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`.
   - `brain_task_orchestrator.py selfcheck --json`.
   - `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents N --json`.
2. Compare `dispatchable_count` with actual `selected_count` after lane priority and boundary selection. A large dispatchable backlog does not imply safe parallel execution.
3. Inspect resource/backpressure fields:
   - `resource_ceiling`, `effective_resource_ceiling`, `quality_slots`, `api_slots`.
   - provider `confidence_gate_status`, hard blockers, soft unknowns.
   - `handoff_backlog_count`, `review_total`, stale claim count.
   - boundary warning groups / `parallel_boundary_conflict`.
4. If fresh evidence downgrades capacity (for example quality slots drop or selected_count falls), update the recommendation immediately. Do not preserve an earlier optimistic plan.

## Canonical implementation surfaces

- `~/.hermes/scripts/brain_task_dispatch_tick.py`
  - runtime config loading, `resolve_parallel_agent_cap`, `api_quota_capacity_probe`, `resource_capacity_probe`, scheduler decision snapshots.
- `~/.hermes/scripts/taskpool_dynamic_runner.py`
  - dynamic recovery and runner cap behavior.
- `~/.hermes/scripts/brain_task_orchestrator.py`
  - `infer_conflict_group_from_task`, `task_parallel_boundary_key`, `parallel_group_key`, boundary selfcheck, parallel dispatch dry-run, review/certification/block resolution.
- `~/.hermes/scripts/model-router.py` and `~/.hermes/scripts/consult_models.py`
  - provider/router health and multi-model certification surfaces.
- Focused tests usually live in `test_brain_task_dispatch_tick.py`, `test_task_boundary_parallel.py`, `test_model_quota.py`, and `test_model_router_quota.py`.

## Multi-model certification pitfalls

- Use exact claim IDs in evidence supports. If claims normalize to `C-001`, evidence must support `C-001`, not `C1`; otherwise the truth gate may report `evidence_coverage=0.0` even when raw evidence exists.
- Separate fanout/truth grounding from final ratification:
  - `fanout_quorum_met` and `truth_can_certify=true` are not the same as final `certified`.
  - If discussion status is `not_certified`, report degraded/amend status even when facts are grounded.
- If models propose implementation against vague targets like “implementation file to be located”, run a read-only file-discovery slice first, then recertify.
- If fresh evidence says current `selected_count` or `resource_ceiling` is below the requested cap, the correct certified next step is guard/readiness instrumentation, not a raise.
- Provider/model timeouts are not durable negative facts. Capture the routing/fallback pattern and health-breaker need, not “model X is broken”.

## Safe rollout ladder

1. **No-action / architecture-only certification**: allowed when file targets and evidence are grounded but no code/config mutation is requested.
2. **Read-only readiness/guard slice**: expose a `concurrency_readiness` verdict with blockers; must not mutate `max_parallel_agents`, `dynamic_max_parallel_agents`, or dispatch selection.
3. **Grey 6 for advisory/evidence only**: only after freshness checks pass and boundary/provider/review blockers are green.
4. **8 advisory/evidence**: only after boundary locks, provider TTL health gates, and review/certification pool separation are implemented and verified.
5. **Work/code/self-Hermes** remains lower concurrency (2-3, self-Hermes commonly 2); external/deploy/destructive stays 1 with explicit authority.

## Readiness verifier checklist

A first implementation slice should report, but not change behavior:

- requested cap vs selected_count after lane priority.
- active_count / claimed / running / stale claims.
- resource_ceiling and quality_slots.
- provider confidence gate, hard blockers, soft unknowns, TTL freshness.
- boundary warning groups and selected/skipped counts by reason.
- handoff/review/certification backlog.
- explicit blockers for 6/8.
- proof that the readiness slice is read-only.

Focused tests should prove a future raise is blocked when selected_count is too low, quality/resource slots are too low, provider confidence is fail-closed/unobservable, boundary warnings remain, stale claims exist, or backlog is high.
