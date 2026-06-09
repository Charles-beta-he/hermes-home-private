---
name: development-closure-consensus
description: Use when a software task is handed over for closure checking, full-cycle delivery, or "全盘推进/收口"; first resolve the project profile, then compile a project-specific development closure consensus before implementation, verification, commit, PR, or learning writeback.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - software-development
    - closure
    - project-profile
    - delivery
    - verification
    - workflow
    related_skills:
    - project-profile-maintenance
    - github-pr-workflow
    - requesting-code-review
    - workflow-ecosystem-audit
    - documentation-and-adrs
---

# Development Closure Consensus

## Overview

This skill defines the public, cross-project development closure consensus. It applies when the user asks the agent to check whether a task is truly closed, to push a task through delivery, or to perform "全盘推进/收口". The closure starts at task handoff, not at PR time.

The default runtime shape is:

```text
A. Public development closure consensus
+ B. Project profile
= C. Compiled project development closure consensus
```

C is derived and regenerable. It is not the truth source. When A or B changes, C must be treated as stale and recompiled before execution.

## When to Use

Use this skill when the user asks for any of these:

- "检查某任务闭环情况", "看这条链闭没闭", "全盘推进", "收口", "继续推进到完成"
- a product/Lark/issue/task closeout that may require code inspection, implementation, validation, submission, or learning writeback
- a multi-repo or frontend/backend task where project constraints and delivery evidence matter
- a repeated manual development workflow that should be converted into a reusable consensus/checklist/script/pipeline

Don't use this skill for:

- a narrow command-only request with no closure responsibility
- pure PR mechanics after the task is already verified; use `github-pr-workflow` and its PR closeout reference
- project profile maintenance alone; use `project-profile-maintenance`
- incident response where production is actively broken; use `incident-response` first, then this skill for post-fix closure

## Core Principle

Any closure-check task must first resolve the project profile, then compile the public closure consensus into a project-specific executable closure consensus. The compiled consensus is derived from the public consensus and the project profile; it must become stale when either source changes.

Compact rule:

```text
先找画像，再编译闭环；先判主链，再补实现；先拿证据，再谈完成；PR 只是末段，不是起点。
```

## Public Development Closure Consensus

1. **Closure starts at task handoff.** When the user hands over a task for closure checking, the agent assumes responsibility for intake, mainline discovery, implementation gaps, validation, delivery closeout, and learning writeback as needed.

2. **Seek truth before fixing.** Resolve the real project, task source, project profile, code anchors, prototype/product truth, existing branch state, and acceptance evidence before choosing an implementation path.

3. **Project profile precedes generic process.** Generic closure rules are not directly executable. They must be constrained by the current project's repositories, red lines, validation commands, business chains, and ownership model.

4. **Main chain beats symptom count.** Prioritize whether the primary business chain is closed over the number of scattered issues found.

5. **Evidence precedes completion claims.** No build/test/browser/smoke/compile/runtime evidence, no closure claim. Use the strongest evidence available for the project's risk level.

6. **Baseline changes invalidate old evidence.** Rebase, pull, dependency change, environment switch, or upstream merge means previous validation is stale until rerun.

7. **Local completion is not shared completion.** A local pass is only one layer. Integration, delivery metadata, deployability, rollback/readiness, and collaboration signals may also be closure gates.

8. **Cross-repo dependencies must be explicit.** State which repo/PR depends on which, merge order, and whether follow-up rebase/smoke is required.

9. **Decisions and rationale must be traceable.** Non-trivial choices need a lightweight decision record or equivalent task/PR note: context, decision, alternatives, consequences, and evidence.

10. **Repeatable manual closure should become an asset.** If a closure path is manually proven and likely reusable, classify the lesson into public consensus, project profile, skill, checklist, script, or pipeline.

11. **Product/prototype parity is cross-layer, not screenshot-only.** For product/prototype closeout, verify the visible UI against the prototype/PRD, then descend through frontend service contracts, backend controller/domain state transitions, persistence/migration, permissions, audit/security, and browser/runtime evidence. A pixel/UI pass alone does not close a semantic product task.

12. **Security-sensitive flows need executable proof, not narrative assurance.** For PII, admin actions, GA/MFA-gated operations, money/status/order changes, and audit logs, the closure evidence must prove the real request carries the required guard (for example GA code/header), mutates the intended state, preserves required snapshots, and writes durable audit evidence. Mock success or local toast text is not enough.

