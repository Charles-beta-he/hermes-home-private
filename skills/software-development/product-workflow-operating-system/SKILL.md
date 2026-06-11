---
name: product-workflow-operating-system
description: Use when turning a product idea, market signal, source artifact, PRD request, AI-generated codebase, launch plan, or post-launch signal into a full evidence-gated product workflow from intake through discovery, strategy, PRD, execution, shipping, launch, measurement, and ratchet writeback.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [product-management, workflow, evidence, prd, launch, shipping]
    related_skills: [goal-calibration, project-evidence-grounding, taskpool-control-plane, development-closure-consensus, workflow-ecosystem-audit, browser-harness-integration]
---

# Product Workflow Operating System

Scope: reusable domain-level workflow for product management and product-engineering delivery in Hermes. It governs how product ideas, opportunity signals, PRDs, launches, metrics, and AI-built software move through evidence-gated stages.

Applicability: use for product/workflow tasks that need more than a standalone answer: artifact creation, task candidates, implementation readiness, shipping packets, launch planning, or post-launch learning.

Anti-condition: do not use this skill to encode one repository's local names, social-post claims, temporary project facts, or current-task progress as global truth. Source-specific facts belong in scoped reference notes or project SSOT artifacts.

## Overview

This skill is the Hermes-local product workflow operating system. It adapts the transferable structure of external skill/workflow marketplaces — skills as concepts, workflows as verbs, and plugins as domains — into Hermes' evidence-first, taskpool-aware delivery model.

The goal is not to copy any external marketplace. The goal is to make product work executable and auditable: every stage has an input contract, artifact, evidence gate, next-state decision, and handoff boundary.

## When to Use

Use this skill when the user asks to:

- analyze whether a product/business/opportunity is worth pursuing;
- turn a link, video, source artifact, article, marketplace item, or market signal into a product workflow;
- write or red-team a PRD and then turn it into engineering tasks;
- create a launch/GTM/growth/metrics plan that must connect to evidence and execution;
- assess AI-generated or vibe-coded software before shipping;
- build a full product workflow rather than a standalone document.

Don't use for:

- pure code changes with an already-fixed spec — use development closure / project-specific delivery skills;
- generic research summaries with no product decision or workflow output;
- legal/compliance documents where a specialist/legal review is required;
- taskpool operations alone — use `taskpool-control-plane`.

## Objective Gate

Before advancing, define:

- **Success**: what decision or executable state should exist at the end?
- **Hard constraints**: no mock-as-acceptance, no stale memory writes, no external publishing/payment/credential entry without explicit authorization.
- **Evidence source of truth**: live page/repo/API/docs, project profile, PRD, prototype, production UI/API, metrics/logs.
- **Completion boundary**: document-only, taskpool candidate, implementation-ready, shipping packet, or launched/observed.

If the user says “全盘落地 / 全盘推进”, default to the full chain until a permission, evidence, credential, external side-effect, or product-choice boundary is reached. Do not stop at a plan if a safe local artifact or verification step remains possible.

## 12-Stage Lifecycle

Each stage has a gate. Do not skip gates just because the output can be generated fluently.

1. **Intake / Target Model**
   - Inputs: idea/link/source/request/problem.
   - Output: `intent-card.md` with objective, user, scenario, non-goals, success criteria, authority boundary.
   - Gate: ambiguity that changes path, permission, architecture, or acceptance is resolved or explicitly assumed.

2. **Opportunity Discovery**
   - Output: opportunity map, risky assumptions, experiment backlog.
   - Gate: at least one user/problem hypothesis plus testable assumption exists.

3. **Market / User / Competitor Evidence**
   - Output: evidence bundle with source type, URL/path, freshness, claim linkage, confidence.
   - Gate: claims are separated into evidenced facts, assumptions, and model interpretation.

4. **Product Strategy**
   - Output: strategy canvas, value proposition, business/pricing hypothesis.
   - Gate: target segment, alternatives, differentiation, and stop conditions are explicit.

5. **Metrics Contract**
   - Output: north-star, input metrics, health/guardrail metrics, event/data contract.
   - Gate: at least one metric can be read back from a named system or is labeled as missing instrumentation.

