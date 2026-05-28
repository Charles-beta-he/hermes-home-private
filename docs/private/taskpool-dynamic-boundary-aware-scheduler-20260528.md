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
