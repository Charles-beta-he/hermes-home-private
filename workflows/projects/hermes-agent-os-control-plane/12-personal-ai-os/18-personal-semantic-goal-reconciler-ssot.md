# Personal Semantic Goal Reconciler — Long-Term Stable SSOT

Status: active-ssot
Schema contract: `PersonalSemanticGoalReconciler.v1`
Updated: 2026-07-29T03:02:14+08:00
Project: `hermes-agent-os-control-plane`
Supersedes for this concern: staged Personal AI OS roadmap narration; it does not replace native project/task/memory/authority/evidence owners.

## Objective model

### Goal

Give Hermes a stable, ontology-grounded personal cognitive metamodel and one bounded proactive reconciliation loop that turns evidenced goal deviation into explainable action candidates without creating another project/task/memory/permission SSOT or allowing model output to grant authority.

### Success criteria

1. One canonical flow is replayable: `Event -> Observation -> GoalGap -> ActionCandidate -> Intention -> AuthorityEvaluation -> external executor boundary -> Receipt -> Re-observation -> GoalGap'`.
2. Stable semantic assertions, dynamic observations, model inferences, goals, candidates, grants, and receipts are distinct typed objects.
3. Every semantic assertion carries source, scope, epistemic status, provenance, freshness where applicable, and `authority_effect: none`.
4. Deterministic goal-gap evaluation precedes model explanation or planning for measurable states.
5. Only the Goal Reconciler owns `GoalGap -> ActionCandidate -> Intention` arbitration. Mission, workflow, taskpool, procedure, cron, and external-brain loops may emit events/observations or consume an already authorized intention; they do not independently own the same gap.
6. Candidate generation and grant matching have zero execution side effect. The read-only Agent OS surface never executes capabilities.
7. A fresh post-action observation, not a tool return or receipt alone, determines convergence.
8. Negative evidence proves stale observations, missing provenance, scope leakage, inferred-preference authority smuggling, expired/non-exact grants, duplicate events, packet-local forged Receipts/readbacks, and trusted Receipt without trusted post-action readback fail closed.
9. Capability/semantic projections remain rebuildable from native owners and exclude archived/profile-other sources unless explicitly scoped.
10. Status and verification claims are evidence-bound. `not_certified` remains visible until independent review and fresh objective evidence close it.

### Constraints

- Preserve existing CLI and Agent OS public behavior.
- Extend the existing `hermes agent-os` edge; do not add a model tool or parallel service.
- Use profile-aware `HERMES_HOME`; no hardcoded runtime home.
- Local implementation is reversible and read-only/candidate-only by default.
- No scheduler/worker/taskpool lifecycle mutation, external dispatch, publish/deploy/push, destructive action, payment, credential entry, or physical-device effect.
- No generated shell/Python execution from semantic candidates.
- Explicit preference, repeated behavior, model inference, and authority are never conflated.
- Dynamic state is represented by timestamped observations, never promoted into stable ontology relations solely because it was recently observed.
- Model output may rank/explain/propose; deterministic code owns validation, freshness, gap calculation, exact grant matching, lifecycle state, and receipts.

### Non-goals

- Simulating consciousness, intrinsic desire, a Freudian psyche, or a fixed personality.
- Deploying RDF/OWL/SWRL/ODRL infrastructure merely to imitate standards; typed JSON contracts are acceptable when semantics are preserved.
- Replacing Memory, Project Profile, Mission, Taskpool, Skill/Workflow, Evidence, or Authority Ledger ownership.
- Opening autonomous external execution. This contract produces an exact, inspectable handoff for a separately authorized side-effect sink.
- Inventing long-term user goals or values. The model may propose a candidate goal, which remains unowned and non-durable until explicit promotion.

## Source basis and adaptation boundary

