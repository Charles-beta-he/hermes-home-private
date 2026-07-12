# Workflow Asset Loop Engineering

Scope: use when a user gives a vague process preference, asks to improve workflow behavior, or repeated sessions reveal a reusable workflow pattern. The goal is to decide whether to create or update a governed workflow asset, not to hard-trigger on words like “创建工作流”.

Applicability:
- The request may become a reusable workflow, output contract, gate, template, project SSOT note, skill reference, taskpool candidate, or no durable write.
- The user expects low-friction self-advancement: Hermes should infer safe defaults and continue through local/reversible/evidence-producing steps without excessive questions.
- The workflow may need long-term lifecycle governance, multi-model advisory review, and cleanup/retention policy.

Anti-conditions:
- Do not create a workflow asset only because the user used workflow vocabulary.
- Do not promote a seed directly to canonical.
- Do not treat model consensus as truth or completion evidence.
- Do not put workflow bodies into always-on memory; memory may store only stable compact user preferences or red lines.
- Do not open external dispatch, publish/deploy/push, destructive operations, production writes, payments, or credential entry without exact target, rollback, and readback.

## Decision principle

User wording is a signal, not authority. Ask:

```text
Does this deserve becoming a governed workflow asset?
```

Score the seed on:
- reuse_value: likely future repetition and user explanation saved;
- multi_step_complexity: needs staged context/evidence/output/gates;
- evidence_gap: completion cannot be trusted without readback/test/source proof;
- risk_surface: affects memory, skill, profile, taskpool, cron, AgentOS, external systems, or user-visible state;
- authority_boundary: any side-effect or irreversible boundary;
- longevity_signal: durable preference, repeated pattern, or strategic workflow;
- output_contract_need: table/report/PRD/JSON/message shape requires sorting, dedupe, overlap, evidence, confidence, next-action rules;
- routing_collision_risk: overlaps neighboring workflows or may false-trigger;
- cleanup_cost: likely sprawl or stale asset burden.

Decision bands:
- no_asset: answer/execute normally.
- session_plan: temporary plan only.
- output_template_fragment: reusable formatting/output contract only.
- project_scoped_candidate: project SSOT or project workflow workspace.
- reusable_candidate: workflow workspace + eval cases.
- canonicalization_path: never direct; requires validated/common history, route regression, objective evidence, rollback, and usually multi-model advisory.

## WorkflowAsset lifecycle

Maturity states:

```text
seed -> draft -> candidate -> validated -> common -> canonical
                      \-> quarantine/deprecated/archived/revoked
```

Retention classes:

```text
session_only | project_scoped | domain_reusable | global_reusable | pinned | cleanable | quarantine
```

Promotion gates:
- seed -> draft: assetization score justifies compilation.
- draft -> candidate: scope, applies/does_not_apply, output contract, gates, and eval cases exist.
- candidate -> validated: real rollout or dry-run evidence passes.
- validated -> common: repeated use, low false-trigger rate, neighbor/negative examples pass.
- common -> canonical: evidence-backed regression, rollback/migration plan, and advisory review when risk warrants.

Demotion/cleanup gates:
- false triggers, user correction, stale sources, no usage, superseded-by relation, validation failure, missing evidence, excessive sprawl, or side-effect ambiguity.
- Before deletion, check references from skills, templates, project profiles, cron, taskpool, AgentOS, and workflow workspaces.

## Loop engineering procedure

1. Observe — capture the user seed, corrections, repeated patterns, rollout results, failures, and usage signals.
2. Orient — retrieve similar skills/workflows/project profiles/history; classify scope and risk.
3. Compile — generate or patch a WorkflowAsset draft with lifecycle, retention, output contract, gates, and routing examples.
4. Simulate — run positive, negative, and neighbor route evals; check output contract requirements.
5. Execute — advance only safe local/reversible/verifiable steps by default.
6. Verify — read back files, schemas, tests, screenshots, API/logs, taskpool dry-runs, or other objective evidence.
7. Ratchet — promote, demote, quarantine, or emit an experience-ratchet proposal.
8. Monitor — track reuse, false triggers, evidence gaps, authority blocks, and cleanup candidates.
9. Cleanup — deprecate/archive/revoke with redirects and evidence, not silent deletion.

