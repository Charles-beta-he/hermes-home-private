# Workflow-kernel candidate governance → runtime-boundary gated slice

Use this when a taskpool contains many `workflow-kernel` import candidates stuck as `proposed` / `human_gate` / `taskpool_candidate`, especially after a dry-run/import-write generated leaf candidates plus consolidated candidates.

## Applicability

- Candidate backlog is not blocked/running, but also not dispatchable.
- Tasks are review candidates for workflow-kernel contracts, routes, module contracts, or safety flags.
- User authorizes candidate governance or bounded runtime-boundary advancement.
- Goal is to reduce candidate noise into a small, auditable execution slice without faking production runtime completion.

## Anti-conditions

- Do not use this to enable production runtime, model calls, adapter writes, write-through, or external side effects.
- Do not mark leaf candidates `done` as if individually implemented when they were only absorbed by consolidated decisions.
- Do not treat advisory multimodel `PASS_ADVISORY_ONLY` as completion; it is evidence/triage only.
- Do not mix unrelated dirty repo changes into the scoped commit.

## Procedure

1. Baseline first:
   - `brain_task_orchestrator.py list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
2. Classify candidates:
   - leaf import guards (for example evidence/model-policy/prefix/human-gate/runtime-disabled/workflow-contract criteria),
   - leaf `model_route:*`,
   - leaf `module_contract:*`,
   - leaf `safety_flag:*`,
   - consolidated candidates (`model routes`, `module contracts`, `safety flags`).
3. Write a governance artifact with:
   - source dry-run/import-write IDs if available,
   - consolidation map leaf → consolidated decision,
   - explicit red lines (no runtime/model/adapter/write-through/external side effects),
   - approved bounded slice shape and verification requirements,
   - artifact sha256.
4. Transition lifecycle honestly:
   - leaf candidates → `archived` with `classification:absorbed_leaf_candidate` evidence,
   - consolidated candidates → `done` only if their acceptance is review/consolidation, with governance artifact evidence.
5. Create one bounded implementation slice rather than leaving many leaf tasks dispatchable. For first implementation layer, prefer a static registry + deterministic validator:
   - registry/manifest covers module contracts, model routes, safety flags, and import guard criteria,
   - validator checks evidence requirement, model policy, evidence prefixes, human-gate packet fields, phase-1 runtime disabled, workflow contract validity, route aliases, module contracts, and safety flags,
   - tests include failure cases for enabled runtime/side-effect flags.
6. If user then authorizes runtime-boundary advancement, land only a local no-op/dry-run runtime gate unless they explicitly authorize external side effects:
   - human-gate packet with required fields and digest,
   - local dry-run plan that can be `READY_LOCAL_DRY_RUN`,
   - model calls, adapter writes, write-through, and external side effects remain false,
   - tampered packet and forbidden side-effect flag fail closed.
7. Record work in taskpool with a bounded task note and close only after proof-gated evidence matches the task type.
8. Final checks:
   - `list --json`, `next --json`, `dispatch-dry-run --json`, `selfcheck --json`, `proof-check --json`, `multimodel-intervention-jobs --json`,
   - targeted compile/tests/sample-run,
   - scoped git status/commit if editing Hermes repo.

## Pitfalls found in session

- Adding a new workflow-kernel task may automatically trigger advisory multimodel and temporarily claim/run it. Poll `multimodel-intervention-jobs --json` until `alive_count=0`, then read back the task; advisory pass usually returns it to `pending`, not complete.
- If direct `python -m pytest` fails because repository pytest config injects runner-specific options, use the project’s test wrapper (`./scripts/run_tests.sh ...`) rather than encoding a generic tool failure.
- Existing tests may be stale against current runtime phase. If a test asserts an old phase/switch value but current package exports a newer runtime contract, update the test to the current contract and verify the broader workflow-kernel test set.
- Closeout evidence for runtime-boundary work must include both positive readiness and negative side-effect checks.
