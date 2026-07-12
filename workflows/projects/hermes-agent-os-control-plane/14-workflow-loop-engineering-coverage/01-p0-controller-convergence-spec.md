# Loop Engineering P0 Convergence Spec

Date: 2026-07-10
Scope: local Hermes taskpool control plane only
Authority: user approved “认可，loop推进” and “继续”

## 1. Objective model

### Success criteria

1. Event hook, dynamic/cron path, parallel dispatch path, and hourly agent-team controller cannot claim a task merely because `dispatchable=true`.
2. Every automated claim projects the exact task through the canonical `eligibility-check` semantics: autorun enablement, allowlist, dispatchability, permission/certification gates, write guard, and execution-flow boundary.
3. `claimed -> running` is fail-closed when the required handoff contract is empty.
4. Existing proof/review/done gates remain unchanged.
5. Changes are local, reversible, test-backed, and do not enable global autorun or external side effects.

### Constraints / non-goals

- No scheduler/cron mutation.
- No allowlist expansion.
- No worker dispatch canary against a real project task.
- No production/external write, publish, push, deploy, credential entry, or destructive action.
- Do not weaken proof hashes, review authority, leases, CAS transitions, stale-claim reconciliation, or human gates.
- Do not redesign the full taskpool state machine in this slice.

### Chosen bounded loop

`Observe -> Select -> Eligibility/Contract Gate -> Claim -> Handoff -> Running -> Evidence -> Review -> Learn/Stop`

Stop/fail branches:

- eligibility denied -> remain pending; structured reasons
- claim created without handoff -> retry before enqueue
- queued/consumed claim without handoff -> retry before running
- stale claim -> existing stale-claim reconciliation
- worker blocked -> existing blocked/retry policy

## 2. Current-state evidence and root cause

Observed task transition:

- `pending -> claimed -> running -> blocked`
- event route classified the task as deferred/allowlist-miss
- hourly agent-team controller nevertheless claimed it
- worker job carried `handoff: ""`

Root cause A — duplicated claim authority:

- `agent_team_controller.claim_task()` called the low-level `claim` command directly.
- That bypassed the canonical `auto-claim-and-handoff -> eligibility-check` bridge.
- Therefore `dispatchable=true` was treated as sufficient authority by the hourly controller.

Root cause B — parallel batch selected by dispatchability only:

- `command_parallel_claim_and_handoff()` called `select_parallel_dispatch()` and then claimed selected tasks.
- Each selected task was not re-projected through exact-task autorun eligibility before mutation.
- The dynamic/cron path could preflight one task and then claim a batch containing a different unallowlisted task.

Root cause C — handoff was data, not an invariant:

- claim-cycle created envelopes without passing a handoff.
- execute-cycle and consume-claimed accepted empty handoff values and could transition to `running`.

## 3. P0 implementation

### Canonical claim path

`agent_team_controller.claim_task()` now invokes:

`brain_task_orchestrator.py auto-claim-and-handoff --task <id> --actor <actor> --no-reconcile --json`

Success now requires all of:

- `status == OK`
- `claimed == true`
- non-empty `handoff`

### Per-task parallel eligibility

`command_parallel_claim_and_handoff()` now evaluates every selected task through `command_eligibility_check()` before any claim mutation.

Denied tasks are emitted as:

- `reason: autorun_eligibility_denied`
- exact `reasons`
- exact `warnings`
- `eligibility_decisions` readback

### Pre-running handoff invariant

The agent-team controller now rejects an empty handoff at three boundaries:

1. claim-cycle before envelope creation
2. execute-cycle before `claimed -> running`
3. consume-claimed before envelope creation and `claimed -> running`

The fail-closed recovery path is `claimed -> retry` with structured evidence.

## 4. TDD evidence

Red tests first:

- hourly controller used direct `claim`, not canonical bridge
- consume-claimed without handoff entered the running path
- parallel claim selected an unallowlisted task
- parallel claim skipped selfcheck and execution-flow projection
- batch-merge executor called low-level `claim` and emitted no handoff

Green evidence:

- full scoped controller/orchestrator/runner/dispatch-tick bundle: 209 passed
- `py_compile`: passed
- scoped `git diff --check`: passed

New regression cases:

- `test_claim_task_uses_canonical_auto_claim_and_handoff_gate`
- `test_claim_task_preserves_structured_denial_on_nonzero_exit`
- `test_consume_claimed_batch_missing_handoff_fails_closed_before_running`
- `test_claim_cycle_releases_claim_if_canonical_bridge_returns_no_handoff`
- `test_parallel_claim_and_handoff_filters_each_task_through_canonical_eligibility`
- `test_parallel_claim_and_handoff_honors_execution_flow_gate_before_claim`
- `test_batch_executor_canonical_denial_does_not_trigger_worker`
- batch-executor regression asserts canonical handoff propagation into `consume-claimed`

Combined scoped convergence suite: 209 passed in 73.44s.

## 5. Independent review and remediation

Independent review `deleg_9876d13e` returned `BLOCK` with two high findings:

1. parallel write mode used `skip_selfcheck=True` and omitted the execution-flow gate;
2. dispatch-tick batch executor used low-level `claim`, created no handoff, and could churn claim -> retry.

Both findings were remediated:

- parallel candidates now run exact eligibility with selfcheck enabled and then the same execution-flow dry-run/dispatch decision as the single-task bridge;
- batch executor now calls exact-task `auto-claim-and-handoff`, requires `claimed=true` plus a non-empty handoff, propagates handoff/proof/run metadata to `consume-claimed`, preserves structured denials, and never triggers a worker when all candidates are denied;
- defensive missing-handoff cleanup releases/retries any anomalous claimed row.

The two stale dispatch-tick tests were corrected without weakening production semantics:

- starvation telemetry is tested directly with complete claim ownership metadata, while reconciliation behavior remains covered separately;
- evidence-spine WARN now mocks the actual `run_orchestrator_json` boundary and verifies visible WARN/nonfatal behavior.

Fresh independent re-review `deleg_cd1d02f2` returned `PASS`:

- no remaining P0 automated low-level claim bypass was found across event hook, dynamic runner/cron, hourly controller, parallel mutation, and batch merge executor;
- the verifier independently reran the scoped suite: `209 passed in 71.67s`;
- verifier `py_compile` and scoped `git diff --check` passed;
- no external dispatch or tracked-file mutation was performed by the verifier.

Certification status: `CERTIFIED_SCOPED_P0`. This certification is limited to local controller convergence and does not certify the original advisory research task, global autorun, external dispatch, deploy/publish/push, or the complete taskpool system.

Fresh task-file readback also showed that a separate controller path had already advanced the original X advisory task after the earlier blocked snapshot:

- `blocked -> review` by `hermes-blocked-resolver` at 17:11:23;
- `review -> done` by `hermes-auto-evidence` at 17:12:20;
- task boundary remains `completion_boundary=document_only`;
- `certification_status=not_certified` and `ratification_artifact=proof:ratification-pending` remain explicit.

Therefore its `done` state means document-only advisory evidence deposition was closed; it must not be represented as certified article truth, a passing multimodel ratification, or implementation authority. This P0 slice did not perform either lifecycle mutation.

## 6. Verification and rollback

### Required convergence checks

- canonical orchestrator suite green
- agent-team controller suite green
- dynamic runner suite green
- event-hook focused suite green
- no real external dispatch
- no global autorun/allowlist/scheduler mutation

### Rollback

Revert only the scoped changes in:

- `scripts/brain_task_orchestrator.py`
- `scripts/agent_team_controller.py`
- `scripts/brain_task_dispatch_tick.py`
- associated tests

No state migration is required.

## 7. Remaining slices

P1:

- make handoff schema explicit and versioned, not merely non-empty
- add `handoff_sha256`, task-id binding, authority projection, acceptance/evaluator contract, budget, stop conditions, and expiry
- add a single isolated canary fixture covering event -> eligibility -> claim -> handoff -> running denial/readback

P2:

- add controller decision receipts and controller-ID observability
- detect multi-controller policy drift automatically

P3:

- bounded compound loop promotion into tests/skills/policies only after independent verification
