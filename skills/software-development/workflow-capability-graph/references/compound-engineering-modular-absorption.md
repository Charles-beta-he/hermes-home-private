# Compound Engineering Modular Absorption

Scope: absorb Every/AI MBA Compound Engineering as a reusable Hermes capability graph, not as a Claude Code plugin dependency.

Source boundary:
- Every guide: `https://every.to/guides/compound-engineering`
- Plugin repo: `https://github.com/EveryInc/compound-engineering-plugin`
- Practitioner article: `https://ai-mba.io/articles/a-practitioners-guide-to-compound-engineering`
- Treat these as external references. Do not install the plugin, import commands, or assume Claude Code semantics unless a later explicit evaluation task authorizes that path.

Core invariant:

```text
Every substantial engineering task should start from prior project/workflow knowledge, end with verified evidence, and route reusable learning back into the narrowest durable surface that will help the next task.
```

## Intent Router

Use this reference when the user asks to absorb, modularize, implement, or adapt Compound Engineering / 复利工程 / Plan→Work→Review→Compound into Hermes, taskpool, project workflows, or skill systems.

Routes:

1. **Advisory analysis only** — explain concepts and fit; no writes.
2. **Local workflow absorption** — write skills/references/templates/checklists only; no runtime install.
3. **Project-level adoption** — add project docs/checklists/tests in a named repo/project SSOT.
4. **Runtime automation** — only after separate authority; may touch hooks/taskpool/cron/code.

Anti-routes:
- Do not treat a media/video/article as install authorization.
- Do not write global memory for task-local lessons.
- Do not copy all external plugin agents/commands into Hermes one-to-one.
- Do not claim self-improving runtime behavior from docs alone.

## Capability Graph

### CE-0 Source + Scope Pinning

```yaml
id: ce.source_scope_pinning
kind: atomic_module
responsibility: Pin source identity, user intent, target landing zone, and side-effect boundary.
consumes: [user_request, source_urls, target_project_or_skill]
produces: [source_scope_packet]
preconditions: [external_source_read_or_user_provided_evidence]
gates: [source_untrusted_gate, side_effect_authority_gate]
side_effects: none
closure_states: [source_pinned, blocked_missing_source, blocked_authority]
```

### CE-1 Prior Context Intake

```yaml
id: ce.prior_context_intake
kind: atomic_module
responsibility: Gather project/workflow history before planning.
consumes: [project_profile, SSOT, skills, docs/solutions, ADRs, regression_notes, taskpool_cards]
produces: [prior_context_digest]
gates: [freshness_gate, scope_relevance_gate]
side_effects: none
closure_states: [context_ready, context_partial, context_unavailable]
```

Minimum read set by scope:
- Hermes/system change: relevant skill(s), AGENTS.md, SSOT/private review note when present.
- Project code change: project profile, repo instructions, existing docs/solutions/ADRs/tests.
- Public-media absorption: media metadata, external artifact readback, source claim map.

### CE-2 Objective Model Plan

```yaml
id: ce.objective_model_plan
kind: composite_module
responsibility: Convert intent + prior context into a compact executable plan.
consumes: [source_scope_packet, prior_context_digest, user_request]
produces: [plan_packet]
subnodes: [success_criteria, constraints_non_goals, viable_paths, chosen_path, verification_plan]
gates: [objective_model_path_gate]
side_effects: none
closure_states: [plan_ready, plan_needs_user_decision, plan_blocked]
```

Plan packet fields:
```yaml
goal: string
success_criteria: []
constraints: []
non_goals: []
red_lines: []
prior_lessons_used: []
work_slices: []
review_matrix: []
verification_commands_or_observables: []
compound_writeback_candidates: []
```

### CE-3 Work Slice Executor

```yaml
id: ce.work_slice_executor
kind: workflow
responsibility: Execute the smallest safe vertical slice from the plan.
consumes: [plan_packet]
produces: [changed_artifacts, command_log, evidence_refs]
gates: [authority_gate, vertical_slice_gate, rollback_gate]
side_effects: local_write | external_read | external_write_requires_gate
closure_states: [slice_done, slice_failed, slice_blocked, rolled_back]
```

Execution rules:
- Prefer vertical slices that are independently verifiable.
- Keep prototype/runtime/install/deploy/push external side effects closed unless specifically authorized.
- For code, real tests or runtime proof are required before done claims.

### CE-4 Verification Evidence Packet

```yaml
id: ce.verification_evidence_packet
kind: artifact_template
responsibility: Record proof that the work did what the plan required.
consumes: [changed_artifacts, command_log, screenshots, API_readbacks, test_output]
produces: [evidence_packet]
gates: [same_slice_evidence_gate, no_stale_claim_gate]
side_effects: local_write
closure_states: [evidence_sufficient, evidence_partial, evidence_missing]
```

Evidence packet fields:
```yaml
request: string
artifact_refs: []
commands_run: [{cmd: string, exit_code: int, excerpt: string}]
readbacks: []
screenshots_or_media: []
claims_supported: []
claims_not_proven: []
residual_risks: []
```

### CE-5 Review Matrix

```yaml
id: ce.review_matrix
kind: composite_module
responsibility: Review implementation and evidence with risk-specific reviewer roles.
consumes: [plan_packet, changed_artifacts, evidence_packet]
produces: [review_verdict, fix_list, learning_candidates]
subnodes: [regression_reviewer, architecture_reviewer, simplicity_reviewer, domain_reviewer, evidence_reviewer, security_reviewer]
gates: [blocker_gate, severity_calibration_gate]
side_effects: none
closure_states: [pass, pass_with_warnings, fix_required, blocked]
```

