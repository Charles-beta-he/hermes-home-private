# Candidate governance → bounded implementation slice

Use when the active taskpool contains many `proposed` import/review candidates that are not execution backlog yet, especially workflow-kernel / control-plane candidates with `workflow_stage: human_gate` and `completion_boundary: taskpool_candidate`.

## Objective

Convert candidate backlog into a smaller executable chain without opening runtime authority or faking completion.

## Procedure

1. Baseline first:
   - `brain_task_orchestrator.py list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
2. Classify candidates:
   - leaf candidates: individual criteria/routes/contracts/safety flags;
   - consolidated candidates: group-level review items;
   - downstream bounded slice: the smallest implementation task that can safely execute.
3. Write a governance artifact before mutating task states.
   - Include upstream import/run ids if present.
   - Include leaf → consolidated absorption map.
   - Include explicit anti-conditions: no runtime executor, no model calls, no adapter write-through, no external side effects unless separately authorized.
   - Hash the artifact and use it as transition evidence.
4. Transition candidates:
   - leaf candidates that are covered by the consolidated decision → `archived` with reason `absorbed_by_...` and evidence `artifact:<governance-artifact>` + `proof:sha256:<hash>`.
   - consolidated candidates that were reviewed/approved → `done` only if their objective is candidate review/consolidation, not implementation. Record that implementation is delegated to the bounded slice.
   - reject candidates explicitly if they should not feed the slice; do not leave ambiguous proposed leftovers.
5. Create one bounded implementation slice with `brain_task_orchestrator.py add`.
   - Set `status: pending`, `lane: evolution`, project/priority metadata, `priority_layer`, `dependency_order`, `workflow_contract`, `workflow_stage: execute`, and `completion_boundary: implementation_ready`.
   - Acceptance should require concrete artifacts plus deterministic local verification.
   - Red lines must preserve the runtime boundary.
6. If adding the slice triggers background multimodel advisory:
   - Poll `multimodel-intervention-jobs --json` until `alive_count=0`.
   - Expect advisory rounds may end as `PASS_ADVISORY_ONLY` + `CONTINUE_LOOP`; that is not completion proof.
   - Verify the task returns to `pending` and is dispatchable, with no stale `claimed/running` state.
7. Final verification:
   - `reconcile --write --json`
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
   - `proof-check --json`
   - `evidence-spine --json`
   - `multimodel-intervention-jobs --json`

## Pitfalls

- Candidate backlog is not execution backlog. Do not claim or dispatch leaf candidates that are still at `human_gate` review stage.
- Do not close leaf candidates as `done` when they were only absorbed into a consolidated decision; prefer `archived` with absorption evidence.
- Do not mark a new bounded slice `done` after multimodel advisory. Advisory pass only clears planning confidence; implementation still needs real artifacts and deterministic verification.
- Bulk transition loops may time out because transition hooks refresh dashboards and run event hooks. Treat this as partial progress, re-baseline with `list --json`, then continue idempotently on the remaining candidates.
- `add` may require explicit `priority_layer`; include it on first attempt for governed evolution tasks.

## Good end state

- No leftover proposed leaf candidates from the governed batch.
- Consolidated review tasks are terminal with evidence.
- Exactly one or a small number of bounded executable slices remain pending/dispatchable.
- Runtime/model/write/external-side-effect gates are still closed unless separately authorized.
