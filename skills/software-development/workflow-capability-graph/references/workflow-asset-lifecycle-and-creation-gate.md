# Workflow Asset Lifecycle and Creation Gate

Scope: class-level governance for deciding when a fuzzy user request, repeated behavior, correction, or process preference should become a governed workflow asset. Applicability: use when improving or creating reusable workflows, workflow templates, capability graphs, route policies, or loop-engineering self-advancing systems. Anti-condition: do not trigger merely because the user says "create workflow"; do not create durable assets for one-off task progress or transient session plans.

## Core rule

Workflow creation is judgment-driven, not keyword-driven.

Do not ask only: "Did the user say workflow?"
Ask: "Does this deserve becoming a reusable, verifiable, governable workflow asset?"

User words such as "创建工作流", "以后这样", "自动", "常用", or "形成流程" are signals, not commands. They raise the decision score but must pass the assetization gate below.

## Landing-zone classifier

Before writing anything durable, classify the request or lesson:

- One-off task/session plan -> no durable workflow write; keep in active context or task-local notes.
- Stable user preference -> memory/user profile; do not store the whole workflow body in memory.
- Reusable procedure/checklist/pitfall -> skill or skill reference.
- Project-specific convention or workflow -> project SSOT/profile or explicitly scoped project reference.
- Concrete future engineering work -> taskpool candidate/proposal, not a fake skill.
- Possible cross-project lesson lacking validation -> experience-ratchet proposal.
- Execution automation -> taskpool/cron/AgentOS only after side-effect gates, exact target, rollback/readback, and evidence contracts.

Split mixed conclusions instead of storing one coupled blob.

## Workflow assetization gate

Create or upgrade a workflow asset only when enough of these are true:

1. Reuse value
   - The pattern is likely to recur.
   - A durable workflow will reduce future user steering.
   - It has stable input -> output -> verification structure.

2. Complexity
   - The task has multiple stages, context lookup, evidence requirements, routing choices, or verification gates.
   - A simple answer, one-shot table, or one-command task is insufficient.

3. Risk surface
   - The workflow may touch memory, skills, project profiles, taskpool, cron, AgentOS, external writes, publish/deploy, destructive actions, credentials, or production systems.
   - It can cause repeated misrouting, over-saving, or false completion claims if not governed.

4. Evidence gap
   - The workflow needs a clear definition of completion.
   - Model-only judgment is not enough; tool/readback/screenshot/API/test evidence may be needed.

5. Long-termity
   - The user indicates future reuse, automation, or stable behavior, or the pattern appears repeatedly in sessions.
   - These are weighted signals, not hard triggers.

6. Governability
   - The workflow can define applies_when, does_not_apply_when, inputs, outputs, gates, fallback, cleanup, and promotion/demotion rules.

If these are weak, do not create a workflow asset. Use an existing workflow, session plan, output-template fragment, project note, or no-write decision.

## Lifecycle levels

Use maturity plus retention, not a binary exists/does-not-exist flag.

Maturity:

- seed: raw user utterance or observed pattern.
- draft: system-expanded scope, still unverified.
- candidate: reusable enough to try; has applies/does_not_apply and output contract.
- validated: at least one real closed-loop run with evidence.
- common: frequently reused and route-prioritized.
- canonical: long-term protected standard path; requires route/eval evidence before broad use.
- deprecated: superseded by another workflow, with redirect.
- archived: historical read-only.
- revoked: proven harmful or wrong.

Retention:

- session_only: current conversation only.
- project_scoped: one project or SSOT.
- domain_reusable: reusable within a domain.
- global_reusable: cross-domain reusable.
- pinned: protected from cleanup.
- cleanable: eligible for TTL/usage cleanup.
- quarantine: isolated because of conflict, weak evidence, or high misroute risk.

## Creation / compilation loop

A robust workflow compiler follows this ladder:

1. IntentSeedCapture
   - Preserve the user's original phrase as seed evidence.

2. GoalCalibration
   - Infer task class, long-term target, and ambiguity level.
   - Ask only when ambiguity changes architecture, side effects, acceptance, or long-term behavior.

3. ContextRetrieval
   - Check relevant existing skills, project profiles/SSOTs, memory, session history, taskpool, and neighboring workflows before creating a new one.

4. TypeInference
   - Classify as answer, artifact, execution, automation, governance, product, research, visual, or hybrid workflow.

5. ReferencePatternScan
   - For long-term/canonical workflows, inspect internal neighbors and, when useful, external/competitor/open-source patterns.
   - Extract transferable structure and rejected mechanics; do not cargo-cult reference implementations.

6. ScopeModel
   - Define applies_when, does_not_apply_when, non-goals, inputs, outputs, side effects, authority boundary, evidence needs, and cleanup policy.

7. CapabilityGraphCompilation
   - Compile nodes such as intent_router, source_intake, context_loader, reference_scanner, scope_modeler, output_contract_builder, verifier, ratchet_writer, and cleanup_decider.
   - Agents wrap capability nodes with policy and authority; they are not mere labels.

