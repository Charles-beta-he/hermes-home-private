# Existing Workflow Integration After Local Contract

Use when a user accepts an architecture audit and asks to update existing workflows after a safe local contract/doctor slice has landed.

## Applicability

- Hermes/control-plane/workflow-kernel work where a new contract, validator, or dry-run doctor already exists.
- The next request is not to enable runtime side effects, but to make existing workflow projections/readiness/sequence artifacts consume the new contract.
- The user says “推进现有工作流更新”, “项目级别全盘推进”, or equivalent.

Anti-conditions:

- Do not silently enable scheduler, worker spawn, taskpool write-through, mission executor promotion, external dispatch, credentialed generation, publication, or destructive action.
- Do not resolve unrelated open human gates just because the current workflow update succeeded.

## Pattern

1. Re-read the active workflow artifacts and identify the existing operator surfaces that should consume the new contract:
   - readiness summary / health summary;
   - sequence map / phase map;
   - Control Tower projection / dashboard projection;
   - stage report / evidence ledger.
2. Use TDD against the existing workflow surface, not only the new helper:
   - RED test that readiness output includes the new contract receipt/artifact and exposes a boolean check;
   - RED test that sequence/phase map includes the new adoption phase and keeps runtime disabled;
   - RED test that CLI/report output still exposes safe boundaries.
3. Implement the smallest read-only integration:
   - find latest deterministic dry-run receipt;
   - add a check such as `loop_runtime_contract_doctor_passed`;
   - add an artifact state/projection entry;
   - add a phase/adoption gate with `*_enabled=false` fields explicit.
4. Regenerate only the scoped local reports/artifacts that are owned by this workflow surface.
5. Record a stage report as durable evidence, but treat it as evidence only, not as an actionable wake signal or lifecycle completion.
6. Run focused tests and py_compile; read back the generated JSON fields that prove the integration.
7. Make a scoped commit containing only the workflow integration files and generated artifacts; leave unrelated dirty files untouched.

## Verification evidence shape

- Focused tests pass, e.g. `pytest ...test_loop_runtime_contract_doctor.py ...test_workflow_runtime_readiness_summary.py ...test_workflow_sequence_map.py`.
- Generated readiness JSON has:
  - contract artifact state present;
  - contract check true;
  - runtime/side-effect fields still false or disabled.
- Generated sequence JSON has:
  - new adoption phase;
  - previous terminal phase points to it;
  - next_unlocked remains empty unless a real next phase is authorized;
  - gate string names disabled runtime/scheduler/worker/external effects.
- `git diff --cached --name-only` contains only the scoped files before commit.

## Pitfalls

- A readiness summary may remain `DEGRADED_NOT_BLOCKED` because older unrelated probes are stale. Do not treat that as failure of the new contract integration; report it separately.
- A sequence-map update can make older tests asserting “terminal phase reached” stale. Update tests to assert the new adoption gate and preserve the old closure boundary as a prerequisite, not the final state.
- Mission `stage-report` is durable readback evidence only. It must not clear unrelated human decisions or wake executors by itself.
