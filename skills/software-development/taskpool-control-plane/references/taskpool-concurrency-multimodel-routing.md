# Taskpool concurrency expansion with multi-model routing

Use when the user asks whether Hermes taskpool can support more parallel workers, or asks for a long-term concurrency plan.

## Landing-zone classification

- Reusable procedure / verification checklist -> this reference.
- Exact run artifacts, tick dirs, one-day task ids -> do not save as durable rules; cite them only in the current report.
- Concrete implementation work such as adding boundary locks/provider health gates -> taskpool proposal, not a fake skill.

## Evidence-first inspection sequence

1. Read current taskpool config and do not infer concurrency from a single knob:
   - `taskpool.dispatch_mode`
   - `taskpool.max_parallel_agents`
   - `taskpool.dynamic_max_parallel_agents`
   - `taskpool.batch_executor_*`
   - delegation and cron parallelism if workers can spawn children.
2. Run/read the control-plane evidence:
   - `brain_task_orchestrator.py selfcheck --json`
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`
   - `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents <N> --json`
3. Separate these facts:
   - configured ceiling;
   - runtime `resource_ceiling`;
   - dry-run candidate supply;
   - active/running/claimed count;
   - stale claim count;
   - boundary conflict groups;
   - review/certification backlog;
   - provider quota/health confidence.

## Capacity model

Do not recommend persistent higher concurrency from `selected_count` alone. Use:

`effective_concurrency = min(machine_slots, provider_slots, boundary_safe_slots, proof_gate_slots, review_capacity_slots, dynamic_ceiling, human_policy_cap)`

A dry-run that selects 8 tasks proves candidate supply, not safety. Persistent 8+ requires evidence that provider health, boundary locks, proof/review, and certification queues can absorb the load.

## Safe rollout pattern

- Safe-now default: keep the current runtime/resource ceiling unless selfcheck/tick/provider readback shows headroom.
- Grey 6: advisory/evidence/read-only only, after fresh guard readbacks.
- Advisory/evidence 8: only after boundary locks, provider TTL breakers, and review/certification pool separation are implemented and verified.
- Code-writing/work: usually 2-3.
- Hermes self-code changes: usually 2 unless isolated.
- Review/certification: separate pool, usually 1-2.
- External/deploy/destructive: 1 plus explicit authority and rollback/readback.

## Required hardening before persistent 8+

1. Boundary lock matrix:
   - same task exclusive;
   - same parent exclusive unless explicit `parallel_group`;
   - same repo write exclusive;
   - same evidence path exclusive;
   - same `conflict_group` incompatible;
   - read-only shared.
2. Provider health/routing:
   - TTL breakers for timeout/quota/auth failures;
   - hard quota/auth/rate-limit blocker -> provider slots 0;
   - unknown/unobservable quota may permit grey low-risk advisory routing but must not certify persistent 8+.
3. Queue separation:
   - worker, review, and certification queues/pools separated;
   - worker intake throttles when review/certification backlog rises;
   - parent unblock requires children + evidence + certification;
   - workers never mark done directly.
4. Backpressure checks:
   - stale claims;
   - timeout rate;
   - handoff backlog;
   - continuation backlog;
   - review/certification backlog;
   - proof quality / certification inconclusive rate.

## Multi-model routing/certification boundary

For a long-term plan, route to role-separated models when available:

- Claude: architecture/control-plane arbitration.
- DeepSeek: adversarial/safety review.
- GPT/Codex: implementation/runtime patch feasibility.
- Gemini: UI/visual/operator dashboard aspects when relevant.
- MiMo: low-cost T0/Chinese execution-policy sanity check when healthy.

Report the certification boundary precisely:

- `fanout_quorum_met` + `truth_grounded` means the facts were grounded and enough planners answered.
- It does **not** mean final certification passed.
- Full certification also needs ratification approvals, `best_within_constraints=true`, no unresolved severity>=3 issues, agreement above threshold, and clear noop-vs-change intent.
- If all votes are `amend`, call the plan `multi-model routed / truth-grounded / not fully certified`, not `certified`.

## Common pitfall: increasing max_agents is not the fix

If the pool shows boundary conflicts, stale claims, review/certification backlog, or provider health uncertainty, raising `max_agents` can create more blocked/review work instead of throughput. First classify the limiting factor, then either improve locks/health/backpressure or restrict higher concurrency to low-risk read-only/advisory work.
