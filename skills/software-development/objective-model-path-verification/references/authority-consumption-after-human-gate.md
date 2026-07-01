# Authority Consumption After Human Gate

Scope: generic agent-control-plane runtime transitions where a prior gate packet separates local readback/API activation from schedulers, workers, lifecycle writes, external effects, publishing, and destructive operations.

Applicability: use when an explicit `HUMAN_AUTHORIZATION_REQUIRED` packet exists and the user gives a terse or broad approval such as `授权`, `approved`, or `continue authorized`.

Anti-condition: do not use this for production deploys, payments, credential entry, destructive cleanup, external publishing, or service restarts unless those exact actions are separately named in the gate packet and freshly authorized.

## Rule

A broad approval consumes only the smallest safe authority already described by the packet. It is not blanket permission to open neighboring gates.

## Procedure

1. Re-read the gate packet and list each requested authority class.
2. Choose the narrowest local/reversible authority that can be consumed now.
3. Keep every non-authorized side-effect class explicitly closed in code and receipts.
4. Write a RED test for the state transition or API route before implementation. Assert both the positive state and all still-closed gates.
5. Implement a receipt/ledger writer that records actor, decision, packet id, exact executor binding, budget, rollback command, kill switch, evaluator command, readback surface, and explicit false values for unopened authority classes.
6. Project the receipt into the live operator snapshot and any generated report/readback artifacts.
7. Verify with targeted tests, syntax checks, and live readback.
8. Commit only the scoped authority-consumption slice; leave unrelated dirty files untouched.
9. Report the remaining boundary as the next exact gate.

## Verification checklist

- RED test failed before implementation for missing transition/readback.
- Authorized state is visible through the readback surface.
- Scheduler, worker, lifecycle-write, external, publish, and destructive booleans remain false unless specifically authorized.
- Rollback and kill-switch are written in the receipt.
- No service restart, push, deploy, external side effect, or destructive action occurred without a separate exact authorization.