Stop only at concrete boundaries: exact authority needed, missing evidence after attempted retrieval, destructive/external side effect, production/credential/payment boundary, or unresolved user preference conflict.

## Landing-zone classifier

- `no_write`: one-off answer/task.
- `session_plan`: temporary execution plan.
- `output_template_fragment`: reusable format, table/report shape, ordering/dedupe/overlap/evidence rule.
- `project_ssot`: project-specific workflow or decision.
- `workflow_workspace`: seed/draft/candidate/validated asset under scoped workflow assets.
- `skill_reference` or `template`: reusable validated/common procedure.
- `experience_ratchet`: promising pattern not yet safe to formalize.
- `taskpool_candidate`: concrete future engineering or validation work.
- `cron` / `AgentOS`: automation only with exact side-effect gates.
- `memory` / `user_profile`: stable compact preference/red line only; not the workflow body.

Mixed conclusions must be split across landing zones.

## Multi-model routing

Use multi-model review as an advisory gate, not as proof.

- T0: ephemeral/session work — single model plus tool/readback if useful.
- T1: candidate workflow — main model + self-check/eval examples.
- T2: validated/common promotion — independent reviewer or multi-model advisory.
- T3: canonical/global/automation/side-effect surfaces — multi-model/adversarial review + objective evidence + rollback/readback.

Surface specialists:
- visual/UI -> visual reviewer plus screenshot/browser evidence;
- architecture/lifecycle -> architecture reviewer;
- implementation -> code/test reviewer;
- policy/authority -> safety reviewer;
- completion/evidence -> verifier;
- red-team -> adversarial reviewer.

If quorum or evidence is missing, report `degraded_not_certified` or `advisory_only`; do not claim full certification.

## Output contract checklist

For any workflow that produces artifacts, define:
- format: table, list, report, JSON, PRD, task candidates, message, mixed;
- audience/surface: terminal, Telegram, docs, UI, dashboard, repo;
- one artifact or multiple;
- row/section dimensions;
- ordering rule;
- dedupe rule;
- overlap handling;
- evidence and confidence fields;
- next-action requirement;
- negative cases and forbidden outputs.

## Metrics

Track:
- assetization_precision;
- false_asset_rate;
- false_trigger_rate;
- reuse_count;
- time_to_validated;
- human_intervention_rate;
- evidence_gap_closure_rate;
- blocked_by_authority_count;
- cleanup_success_count;
- canonical_regression_count.

Guardrails must keep these at zero:
- external_side_effect_without_authority;
- canonical_without_validation;
- model_consensus_as_truth;
- workflow_body_written_to_memory.

## Engineering foundations

This pattern is grounded in:
- PDCA/PDSA and Deming quality loops: workflows improve through plan/do/check/act, not one-shot docs.
- OODA: observe/orient before deciding and acting; wording is only signal.
- Argyris/Schön double-loop learning: update governing assumptions and gates after failures.
- Workflow Patterns / BPM: workflows require state, control flow, exception paths, resources, and transitions.
- Continuous Delivery / DORA / Accelerate: small batches, fast feedback, automation, and measurable reliability.
- SRE: observability, toil reduction, error budgets, and fail-closed automation.
- Team Topologies: split roles and reduce cognitive load; avoid one giant workflow brain.
- Deep modules: expose a simple WorkflowAsset interface over complex compilation/routing/verification internals.
- Enterprise Integration Patterns: routing, filtering, transformation, idempotency, and message history.
- ReAct/Reflexion/SkillOpt: rollout/reflection/update/gate loops for improving externalized agent skills.

## Pitfalls

- Keyword hard-trigger: user saying “workflow” is signal, not sufficient cause.
- Asset sprawl: creating durable assets without retention and cleanup.
- Canonical leap: seed or one successful run promoted directly to canonical.
- Consensus laundering: model agreement treated as truth.
- Missing negative/neighbor evals: route regressions hidden until later.
- Output underspecification: “make a table” without sort/dedupe/overlap/evidence/next-action rules.
- Over-questioning: ask only when ambiguity changes durable architecture, authority, or preference outcome.
- Blocked-as-stop: if safe local/reversible evidence work remains, continue; stop only at real gates.