The book *本体驱动的AI数据管理* provides the enterprise pattern `事实 -> 事理 -> 行动 -> 目标与评估`, the “7+1” semantic framework, ODRL-style authority semantics, decision-to-action modes, and feedback optimization. This SSOT adapts those mechanisms to a personal agent. The book does not explicitly define a “personal cognitive metamodel”; personal epistemic, metacognitive, revision, privacy, and anti-authority-smuggling rules below are Hermes-specific extensions.

## Native ownership and projection boundary

| Native owner | Owns | Reconciler treatment |
|---|---|---|
| user/profile memory | stable, curated, explicit personal facts/preferences | typed references; never copied as a second mutable memory store |
| project profile/SSOT | project facts, conventions, objective model | typed references with project scope |
| skills/workflows | reusable procedures and action contracts | rebuildable capability/action projection |
| mission runtime | durable goal lifecycle | goal references and current mission state |
| taskpool/Kanban | task lifecycle | event/observation source or authorized-intention consumer |
| runtime probes/native APIs | current external/system state | timestamped Observation |
| evidence/receipt store | execution and verification proof | evidence/receipt references |
| authority ledger/policy sink | grants, prohibitions, budgets, expiry | exact grant evaluation; never inferred from graph edges |
| Personal Semantic Graph | typed rebuildable relationships only | no competing lifecycle or authority ownership |

## Stable semantic object model

### SemanticAssertion

Required fields:

```yaml
assertion_id: string
subject_ref: string
predicate: string
object: any
epistemic_status: explicit | observed | derived | inferred | hypothetical
scope:
  kind: global | role | project | task | session
  ref: string | null
source_ref: string
source_owner: user_profile | project_profile | skill_workflow | mission | taskpool | runtime_probe | evidence_store | authority_ledger
asserted_by: user | native_system | deterministic_rule | model
observed_at: ISO-8601 | null
valid_from: ISO-8601 | null
valid_until: ISO-8601 | null
confidence: number | null
revision_of: string | null
authority_effect: none
```

Invariants:

- `authority_effect` must be exactly `none`.
- `inferred` and `hypothetical` assertions cannot be emitted as explicit user facts.
- Role/project/task/session assertions cannot leak into a different scope.
- Contradictory context-scoped preferences coexist until an explicit revision resolves them.
- Model-generated behavior cannot validate the model's own user-model inference.

### GoalSpec

```yaml
goal_id: string
owner_ref: string
parent_goal_ref: string | null
subject_ref: string
predicate: string
operator: eq | ne | gte | lte
desired_value: scalar
tolerance: number | null
priority: low | medium | high | critical
observation_sources: [string]
max_observation_age_seconds: integer
scope: {kind, ref}
budget: {interruptions, executions, cost_units}
side_effect_ceiling: S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7
cooldown_seconds: integer
stop_conditions: [string]
revision: string
```

Invariants:

- A durable goal requires an owner and revision.
- Generated subgoals must reference a parent and cannot widen scope, budget, side-effect ceiling, or authority.
- Goal existence and priority do not authorize action.
- `goal.budget.executions` and `goal.budget.cost_units` are total ceilings for the goal revision, not remaining counters. Exact externally trusted Receipts for the selected intention consume one execution and that action contract's estimated cost. `cooldown_seconds` is measured from the latest exact trusted Receipt `finished_at`; equality at the boundary permits reconsideration.

### Observation

```yaml
observation_id: string
subject_ref: string
predicate: string
value: scalar
observed_at: ISO-8601
source_ref: string
provenance_ref: string
```

An Observation can influence current state, GoalGap, ranking, or convergence only when the native probe owner supplies an out-of-band `trusted_observation_bindings` token computed over the entity type and canonical exact row. Reusing a trusted ID while substituting any row byte invalidates the binding. Packet-local `source_ref` and `provenance_ref` strings cannot authenticate the row. Freshness is then computed from the out-of-band, timezone-aware UTC `evaluation_time`, `observed_at`, and the goal's maximum age. Packet-local `now` is only a declared `as_of` value: it is validated but cannot roll back freshness, Grant expiry, assertion validity, cooldown, or Intention selection time. If the trusted clock or Observation binding is unavailable, reconciliation fails closed as `needs_observation` or structured validation failure.

