# High-risk boundary projection and exact execution

Use when a user broadly authorizes high-risk Agent/control-plane capabilities such as publish/deploy/push, destructive operations, payment/credential entry, or broad fan-out.

## Core rule

Treat the user's broad approval as authority to open the **governed projection/readback boundary**, not as authority to invent missing concrete targets. Each high-risk class still needs an exact executable target before real side effects.

## Procedure

1. **Project and read back the authority**
   - Add or enable default-off gates for each named high-risk class.
   - Read back live status/config for every gate.
   - Add prompt/runtime guidance that scopes execution to exact target + receipt + rollback/readback.

2. **Execute only exact, scoped, reversible actions already determined by context**
   - Example: if the active repo, branch, remote, and user-owned/private target are already known, an exact `git push origin <branch>` can be the publish/deploy/push smoke.
   - Verify remote/readback (`git ls-remote`, deployment status, publish URL, etc.).

3. **If the user explicitly grants “you supplement permission details / initial vision to executable end,” choose safe generated exact defaults instead of stalling**
   - This is not permission to guess real business targets. It is permission to manufacture a harmless exact smoke target that proves the gate.
   - Local taskpool default: if the current context already contains one exact task id and one exact local workspace/ledger id, perform only that task's local lifecycle write-through and record receipt/readback for each transition. Do not generalize to other tasks or workers.
   - Destructive smoke default: create a disposable canary under an isolated run/workspace artifact directory or `/tmp`, copy it to a `.bak`, delete only that exact generated file, verify absent, restore from `.bak`, and verify hash equality. The blast radius is the canary and its backup only.
   - Broad fan-out default: use a self-only exact channel set when available; exclude third-party DMs unless explicitly named. Include an idempotency key and receipt/readback.
   - Payment/credential default: create a human-side gate plus redacted receipt schema. The agent still must not type passwords, API keys, cards, OTPs, seed phrases, or other secrets.
   - Publish/deploy/push default: if an owned private repo/remote/branch is already known, a push can be the exact smoke; otherwise require an exact target/environment.

4. **Do not infer missing real high-risk targets**
   - Destructive operations against real user/project resources require exact path/resource plus backup/restore path.
   - Payment/credential entry is projection/human-gate-only for the agent: never type passwords, API keys, cards, or secrets.
   - Broad fan-out requires an exact channel set and payload. Do not infer “all available contacts,” especially when targets include third-party DMs.

5. **Record differential evidence**
   - Receipt should separately mark: gate projected/readback true, exact action(s) executed, generated smoke targets, and high-risk classes not executed due to missing exact target or secret-safety boundary.
   - Multi-model certification should certify only the grounded claims: e.g. “projection + exact private repo push smoke + disposable canary delete/restore + self-only fanout + human credential gate,” not real destructive/payment/third-party fan-out execution if those did not occur.

6. **Run a post-authorization exactness audit**
   - After broad authorization is consumed, re-check the touched task cards, SSOT/spec docs, and class-level references for all four fields: `exact target`, `payload`, `rollback`, and `readback`.
   - Narrative statements like “exact-target gated” are insufficient if they do not name what a future executor must supply for each high-risk class.
   - Patch the governing class-level skill/reference, not only the one task card, so future sessions inherit the boundary.
   - Keep the audit scoped: task/session progress stays in the task record; reusable four-field matrices and pitfalls belong in skills/references.

## Pitfalls

- Broad user approval is not a concrete target. Do not turn `destructive_operations: true` into a guessed deletion or cleanup command.
- Do not treat payment/credential authorization as permission to type secrets; it only means the workflow can surface the human gate and record human-side receipts.
- Broad fan-out is not “send to everyone.” Require named recipients/channels and a payload.
- Certification wording must be scoped: certify what was actually executed and read back, and explicitly exclude unexecuted high-risk classes.
