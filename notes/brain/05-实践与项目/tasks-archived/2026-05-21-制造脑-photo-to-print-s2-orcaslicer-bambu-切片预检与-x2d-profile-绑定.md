---
type: task
lane: work
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["2"]
created: 2026-05-21T01:32:13+08:00
updated: 2026-05-21T02:20:35+08:00
expires_at: 2026-06-04T01:32:13+08:00
project: manufacturing
architecture_target: 
capability_delta: 
anti_drift_check: 
acceptance_evidence: 真实 OrcaSlicer --help/profile 探测 + fixture STL 切片 smoke + 切片报告写入 job artifacts + fail-closed 测试
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: autonomous-execution
max_authority: yolo-execution
permission_tier: autonomous-execution
write_surfaces: ["taskpool", "codebase"]
completion_gate: project-evidence-review-done
lane_semantics: "work/product delivery: project evidence, tests/build, scoped commit, report/push policy as required"
multimodel_triage_result: P2
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: manufacturing-photo-to-print-slicing
evidence:
  - proof:cron_follow_through_claimed_orcaslicer_profile_slice_preflight
  - proof:reading_note_and_executing_real_orcaslicer_cli_profile_smoke
  - artifact:/Users/charles/.hermes/scripts/manufacturing_preflight.py
  - artifact:/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke/slice-preflight-report.json
  - artifact:/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke/fixture_cube.3mf
  - proof:real_orcaslicer_2_3_2_fixture_slice_smoke_passed_export_3mf_with_x2d_alias_to_bambu_h2d_profile_and_fail_closed_slice_attempts_captured
  - proof:orcaslicer_2_3_2_profile_binding_and_export_3mf_passed_but_slice0_filament_mapping_remains_fail_closed
