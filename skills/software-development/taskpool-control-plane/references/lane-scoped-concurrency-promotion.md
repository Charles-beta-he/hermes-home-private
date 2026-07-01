# Lane-scoped concurrency promotion

Scope: Hermes taskpool/control-plane only. This reference is for local taskpool lane-scoped concurrency promotion and readback. It is not a global rule for other projects or schedulers.

Applicability:
- Raising taskpool concurrency for a named lane such as `advisory`.
- Local config/readback/autorun verification is authorized.

Anti-conditions:
- Not authority for global concurrency, external dispatch, deploy/push, destructive cleanup, payment, credential entry, or non-taskpool schedulers.
- Not proof that N workers are running unless final task/worker readback shows N non-stale active tasks.

Checklist:
1. Separate scope from capacity.
   - State whether target is global or lane-scoped.
   - Read back `max_parallel_agents`, `dynamic_max_parallel_agents`, `parallel_dispatch_lane`, and optional `api_quota_models`.

2. Separate selection from provider/resource gates.
   - Use read-only lane dry-run (`parallel-dispatch-dry-run --max-agents N --lane <lane> --json`).
   - Inspect `selected_count`, `active_count`, `projected_active_count`, and `boundary_readiness.status`.
   - If boundary conflicts limit selection, current task supply cannot fill N even if config cap is N.

3. Test target config before production config.
   - Use a temporary config with target cap, dynamic cap, lane, and active quota model set.
   - Tick readback must show target readiness PASS with resource, quality, API, stale-claim, and boundary blockers clear.

4. Gate quota against the active worker/reviewer model set.
   - Use `taskpool.api_quota_models` for the actual worker/reviewer models rather than a stale default certification set.
   - If a model route is unavailable, verify a replacement route and update verifier defaults or env override.
   - Refresh provider evidence with appropriate smoke/probe when confidence flips to unknown.
   - Pitfall: successful calls with no quota headers may overwrite documented no-header evidence as unknown; refresh the documented smoke/probe before judging readiness.

5. Treat multi-model certification carefully.
   - Fanout quorum and truth grounding are not the same as discussion certification.
   - If discussion is `not_certified`, report degraded review explicitly and keep any local bounded action scoped to the already-authorized boundary.

6. Apply with official config commands.
   - Prefer `hermes config set` for production config changes.
   - For lane-scoped promotion, set cap, dynamic cap, lane, and active quota model set.

7. Verify real autorun.
   - Run one bounded `brain_task_dispatch_tick.py --summary --parallel-autorun --no-state --max-agents N`.
   - Read back autorun claimed count, worker trigger, task list, worker jobs, stale claims, and escape state.
   - If human escape blocks worker consumption, inspect envelope stats and recent terminal rows. Only acknowledge the escape watermark after verifying there are no live timeouts or claimed/running orphans.

Acceptance language:
- “Configured/admitted N” = config/readiness supports N.
- “Claimed N” = a real autorun claimed N tasks.
- “Running N” = final task/worker readback shows N non-stale active tasks.
- If boundary conflicts or task supply reduce active count, say: cap/readiness is N, current pool can only run M non-conflicting tasks.