13. **Repository-scope determines the best fix point.** For every product/prototype/code closeout, first determine the repository boundary actually in scope (single frontend, frontend+backend, multi-service, data/migration, infra, or cross-app shared capability). Apply the globally best architecture within that boundary, not the smallest visible patch. UI-only fixes are valid only when the change is purely presentational and does not affect data semantics, contracts, persistence, permissions, audit, or cross-repo behavior. If the repo scope includes the backend and the issue concerns list semantics such as sorting, pagination, filtering, export, status, money, time, identity, permissions, or state refresh, the default best fix point is the backend/query/domain layer with the frontend carrying an explicit contract and display state. Do not use frontend fetch windows, current-page-only transforms, mocks, or toasts to simulate whole-system correctness.

14. **Prototype field parity needs a contract, not display forgery.** When a prototype/PRD requires canonical IDs, sensitive identifiers, finance/card/wallet fields, or admin drawer/detail semantics that current list APIs do not expose, close the gap at the strongest available contract boundary: add or extend a detail endpoint/domain mapper, make unavailable sensitive data explicit with a typed placeholder flag, and let the UI render the contract state. Do not fabricate full identifiers, card numbers, balances, limits, or audit/security state in the frontend just to satisfy visual parity. Validation must prove both the backend contract and the real browser path that consumes it.

15. **Queries start from an entry point, not a boundary.** For project/code/product/document queries, the named file, page, route, field, status, action, API, metric, or bug symptom is only the first handle. Before answering or closing, expand to the associated system surfaces that can change the truth of the answer: canonical doc/profile/prototype, producers/writers, transformers/adapters/fallbacks, display consumers, action consumers, routes/menus/dashboard/deep links, permissions/guards, KPI/badge/count/report/export口径, tests/fixtures, and runtime evidence. A narrow answer is valid only when the user explicitly requests a narrow lookup or when uncovered associated surfaces are named as unverified.

## Runtime Protocol

### Phase 0 — Detect closure mode

Enter closure mode when the user asks to inspect/finish/close a task, not only when they ask for PR work.

### Phase 1 — Resolve project profile

Before applying generic rules, locate and inspect the relevant project profile or project-local guidance:

