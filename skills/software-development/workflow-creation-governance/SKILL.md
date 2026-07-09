---
name: workflow-creation-governance
description: Use when deciding whether a fuzzy user request, repeated behavior, correction, or process preference should become a governed workflow asset. Applies judgment-driven assetization, lifecycle gates, evidence requirements, and loop engineering; do not load merely because the user says workflow unless reuse/risk/evidence/governance signals justify it.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
      - workflow
      - governance
      - lifecycle
      - loop-engineering
      - evidence-gates
    related_skills:
      - workflow-capability-graph
      - objective-model-path-verification
      - hermes-experience-ratchet
      - incremental-implementation
---

# Workflow Creation Governance

## Overview

This skill governs whether a user seed should become a durable workflow asset. The core rule is judgment-driven assetization, not keyword triggering. A phrase like “创建工作流”, “以后这样”, “自动”, or “长期稳定” is a signal; it is not sufficient authority to write durable assets, alter routing, enable automation, or create global behavior.

Use Workflow Kernel Loop Engineering: Observe → Orient → Compile → Simulate → Execute → Verify → Ratchet → Monitor → Cleanup. Safe local/reversible/evidence-producing steps should advance without excessive questions. External side effects, global canonicalization, taskpool/cron/AgentOS mutation, publish/deploy/push, destructive operations, credentials, and production writes remain exact-authority gates.

## When to Use

Use when:
- The user asks to create, improve, stabilize, govern, or automate a workflow.
- The user gives a recurring process preference or correction that may reduce future steering.
- A request has high reuse value, multi-step complexity, evidence requirements, route collisions, or long-term governance needs.
- You are deciding between no write, session plan, output template fragment, project SSOT, workflow workspace, skill/reference, experience-ratchet proposal, taskpool candidate, cron, or AgentOS.

Do not use for:
- Simple one-off answers or commands.
- Temporary task progress.
- Workflow keyword alone with weak reuse/risk/evidence signals.
- Direct external dispatch or automation enablement without exact authority and readback.

## Assetization Decision Gate

Before any durable write, score the seed on:

1. Reuse value — likely repetition, stable input/output/verification, future steering saved.
2. Complexity — multiple stages, context lookup, routing, evidence, or verification gates.
3. Risk surface — memory, skills, project profiles, taskpool, cron, AgentOS, external systems, production, or user-visible state.
4. Evidence gap — completion cannot be trusted from model output alone.
5. Long-termity — durable preference, repeated pattern, strategic workflow, or automation candidate.
6. Governability — can define applies_when, does_not_apply_when, inputs, outputs, gates, fallback, cleanup, and promotion/demotion rules.
7. Routing collision risk — overlaps neighboring skills/workflows or may false-trigger from broad wording.
8. Cleanup cost — could create stale asset sprawl if not bounded.

Decision bands:
- `no_asset`: answer/execute normally; no durable workflow write.
- `session_plan`: temporary plan only.
- `output_template_fragment`: reusable format or output contract only.
- `project_scoped_candidate`: project SSOT/workspace candidate.
- `reusable_candidate`: workflow workspace + route eval cases.
- `canonicalization_path`: never direct; requires validated/common history, regression evidence, rollback, and advisory review when risk warrants.

## Required WorkflowAsset Shape

A candidate asset must include:
- source seed and refs;
- classification: type, scope, maturity, retention;
- intent model: goal, success criteria, non-goals, assumptions, ask-user-only-when;
- routing: applies_when, does_not_apply_when, neighbor workflows, forbidden triggers, positive/negative examples;
- output contract: format, ordering, dedupe, overlap, evidence/confidence/next-action requirements;
- gates: pass/warn/fail/blocked outcomes and recovery behavior;
- model routing: default tier, specialist lanes, multi-model-required conditions;
- evidence: required refs and verification commands;
- lifecycle policy: promote/demote/cleanup/protect/superseded_by;
- loop policy: self-advance rules and exact stop boundaries.

Use the local helper when available:

```bash
python3 ~/.hermes/scripts/workflow_asset_decision.py decide --seed '<seed>' --observed-repetition 2
python3 ~/.hermes/scripts/workflow_asset_decision.py compile --seed '<seed>' --observed-repetition 2
python3 ~/.hermes/scripts/workflow_asset_decision.py scaffold --seed '<seed>' --observed-repetition 2
python3 ~/.hermes/scripts/workflow_asset_decision.py validate --asset ~/.hermes/workflows/assets/<id>/workflow.json
```

## Lifecycle

Maturity:

```text
seed -> draft -> candidate -> validated -> common -> canonical
                      \-> quarantine/deprecated/archived/revoked
```

Retention:

```text
session_only | project_scoped | domain_reusable | global_reusable | pinned | cleanable | quarantine
```

Promotion requires evidence. Canonical promotion requires route regression, negative/neighbor examples, rollback/migration plan, and usually independent/multi-model advisory. Model agreement is advisory only.

## Landing-zone Rules

- One-off task/session plan → no durable workflow write.
- Stable user preference/red line → compact memory/user profile only; never store workflow body in memory.
- Reusable checklist/procedure/pitfall → skill or skill reference.
- Project-specific convention → project SSOT/profile/reference.
- Concrete future work → taskpool candidate/proposal.
- Promising but not validated pattern → experience-ratchet proposal.
- Automation → cron/taskpool/AgentOS only with exact target, rollback/readback, and side-effect evidence gates.
- Mixed conclusion → split landing zones.

## Loop Engineering Procedure

1. Observe — capture seed, corrections, repeated patterns, failures, usage signals.
2. Orient — retrieve similar skills/workflows/project profiles/history/taskpool before creating new assets.
3. Compile — generate or patch a WorkflowAsset draft.
4. Simulate — run positive, negative, neighbor, and forbidden route evals.
5. Execute — advance only safe local/reversible/verifiable steps by default.
6. Verify — read back files, schemas, tests, dry-runs, logs, screenshots, API outputs, or other objective evidence.
7. Ratchet — promote, demote, quarantine, or emit an experience-ratchet proposal.
8. Monitor — track reuse, false triggers, evidence gaps, authority blocks, cleanup candidates.
9. Cleanup — deprecate/archive/revoke with redirects and evidence, not silent deletion.

## Common Pitfalls

1. Keyword hard-trigger: treating “workflow” vocabulary as sufficient cause.
2. Seed literalism: saving the raw user phrase instead of compiling scope, gates, output, and negative cases.
3. Canonical leap: promoting a seed or one successful run directly to canonical.
4. Memory pollution: writing workflow bodies or task progress into always-on memory.
5. Consensus laundering: treating multi-model agreement as truth or completion evidence.
6. Missing negative/neighbor evals: route regressions remain hidden.
7. Over-questioning: asking the user to choose routine defaults that can be safely inferred and locally verified.
8. Under-gating: external/destructive/global side effects without exact authority, rollback, and readback.

## Verification Checklist

- [ ] Decision is based on reuse/risk/evidence/governability, not keyword presence.
- [ ] Landing zone is selected before durable writes.
- [ ] Scope, applies_when, does_not_apply_when, neighbor workflows, and forbidden triggers are explicit.
- [ ] Output contract covers ordering, dedupe, overlap, evidence, confidence, and next action where relevant.
- [ ] Gates define pass/warn/fail/blocked and safe recovery behavior.
- [ ] Model routing is risk-based and objective evidence remains authoritative.
- [ ] Promotion, demotion, cleanup, and supersession policies exist.
- [ ] Positive, negative, neighbor, and forbidden route examples exist before canonical promotion.
- [ ] Any scaffold/readback used local files only unless exact authority was granted.
