# Runtime promotion authorization gate

Scope: agent-control-plane / self-architecture workflows only. Applicability: a local dry-run runtime contract has already been landed, surfaced in readiness/sequence/projection views, and the next tempting step is to activate a runtime/API, scheduler, worker, lifecycle write-through, executor promotion, credentialed generation, external dispatch, publish, or destructive action. Anti-condition: this reference is not permission to activate runtime behavior; it governs how to stop safely at the authority boundary while still landing reversible evidence.

## Pattern

1. Keep the candidate fail-closed: runtime disabled, scheduler disabled, worker spawn disabled, lifecycle write-through disabled, executor promotion disabled, and external side effects disabled.
2. Generate a human-gated authorization packet as an artifact, not as an authorization grant.
3. The packet should include:
   - packet id and `HUMAN_AUTHORIZATION_REQUIRED` status;
   - candidate contract id, receipt id, and doctor/evaluator status;
   - preconditions proving the candidate doctor passed and all write/side-effect gates remain disabled;
   - requested authority split by boundary, with only the smallest proposed next boundary set true;
   - explicit fields requiring human decision: exact executor binding, runtime/API scope, budget, rollback owner/command, kill switch, independent evaluator command, and post-action readback surface;
   - default safe decision: do not promote until all required fields are explicitly authorized;
   - rollback/escape hatch and blast radius;
   - post-action verification checklist.
4. Surface the authorization packet in the same operator views that show the candidate: projection artifact, static dashboard/report, and live operator snapshot/readback if available.
5. Verify with TDD: first add failing assertions for the packet/projection/snapshot fields, then implement, regenerate artifacts, run focused tests, and compile touched scripts.
6. Write the stage report or ledger entry as evidence, then scoped commit only the files belonging to this slice.
7. Stop at the gate unless the user supplies the missing exact authority. If asked to continue without the authority fields, continue only safe reversible work such as a dry-run verifier for the authorization packet.

## Verification evidence shape

- Generated authorization packet path.
- Projection/readback shows `HUMAN_AUTHORIZATION_REQUIRED`.
- Readback shows the smallest proposed runtime/API authority request while scheduler/worker/lifecycle-write/executor/external/publish/destructive authority remain false.
- Focused tests pass and scripts compile.
- Scoped commit excludes unrelated dirty runtime ledgers or receipts.
