# Structured semantic intent and idle-neutral readiness

Use this when auditing or extending a local brain/taskpool that must process knowledge, plans, decisions, or learning without keyword-triggered authority.

## Applicability

- Task routing or content processing currently uses substring/regex/token lists.
- “Knowledge”, “solution”, “workflow”, or similar words must not directly trigger execution, durable learning, multimodel intervention, or completion.
- Autonomy readiness incorrectly fails when the canonical taskpool is empty.

Anti-conditions:

- Do not use a semantic label as evidence or execution authority.
- Do not replace keyword lists with an equally opaque fixed task-type switch and call it semantic routing.
- Do not require active work merely to make a readiness check pass.

## Contract pattern

Require a versioned semantic intent envelope before any semantic decision can carry authority:

- `schema_version`
- `intent_class`: observe, investigate, decide, govern, evolve, or deliver
- `domain_capabilities`: stable capability IDs resolved through a declarative capability registry/graph
- `requested_outcome`
- `risk_dimensions`
- `evidence_requirements`
- `learning_scope`
- `side_effect_class`
- `confidence`
- `source_refs`

The model/calibration layer may infer this envelope, but downstream gates consume only the validated structure. Surface text is diagnostic context, never authority.

Unknown schema, missing fields, low confidence, unknown capability, conflicting brain ownership, or unsupported intent/capability combinations fail closed to clarification/evidence collection.

High-side-effect classes remain authority-blocked even when the semantic route is otherwise valid: external write, publish, destructive action, payment, credential entry, or physical actuation still require an exact independent grant.

## Knowledge and solution boundary

Map intent to processing behavior rather than words:

- observe -> evidence observation
- investigate -> source-grounded investigation
- decide -> decision synthesis
- govern -> governance evaluation
- evolve -> capability evolution
- deliver -> delivery planning/controlled execution

Keep writeback classification separate:

- task/project evidence may be deposited under existing gates;
- reusable procedure, stable user preference, or ratchet candidate requires repeated evidence plus a writeback classifier;
- intent inference alone must never mutate Skill, Memory, or global policy.

Legacy lexical classification may remain temporarily as explicitly advisory compatibility output. Mark it `warn_only`; do not let it open claim, execution, learning, or done gates.

## Required metamorphic tests

1. Same semantic envelope + radically different wording -> identical route/policy.
2. Same wording + different semantic envelopes -> different route/policy.
3. Trigger-like words + observe/no-write envelope -> no execution and no durable learning.
4. No trigger-like words + investigate/decide envelope -> correct content processing.
5. Missing/malformed/low-confidence/unknown-capability envelope -> fail closed.
6. Harmless wording + external-write envelope -> authority blocked.
7. Reusable-learning scope without repeated evidence -> ratchet candidate only, no Skill write.

## Idle-neutral readiness

Separate architectural readiness from workload availability:

- If `active == 0` and `dispatchable == 0`, priority-lane selection is neutral PASS; there is nothing to preempt.
- If dispatchable work exists, the configured priority lane must be selected.
- An eligibility result of `status=PASS`, `eligible=false`, `reasons=[no_dispatchable_task]` is explicit safe idle.
- Error-shaped denials or mixed unknown reasons remain FAIL.

Do not use historical done/archived lane counts as evidence that a live priority lane should have been selected.

## Producer propagation and persistence invariants

A canonical validator is insufficient if wrappers, batch ingestors, or generated-child paths drop the envelope. Inventory every internal call into task creation (AST call-site enumeration is preferable to a name search) and classify each as:

- direct CLI input with an explicit envelope argument;
- wrapper forwarding the caller-supplied envelope unchanged;
- generated child inheriting only a parent envelope already marked validated;
- legacy/non-strict compatibility, which must still fail closed before executable states.

Never synthesize authority from a title, inbox line, metadata fragment, truth-gate text, evidence description, or review-gap prose. A generated repair child may inherit a validated parent envelope unchanged; canonical task creation must revalidate it, and inheritance must not increase lane, task class, side-effect, execute, or multimodel authority.

Treat serialization as part of the authority boundary. A structure that validates in memory but reloads as a string is a broken SSOT. For Markdown/frontmatter stores:

- serialize envelope objects with reversible JSON or a real nested-data format, not language-specific `repr`;
- reload the saved task through the production parser and assert object equality;
- recompute the semantic decision after reload;
- prove malformed object-looking strings stay strings and cannot become authority;
- test both tasks when a wrapper creates a pair or batch.

## Verification loop

1. Write acceptance and negative cases first.
2. Add RED tests for semantic invariance, authority blocking, idle neutrality, producer propagation, and save/reload equality.
3. Implement the smallest structured contract and declarative capability registry.
4. Enumerate all canonical task-creation call sites; prove each has an explicit semantic source and no prose-inference path.
5. Integrate a semantic-contract selfcheck into autonomy readiness.
6. Run focused tests, full taskpool tests, syntax checks, selfcheck, proof-check, memory replay gate, brain registry validation, and live readiness JSON readback.
7. Run isolated strict-root probes for missing, malformed, conflicting, unvalidated-parent, and multimodel-forbidden cases; assert no task artifact is left behind on refusal.
8. Ask an independent verifier to read the latest bytes and run its own tempfile probes. Reject stale verifier findings by timestamp/hash only after reproducing the claimed issue against current code; never dismiss a newly found persistence or producer gap because the suite is green.
9. Confirm readiness reports the semantic-contract check explicitly and lists no architecture blockers.
10. Inspect scoped diff. In a concurrently dirty orchestrator file, do not commit unrelated hunks; preserve a hash-bound patch/evidence packet or use exact hunk staging only after verifying the existing index is unchanged.

## Qualification claim boundary

A passing structured semantic contract certifies routing/writeback authority separation for the covered control-plane path. It does not prove every legacy intake producer emits the envelope, every external adapter is enabled, or every historical task is migrated. State those migration/runtime boundaries explicitly.
