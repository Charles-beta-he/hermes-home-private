# Taskpool dynamic boundary-aware scheduler SSOT — 2026-05-28

schema: hermes_runtime_self_change_v1
id: taskpool-dynamic-boundary-aware-scheduler-20260528
scope: /Users/charles/.hermes/scripts/brain_task_dispatch_tick.py
request: 全盘落地任务池动态并行、双向 hooks、多任务合并修改流程，并保持目标不变、感知边界。

## Non-negotiable goals

- 提高 taskpool 吞吐，不能靠削弱任务验收或安全边界。
- 任务验收仍逐任务完成：batch 可以共享实现/验证链，但不能合并 acceptance 语义。
- Worker 不得直接 mark done；只能推进到 running/review/retry/blocked，done 仍由 proof-gated closeout 处理。
- parallel_boundary / dependency / side-effect / external-control / production risk 是硬边界；机器/API/质量只决定资源天花板。
- Hooks 只能通过结构化事件和 ack 影响调度；不得绕过权限、扩大任务范围或静默吞错。

## Multi-model advisory evidence

This change is grounded in the live multi-model discussion from this session:

- Claude Opus 4.7 advisory: keep per-task atomicity, fail isolation, no shared worktree without proof, no merged acceptance, reviewer separate from writer.
- Codex / GPT-5.5 advisory: implement conservative dynamic parallelism + bidirectional hooks + controlled merge coordinator; resources/boundaries/quality are joint gates, not weighted scores.

Certification status: advisory, not truth-gate certification. Code evidence and tests below are the implementation SSOT.

## Landed design

### 1. Resource-aware dynamic ceiling

`dynamic_max_parallel_agents` is treated as a probe ceiling. The effective probe is further capped by `resource_capacity_probe()`. Resource pressure may lower effective concurrency below the configured floor unless the operator explicitly passes `--max-agents`:

- machine slots: CPU count, 1m load average, disk pressure;
- API slots: optional `HERMES_TASKPOOL_RESOURCE_CAP` / `HERMES_TASKPOOL_API_CAP` and `model_quota.py confidence-gate --json` hard-blocker evidence; unknown/unobservable quota remains telemetry and does not collapse concurrency by itself;
- quality slots: reserved hook point for live success/timeout/review feedback.

The scheduler asks the boundary selector only up to the resource-aware ceiling. Boundary/dependency checks still decide which tasks can actually run.

### 2. Drain-first hook

Under explicit `--parallel-autorun`, dispatch tick now checks existing `claimed` tasks before claiming more pending work:

1. re-read the freshest task list;
2. read `agent_team_controller.py worker-jobs`;
3. identify strictly Hermes-owned parallel claimed rows (`hermes-parallel` / `hermes-parallel-follow-through`) not covered by live worker jobs; stale foreign-actor cleanup remains a separate stale-claim path;
4. trigger `consume-claimed` for those rows;
5. do not claim new tasks inside the drain hook;
6. do not mark tasks done.

This prevents claimed leases from occupying boundary slots with no worker owner.

### 3. Scheduler decision telemetry

Every summary now includes `scheduler_decision`:

- active_count;
- resource_ceiling;
- selected_count;
- skipped_reason_counts;
- action classification;
- selected=0 reason classification;
- batch merge candidates.

This separates "resource full" from "boundary conflict" from "no dispatchable task".

### 4. Bounded completion refill hook

`event_next_tick_follow_through()` can now, when explicitly enabled in taskpool config (`event_refill_enabled: true`; default is fail-closed false) and worker output requests follow-through:

1. auto-close review;
2. run boundary dry-run at current max_agents;
3. run exactly one bounded `parallel-claim-and-handoff` refill if slots exist;
4. start `consume-claimed` for the refill batch;
5. stop at bounded depth.

No recursive unbounded tick and no direct done by workers.

### 5. Batch merge candidate detection

When boundary conflicts accumulate, the scheduler emits `batch_merge_candidates` grouped by boundary key. This is propose-only:

- it does not execute merged code changes;
- it does not close child tasks;
- it only identifies likely merge groups for a future coordinator.

A future Batch Coordinator must prove goal compatibility, touched-file compatibility, per-task acceptance mapping, rollback strategy, and risk class before execution.

## Safety boundaries

- `drain_claimed_first` only runs under explicit `--parallel-autorun`.
- `event_refill_enabled` defaults false; it only matters when a worker requested follow-through and depth > 0.
- Batch merge is telemetry/propose-only in this patch.
- Worker-job coverage is fail-closed: if worker-job status cannot be read, drain-first skips.
- Existing `human_escape`, proof/evidence gates, worker timeout cleanup, and proof-gated review closeout remain in force.