### GoalGap

```yaml
gap_id: deterministic string
goal_ref: string
expected: scalar
observed: scalar | null
gap_type: mismatch | below_minimum | above_maximum | missing_observation
severity: number in [0,1]
confidence: number in [0,1]
evidence_refs: [string]
why_now: string
```

For measurable values, deterministic comparison owns gap creation. Missing or stale observations produce `needs_observation`, not a certain current-state claim.

### ActionContract

```yaml
action_id: string
capability_ref: string
serves_predicates: [string]
target_ref: string
expected_effect: string
risk_class: T0 | T1 | T2 | T3 | T4 | T5
side_effect_level: S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7
required_authority: string
preconditions: [string]
rollback_method: string
readback_method: string
estimated_cost_units: number
```

Every action contract names preconditions, effects, risk, rollback, and readback. Missing any field excludes it from candidacy.

### ActionCandidate and Intention

A candidate is a ranked proposal with evidence and zero authority. An intention is the single selected candidate after deterministic filtering/deduplication, still not executable until the external authority sink validates an exact grant.

Required output fields:

```yaml
candidate_id: deterministic string
action_contract_digest: deterministic string
goal_ref: string
gap_ref: string
action_ref: string
score: number
risk_class: string
side_effect_level: string
required_authority: string
evidence_refs: [string]
authority_status: not_required_read_only | missing | revoked | expired | non_exact | under_budget | untrusted_projection | untrusted_provenance | matched_trusted_projection | goal_budget_exhausted | cooldown
may_execute: false
```

Candidate identity binds `goal_id + predicate + goal revision + the complete canonical ActionContract`, so a material action mutation produces a new candidate identity while equivalent gap re-observations do not.

The promoted Intention is a distinct record, not an alias of the candidate:

```yaml
intention_id: deterministic string bound to intent event, candidate, and ordered selection context
candidate_ref: candidate_id
selection_context_digest: deterministic string
goal_ref: string
action_ref: string
action_contract_digest: deterministic string
selected_at: trusted evaluation_time
authority_status: string
may_execute: false
```

Receipts bind only through the promoted `intention_id + action_ref`. A candidate ID or a nonselected candidate cannot satisfy that binding.

`may_execute` is always false on this Agent OS read-only surface. A matched grant means only that the candidate is eligible for handoff to a separately governed side-effect sink, which must authenticate and revalidate the grant at execution time.

### AuthorityGrant

```yaml
grant_id: string
granted_by: user | configured_policy | external_authority
capability_ref: string
target_ref: string
side_effect_level: string
scope: {kind, ref}
issued_at: ISO-8601
expires_at: ISO-8601
budget: {executions, cost_units}
provenance_ref: string
status: active | revoked
```

Exact match requires capability, target, side-effect level, scope, active status, unexpired time, sufficient budget, authority-ledger provenance, and an out-of-band `trusted_grant_bindings` token over the Grant's entity type and canonical exact row supplied by the native authority owner. Same-ID row substitution invalidates trust. A packet-local Grant, including one with an `authority_ledger:`-looking prefix, remains `untrusted_projection`. Preferences, ontology edges, prior receipts, model confidence, and goal priority cannot satisfy the grant.

### ExecutionReceipt

```yaml
receipt_id: string
intention_ref: string
action_ref: string
status: completed | failed | uncertain | blocked
started_at: ISO-8601
finished_at: ISO-8601
result_evidence_refs: [string]
post_action_observation_refs: [string]
```

A Receipt can affect budget, cooldown, blocking, uncertainty, or convergence only when the native receipt/evidence owner supplies an out-of-band `trusted_receipt_bindings` token over the Receipt's entity type and canonical exact row. Same-ID row substitution invalidates trust. A packet-local Receipt is ignored even when it names an exact deterministic `intention_id + action_ref`.

