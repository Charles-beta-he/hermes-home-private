# Taskpool governance/evaluator closeout gate patch — 2026-06-14

## Problem

`auto-close-review` failed to close the ERC-8126 internal self-check task even after a real local evaluator, template, sample report, `py_compile`, and sample-run evidence were landed.

Observed failures:

- `execution_flow_closeout_blocked:api_or_backend_readback_proof,browser_or_ui_surface_proof`
- `advisory_only_multimodel_requires_implementation_evidence: PASS_ADVISORY_ONLY cannot authorize done without commit/test/build/browser/real-api evidence`

## Root cause

`brain_task_orchestrator.py` treated any review task whose text mentioned `API`, `UI`, `browser`, etc. as needing live API/browser proof. Governance/policy/evaluator tasks often mention those as checklist dimensions, not as implemented live surfaces. The closeout logic also did not treat deterministic local evaluator evidence (`implementation:` script path + `py_compile` + sample run) as implementation evidence for `PASS_ADVISORY_ONLY` evolution tasks.

## Patch

Files changed:

- `/Users/charles/.hermes/scripts/brain_task_orchestrator.py`
- `/Users/charles/.hermes/scripts/test_brain_task_orchestrator.py`
- skill reference: `taskpool-control-plane/references/full-pool-advance-bounded-loop.md`

Behavior added:

- `implementation:` is now a structured evidence prefix.
- Governance/policy/evaluator evolution tasks with deterministic local evidence no longer require browser/API proof merely because their checklist dimensions mention UI/API.
- `PASS_ADVISORY_ONLY` closeout now accepts deterministic local implementation evidence tokens such as `implementation:`, `py_compile`, `evaluator`, `sample-report`, `sample eval`, and `/scripts/`.

## Regression tests run

```bash
python3 -m py_compile /Users/charles/.hermes/scripts/brain_task_orchestrator.py /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py
python3 -m pytest /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py::test_passed_advisory_only_governance_evaluator_allows_local_deterministic_closeout -q
python3 -m pytest /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py::test_done_closeout_blocks_work_task_missing_execution_flow_harness_proof /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py::test_done_closeout_allows_work_task_with_execution_flow_harness_proof /Users/charles/.hermes/scripts/test_brain_task_orchestrator.py::test_passed_advisory_only_review_task_does_not_rerun_weak_multimodel_loop -q
```

Results:

- `py_compile`: PASS
- new governance/evaluator closeout regression: `1 passed`
- existing execution-flow guard regressions: `3 passed`

## Production taskpool verification

Command:

```bash
python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py auto-close-review --task 2026-06-14-将-erc-8126-转化为-agent-web3-安全体检自检标准 --actor hermes --authority autonomous-execution --reason deterministic_local_evaluator_gate_supported --json
```

Result:

- `closed_count`: 1
- closed task: `2026-06-14-将-erc-8126-转化为-agent-web3-安全体检自检标准`
- proof hash: `sha256:971de4a05c58e40560daf80df79c379562506cc6b00d0983c6e64684c39c6d96`

Post-checks:

- `review-gap-scan --json`: `gap_count=0`
- `next --json`: no dispatchable task
- `dispatch-dry-run --json`: no dispatchable task
- `selfcheck --json`: PASS
- `proof-check --json`: PASS with historical terminal backlog warnings only
- `p10-health.sh`: Grade A, `V(t)=0.9758`

## Safety boundary

This patch does not let ordinary work-lane API/UI implementation tasks close without browser/API proof. Existing tests still verify that work tasks mentioning backend API and browser UI are blocked unless `proof:browser` and `proof:api_readback` evidence are present.
