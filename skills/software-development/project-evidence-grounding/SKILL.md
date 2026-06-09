---
name: project-evidence-grounding
description: Use when project work must be grounded across PRD/product docs, prototype/source repos, live implementation, browser/static proof, and durable project profiles; use it for evidence-first audits, closure checks, and profile updates that must survive future sessions.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
      - project-evidence
      - prototype
      - code-audit
      - project-profile
      - closure
    related_skills:
      - development-closure-consensus
      - browser-harness-integration
      - codebase-intelligence
---

# Project Evidence Grounding

## Overview

Use this as the class-level workflow for project work where the answer must be anchored in more than one truth source: PRDs/product docs, prototype/source repos, current frontend/backend implementation, browser/static proof artifacts, and canonical project profiles.

The core job is to stop project work from drifting into filename guesses, stale session memory, or one-off reports. Every claim should identify which source proves it, where the current implementation lands, and whether the result should become durable project knowledge.

## When to Use

- The user asks whether implementation matches a PRD, prototype, product doc, or design source.
- You need to audit missing pages, fields, labels, default states, permissions, PII controls, monitoring hooks, or business-loop gaps.
- You need to update a canonical project profile after transcript recovery, prototype/source repo discovery, or codebase archaeology.
- You need to build durable navigation maps from prototype domains to current frontend/backend/test entrypoints.
- You are closing a product/prototype gap and must prove it with static checks, browser proof, or build/test evidence.

Don't use this for generic code review without product/prototype/profile grounding; use the relevant code review or debugging skill instead.

## Truth-Source Order

Prefer explicit source layering:

1. Newest product/PRD requirement or canonical project profile.
2. Prototype/source repo route/page/component evidence.
3. Current implementation files, routes, controllers, services, migrations, and tests.
4. Runtime/browser/static proof artifacts.
5. Historical sessions only as lineage, never as unverified truth.

When sources disagree, report the divergence instead of averaging them. State which source is newest/canonical and which implementation surface is stale or absent.

## Audit Mode: Product / Prototype / Code

Use audit mode when the output is a gap report or closure plan.

1. Locate canonical evidence sources: latest PRD/doc, prototype/reference repo, and current implementation.
2. Build the expected closed loop: user entry, admin/ops surface, monitoring, downstream reconciliation, failure/refund path, and operator visibility.
3. Compare prototype/source vs implementation page-by-page where possible; fall back to business-vocabulary search when filenames differ.
4. Check defaults and operator legibility: tabs, filters, empty states, linked records, failure wording, alert tiles, structured actor/counterparty rendering, sync timestamps.
5. Report gaps with severity, exact evidence, operational impact, and recommended landing point.
6. If moving to implementation, write a deterministic regression/static closure harness before patching and verify RED/GREEN/build/browser proof before claiming closure.

## General Query Full-Coverage Mode

Use this mode for project/code/product/document queries in general, not only status/source checks. Treat the named object as an entry point, not the boundary.

Mandatory default:
1. Internally classify the queried object: page, field, status, action, API, route, workflow, metric, permission, document claim, or bug symptom.
2. Before answering, build the associated-surface map where relevant: canonical source, producers/writers, transformers/adapters/fallbacks, consumers/displays, action consumers, routes/entries, permissions/guards, metrics/badges/counts, tests/fixtures/runtime evidence.
3. Search by both names and semantics: filenames/routes plus enum labels, user-facing text, business verbs, controller/service/repository/migration, summary/count/badge/permission terms.
4. Classify nontrivial hits as producer, transformer, display consumer, action consumer, entry, permission, metric, test, doc/prototype, or irrelevant.
5. If the question is simple, answer concisely but still name the checked scope and any uncovered associated surfaces. If high-risk, include evidence paths/lines and a falsifier/test.

Fail-closed rule: do not answer from the named file/page only when related modules can change the truth of the answer. If budget prevents full expansion, explicitly state which associated surfaces were not checked.

For the detailed generalized protocol, read `references/general-query-full-coverage.md`.

## Status / Source Full-Coverage Mode

Use this mode as a specialized stricter version of General Query Full-Coverage whenever the user asks whether a status column, source field, badge, queue, KPI, or PRD state is aligned. A status/source is a workflow contract, not a one-page UI label.

