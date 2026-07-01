# Dev-closure to taskpool certification adapter pattern

Applicability: use when a project-local dev-closure runner already produces local proof and closure packets, but canonical taskpool lifecycle still rejects `done` because review/certification gates are missing or inconclusive. This is especially relevant for tasks with `requires_multimodel`, `project-evidence-review-done`, or prior `blocked -> done illegal` failures.

Anti-conditions:

- Do not use this as authority to force `done`, `review`, or `certified`.
- Do not treat local tests or model consensus as certification by themselves.
- Do not execute generated model-discussion commands inside the diagnostic adapter unless the user/task explicitly authorizes a separate governed certification run.
- Do not bypass taskpool lifecycle order; `done` must still come from allowed states such as `review` or `certified` when policy requires it.

## Pattern

Build the closure pipeline in layers, each with a receipt:

1. **Project dev-closure runner**
   - Input: task id.
   - Reads task metadata/profile/router.
   - Runs local proof commands only.
   - Writes a closure packet.
   - Emits `lifecycle_mutation=false` and a canonical done boundary.

2. **Taskpool closeout adapter**
   - Reads the closure packet and computes a stable hash.
   - Calls canonical `brain_task_orchestrator.py done <task> --authority dry-run --evidence artifact:<packet>; sha256:<hash>`.
   - If rejected, records the exact policy blocker in an intervention packet.
   - Never uses `--force` or performs a real transition.

3. **Certification review adapter**
   - Runs/refreshes the dev-closure packet when explicitly requested.
   - Runs the closeout adapter in dry-run mode.
   - Runs canonical dry-run diagnostics such as:
     - `multimodel-intervention-dry-run --task <task> --json`
     - `review-gap-scan --task <task> --authority dry-run --json`
     - `blocked-resolve-step --task <task> --authority dry-run --no-transient-to-retry --json`
   - Summarizes whether the generated certification sequence is present: state builder, discussion command, and ratification-gate template.
   - Emits a recommendation such as `RUN_MULTIMODEL_CERTIFICATION_LOOP`, `READY_FOR_GOVERNED_CLOSEOUT_RECHECK`, or `INTERVENTION_REQUIRED`.
   - Writes a receipt and next-step packet; no claim, no certification, no lifecycle mutation.

## Verification checklist

- [ ] Adapter scripts pass `python3 -m py_compile`.
- [ ] Local verifier checks all required runner/adapter markers.
- [ ] Project profile JSON validates after writeback.
- [ ] `brain_task_orchestrator.py selfcheck --json` passes.
- [ ] `brain_task_orchestrator.py proof-check --json` passes, or failures are clearly pre-existing and not introduced by the adapter.
- [ ] Receipts include: packet path/hash, closeout decision, multimodel dry-run tier, blockers, recommendation, next safe step, `lifecycle_mutation=false`.
- [ ] Source task proof log and project ledger record the receipt path and boundary.

## Pitfalls

- Parsing large JSON from `multimodel-intervention-dry-run` can fail if only the tail is kept; parse full stdout, then store a truncated tail for logs.
- A closeout dry-run rejection is useful signal, not failure: preserve exact blocker text as the next-step contract.
- If the generated multimodel state/discussion/ratification commands are present, the correct next slice is a governed certification run, not an adapter that secretly executes them.
- When a task already has local proof, avoid looping back to implementation; first resolve certification/lifecycle blockers.
