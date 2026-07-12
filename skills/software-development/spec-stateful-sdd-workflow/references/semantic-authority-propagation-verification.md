# Semantic Authority Propagation Verification

## Applicability

Use when a structured semantic envelope, policy evaluator, capability registry, or intent classifier controls dispatch, claims, lifecycle transitions, external effects, multimodel routing, or durable learning.

Anti-condition: do not require this matrix for purely descriptive classification with no downstream authority-bearing consumer.

## Core verifier rule

A fail-closed evaluator is insufficient unless every authority-bearing consumer enforces its output. Verify the complete chain:

```text
input/envelope -> validator -> policy projection -> dispatchability -> claim -> running -> review/done -> side-effect/writeback sink
```

A result such as `decision=route` is routing authority only. It must not be treated as execution authority when `policy.may_execute=false`. Likewise, `may_write_learning=false`, `multimodel.mode=forbidden`, and external-write authority blocks must remain effective at their final sinks.

## Required negative matrix

1. **Malformed envelope:** top-level string/dict/empty/bool/number/list plus malformed nested maps and list elements. Assert no exception opens authority and no case routes executable work.
2. **Non-executable valid envelope:** build a fully valid envelope that returns `decision=route` and `policy.may_execute=false` (for example observe/advisory). Assert all executable states and sinks reject it.
3. **Strict-root coverage:** test intake, `is_dispatchable`, manual claim, every executable lifecycle transition, and force/manual override. Semantic authority failures must be appended outside `if not force` branches.
4. **Forbidden multimodel:** combine `mode=forbidden` with retry thresholds, stale claims, explicit legacy flags, and runtime triggers. Assert the final multimodel spawn-reason set remains empty.
5. **Registry corruption:** corrupt schema, `allowed_intents`, and every string-list field with wrong container and wrong element types. Assert both evaluator and readiness fail.
6. **Surface-text invariance:** vary titles/body/log-like text while holding the envelope constant. Compare the complete projected decision, not only route/brain labels.
7. **Independent side-effect gates:** external write and durable learning must each remain blocked at the sink despite otherwise valid delivery intent.
8. **Legacy compatibility:** prove old lexical/metadata paths cannot create execution, lifecycle, multimodel, or learning authority without the structured contract.

## Probe design

Prefer independent in-process probes that monkeypatch only registry/task-root readers and construct minimal task objects. Do not write live task files merely to test rejection. Report exact JSON fields such as:

```json
{
  "decision": "route",
  "policy_may_execute": false,
  "claimed_failures": [],
  "running_failures": [],
  "done_failures": []
}
```

The example above is a blocker: the policy says non-executable while lifecycle consumers accept executable states.

## Readiness caveat

A green readiness/selfcheck is not convergence unless corrupted-registry probes and authority-sink probes are also run. Selfchecks often validate evaluator behavior but miss propagation into dispatch/lifecycle consumers.

## Closure rule

Approve only when every material policy bit is enforced by every relevant consumer and negative cases prove force, retry, stale-runtime, legacy, and surface text cannot override it. Passing unit suites with a missing authority-propagation assertion warrants `amend`, not `approve`.