Mandatory expansion:
1. Start from the newest PRD/profile status semantics, then build a source-to-sink map.
2. Search producers and backend contracts: user/PAD/admin actions, jobs/webhooks, controllers, services, DTOs, repositories, migrations, enums, and default/fallback paths.
3. Search frontend normalizers and all consumers: services/stores/adapters, list/detail/dashboard/widget/drawer/tab, filters, sorting, exports, notifications, and unknown-state renderers.
4. Search route and operator entry points: App routes, Sidebar, WorkspaceTabs, Dashboard cards, direct URLs, breadcrumbs, and empty states.
5. Search permissions and KPI/badge口径: view/action perms, route guards, mutation guards, dashboard summary, sidebar badges, tab counts, and backend counts.
6. Verify state transitions and downstream effects: review/approve/reject actions, account/card/funds locks or unlocks, audit logs, CS/ops visibility, and after-action synchronization.

Fail-closed rules:
- Do not conclude from the starting page alone; the starting page is only one consumer.
- Every enum value or user-facing status label found by search must be classified as producer, normalizer, display consumer, action consumer, route/entry, permission, KPI, test, or irrelevant.
- If a Dashboard/sidebar/tab count claims to summarize a queue, compare its predicate/source to the queue predicate/source before calling it aligned.
- If unknown or legacy states fall back to a success label, flag it as a semantic-risk gap.

For the detailed matrix, search expansion, falsifiers, and UVISA KYC example anchors, read `references/status-source-full-coverage-audit.md`.

## Profile Mode: Durable Project Memory

Use profile mode when the output is a canonical project profile update.

1. Locate the profile source of truth, usually under `~/.hermes/project-profiles/` unless repo docs explicitly say otherwise.
2. Recover historical evidence only to extract durable facts: module maps, architecture invariants, stable UX rules, route groups, prototype anchors, verified data flows.
3. Reconfirm against current code before writing; stale transcript claims do not belong in durable profiles.
4. Add structured navigation layers: `prototype_source_repo`, route/page indexes, domain landing maps, deep maps from prototype → frontend → backend → tests/evidence.
5. Record compact lineage in `profile_update_history` without session-local task progress.
6. Re-parse the profile and sanity-check all new file/path anchors.

## Cross-Mode Handback

Audit findings often create profile updates, and profile discoveries often change audit scope.

- If an audit reveals a durable project rule, profile-first is the default writeback target; repo docs are optional and require explicit project/user intent.
- If a profile refresh discovers prototype/source truth that contradicts current implementation, create an audit/closure queue item rather than silently rewriting profile claims.
- Session-specific examples, long PRD excerpts, or case studies belong in `references/`, not in the root skill body.

## Evidence Format

For each finding or profile fact, capture:

- expected source: doc/prototype/profile file + line or exact string
- current source: implementation file + line or exact string
- runtime/static proof: command, browser screenshot, test, or build output when applicable
- impact: why it matters operationally or for future navigation
- writeback target: code fix, profile update, reference note, or explicit no-action

## Support Files

- `references/product-prototype-code-audit.md` — archived detailed audit workflow and UVISA examples from the former narrow skill.
- `references/project-profile-maintenance.md` — archived detailed profile-maintenance workflow and prototype/source profile examples from the former narrow skill.
- `references/prd-compliance-audit-patterns.md` — recurring anti-patterns when cross-referencing code changes against PRD/product docs: input-vs-submit validation gaps, service-layer fields read but not enforced in UI, language detection for error localization.
- `references/multi-repo-health-check.md` — operational workflow for scanning all project repos (frontend/backend/admin) for uncommitted changes, unpushed commits, open PRs, and validating found changes against PRD.

## Common Pitfalls

1. Stopping at route/file existence instead of reading the page body, service contract, and backend/data path.
2. Treating a missing filename as absence before searching by business vocabulary, enum, route text, and user-facing labels.
3. Mixing latest PRD semantics with older prototype/session semantics without naming the conflict.
4. Writing session-local task progress into a canonical project profile.
5. Updating repo-local `AGENTS.md` by default for assistant-only project guidance; profile JSON is usually the right durable target.
6. Calling closure before the regression harness, browser proof, or build/test evidence has been read back.

## Verification Checklist

- [ ] Truth-source order and canonical source were stated.
- [ ] Current implementation anchors were inspected, not guessed.
- [ ] Every gap/fact includes evidence and impact.
- [ ] Durable profile writes were re-parsed and checked against real code paths.
- [ ] Session-specific detail was moved to references instead of bloating the profile or root skill.
- [ ] Closure claims include static/browser/build/test proof, not only prose.
- [ ] If the user challenges a conclusion and evidence shows the user is right, perform error absorption before continuing: explicitly acknowledge the wrong assumption, identify the missed evidence gate, patch the check/skill/profile where appropriate, and sweep adjacent producers/consumers/contracts for the same architectural drift instead of treating it as a one-off typo.