6. **PRD / Spec**
   - Output: PRD with UI behavior, API contract, state machine, permissions, data model, error states, non-goals, acceptance criteria.
   - Gate: acceptance is observable; “looks good” alone is insufficient.

7. **Red-team / Pre-mortem / Risk Register**
   - Output: kill assumptions, risk register, mitigation plan, stakeholder/communication notes where relevant.
   - Gate: high-risk items have detection and rollback/mitigation.

8. **Planning / Taskpool / Backlog**
   - Output: stories, test scenarios, dependency order, task candidates.
   - Gate: task candidates include objective, acceptance evidence, anti-drift check, parallel boundary, priority, and project.

9. **Build / Real Verification**
   - Output: implementation diff, tests, build, API/browser evidence.
   - Gate: no mock-only acceptance unless explicitly allowed by the user and labeled.

10. **AI-Code Shipping Check**
   - Output: app documentation, derived test coverage map, static security/performance audit, shipping packet.
   - Gate: intent-vs-implementation gaps are either fixed, blocked, or explicitly accepted by a human.

11. **Launch / GTM / Growth**
   - Output: launch plan, ICP/beachhead, messaging, growth loop, battlecard if relevant.
   - Gate: launch state is machine-readable (`ready`, `blocked`, `launched`, `rollback`, `observing`) and linked to smoke/readback evidence.

12. **Measure / Retro / Ratchet**
   - Output: post-launch readback, decision (`ship`, `iterate`, `rollback`, `stop`), retro, skill/workflow/taskpool follow-up.
   - Gate: learning is classified into the right boundary: memory, skill, project SSOT, taskpool candidate, or do-not-save.

## Default Chains

### Chain A — Opportunity Analysis

Use for links, videos, repositories, marketplace items, business ideas, market signals.

```text
Intake → Evidence → User/Competitor/Market → Strategy sketch → Assumption priority → Experiments → Taskpool candidate decision
```

Required artifacts:

- `intent-card.md`
- `evidence-bundle.json`
- `opportunity-analysis.md`
- optional `task-candidates.json`

### Chain B — PRD to Engineering

Use when a concept should become work items or code.

```text
Strategy/Opportunity → PRD → Red-team → Stories → Test Scenarios → Governed task candidates → Implementation-ready packet
```

Required artifacts:

- `prd.md`
- `risk-register.md`
- `stories-and-tests.md`
- `task-candidates.json`

### Chain C — AI Code Shipping

Use for AI-generated code, vibe-coded apps, or fast prototypes that need delivery confidence.

```text
Repo/app intake → Document app → Derive tests → Static security audit → Static performance audit → Build/test/browser/API verification → Shipping packet
```

Required artifacts:

- `system-docs.md`
- `test-coverage-map.md`
- `security-audit.md`
- `performance-audit.md`
- `shipping-packet.md`

## Evidence Bundle Rules

Use `templates/evidence-bundle.json` as the minimum shape. Each claim should be linked to evidence:

- `source_type`: official_doc, repo, live_ui, api, transcript, screenshot, metric, log, model_inference, user_statement.
- `source_ref`: URL/path/command/screenshot path.
- `claim`: the exact claim supported.
- `freshness`: timestamp or date.
- `confidence`: high, medium, low.
- `verification_status`: verified, degraded, blocked, assumption.

Model interpretation is allowed, but must not masquerade as evidence.

## Workflow State Rules

Use `templates/workflow-state.yaml.md` for stage tracking. Valid states:

- `not_started`
- `in_progress`
- `blocked`
- `ready_for_review`
- `accepted`
- `rejected`
- `superseded`

Each state transition should name stage, artifact path, evidence path, blocker/next action, and authority boundary if human intervention is required.

## Taskpool Candidate Rules

Use `templates/task-candidates.json` for governed intake. Fail closed if a candidate lacks:

- `dedupe_key`
- `title`
- `priority`
- `project`
- `objective`
- `acceptance_evidence`
- `anti_drift_check`
- `parallel_boundary`
- `evidence_bundle`
- `dependency_order`

Ordinary news, broad market trends, or low-confidence product ideas should not become tasks. Convert only directly actionable, evidence-backed work.

## Scaffold Script