concepts: ["photo-to-print", "orcaslicer", "slicing", "x2d", "preflight"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#134"
---

# Task - 制造脑 Photo-to-Print S2: OrcaSlicer/Bambu 切片预检与 X2D profile 绑定

## Objective

在已有 manufacturing_preflight.py 基础上接入真实 OrcaSlicer CLI/profile，产出 3MF/切片报告/耗材时间/失败原因；仍不上传/不启动打印。

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.
- [x] Real OrcaSlicer CLI discovery/profile binding is recorded.
- [x] Fixture STL smoke emits a 3MF artifact and machine-readable slice-preflight report.
- [x] Fail-closed behavior is captured for incomplete real `--slice`/filament mapping, with no printer upload/start path invoked.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator next --reconcile --json | PASS | selected this task as highest dispatchable work item |
| python3 -m py_compile /Users/charles/.hermes/scripts/manufacturing_preflight.py /Users/charles/.hermes/scripts/test_manufacturing_preflight.py | PASS | syntax/import check after adding `slice-smoke` / `fixture-slice-smoke` |
| python3 /Users/charles/.hermes/scripts/test_manufacturing_preflight.py | PASS | `OK 3 tests`; review pass also fixed the test harness to resolve `manufacturing_preflight.py` via `__file__` instead of worker `Path.home()` |
| /Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer --help | PASS | reports `OrcaSlicer-2.3.2` and CLI `--load-settings`, `--export-3mf`, `--slice` support |
| python3 /Users/charles/.hermes/scripts/manufacturing_preflight.py fixture-slice-smoke --profile x2d --output-dir ... --report ... --json | PASS | review rerun produced `slice-preflight-report.json` status `pass`; profile `x2d` explicitly aliases to `Bambu Lab H2D`; review artifact sha256 `3deff08d3b7f2f3022d8ccb4b41491bb8704629ce19554261370982b5f1550af` |
| real Orca `--slice 0` experiments | FAIL-CLOSED / captured | H2D multi-extruder filament mapping still returns nonzero (`plate 1 : some filaments can not be mapped under auto mode`); stored in `real-slice*-stdout.txt`; no upload/start/physical action attempted |

## Proof Log

- 2026-05-21T01:32:13+08:00: Task created from local-brain control point.
- 2026-05-21T02:12+08:00: Added bounded OrcaSlicer profile/smoke tranche to `~/.hermes/scripts/manufacturing_preflight.py`: new `slice-smoke` and `fixture-slice-smoke` commands resolve local `x2d` label to installed Orca/Bambu `Bambu Lab H2D` profiles, record exact machine/process/filament JSON paths, run real `OrcaSlicer --info`, export fixture STL to 3MF, and write a JSON report under `/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke/`.
- 2026-05-21T02:12+08:00: Verified real artifact output: `/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke/fixture_cube.3mf` size 25288 bytes, sha256 `4ed30ab3a06fb187c972d24e0d1ec4838261d158db8aba7917bbe7865511692a`; report `status: pass`; profile alias recorded instead of silently claiming an X2D-named profile exists.
- 2026-05-21T02:12+08:00: Captured remaining full slicing gap as fail-closed evidence: direct `--slice 0` with H2D profiles still fails on multi-extruder filament mapping; stdout artifacts retained; this blocks claiming complete耗材/时间 extraction but does not block the safe 3MF/profile preflight tranche.
- 2026-05-21T02:20+08:00: Review pass re-verified the tranche end-to-end with absolute script paths, fixed `test_manufacturing_preflight.py` to resolve `manufacturing_preflight.py` via `Path(__file__)` instead of worker-scoped `Path.home()`, and reproduced a fresh fixture smoke artifact under `/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke-review/` with 3MF sha256 `3deff08d3b7f2f3022d8ccb4b41491bb8704629ce19554261370982b5f1550af`.

## Blockers / Confusions

- Residual: full G-code/slicedata output and耗材/时间 extraction still need a correct H2D/X2D multi-extruder filament mapping (`--slice 0` currently exits nonzero). No printer upload/start path was invoked.

## Final Handoff

- Status: review accepted and task completed for the bounded preflight/profile-binding tranche; validation now re-runs cleanly from this worker context after fixing the test harness path resolution.
- Evidence: `manufacturing_preflight.py`, `test_manufacturing_preflight.py`, `slice-preflight-report.json`, `fixture_cube.3mf`, `real-slice-stdout.txt`, `real-slice2-stdout.txt`, `/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke-review/`.
- Residual risk: Orca profile alias is explicit (`x2d` -> `Bambu Lab H2D`) and should be replaced with a true X2D profile if one appears; full `--slice` remains fail-closed until filament mapping is solved.

- 2026-05-21T02:09:51+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-follow-through`. Reason: bounded_evidence_tranche_start Evidence: proof:cron_follow_through_claimed_orcaslicer_profile_slice_preflight

- 2026-05-21T02:09:52+08:00: Lifecycle transition `claimed` -> `running` by `hermes-follow-through`. Reason: bounded_evidence_tranche_running Evidence: proof:reading_note_and_executing_real_orcaslicer_cli_profile_smoke

- 2026-05-21T02:14:14+08:00: Lifecycle transition `running` -> `review` by `hermes-follow-through`. Reason: bounded_orcaslicer_profile_3mf_smoke_ready_for_review_full_slice_time_filament_gap_declared Evidence: artifact:/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke/slice-preflight-report.json, artifact:/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke/fixture_cube.3mf, proof:orcaslicer_2_3_2_profile_binding_and_export_3mf_passed_but_slice0_filament_mapping_remains_fail_closed
- 2026-05-21T02:20:35+08:00: Lifecycle transition `review` -> `done` by `brain-mirror`. Reason: review_accepted_after_repro_fixing_worker_path_sensitive_test_harness Evidence: artifact:/Users/charles/.hermes/scripts/test_manufacturing_preflight.py, artifact:/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke-review/slice-preflight-report.json, artifact:/Users/charles/.hermes/brains/manufacturing/jobs/photo-to-print/artifacts/2026-05-21-x2d-slice-smoke-review/fixture_cube.3mf
