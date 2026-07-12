# Dispatch-Tick Baseline Independence and Test-Seam Drift

Use this when a scoped controller/dispatch change is green but broader dispatch-tick baseline tests fail.

## Applicability

- A composed tick performs reconciliation, cleanup, refresh, or liveness checks before the asserted projection.
- A test monkeypatches one command wrapper while production uses another wrapper or timeout adapter.
- Certification scope must distinguish a feature invariant from a full dispatch-tick/full-suite claim.

## Anti-conditions

- Do not call a failure “baseline” only because it predates the current patch; reproduce it and trace the causal path.
- Do not waive a failure that intersects a changed invariant.
- Do not weaken reconciliation, liveness, proof, or safety gates to preserve a stale fixture expectation.

## Independent diagnosis protocol

1. Reproduce each failure alone and record the first divergent value.
2. Capture fixture state before the tick, reconciliation actions, projection input, and final state.
3. Call the pure telemetry/projection builder directly with the intended synthetic input. If it returns the expected value, diagnose upstream fixture/setup drift rather than projection logic.
4. Audit test-double seams: compare every monkeypatched function with the production call site and its full signature.
5. Use blame/log only after causal tracing; chronology supports but does not prove root cause.
6. Search the current feature diff for the causal symbols and run the feature's narrow invariant tests.
7. Classify impact explicitly:
   - `substantive scoped blocker`: failure touches a changed feature invariant;
   - `procedural full-suite blocker`: independent drift prevents an unqualified all-green claim;
   - `non-blocking with recorded exclusion`: scoped acceptance permits known unrelated failures and documents the exclusion.

## Pattern A: reconciliation invalidates synthetic claim fixtures

A lease-valid `claimed` or `running` row may be requeued when no live owner receipt exists. A test asserting claim telemetry after a full tick may therefore observe the correct post-reconcile state rather than the synthetic pre-tick state.

Preferred repairs:

1. Test the pure telemetry builder when telemetry semantics are the actual subject.
2. Provide a realistic live-owner receipt when reconciliation is part of the scenario.
3. Mock reconciliation only when the test explicitly excludes lifecycle repair.

Never relax orphan-claim reconciliation solely for a fixture.

## Pattern B: wrapper migration bypasses a fake

When production introduces a specialized runner for timeout or structured diagnostics, a test patching only the old runner can invoke the real command and leak ambient state.

Repair checklist:

- patch the wrapper actually called;
- accept its complete signature, including keywords such as `timeout=None`;
- save and restore every replacement in `finally` or a scoped patch context;
- assert the fake was called so future seam migrations fail clearly;
- keep the unit test hermetic and cover real-command behavior separately.

## Verification packet

- isolated failure outputs;
- before/reconcile/projection/after state;
- direct pure-function result;
- current-diff causal-symbol intersection check;
- focused feature-invariant results;
- bounded language distinguishing scoped certification from full dispatch/full-suite certification.