## Verification commands

- `python3 -m py_compile ~/.hermes/scripts/brain_task_dispatch_tick.py ~/.hermes/scripts/test_brain_task_dispatch_tick.py`
- `python3 ~/.hermes/scripts/test_brain_task_dispatch_tick.py`
- `python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --no-state`

## Derived entrypoints

- Chat summary should reference this SSOT rather than restating a second source of truth.
- Taskpool future evolution tasks should reference this SSOT path when implementing the actual Batch Coordinator executor.
- Skill updates should describe procedure only; this document controls the specific 2026-05-28 runtime landing.

## Post-implementation multi-model amendment ledger

A second real multi-model review of the diff returned AMEND, and the must-fix items were applied before commit:

- Drain-first now filters strictly to Hermes-owned parallel claims, re-reads fresh task rows before worker coverage, and leaves human/foreign claims untouched even if stale (stale foreign-actor cleanup remains separate).
- Event refill default is fail-closed (`false`); enabling it requires explicit taskpool config.
- Resource pressure now initializes the effective cap and can lower effective concurrency below the configured floor for non-CLI runs, even if later boundary probe fails.
- Added focused refill-path tests proving one bounded refill round when explicitly enabled, timeout cleanup for follow-through claims, and no claim side effect when refill remains default-off.

Remaining accepted risks:

- API slots now consume `model_quota.py` confidence-gate hard blockers and explicit env caps; quality slots are still conservative hook points rather than live success/timeout integrations.
- Batch merge candidates are propose-only telemetry; no coordinator executor consumes them yet.

- Final Codex复审指出 follow-through refill worker timeout 需要与主 autorun 同等 cleanup；已补充 `refill_worker_timeout_cleanup`，actor=`hermes-parallel-follow-through`。

- Final Codex复审继续要求 refill worker 任意失败都释放刚 claim 的任务；已将 cleanup 扩展到所有非 OK/PASS/SKIP worker trigger failure，并保留 timeout alias。


## Follow-up landing: API quota hard-blocker cap

After the initial commit, `resource_capacity_probe()` was extended to call `api_quota_capacity_probe()`, which reads `model_quota.py confidence-gate --json`. The mapping is deliberately non-catastrophic:

- `exhausted`, `rate_limited`, `malformed`, and `unavailable` snapshots are hard blockers and reduce API slots.
- `unknown` / `unobservable` / stale confidence failures remain visible as soft unknown telemetry but do not collapse taskpool concurrency by themselves.
- `HERMES_TASKPOOL_API_CAP` is an explicit operator override for API slot cap.
- `HERMES_TASKPOOL_RESOURCE_CAP` remains the global cap override.

This turns provider quota evidence into a real scheduling input without making missing quota evidence slower than the old fixed pool.

- Follow-up multi-model review required that confidence-gate unavailable errors must not echo stdout/stderr because provider errors may contain sensitive context; `api_probe.confidence_gate_error` now keeps only status/reason/returncode and has focused regression coverage.


## Follow-up landing: boundary-aware completion slices

The full landing after the API hard-blocker cap adds the remaining safe slices agreed by real multi-model review:

- Sanitized API quota TTL cache: `model_quota.py confidence-gate --json` evidence is cached briefly under state to avoid making every tick pay the full provider-probe cost. The cache stores only controlled fields (status/counts/hard/soft blocker summaries) and never raw command output or environment.
- Quality slots: recent dispatch tick history and worker-job failures produce a concurrency reducer only. Insufficient history is neutral. Quality slots never increase capacity, never change boundary selection, and never bypass proof/acceptance.
- Stale Hermes-owned claim reclaim: implemented as a dedicated path separate from drain-first. It only considers expired `claimed` rows owned by `hermes-parallel` / `hermes-parallel-follow-through`, with `run_id`, no alive worker coverage, and defaults to dry-run unless explicitly enabled for apply.
- Batch merge plan manifest: batch candidates now produce a propose-only JSON artifact under state. The artifact contains candidate boundaries, task IDs, required proof/acceptance mapping, non-goals, and explicit human-approval requirement. It performs no source edits and no lifecycle transitions.

Still forbidden: automatic batch code execution, merged acceptance, default-on event refill, foreign-actor claim reclaim, and any done transition outside the existing proof-gated closeout.


### Multi-model AMEND closure for completion slices

Final review raised two hard requirements and two config-drift risks; all were closed before commit:

- Stale reclaim apply now requires `stale_claim_reclaim_enabled: true`; `--parallel-autorun` may surface dry-run candidates but cannot apply if the reclaim feature is disabled.
- Stale reclaim revalidates immediately before mutation by re-reading task rows and worker jobs, then only transitions if the row is still an expired Hermes-owned claim with no alive worker coverage.
- `quality_slots_enabled` is honored by `resource_capacity_probe()`; disabled quality slots become a neutral cap.
- `api_quota_cache_ttl_seconds` is passed into the API quota probe instead of relying only on environment overrides.


## Runtime enablement approval (2026-05-28)

User approved enabling all implemented boundary-aware controls. Runtime config now enables:

- `taskpool.max_parallel_agents: 24`
- `taskpool.dynamic_max_parallel_agents: 24`
- `taskpool.drain_claimed_first: true`
- `taskpool.event_refill_enabled: true`
- `taskpool.api_quota_cache_ttl_seconds: 45`
- `taskpool.quality_slots_enabled: true`
- `taskpool.stale_claim_reclaim_enabled: true`
- `taskpool.stale_claim_reclaim_dry_run: false`
- `taskpool.batch_merge_manifest_enabled: true`

Boundary retained after approval:

- Batch merge remains `propose_only`; the dispatcher writes durable manifests but does not execute merged source edits or merged acceptance.
- Stale reclaim is apply-enabled only for expired Hermes-owned parallel claims with fresh worker coverage revalidation; it never touches human/foreign claims and never transitions to done.
- Event refill is enabled, but still bounded by resource/API/quality slots, selected task count, and fail-closed worker-start cleanup.
- API quota cache remains sanitized; raw stdout/stderr/env are not persisted.


## Batch Coordinator executor landing (2026-05-28)

A controlled executor has been added for batch merge manifests. Multi-model boundary review converged on a thin coordinator rather than a new execution or acceptance path:

- The executor consumes one manifest boundary bucket at a time.
- It re-reads the fresh task list before any side effect.
- It only claims `pending` / `retry` tasks that are still dispatchable.
- It claims with actor `hermes-batch-coordinator` and a batch run id.
- It hands the claimed rows to the existing `agent_team_controller.py consume-claimed` path, so each child task still advances independently to `running` / `review` / `retry`.
- It writes a durable batch lease under state for idempotence/audit.
- It never writes source files, never marks tasks done, never merges acceptance, and never bypasses proof-gated closeout.
- If the worker trigger fails after claims, it runs the same retry cleanup pattern used by event workers.

Runtime enablement after user approval:

- `taskpool.batch_executor_enabled: true`
- `taskpool.batch_executor_dry_run: false`
- `taskpool.batch_executor_require_approval: false` (the chat approval is the operator approval for this rollout)
- `taskpool.batch_executor_max_tasks_per_batch: 8`
- `taskpool.batch_executor_per_batch_parallelism: 1`
- `taskpool.batch_executor_skip_when_regular_selected: true`

The last flag preserves the current high-throughput path: when normal boundary-safe parallel dispatch already selected tasks, the executor skips instead of over-claiming beyond the resource/API/quality ceiling. It activates when the scheduler is otherwise stalled on batchable boundary conflicts.


### Batch executor AMEND closure

Post-diff multi-model review returned AMEND and the must-fix items were applied:

- Batch executor eligibility now requires `dispatchable is true`; missing/unknown dispatchability is not enough to claim.
- `consume-claimed` status `SKIP` after claims is treated as a worker trigger failure and runs cleanup, preventing claimed-without-worker wedges.
- Scheduler execution requires the current tick manifest path; it does not fall back to the latest historical manifest during automatic runs.
- Batch run ids include a microsecond timestamp suffix so audit leases are not overwritten by repeated manifest attempts.
- Runtime summary exposes `batch_executor_skip_when_regular_selected` for overclaim auditability.


## Bounded real-flow recovery after human escape (2026-05-28)

User explicitly requested real taskpool flow recovery with multi-model boundary control.

Evidence before recovery:
- `envelope_bus.py stats` reported `human_escape_triggered=true`, since_ack blocks=1 and failures=3.
- Post-ack terminal rows were heterogeneous: HTTP 500/502 -> missing_proof, appetite timeout, session_id failure, and one blocked Hermes benchmark task.
- Taskpool had claimed rows but `agent_team_controller.py worker-jobs` had no alive worker for those rows.