A trusted `completed` Receipt still does not authenticate packet-local readback rows. Each referenced post-action Observation must also match an out-of-band `trusted_post_action_observation_bindings` token over its entity type and canonical exact row supplied by its native probe owner; match the goal subject/predicate/source contract, and be strictly newer than `finished_at`. Without that independent binding the result remains `uncertain_without_readback`. A receipt proves only its evidenced runtime claim; fresh trusted referenced readback is classified as `reobserved_converged` or `reobserved_gap`, and an unrelated converged observation cannot upgrade a Receipt's gap readback.

### ReconciliationResult

```yaml
schema: PersonalSemanticReconciliationResult.v1
intent_id: string
goal_ref: string
state: converged | needs_observation | candidate | waiting_authority | eligible_for_executor | blocked | uncertain
selected_observation_ref: string | null
gap: GoalGap | null
candidates: [ActionCandidate]
intention: Intention | null
receipt_evaluation: none | uncertain_without_readback | reobserved_converged | reobserved_gap | failed | blocked | uncertain
why_now: string
boundary:
  runtime_mutation: false
  capability_execution: false
  authority_expansion: false
  external_side_effects: false
  durable_semantic_writeback: false
```

## One coordination loop

```text
Event
  -> resolve references against Personal Semantic Graph
  -> read fresh native Observation
  -> deterministically evaluate GoalGap
  -> generate/rank ActionCandidate records
  -> dedupe, cooldown, budget, risk, interruption, confidence filters
  -> commit at most one candidate as Intention
  -> evaluate exact AuthorityGrant as projection only
  -> stop at separately governed executor boundary
  -> ingest ExecutionReceipt
  -> require fresh native Re-observation
  -> recompute GoalGap'
  -> converge, continue, block, or remain uncertain
```

Ownership rule: only the Goal Reconciler arbitrates a given `goal_id + predicate + revision` gap. Mission/workflow/taskpool/procedure/cron controllers must carry this arbitration key when consuming an intention. Replay of the same intent event and equivalent selection context produces the same deterministic Intention identity; a distinct intent event or ranking context produces a distinct Intention while preserving stable Candidate identity.

Candidate identity is independent of the caller event/`intent_id` and transient gap observation. It binds `goal_id + predicate + revision` plus the complete normalized `ActionContract`, so equivalent replay events deduplicate while any material action-semantics change (capability, target, effect, risk, side effect, authority requirement, preconditions, rollback/readback, or estimated cost) produces a successor identity that cannot consume an old receipt.

This v1 contract proves action-to-goal scope containment conservatively: `global` goals may address an explicit target, while `role | project | task | session` goals accept only an action whose `target_ref` exactly equals the goal scope `ref`. Rich hierarchical containment is intentionally unsupported until a separately evidenced scope registry is part of the packet; unknown containment fails closed rather than widening scope.

## Candidate ranking

The default deterministic rank is:

```text
score = gap_severity
      * goal_priority_weight
      * observation_confidence
      - risk_penalty
      - normalized_cost
```

Tie-breaker: lexicographically smallest `action_id`. Cognitive assertions may influence explanation, evidence requirements, interruption cost, or ranking only when an out-of-band `trusted_preference_assertion_bindings` token over the assertion's entity type and canonical exact row arrives from its native owner, their native owner/source contract is valid, their scope applies, and epistemic status is `explicit` or independently `derived`. Packet-local source strings cannot self-authenticate. Assertions can never modify authority status or `may_execute`.

## Runtime placement

```text
CLI / dashboard / mission event
  -> intent resolver
  -> rebuildable semantic/capability projection
  -> pure Personal Semantic Goal Reconciler
  -> candidate/intention/authority-evaluation readback
  -> separately governed executor (closed here)
  -> receipt/evidence store
  -> native probe re-observation
```

Implementation footprint: extend `hermes agent-os`; no new model tool, daemon, graph database, scheduler owner, or parallel lifecycle store.

## CLI contract