Default reviewer roles:
- **Regression reviewer** — feature/field/entrypoint loss, backward compatibility, state-machine drift.
- **Architecture reviewer** — boundary depth, locality, needless seams, hidden coupling.
- **Simplicity reviewer** — overengineering, duplicated logic, needless abstraction.
- **Domain reviewer** — project-specific business semantics and red lines.
- **Evidence reviewer** — whether each completion claim has fresh same-slice proof.
- **Security reviewer** — auth, SQL/XSS/secret/permission or destructive-path risk when relevant.
- **UI reviewer** — only when UI is touched; real screenshot/interaction evidence beats DOM-only proof.

### CE-6 Compound Writeback Router

```yaml
id: ce.compound_writeback_router
kind: gate
responsibility: Decide where each reusable lesson belongs, or reject it.
consumes: [learning_candidates, evidence_packet, review_verdict]
produces: [writeback_actions]
gates: [scope_gate, evidence_gate, anti_ghost_gate]
side_effects: local_write
closure_states: [writeback_done, proposals_only, rejected_as_task_state, blocked]
```

Routing table:

| Candidate type | Landing zone | Gate |
|---|---|---|
| Project-specific constraint | project docs / profile / SSOT | still true across future tasks in that project |
| Cross-project procedure | Hermes skill or reference | reusable, evidence-backed, not task progress |
| One-off status/progress | reject from memory/skill | anti-ghost gate |
| Unproven but promising lesson | experience atom draft / taskpool follow-up | needs independent validation |
| Bug recurrence prevention | regression test / lint / fixture | executable proof preferred |
| Architecture decision | ADR / decision record | rationale + consequences |

Anti-ghost gate:
- Reject PR numbers, issue numbers, commit SHAs, “phase done”, “fixed bug X”, and session-local progress.
- Prefer declarative durable facts or procedural skills over memory.

### CE-7 Next-Loop Hook

```yaml
id: ce.next_loop_hook
kind: adapter
responsibility: Make future plans consume prior writebacks.
consumes: [writeback_actions]
produces: [retrieval_hint_or_checklist]
gates: [retrievability_gate]
side_effects: local_write
closure_states: [hooked, manual_retrieval_only, blocked]
```

Examples:
- Add a checklist line in the project task template: “read docs/solutions before plan.”
- Patch a Hermes skill trigger or reference pattern.
- Add a regression test that future work naturally runs.
- Add a taskpool card field for evidence refs / prior lessons used.

## Stage Contract

```text
Source/scope pin → prior context intake → objective plan → vertical work slice → verification evidence → review matrix → compound writeback → next-loop hook
```

No-skip rules:
- Do not skip prior context intake for project/Hermes changes.
- Do not skip verification before review/closure.
- Do not skip writeback routing after complex tasks; explicit “no durable lesson” is acceptable.
- Do not promote a lesson globally from one weak example.

## Minimal Adoption Template

For a concrete task, attach this footer to the plan or task card:

```yaml
compound_engineering:
  prior_context_read:
    - skill_or_doc: ...
      relevance: ...
  work_slice: ...
  verification:
    - command_or_observable: ...
  review_matrix:
    - reviewer: regression
      required: true
    - reviewer: evidence
      required: true
    - reviewer: architecture
      required: auto_if_code_or_workflow
  writeback_candidates:
    - candidate: ...
      proposed_landing: project_doc|skill|test|taskpool|reject
      evidence_ref: ...
```

## Taskpool Card Shape

When converting Compound Engineering into taskpool items, prefer one vertical card per safe slice:

```yaml
title: "[CE] <vertical outcome>"
objective: "Make the next task easier by delivering <artifact> with evidence and writeback."
acceptance_criteria:
  - prior_context_digest exists or not-applicable is justified
  - plan_packet lists constraints/non-goals/red lines
  - changed artifact has direct verification evidence
  - review matrix pass/warn/fail recorded
  - compound writeback router outcome recorded
red_lines:
  - no external install/import/deploy/push without separate authority
  - no global memory for task-local progress
  - no unsupported self-improvement claims
verification:
  - exact command/readback/screenshot path
writeback_target: project_doc|skill_reference|test|proposal_atom|none
```

## Done Definition

A Compound Engineering absorption slice is done only when:

1. The target landing zone is explicit.
2. At least one local reusable artifact exists, or the slice explicitly closed as advisory-only.
3. The artifact was read back/validated.
4. Remaining unproven claims are listed.
5. The next loop knows where to retrieve the lesson.

## Common Pitfalls

1. **Plugin cargo culting** — copying `/workflows:*` commands without translating the underlying capability.
2. **Documentation graveyard** — writing long lessons that no future plan reads.
3. **Review theater** — many reviewers with no severity boundary or evidence anchor.
4. **Global pollution** — turning one project-specific lesson into a global skill/memory rule.
5. **No next-loop hook** — compound notes exist but future plans never consume them.
6. **Overplanning tiny tasks** — use a lightweight version for small safe changes.
7. **Completion overclaim** — docs/skill absorption does not prove runtime automation.

## Lightweight Mode

For low-risk tasks, compress the loop:

```text
Prior context? → 3-bullet plan → do slice → run proof → 2-line review → writeback yes/no
```

Use full mode for Hermes self-changes, production code, high-risk UI/finance/auth flows, taskpool/control-plane work, or user requests like “全盘推进/落地吸收”.
