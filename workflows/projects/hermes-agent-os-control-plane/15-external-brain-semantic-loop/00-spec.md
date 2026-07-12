# External Brain Semantic Lifecycle Loop — Spec

Date: 2026-07-11
Scope: local Hermes brain/taskpool control plane
Risk: local reversible implementation only

## Goal

Make the local brain a qualified external brain: intake is converted into an explicit semantic intent envelope; routing, lifecycle policy, evidence requirements, learning writeback, and stop/continue decisions consume that envelope; repeated execution converges through evidence-backed lifecycle states.

## Non-goals

- No keyword/substring/regex list may grant routing, execution, completion, multimodel intervention, or durable learning authority.
- No model vote or inferred label may replace task evidence.
- No external send, deploy, push, destructive action, credential entry, payment, production write, or broad fan-out.
- No taskpool lifecycle force-close and no allowlist expansion.
- Legacy lexical classification may remain only as an explicitly advisory compatibility observation; it cannot open an authority gate.

## Semantic intent contract

Each actionable task must carry a versioned `semantic_intent` envelope with:

- `schema_version`
- `intent_class`: deliver | investigate | decide | evolve | govern | observe
- `domain_capabilities`: stable capability IDs from the brain registry/capability graph
- `requested_outcome`
- `risk_dimensions`
- `evidence_requirements`
- `learning_scope`: none | task | project | reusable_procedure | stable_user_preference | ratchet_candidate
- `side_effect_class`
- `confidence`
- `source_refs`

Unknown/ambiguous/malformed envelopes fail closed to advisory clarification or evidence collection. They never default to execution authority.

## Lifecycle loop

Observe -> Frame -> Route -> Plan -> Gate -> Execute -> Verify -> Reflect -> Writeback/Stop

Every stage must emit a structured decision/evidence record. Continue only when the evaluator reports an unmet acceptance criterion with a safe local reversible next slice. Stop on done, explicit evidence boundary, authority boundary, budget exhaustion, kill switch, or non-convergence.

## Acceptance criteria

AC1. Classifier decisions are determined from structured semantic fields and registry capability ownership, not words in title/body.
AC2. Two texts with different words but the same semantic envelope produce the same route, lane, risk, evidence, and learning policy.
AC3. Two texts containing the same words but different semantic envelopes produce different policy decisions.
AC4. Missing, malformed, low-confidence, unknown-capability, or authority-smuggling envelopes fail closed and do not become executable.
AC5. Knowledge/solution content can trigger investigate/decide/evolve processing only through semantic intent fields; durable writeback is separately classified and evidence gated.
AC6. Empty taskpool is a valid idle state for readiness checks; architecture readiness does not fail merely because no priority-lane task exists.
AC7. The autorun bridge readiness probe distinguishes safe idle/no-task from an unsafe bypass and remains read-only.
AC8. Focused tests, relevant existing suites, py_compile, live CLI readback, selfcheck, proof-check, memory replay gate, and diff check pass.
AC9. No forbidden external or destructive side effect occurs.
AC10. Specialized intake wrappers may forward an explicit validated envelope into canonical `command_add`, but may not synthesize authority from titles, source metadata, truth-gate text, or evidence-bundle text.
AC11. Producers that do not yet emit a valid envelope remain fail-closed at strict intake/lifecycle; they require an upstream semantic-calibration contract rather than a Python keyword fallback.
AC12. Every validated strict intake automatically performs a bounded local-brain recall derived only from semantic envelope fields, persists content-hash-bound source refs, exposes them to the worker plan before execution, and binds the receipt to the canonical semantic envelope digest.
AC13. Recall text, scores, paths, or an empty result never expand route, execute, side-effect, multimodel, lifecycle, or learning authority; recall errors fail closed before task creation in strict roots. Executable lifecycle transitions recompute the expected query plan, verify receipt/ref/evidence consistency, and confirm non-empty hash-bound refs against the current local-brain search source; malformed, stale, unavailable, or forged sources fail closed.
AC14. Generated children and specialized wrappers traverse the same canonical recall boundary; no producer may bypass recall by calling a lower-level writer.

## Negative cases

- Title contains “知识/方案/闭环/workflow” but envelope says observe+no-write: no execution or learning writeback.
- Title contains no known trigger words but envelope says investigate with evidence requirements: route and evidence plan are produced.
- `learning_scope=reusable_procedure` without repeated evidence/source refs: fail closed to ratchet candidate, not Skill mutation.
- Empty taskpool: readiness reports idle-neutral checks, not architecture failure.
- No task selected: eligibility readiness is safe-idle only when canonical no-task result is explicit; arbitrary errors still fail.

## Evidence required

RED/GREEN tests; exact file diff; CLI JSON readback; taskpool and memory gates; independent read-only review; scoped commit that excludes unrelated dirty files.