- `hermes agent-os cognitive-schema --json` returns the stable object contract and safety invariants.
- `hermes agent-os reconcile --input PATH --json` reads one explicit packet, injects the current UTC evaluation clock, trusts no packet-local Observation, preference, Grant, Receipt, or post-action Observation IDs by default, validates the packet, and emits one deterministic semantic `ReconciliationResult`; without a native Observation trust adapter it therefore returns `needs_observation` rather than projecting packet-local state as current truth.
- Invalid input exits non-zero with structured findings and performs no reconciler-owned domain or lifecycle writes. Generic Hermes process startup may initialize profile logs/state, so black-box tests must bind `HERMES_HOME` to disposable storage and must never target the real profile.
- The command does not update the input file, project packet, memory, mission, taskpool, authority ledger, receipts, workflow state, cron configuration, or runtime state.

## Fail-closed and negative requirements

The reconciler must reject or stop safely when:

- provenance, source, scope, owner, revision, timestamp, rollback, or readback fields are absent;
- a timestamp is malformed, in the future beyond declared tolerance, or stale;
- assertions attempt `authority_effect != none`;
- an inferred/hypothetical or packet-local untrusted preference is used to claim explicit user intent, select an Intention, or claim authorization;
- an action contract lacks rollback/readback, exceeds the goal/mission ceiling, or targets outside the exact non-global goal scope;
- a grant is expired, revoked, non-exact, under-budgeted, lacks authority-ledger provenance, or lacks out-of-band native-owner trust;
- a receipt claims completion without a referenced fresh re-observation;
- duplicate events could create duplicate intention identities;
- a model-proposed goal lacks owner promotion;
- scope would widen from parent goal to subgoal;
- any candidate attempts executable shell/Python, secrets, payment, publish/deploy/push, destructive, broad fan-out, or physical action without a separate exact runtime gate.

## Compatibility and migration rule

Existing Agent OS status/doctor/route/replay/report behavior remains unchanged. Existing `UserGoal`, `MissionRuntimeState`, `CapabilityNode`, `AuthorityRecord`, and `EvidenceNode` data remain native inputs; adapters normalize them into this contract. The v0 packet is retained as history. This SSOT is the canonical stable definition for personal cognition and goal reconciliation, replacing roadmap-phase reasoning for this concern.

## Verification contract

Positive evidence:

1. Fresh observation within tolerance returns `converged`, no gap, no candidate.
2. Fresh measurable deviation returns deterministic gap and candidates.
3. Exact active grant returns `eligible_for_executor` while `may_execute=false` and all boundary flags remain false.
4. Duplicate identical input returns identical semantic result and deterministic IDs.
5. A completed receipt plus fresh referenced re-observation recomputes the goal and can converge.
6. CLI output is valid JSON and input/source files are byte-identical before and after.

Negative evidence:

1. Stale/missing observation returns `needs_observation` and no executable claim.
2. Missing provenance or non-`none` authority effect is rejected.
3. Inferred or packet-local untrusted preference cannot change Candidate ranking or promoted Intention.
4. Expired, revoked, non-exact, under-budget, or packet-local untrusted Grant returns `waiting_authority`.
5. Rolling packet `now` backward cannot revive stale evidence or expired authority, and `selected_at` remains bound to trusted evaluation time.
6. Completed receipt without post-action readback returns `uncertain`, even when an execution-preceding observation already satisfies the goal.
7. Scope-widening child goal is rejected.
8. Missing rollback/readback excludes or rejects an action contract.
9. Hostile Python key/scalar subclasses and cyclic/over-deep typed JSON fail through structured validation without invoking attacker-controlled formatting or representation methods.
10. No test writes to the real `~/.hermes`.

Closure requires:

- focused tests and real CLI import path pass from an isolated `HERMES_HOME`;
- existing Agent OS focused suite remains green;
- input immutability is hash-verified;
- code diff is independently reviewed with P0/P1 findings closed;
- fresh `hermes agent-os status --json`, `doctor --json`, and reconciliation readback are captured;
- global Agent OS certification remains honestly reported; this implementation cannot self-certify the wider system.
