# Local control-console operator-decision write-through boundary

Scope: localhost/operator control consoles that render approval-request, Human Inbox, or operator-decision choices. Applicability: when a UI choice should produce a real governed side effect rather than a display-only draft. Anti-condition: do not use this pattern to skip adapter-specific authorization, lifecycle gates, external sends, arbitrary shell/tool execution, destructive production mutation, or credential handling.

## Problem signature

- UI shows operator choices such as accept / approve with edit / request more evidence / hold.
- Receipt copy implies a decision, adapter mutation, or executor action landed, but only React state or a read-only projection changed.
- Direction cards use button-like chips that are actually static text elements.
- User asks why the operation cannot directly land, says the screen shows incomplete interaction, or says a prior “full push” stopped at a plan/ledger/projection layer.

Treat this as a false-interaction bug. Do not defend it as safety governance. Make the current boundary explicit, then land the next safe layer.

## Correct staged boundary

1. Draft-only projection
   - Button may generate local UI feedback only.
   - Copy must say draft / not written / needs capability.
   - It must not say registered, applied, resumed, or dispatched.

2. Local operator-decision ledger
   - Add a registered capability such as `*.decision.record`.
   - Add a narrow local endpoint.
   - Require same-origin/localhost guards, JSON content type, auth token/cookie, `capability_allowed(action)`, exact `confirm == requestId`, decision allowlist, and bounded payload size.
   - Write only an append-only local ledger plus audit log.
   - Read back the ledger row in tests/probes.

3. Adapter apply boundary
   - Do not pretend the local decision ledger changes task/application state.
   - Add a separate adapter capability such as `taskpool.decision.apply`.
   - Consume the exact recorded decision by `requestId` and confirm.
   - Recheck the current adapter state immediately before mutation.
   - Map decisions to a small allowlist of target states/actions.
   - Perform exactly one adapter-specific mutation or classify as already-applied.
   - Read back the adapter state and write an apply ledger row.
   - Make replay idempotent for the same request / decision / target / status tuple.

4. Executor dispatch boundary
   - Do not dispatch workers just because adapter state changed.
   - Add a separate executor capability that consumes the verified adapter mutation.
   - For taskpool Human Inbox resume, `taskpool.executor.dispatch` should mean governed claim-and-handoff only: consume the verified apply row, require a compatible decision such as `approve_with_edit`, call the taskpool handoff CLI with `shell=False`, read back `claimed`, append a dispatch ledger, and make replay idempotent.
   - Keep actual worker process start, task-body execution, external side effects, platform sends, deployment, destructive writes, and arbitrary shell out of this boundary unless a later separately registered capability opens them.

## Full-landing / one-time-open interpretation

When the user says “全盘推进直至完整落地”, “继续增强，直至可一次性开放”, or equivalent for this class of console work, completion means the intended user-visible effect is actually carried to the relevant production-grade safe boundary. Do not equate “we reached a safe stop” with “done”; first model the full chain, then implement the next safe capability boundary until only a genuinely higher-risk action remains.

- if the desired effect is “record my choice”, stop at local decision ledger only after saying it is record-only;
- if the desired effect is “apply my choice to task state”, continue to adapter apply/readback;
- if the desired effect is “resume execution”, create the next executor-dispatch capability instead of implying dispatch happened;
- if the desired effect is “one-time open”, arm a short-lived registered capability set once, but keep each action independently validated and audited rather than collapsing all side effects into an arbitrary executor.

For a Human Inbox taskpool resume chain, the preferred one-click UI path after arm is:

1. `human.decision.record` writes the local decision ledger.
2. `taskpool.decision.apply` consumes the decision and writes/readbacks the adapter state.
3. `taskpool.executor.dispatch` consumes the verified apply row and creates a claim-and-handoff executor handoff, readbacking `claimed`.
4. Actual worker process start remains a later capability such as `taskpool.worker.execute`.

A response that stops at proposal, draft, read-only projection, mock, visual button, copy-only change, or local ledger when adapter/executor state was intended is not complete. A response that claims worker execution from a handoff-only boundary is also not complete; label it as claim-and-handoff only.

## UI rules

- If it looks like a button, make it a native `<button>` with visible feedback, or render it clearly as non-action text.
- Operation feedback must distinguish: draft generated, local ledger recorded, adapter state changed/read back, executor dispatched.
- Never show executor-resumed copy unless a real backend path wrote or enqueued that fact.
- For strategy/options not backed by side-effect capability, label the result as a draft and point to the required future capability.

## Minimal tests/probes

- API contract: unarmed record/apply capabilities return 403 `capability_not_armed`.
- API contract: invalid decision returns a decision-not-allowed error.
- API contract: apply rejects missing prior decision record.
- API contract: apply rejects unsafe targets and evidence-free “accept/done” when the lifecycle requires evidence.
- API contract: armed valid record writes the decision ledger and audit row.
- API contract: armed valid apply mutates or classifies already-applied, reads back state, writes apply ledger, and is idempotent.
- UI contract: app contains endpoint paths, local-ledger receipt copy, adapter-apply/readback receipt copy, and no misleading registered/resumed copy for draft-only choices.
- Browser/live probe: arm session, click an operator choice, read back the local ledger and adapter-apply ledger rows, then reset public snapshot/session to unarmed/no-token.

## Pitfalls

- Directness means one click through a registered, audited capability chain. It does not mean skipping digest/current-state/readback boundaries.
- Do not collapse local decision, adapter mutation, and executor dispatch into one hidden action.
- If adapter state is already at the target status, treat it as already-applied with readback proof, not as a failed transition.
- If a “done/accept” path needs evidence, reject without evidence rather than fabricating completion.
