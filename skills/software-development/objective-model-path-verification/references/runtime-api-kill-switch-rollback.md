# Runtime API Kill-Switch Rollback Verifier

Scope: agent-control-plane or workflow-kernel runtime transitions where a prior human gate enabled a narrow local runtime API/readback surface, and the next safe advancement is to prove that the kill switch can disable that surface.

Applicability: use after a `runtime_api_only` / local-readback activation receipt exists and the user gives broad approval such as `授权推进`, `continue`, or `advance`. This is the smallest safe next slice when scheduler, worker, lifecycle-write, external, publish, or destructive authority has not been separately granted.

Anti-conditions:
- Do not treat rollback verification as permission to enable scheduler, spawn workers, mutate taskpool/mission state, call external adapters, publish, deploy, restart services, or delete unrelated files.
- Do not rewrite history or remove the original enable receipt unless the explicit rollback command in the authorization packet says to do so and the user grants that exact action.
- Do not call the runtime disabled unless a fresh readback surface shows the disabled projection.

## Procedure

1. Re-read the latest activation receipt and identify its kill-switch name, readback surface, and unopened authority classes.
2. Write a RED test for the disable/rollback endpoint or command. Assert both:
   - positive transition: latest projection becomes `RUNTIME_API_DISABLED_BY_KILL_SWITCH` (or the project’s equivalent disabled status);
   - negative invariants: scheduler, worker spawn, lifecycle writes, external effects, publish, and destructive actions remain false.
3. Implement a minimal disable writer that appends a new receipt/event instead of deleting the prior activation receipt.
4. The disable receipt should record actor, decision, reason, kill switch, readback surface, event digest, explicit `runtime_api_enabled: false`, and explicit false values for all unopened authority classes.
5. Update the projection builder to derive status from the latest ledger event:
   - latest recorded enable event -> runtime API authorized/local-only;
   - latest recorded disable event -> disabled by kill switch;
   - no valid event -> human authorization required.
6. Project the disabled state into live operator snapshots and generated reports/artifacts.
7. Execute the disable path once against the real local ledger and read back the live snapshot/report.
8. Run focused tests + syntax checks, append a stage report, and make a scoped commit containing only the rollback verifier slice.
9. Report the next boundary clearly: any re-enable or broader scheduler/worker/lifecycle/external/publish/destructive promotion needs a fresh exact authorization packet.

## Verification checklist

- RED test failed because the disable route/transition was missing.
- Disable receipt exists and is append-only.
- Live snapshot/readback shows disabled status and `runtime_api_enabled: false`.
- All neighboring gates remain false.
- Projection/report artifacts include the disabled state.
- Commit excludes unrelated pre-existing dirty files.