Multi-model boundary review:
- Claude Opus 4.7: RESUME_WITH_BOUNDS; release claimed-without-worker rows, ack escape explicitly, recover in a bounded single/canary round, keep proof gates and no auto-done.
- MiMo v2.5 Pro via `consult_models.py` T0 fanout: staged restart at reduced capacity, reaper/release phantom claims, keep human escape logic unchanged, monitor worker_alive_count / phantom_claim_count / consecutive failures.
- A Codex read-only run timed out; its absence was treated as degraded advisory, not a reason to skip the two successful real-model checks.

Actions taken:
1. Released 9 Hermes-owned claimed-without-worker rows through `agent_team_controller.py consume-claimed` while human_escape was still active. Controller returned `released_count=9` and moved them to retry; no workers ran and no task was marked done.
2. Ran `envelope_bus.py ack-escape` with operator-approved recovery reason. `human_escape_triggered=false`, since_ack blocks=0/failures=0.
3. Ran a bounded real `brain_task_dispatch_tick.py --parallel-autorun --max-agents 6`, which claimed 6 boundary-safe tasks and started a durable async worker job.
4. Temporarily set `taskpool.max_parallel_agents=6` and `taskpool.dynamic_max_parallel_agents=6` for recovery canary safety.
5. Patched `taskpool_dynamic_runner.py` so the cron runner honors `taskpool.dynamic_max_parallel_agents` as the default dynamic ceiling instead of hardcoding 24 when `HERMES_TASKPOOL_DYNAMIC_MAX_CAP` is absent.

Verification after recovery:
- `envelope_bus.py stats`: `human_escape_triggered=false`; by_status includes `RUNNING: 6`.
- `brain_task_orchestrator.py list --json`: 6 running tasks, 9 retry rows, 61 pending rows; no claimed-without-worker wedge in the restored batch.
- `agent_team_controller.py worker-jobs --json`: latest batch `parallel-20260528133208-6` has alive worker PID and `max_agents=6`.
- `taskpool_dynamic_runner.py` now probes `--max-agents 6` and skips overclaim when active boundary-safe slots are full.
- `brain_task_orchestrator.py selfcheck --json`: PASS.

Recovery boundary remains active until a clean canary window is observed:
- parallel cap remains 6, not 24;
- batch executor stays enabled but `skip_when_regular_selected=true` prevents overclaim while ordinary parallel tasks are selected/running;
- no auto-done, no merged acceptance, no proof-gate bypass;
- any new post-ack FAILED/BLOCKED streak should retrigger human_escape and pause scale-up.


## Dynamic recovery scaler and batch headroom gate (2026-05-28)

The previous recovery cap of 6 is now a deterministic canary floor, not a permanent hard ceiling.

Runtime policy landed:
- `taskpool_dynamic_runner.py` computes a `recovery_cap` from the envelope escape watermark before probing dispatch capacity.
- If `human_escape_triggered=true`, or if post-ack `FAILED`/`BLOCKED`/invalid timestamps exist, the runner holds at `dynamic_recovery_min_agents`.
- If the post-ack window is clean, the runner raises the probe ceiling by `dynamic_recovery_step_agents` every `dynamic_recovery_stable_window_seconds`, capped by `dynamic_recovery_max_agents` and any operator env ceiling.
- This scaler only controls the claim ceiling. It does not bypass proof gates, acceptance gates, human escape, stale-manifest rejection, or secret config governance.

Runtime knobs enabled locally through `hermes config set`:
- `taskpool.dynamic_recovery_enabled=true`
- `taskpool.dynamic_recovery_min_agents=6`
- `taskpool.dynamic_recovery_max_agents=24`
- `taskpool.dynamic_recovery_step_agents=2`
- `taskpool.dynamic_recovery_stable_window_seconds=900`
- `taskpool.dynamic_recovery_failure_hold_seconds=1800`
- `taskpool.batch_executor_require_headroom=true`

Batch executor policy landed:
- Batch coordinator now requires explicit parallel headroom before claiming work when `batch_executor_require_headroom=true`.
- `headroom = resource_ceiling - active_count` must be positive; otherwise it returns `SKIP:no_parallel_headroom_for_batch_executor`.
- Effective batch claim size is capped to headroom, preventing overclaim when ordinary parallel workers already fill the pool.
- `batch_executor_skip_when_regular_selected=true` still wins first: ordinary boundary-safe dispatch has priority over batch/cohort execution.

Multi-model boundary interpretation applied:
- Model review may tune scaling policy and classify failure causes.
- Runtime execution remains deterministic and fail-closed for proof, human escape, stale manifests, worker startup cleanup, and config-secret protection.
