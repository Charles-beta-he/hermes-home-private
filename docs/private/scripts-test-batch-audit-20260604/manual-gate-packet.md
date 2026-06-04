# Scripts tests batch audit — 2026-06-04

User choice: A / low-risk tests first.

## Result

NO-GO for automatic bulk commit of all test files. The selected tests are not an isolated low-risk batch because they depend on modified or untracked non-test scripts, and the batch is not green.

Verification:
- py_compile: PASS (`python3 -m py_compile scripts/test_*.py`)
- pytest selected tests: FAIL (`167 passed, 3 failed, 1 error, 48 warnings, 8 subtests passed`)

Failures:
- scripts/test_adapter_integration.py::test_pipeline: TaskPipeline.preflight is TaskPreflight object, not callable
- scripts/test_adapter_integration.py::test_task_spec_serialization: TaskSpec.to_dict source returns TaskSource enum, expected string
- scripts/test_dynamic_workflow.py::test: helper function named test collected as pytest test
- scripts/tests/test_bambu_x2d_safety.py::test_status_refuses_without_access_code_before_network: status attempts network before empty access-code refusal

## Why not commit tests alone

- 27/29 top-level selected test files are untracked; plus 3 files under `scripts/tests/`.
- Several tests import or subprocess-call untracked source files (`task_adapter.py`, `task_pipeline.py`, `bambu_x2d.py`, Bambu helpers, theoretical model helpers).
- The 2 tracked modified tests pass in the current dirty tree, but they exercise modified source scripts (`brainctl.py`, `personal_hermes_brain_export.py`), so committing the tests alone would be misleading.

## Recommended next manual gate

Choose one paired sub-batch instead of bulk tests:

1. `tests-tracked-existing`: review/commit `scripts/test_brainctl.py` + `scripts/test_personal_hermes_brain_export.py` together with their paired source diffs if accepted.
2. `tests-task-adapter`: review task adapter source + tests; current failures indicate either stale tests or source contract gaps.
3. `tests-bambu-x2d`: review Bambu/X2D safety source + tests; current failure indicates status path may network before credential fail-closed.
4. `tests-manufacturing-photo`: review manufacturing/photo-to-print test/source group as a separate feature family.

Machine-readable detail: `summary.json`.
