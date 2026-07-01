# Dev-closure to taskpool certification takeover

Use this reference when a project-local development closure runner is being connected to taskpool lifecycle gates. The reusable lesson is the chain and stop conditions, not the specific project paths from the originating session.

## Applicability

Use when:
- A local/project runner can already produce a closure packet or proof bundle.
- The user asks to "接管", "全盘推进", or otherwise connect local proof to taskpool lifecycle.
- A taskpool task requires project evidence review, multimodel certification, or ratification before `done`.

Do not use when:
- The task is a simple media intake / advisory note with no implementation closeout.
- The user only asked for a report and not lifecycle connection.
- Required credentials or human permissions are missing; stop at an intervention packet instead of bypassing gates.

## Governed takeover chain

Preferred progression:

1. **Project/local closure runner**
   - Classify the task and run local proof commands.
   - Generate a closure packet with evidence paths and explicit `lifecycle_mutation=false`.
   - Verify the runner itself with `py_compile`/artifact checks.

2. **Taskpool closeout dry-run adapter**
   - Read the closure packet.
   - Compute a stable hash for the packet.
   - Call canonical taskpool closeout in dry-run mode (typically `done --authority dry-run`).
   - If policy rejects, write an intervention packet. Do not force `done`.

3. **Certification review adapter**
   - Connect closeout blocker output to canonical certification discovery, e.g. multimodel-intervention dry-run / review-gap scan / blocked-resolve dry-run.
   - Output the recommended next canonical certification step.
   - Still do not claim, transition, certify, or `done`.

4. **Certification loop runner**
   - Execute only the commands emitted by the adapter: state builder -> discussion -> ratification gate.
   - Prefer the official canonical taskpool command when it performs extra required stamping or lifecycle bookkeeping.
   - Keep the runner non-mutating unless the canonical command explicitly owns the lifecycle step.

5. **Lifecycle advancement**
   - Only if the ratification gate passes, proceed through the canonical lifecycle (`review` / `certified` / `done` dry-run / `done`).
   - If the gate fails, write an intervention packet and stop.

## Pitfalls

- **`blocked -> done` is illegal.** A valid local packet does not authorize skipping `review`/`certified` or multimodel certification.
- **Task binding matters.** Directly invoking a ratification gate on a discussion artifact may fail with `target_task_binding_missing`. Prefer the official canonical step if it stamps `task_id`, `target_task_id`, `target_task_path`, and `taskpool_binding` before gate evaluation.
- **Provider auth failures are not evidence failures.** If a required model fails with 401/auth errors, the correct outcome is `not_certified` + intervention packet. Do not downgrade the model requirement or treat other-model quorum as enough unless a separate governed policy change says so.
- **Adapter success is not lifecycle success.** Distinguish `adapter ok`, `closeout dry-run blocked`, `certification gate FAIL`, and `done PASS` in reports.
- **Use explicit env gates.** If canonical autorun is gated by an env var (for example `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1`), set it only after user authorization and record it in proof.

## Verification checklist

Before reporting takeover completion:

- Project profile / SSOT JSON validates.
- Runner scripts compile.
- Artifact verifier passes.
- `brain_task_orchestrator.py selfcheck --json` passes.
- `brain_task_orchestrator.py proof-check --json` passes.
- The task proof log records either:
  - gate PASS and resulting lifecycle transition evidence, or
  - gate FAIL plus intervention packet path and exact blocker.

## Reporting standard

Report the deepest layer actually reached:

- `local proof only`
- `closeout dry-run connected`
- `certification dry-run recommendation connected`
- `canonical certification loop executed`
- `ratification PASS`
- `review/certified reached`
- `done completed`

Never summarize a failed certification run as "done" or "接管完成" without naming the remaining gate.