8. OutputContractDesign
   - Define output format(s), ordering, grouping, dedupe, overlap handling, evidence columns, confidence columns, next-action fields, and audience/channel constraints.
   - For tables, decide one vs multiple tables, row/column dimensions, ordering, overlap, and evidence/decision columns rather than blindly emitting a table.

9. GateSystem
   - Every gate has pass/warn/fail/blocked outcomes.
   - Blocked should trigger the next safe recovery step when possible: evidence search, context readback, dry-run, smaller scope, or exact authorization request.

10. LandingZoneDecision
   - Place the asset in session, project SSOT, workflow workspace, skill/reference/template, experience-ratchet, taskpool, cron, or AgentOS according to scope and side effects.

11. RouteEval / Simulation
   - Test positive, negative, neighbor, and forbidden examples.
   - Check that the workflow does not over-trigger from keywords and does not under-trigger on high-reuse patterns.

12. Promotion / Demotion / Cleanup
   - Promote only with evidence.
   - Demote or quarantine on misroutes, false completion, stale assumptions, or lack of use.
   - Cleanup requires reference checks for cron, taskpool, skills, profiles, AgentOS projection, and project SSOTs.

## Multi-model routing policy

Do not run all-model review for every workflow. Route by risk and verification surface.

- T0: low-risk temporary output; single model plus basic readback.
- T1: medium complexity; main model plus self-check.
- T2: long-term workflow, routing, or skill/template changes; add independent reviewer or specialized lane.
- T3: canonical/global workflow, taskpool/cron/AgentOS, external side effects, memory/skill/profile mutation, publish/deploy/destructive/credential boundaries; require multi-model or independent review plus objective evidence.

Surface specialists:

- Goal/ambiguity: goal calibration lane.
- Architecture/lifecycle: architecture reviewer.
- Output UX/tables/reports: output-contract reviewer.
- Implementation: implementation reviewer.
- Safety/authority: policy reviewer.
- Evidence/completion claims: verification reviewer.
- Visual/UI: visual specialist.
- Red-team: adversarial reviewer.

Model agreement is advisory, not proof. Completion-critical claims still need objective evidence such as file readback, tests, browser/screenshot evidence, API/log readback, taskpool dry-run, or explicit human acceptance.

## Minimal workflow asset schema

```yaml
schema: hermes_workflow_asset_v1
id: string
title: string
version: 1
source:
  user_seed: string
  source_refs: []
classification:
  workflow_type: answer|artifact|execution|automation|governance|product|research|visual|hybrid
  scope: session|project|domain|global
  maturity: seed|draft|candidate|validated|common|canonical|deprecated|archived|revoked
  retention: session_only|project_scoped|domain_reusable|global_reusable|pinned|cleanable|quarantine
intent_model:
  user_goal: string
  success_criteria: []
  non_goals: []
  assumptions: []
  ask_user_only_when: []
routing:
  applies_when: []
  does_not_apply_when: []
  neighbor_workflows: []
  forbidden_triggers: []
  examples_positive: []
  examples_negative: []
output_contract:
  allowed_formats: []
  default_format: string
  ordering_rule: string
  dedupe_rule: string
  overlap_rule: string
  evidence_required: true
  confidence_required: true
  next_action_required: false
gates:
  - id: string
    pass: string
    warn: string
    fail: string
    blocked: string
model_routing:
  default_tier: T0|T1|T2|T3
  specialist_lanes: []
  multimodel_required_when: []
evidence:
  required_refs: []
  verification_commands: []
lifecycle_policy:
  promote_when: []
  demote_when: []
  cleanup_when: []
  protect_when: []
  superseded_by: null
loop_policy:
  self_advance: true
  max_autonomous_iterations: 3
  stop_only_on:
    - authority_boundary
    - missing_evidence_after_attempt
    - destructive_or_external_side_effect
    - user_preference_conflict
```

## Pitfalls

- Keyword-trigger trap: creating a workflow merely because the user said "workflow".
- Literal-seed trap: storing the user's raw phrase as the full workflow instead of compiling scope, gates, and output contract.
- Over-canonicalization: promoting a candidate directly to global/canonical without route eval and evidence.
- Memory pollution: storing workflow bodies or task progress in memory instead of skills, project SSOT, workflow workspace, or experience-ratchet.
- Model-vote-as-proof: treating multi-model agreement as completion evidence.
- Human-gate overuse: asking the user to decide routine defaults that can be safely inferred and validated locally.
- Human-gate underuse: making external, destructive, credential, publish/deploy, or global-canonical changes without exact authority and readback.

## Verification checklist

- [ ] The decision to create/update a workflow asset is based on reuse/risk/evidence/governability, not keywords.
- [ ] Landing zone was chosen before durable writes.
- [ ] Scope, applies_when, does_not_apply_when, and neighboring workflows are explicit.
- [ ] Output contract includes ordering, dedupe, overlap, evidence, and confidence rules where relevant.
- [ ] Gates define pass/warn/fail/blocked and recovery behavior.
- [ ] Model routing is risk/surface-based and objective evidence remains authoritative.
- [ ] Promotion/demotion/cleanup rules are defined.
- [ ] Positive, negative, neighbor, and forbidden route examples exist before canonical promotion.
