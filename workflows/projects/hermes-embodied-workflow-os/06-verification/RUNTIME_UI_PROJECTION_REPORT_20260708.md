# Runtime UI projection report — 2026-07-08

Project: `hermes-embodied-workflow-os`
Scope: Ego-NeuroLoop LoopCore runtime UI projection in the local HEWOS Workbench.
Status: `validated-local-runtime-ui-projection-slice`

## Implemented surface

- Static/local Workbench now includes an `Ego-NeuroLoop LoopCore` card.
- Runtime server exposes read-only endpoint: `/projection/ego-neuroloop`.
- Dashboard projection now includes loop receipt aggregate fields:
  - `loop_receipt_count`
  - `loop_receipts_by_exit`
  - `latest_loop_receipts`
- Static HTML fixture regenerated at `artifacts/workbench-static-fixture.html`.

## Projected fields

The UI projection renders the local `ego_neuroloop_core_receipt_v0` as safe user/operator-facing information:

- loop depth: `loop_count / loop_budget`
- exit reason
- confidence
- receipt schema
- ActionIntent id
- deferred decode label
- recommended action
- boundary flags, all shown as false in the fixture
- known limits

## Boundary

This is read-only projection. It does not add:

- execution controls
- model routing
- taskpool ingestion
- external dispatch
- hardware actuation
- payment or destructive operation
- secret entry
- deploy/publish/push

The runtime UI intentionally displays the receipt as prediction/status projection, not as authority or proof of real-world model quality.

## Fresh verification

Command:

```bash
python3 -m unittest discover -s implementation/tests -v
```

Result:

```text
Ran 58 tests in 2.554s
OK
```

Runtime smoke:

```text
GET http://127.0.0.1:8801/healthz -> 200 application/json; execution_enabled=false; loop_projection_enabled=true
GET http://127.0.0.1:8801/projection/ego-neuroloop -> 200 application/json; schema=ego_neuroloop_core_receipt_v0; exit_reason=stable; side_effect_open=false
GET http://127.0.0.1:8801/projection/dashboard -> 200 application/json; loop_receipt_count=1; loop_receipts_by_exit={"stable": 1}
```

Browser visual smoke:

- Page title loaded: `HEWOS Workbench Static Fixture`.
- Visible Runtime UI Projection card shows `Ego-NeuroLoop LoopCore`.
- Visible metrics: `2/4` loop depth, `stable` exit reason, `1.0` confidence.
- Visible receipt rows include schema, ActionIntent, decode label, recommended action.
- Visible boundary flags show side effect flags as false.
- No execution controls were visible.

## Files changed

- `implementation/hewos_core/projections.py`
- `implementation/hewos_core/workbench_runtime.py`
- `implementation/hewos_core/workbench_static.py`
- `implementation/tests/test_workbench_projections.py`
- `implementation/tests/test_workbench_runtime.py`
- `implementation/tests/test_workbench_static.py`
- `artifacts/workbench-static-fixture.html`

## Next gate

The next meaningful gate is either:

1. richer runtime UI states for high-risk/human-gate/budget-exhausted receipts, or
2. real model/adapter integration, which requires separate exact authority, evidence readback, and side-effect boundary review.

## Authorized local-state progression — same date

After the runtime UI projection card was validated, the next authorized local/reversible item was advanced without opening external authority:

- Added a local-state gallery for all safe promotable LoopCore receipt states.
- Runtime fixture now projects three receipt classes:
  - `stable`
  - `human_gate`
  - `budget_exhausted`
- Dashboard aggregate now reports `loop_receipt_count=3` and exit distribution `stable=1`, `human_gate=1`, `budget_exhausted=1`.
- Browser visual readback confirmed the gallery is visible and no execution controls are present.

Additional runtime readback:

```text
GET /projection/ego-neuroloop -> count=3; exits=['budget_exhausted', 'human_gate', 'stable']; side_effects=[False, False, False]
GET /projection/dashboard -> loop_receipt_count=3; loop_receipts_by_exit={'budget_exhausted': 1, 'human_gate': 1, 'stable': 1}
```

Additional test readback:

```text
python3 -m unittest discover -s implementation/tests -v
Ran 58 tests in 3.042s
OK
```

Boundary remains unchanged: read-only projection, no model routing, no taskpool ingestion, no external dispatch, no hardware actuation, no deploy/publish/push, no secret entry, payment, or destructive action.