- canonical project profile (`~/.hermes/project-profiles/<project>.json` when available)
- repo-level `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, docs, or test scripts
- source-of-truth docs/prototypes/routes/controllers/tests for the task domain

If no usable profile exists, create a minimal working profile from live repo evidence before deep execution, or proceed with explicit assumptions and mark the profile gap.

### Phase 2 — Compile project-specific closure consensus

Derive an execution consensus for the current task:

- project topology: repos, branches, remotes, deploy targets
- repository boundary: single repo, frontend+backend, multi-service, data/migration, infra, or shared capability scope
- task domain: frontend/backend/contract/infrastructure/data/product-doc
- best fix point: the highest-leverage layer inside the actual repo boundary; do not default to the nearest visible UI patch
- main chain: user-visible or system-critical path that defines closure
- red lines: forbidden regressions, security rules, migration rules, UX invariants
- evidence gates: exact commands, browser viewports, tests, compile/build, smoke checks
- delivery gates: commit scope, PR base/head, cross-repo dependency comments, merge order
- learning gates: what to write back to public consensus vs project profile vs skill/script

Use `references/abc-schema.md` as the canonical structure. Use `references/resolver-protocol.md` for the full runtime resolver sequence and terminal report format. For projection-only approval/closeout systems, use `references/evidence-bound-authorization-closeout.md` to keep evidence-bound authorization non-executing and stale-aware.

### Phase 3 — Execute with stage gates

Do not skip stages just because the final delivery step seems obvious:

1. Intake and scope truth
2. Repository-scope, main-chain, and best-fix-point diagnosis
   - Classify the actual repository boundary before choosing the implementation layer.
   - If the boundary includes multiple repos, prefer the globally correct cross-layer fix over a local workaround.
   - For collection/data semantics (sorting, pagination, filtering, export, status, money, time, identity, permissions, state refresh), make the backend/query/domain layer own whole-system correctness and make the frontend expose/consume an explicit contract.
3. Implementation or gap closure
   - Keep UI/prototype shape, backend contract, persistence, security/audit semantics, and permissions in one traceable chain.
   - When manual validation is non-trivial, add a deterministic static/browser/smoke script so the evidence can be rerun after rebase or review fixes.
4. Project-appropriate validation evidence
5. Delivery closeout when requested/appropriate
6. Learning writeback and assetization

### Phase 4 — Invalidation and writeback

When new stable knowledge appears, classify it before writing:

- Cross-project rule -> public development closure consensus or a shared skill/reference
- Project-specific fact -> project profile / project AGENTS.md if relevant
- Deterministic repeated action -> script/template/pipeline
- Session-local progress -> do not persist as memory/profile

If A or B changes, mark compiled C as stale and regenerate before the next closure execution.

## Source Foundations

This consensus is grounded in requirements engineering, pragmatic automation, TDD, CI/CD, DevOps, SRE, ADR, checklist discipline, and flow metrics. See `references/core-sources.md` for the source map.

## Relationship to PR Closeout

PR work is the delivery tail of closure, not the start. For the PR-specific portion, load `github-pr-workflow` and `references/pr-closeout-consensus.md`. This skill owns the upstream closure chain that begins when the task is handed over for closure checking.

## Common Pitfalls

1. Starting with PR mechanics before resolving the project profile and task main chain.
2. Treating a compiled project closure consensus as permanent truth instead of a stale-aware derivative of public consensus and project profile.
3. Claiming closure from local implementation without rerunning validation after base/rebase/dependency changes.
4. Writing project-specific facts into public consensus, writing generic process rules into project profile, or failing to promote a globally reusable best-fix-point rule from a project case into public consensus.
5. Preserving session-local progress in memory/profile instead of keeping it in task notes or PR comments.
6. Using `git add -A` or broad commits in long-lived dirty repos during closeout.
7. Failing to assetize a repeated manual closure path after it is proven.
8. Treating a prototype-parity task as only a UI layout task while missing backend state/audit/permission semantics.
9. Claiming security-sensitive/admin/PII flows are closed without executable evidence that the real request includes the required GA/MFA/audit parameters and writes durable audit/state records.
10. Scope: approval/authorization ledgers in any projection-only control plane. Pitfall: treating human approval as execution authority. Evidence-bound authorization must recompute evidence freshness both at request time and at decision time; approval rows must stay non-executing until a separate executor/adapter contract is designed, gated, and verified. Anti-condition: if the task is purely UI copy or has no approval/evidence/authorization boundary, skip this pitfall.

## Verification Checklist

- [ ] Closure mode was detected from the user request, not delayed until PR time.
- [ ] The relevant project profile or equivalent project-local guidance was located or explicitly marked missing.
- [ ] A project-specific closure consensus was compiled from public rules plus project facts before execution.
- [ ] The actual repository boundary was classified and the best fix point was chosen within that boundary, not from the nearest visible symptom.
- [ ] Prototype/PRD field parity that depends on identifiers, money, cards, wallets, limits, audit, or security state is backed by an explicit backend/detail contract or typed unavailable-state flag, not frontend fabrication.
- [ ] Query answers treated the named object as an entry point and either covered associated producers/consumers/routes/permissions/KPIs/tests or explicitly listed unverified associated surfaces.
- [ ] Main chain, best fix point, red lines, and evidence gates were named before claiming closure.
- [ ] Validation evidence was rerun after any baseline change.
- [ ] Delivery metadata, PR/base/head/dependencies/merge order were handled when delivery closeout was in scope.
- [ ] Stable learnings were classified into public consensus, project profile, skill/script/pipeline, or non-persistent session state.

## Positive / Negative Trigger Examples

Positive:
- "检查兑换任务闭环情况"
- "这个 Lark 任务全盘推进到收口"
- "看这个功能链路是不是已经真正闭环"
- "这次人工跑通的开发流程能不能吸收成共识"

Neighbor loads:
- "给这个 PR 加 label 并看 checks" -> `github-pr-workflow`
- "更新 uvisa 项目画像" -> `project-profile-maintenance`
- "写一份实现计划" -> `writing-plans`

Forbidden/no-load:
- "现在几点" or arithmetic/system facts
- "帮我解释这个 TypeScript 语法" when no closure responsibility exists
