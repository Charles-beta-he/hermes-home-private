# 2026-06-12 mission-envelope-schema-gate bounded slice

Objective model (compact):
- Success: prove current local task-create/add boundaries fail closed against partial mission-envelope frontmatter and produce structured evidence/ratification refs for new mission-envelope tasks.
- Constraints: local-only, no push/deploy/secrets/external sends/deletes; do not treat include-active proof-check as green while known historical debts remain.
- Current evidence: `python3 scripts/brain_task_orchestrator.py proof-check --include-active --json` still fails with 328 checked tasks, including mission-envelope structured-ref debts and terminal autorun proof-hash warnings; therefore lifecycle/dashboard sync must remain blocked from claiming green.
- Chosen bounded path: read-only code/test validation of already-landed mission-envelope schema gate plus durable mission stage report.

Real commands run this tick:
1. `hermes mission status msn_20260610_120149_27c88cfc` => mission active, recent next step asked for bounded read-only pass; current trigger is taskpool task_added mission-envelope-schema-gate.
2. `python3 scripts/brain_task_orchestrator.py proof-check --include-active --json` from `/Users/charles/.hermes` => exit 2, `status: FAIL`, `checked_count: 328`; failures include unstructured evidence and many `mission envelope missing ['evidence_refs:structured_ref']`; warnings include 14 terminal invalid autorun proof-hash debts.
3. `python3 -m py_compile scripts/brain_task_orchestrator.py scripts/test_brain_task_orchestrator.py` => passed inside combined command before broader all-test timeout.
4. Focused mission-envelope test snippet invoking:
   - `test_mission_envelope_create_boundary_synthesizes_complete_envelope`
   - `test_mission_envelope_certified_requires_structured_ratification_ref`
   - `test_mission_structured_ref_canonicalizes_absolute_paths_even_when_present`
   Result: all three printed `PASS`.

Findings:
- Existing code has producer-boundary schema gate coverage: `command_add` calls `ensure_mission_envelope_defaults(... synthesized_reason="task-add-boundary")`, then aborts if `mission_envelope_missing(fm)` remains non-empty.
- `ensure_mission_envelope_defaults` fills required structural fields and canonicalizes absolute/URL/evidence refs to structured `artifact:`, `url:`, or `proof:` refs; certified envelopes require structured `ratification_artifact`.
- This validates forward prevention for newly-added mission-envelope tasks, but does not remediate historical ledger debts.

Risk / boundary:
- Created only this local evidence note and the required mission stage-report; no external side effects, no remote push/merge, no deploy, no secret-entry writes, no destructive deletes.
- One attempted broad script invocation (`python3 scripts/test_brain_task_orchestrator.py -k mission_envelope`) was killed with exit -15 because this script does not implement pytest-style `-k`; focused direct function invocation was used instead and passed.

Next bounded step:
- Add a read-only/schema-debt classifier or bounded local ledger/proof supplement plan that groups the remaining include-active mission-envelope structured-ref debts by safe auto-normalizable vs requiring human ratification artifacts; do not mark proof-check green until debts are actually resolved or explicitly gated.