Reference: `references/landing-and-commit-pitfalls.md` is a scoped packaging note for this workflow class. Scope: product-workflow skill/workspace landing. Applicability: use when committing templates, helper scripts, or scaffolded workflow workspaces. Anti-condition: do not apply it as a general repository rule outside this workflow class.

Use the helper script when a request needs a durable workspace:

```bash
python3 ~/.hermes/skills/software-development/product-workflow-operating-system/scripts/init_product_workflow.py \
  --slug my-product-idea \
  --title "My Product Idea" \
  --chain opportunity-analysis
```

Default output root: `~/.hermes/workflows/product/<slug>/`.

The script creates the SSOT skeleton, evidence bundle, workflow state, decision log, and task candidate file. It does not contact external services and does not enqueue taskpool items.

## Taskpool Ingest Bridge

Reference: `references/taskpool-ingest-bridge.md` documents the governed bridge from product workflow workspaces into the canonical taskpool ingest path. Scope: product-workflow workspace candidates only. Applicability: use when `tasks/task-candidates.json` has deliberate, evidence-backed candidates. Anti-condition: do not ingest placeholder candidates, broad trend summaries, or unverified social-post claims.

Reference: `references/execution-flow-alignment.md` maps product workflow stages and candidate fields to taskpool's unified execution-flow gate. Use it when product workflow candidates will later be dispatched, claimed, reviewed, or closed out; carry `workflow_stage`, completion boundary, harness surfaces, external-side-effect intent, and structured proof expectations through the canonical taskpool add path.

Reference: `references/safe-taskpool-smoke-verification.md` captures the safe verification pattern for product-workflow → taskpool → execution-flow smoke tests. Use file-backed JSON parsing instead of shell pipes into `python3 -c`; safety scanning may correctly block pipe-to-interpreter shapes even when the data is local JSON.

Dry-run:

```bash
python3 ~/.hermes/scripts/product_workflow_taskpool_ingest.py --slug my-product-idea --json
```

Write only when taskpool mutation is intended:

```bash
python3 ~/.hermes/scripts/product_workflow_taskpool_ingest.py --slug my-product-idea --write --json
```

## Positive / Neighbor / Forbidden Routing Examples

Positive loads:

- “分析这个视频里的开源项目，补成完整产品工作流。”
- “把这个商机从用户、竞品、变现、风险到实验全链路落地。”
- “这份 PRD 帮我红队后转成研发任务和验收标准。”
- “AI 写的这个 repo 能不能 ship，补完整验收链。”

Neighbor loads:

- Pure implementation with known acceptance → `development-closure-consensus` / project skills.
- Browser-only UI verification → `browser-harness-integration`.
- Taskpool stalled/no running diagnosis → `taskpool-control-plane`.
- General research digest with no product decision → `research`.

Forbidden loads:

- “帮我润色这段话。”
- “算一下收入同比。”
- “直接修这个 TypeScript 报错。”
- “发送这条消息。”

## Common Pitfalls

1. **Document-as-completion trap**: a PRD, strategy, or launch plan is not complete unless the requested boundary was document-only. For execution requests, continue to tasks, verification, or a human gate.
2. **Evidence laundering**: do not turn model guesses, social-post hype, or README claims into facts without direct source verification.
3. **Workflow over-expansion**: if the user only wants opportunity analysis, do not invent launch or implementation artifacts. Stop at the agreed boundary.
4. **Taskpool pollution**: do not enqueue broad “study this trend” tasks. Candidates need acceptance evidence and an anti-drift check.
5. **Mock acceptance**: prototypes and mock data can support design discussion, but do not satisfy real implementation acceptance unless explicitly allowed.
6. **Memory pollution**: do not save one-off product decisions as durable memory; use project SSOT, task records, or skills for reusable procedures.

## Verification Checklist

- [ ] Objective, non-goals, and completion boundary are explicit.
- [ ] Evidence bundle separates facts, assumptions, and interpretations.
- [ ] Current stage and next stage are machine-readable in workflow state.
- [ ] Any taskpool candidate includes objective, acceptance evidence, anti-drift, dependency order, and parallel boundary.
- [ ] If implementation/shipping was requested, real tests/build/API/browser evidence is attached or blocker is reported.
- [ ] Learning writeback is classified into memory / skill / project SSOT / taskpool / no-write.
