# Compound Agent Loop taskpool mapping

Scope: map compound/self-improving agent loop contracts into canonical taskpool cards without opening runtime, worker, scheduler, external dispatch, deploy, credential, or destructive gates.

Applicability: use when a social/source/research signal or workflow idea should become a governed taskpool candidate, or when a task needs maker/verifier/writeback structure before dispatch.

Anti-conditions: do not use this as authority to execute a worker, create cron jobs, send messages, install external repos, mutate production, or force-close lifecycle gates. Adding a card is tracking/intake, not delivery.

## Core mapping

```text
compound_agent_loop.source                    -> evidence_refs + source_boundary note + claims_not_proven
compound_agent_loop.objective.goal             -> objective / mission_objective
success_criteria                               -> acceptance_criteria
measurable_objective.metric                    -> acceptance metric / measurable objective
measurable_objective.benchmark + comparator    -> baseline/comparator evidence requirement
constraints / non_goals / red_lines            -> mission_constraints / non_goals / red_lines
loop_roles.inner_loop_responsibility           -> bounded execution responsibility in body
loop_roles.outer_loop_responsibility           -> mechanism/search-strategy responsibility in body
budget                                         -> required_authority + stop conditions in body
context_read                                   -> prior_context_read checklist in body
context_read.meta_loop_input_boundary          -> allowed code/trace/log/ledger observation surface
workspace                                      -> workspace + parallel_boundary + rollback note
maker                                          -> executor role / harness_surfaces / required_artifacts
verifier                                       -> validation matrix + completion_gate
outer_loop.outer_loop_change_surface           -> declared mechanism/search-strategy change surface
outer_loop.no_authority_expansion              -> no-authority-expansion boundary in permission gates
required evidence                              -> acceptance_evidence + proof requirements
writeback candidates                           -> compound_writeback section
authority_gates                                -> permission_gates / required_authority / red_lines
closure                                        -> proof log + final handoff fields
```

## Recommended card fields

Use these fields in addition to ordinary task metadata:

```yaml
lane: evolution | advisory | work
architecture_target: taskpool
workflow_stage: evidence | execute | review | writeback | human_gate | done
completion_boundary: taskpool_candidate | implementation_ready | shipping_packet
harness_surfaces:
  - brain_task_orchestrator
  - evidence_ledger
  - verifier_readback
required_artifacts:
  - source-verification-matrix.md
  - verifier-verdict.md
  - writeback-router-decision.md
measurable_objective:
  metric: ""
  benchmark: ""
  comparator: ""
loop_roles:
  inner_loop_responsibility: ""
  outer_loop_responsibility: ""
outer_loop_change_surface: "none | prompt_strategy | skill_reference | workflow | evaluator | search_policy | script_patch | memory_schema_proposal"
meta_loop_input_boundary:
  allowed: [code, traces, logs, benchmark_outputs, experiment_ledger]
  disallowed: [arbitrary_private_context, credentials, unrelated_runtime_state]
claims_not_proven: []
anti_drift_check: >
  Do not treat source claims or executor summaries as proof; preserve maker/verifier separation,
  authority gates, scoped writeback ownership, explicit comparator requirements, and outer-loop
  mechanism-change boundaries.
acceptance_evidence: >
  artifact:/... plus command:/proof:/url:/file: refs that support each acceptance item, including
  benchmark/comparator readback for any claimed meta-loop improvement.
parallel_boundary: >
  State which subtasks may run independently and which files/workspaces must be isolated.
no_authority_expansion: >
  Mechanism/search-strategy changes must not widen scheduler/worker/lifecycle authority,
  external dispatch, publish/deploy, destructive actions, or credential/secret access.
```

## Body checklist

Add a `Compound Agent Loop` section to the task body when the task is likely to dispatch agents:

```markdown
## Compound Agent Loop

### Prior context read
- [ ] Project profile / SSOT:
- [ ] Relevant skills:
- [ ] Existing task/project overlap search:
- [ ] Source claims separated from verified facts:
- [ ] Claims not proven listed:

### Objective and comparator
- [ ] Measurable objective / success metric:
- [ ] Benchmark, fixed scenario, or task suite:
- [ ] Comparator / baseline / inner-loop-only reference:
- [ ] Stop condition tied to verifier evidence, not executor confidence:

### Loop responsibilities
- [ ] Inner-loop responsibility: bounded task attempts inside a fixed objective/evaluator
- [ ] Outer-loop responsibility: mechanism/search-strategy change, not ordinary retry
- [ ] Parameter/prompt/config retuning is not called outer-loop improvement unless exploration behavior changes

### Maker contract
- Role:
- Allowed tools:
- Workspace / rollback:
- Required outputs:

### Verifier contract
- Verifier independence:
- Rubric:
- Evidence-only inputs:
- Pass/warn/fail/blocked outcomes:

### Meta-loop observation boundary
- [ ] Allowed trace/code/log/benchmark/experiment-ledger inputs:
- [ ] Disallowed arbitrary context/private state/credential inputs:

### Outer-loop mechanism-change boundary
- [ ] Declared outer_loop_change_surface:
- [ ] Declared mechanism/search-strategy change surface:
- [ ] Exploration/diversification delta vs repeated retry:
- [ ] Injected mechanism claims_not_proven listed:
- [ ] No authority expansion from mechanism carrier to permissions/lifecycle/scheduler/dispatch/publish/destructive/secrets:

### Evidence requirements
- [ ] command:
- [ ] artifact:
- [ ] screenshot/browser/API/log if applicable:
- [ ] claims_not_proven listed:

### Writeback router
- [ ] Project fact -> project SSOT/profile
- [ ] Reusable procedure -> skill/reference
- [ ] Task progress -> proof log/session only, not memory
- [ ] Unverified social/source claim -> evidence note or follow-up, not durable rule
- [ ] Mechanism discovery -> proposal/reference/experience_atom, not direct runtime mutation

### Authority boundaries
- [ ] No external dispatch/send/publish/deploy
- [ ] No credentials/secrets/payment/destructive operations
- [ ] No scheduler/worker/lifecycle mutation unless exact authority/readback exists
```

## Intake decision matrix

For each source/lesson:

| Decision | Meaning | Next step |
|---|---|---|
| adopt | verified, reusable, safe local landing exists | create/patch skill/reference/template or local artifact |
| recertify | prior coverage exists or evidence is stale | create bounded recertification/delta task |
| reject | false, low-value, unsafe, or non-transferable | record reason; no task |
| child-task | verified actionable work remains | create child with explicit acceptance/evidence/gates |
| blocked | source inaccessible or authority missing | record exact missing evidence/authority |

## Done definition

A compound-loop taskpool intake is done only when:

1. Source boundary and verification status are explicit.
2. Acceptance criteria are independently checkable.
3. Maker and verifier responsibilities are separated or deterministic evidence justifies self-review.
4. Measurable objective, benchmark/comparator, and verifier boundary exist before any compound/bilevel improvement claim.
5. Inner-loop execution responsibility is distinct from outer-loop mechanism/search-strategy change responsibility.
6. Meta-loop inputs are bounded to declared code, traces, logs, benchmark outputs, or experiment ledgers.
7. Outer-loop injections preserve no-authority-expansion: mechanism carriers do not widen permissions, lifecycle, scheduler, dispatch, publish/deploy, destructive operations, or secret access.
8. Writeback target is selected or rejected by anti-ghost gate.
9. Remaining work is either represented as verified child tasks or stopped at concrete authority/evidence boundaries.
