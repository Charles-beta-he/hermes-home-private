# Local control-console worker execute boundary

Scope: localhost/operator consoles that already support Human Inbox decision record, adapter apply, and executor dispatch. Applicability: when the intended user-visible effect is not merely "claim/handoff created" but "start the existing governed worker lane" after a human approval. Anti-condition: do not use this pattern for arbitrary shell, external sends, deploys, credential handling, destructive mutation, or direct `done` closeout.

## Correct production chain

For a one-click / one-session-arm Human Inbox resume flow, keep the runtime actions separate but allow the UI to call them in sequence when all are registered and armed:

1. `human.decision.record`
   - Append the operator choice to a local decision ledger.
   - Require exact `confirm == requestId`, decision allowlist, same-origin/localhost auth, and bounded payload.

2. `taskpool.decision.apply`
   - Consume the recorded decision.
   - Recheck current task state.
   - Map only allowlisted decisions to allowlisted taskpool statuses.
   - Write an apply ledger and read back the target status.

3. `taskpool.executor.dispatch`
   - Consume a successful apply row.
   - For resume-style decisions such as `approve_with_edit`, require `targetStatus/readbackStatus == pending`.
   - Run the existing taskpool claim-and-handoff command with `shell=False`.
   - Read back `claimed` and write an executor dispatch ledger.

4. `taskpool.worker.execute`
   - Consume a successful executor dispatch row.
   - Require the task to still read back as `claimed`.
   - Start the existing worker extension, e.g. `agent_team_controller.py consume-claimed --background`, with a bounded `claimed-json` payload containing only task id, handoff reference, and request id.
   - Write a worker execute ledger and rely on `agent_team_controller.py worker-jobs` for readback.
   - The worker boundary owns later lifecycle: `claimed -> running -> review/retry/blocked`; the console must not directly mark `done`.

## One-time arm semantics

"一次性开放" means one short-lived capability session can include all registered actions, not that validations are collapsed. Each endpoint still needs its own capability check, exact request confirmation, predecessor ledger/readback, idempotency key, and audit row.

Recommended registered capability set for this class:

- `snapshot.refresh`
- `mission.decide`
- `human.decision.record`
- `taskpool.decision.apply`
- `taskpool.executor.dispatch`
- `taskpool.worker.execute`

## API/ledger shape

- Decision ledger: `~/.hermes/control-console-human-decisions.jsonl`
- Apply ledger: `~/.hermes/control-console-taskpool-applies.jsonl`
- Dispatch ledger: `~/.hermes/control-console-executor-dispatches.jsonl`
- Worker execute ledger: `~/.hermes/control-console-worker-executes.jsonl`

Idempotency keys should bind the user-visible request and target task:

- apply: `requestId:decision:taskId:targetStatus`
- dispatch: `requestId:taskId:claim-and-handoff`
- worker execute: `requestId:taskId:worker-background`

## Verification pattern

Minimum regression coverage:

- Unarmed worker execute returns `capability_not_armed`.
- Worker execute without dispatch returns `executor_dispatch_not_verified`.
- Dispatch must require successful apply and claimed readback.
- Worker execute must require claimed readback.
- Worker execute invokes the existing worker controller with `shell=False` and bounded claimed-json.
- Replay returns an idempotent success and does not start a duplicate job.
- UI contract exposes `taskpool.worker.execute` and `/api/console/taskpool/worker/execute`.
- Live probe verifies `/api/console/health` registers the capability and `agent_team_controller.py worker-jobs` returns the expected existing worker-job schema.
- Browser probe verifies one arm exposes copy for the full record/apply/dispatch/worker chain, then reset public snapshot to unarmed/no-token.

## Pitfalls

- Do not create a second worker system in the console. Reuse the existing taskpool/agent-team worker controller and treat the console as a governed trigger surface.
- Do not treat worker job start as task completion. Completion still requires worker proof, review gate, and lifecycle closeout rules.
- Do not skip predecessor ledgers because the UI called all steps in one chain.
- Do not store raw prompts, secrets, or arbitrary payloads in the worker execute ledger; store ids, job file/log references, hashes/summaries, and readback fields.
- Do not leave the capability session armed after live probes; reset session and regenerate the public snapshot to no-token/unarmed before commit.
