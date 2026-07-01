---
name: product-prototype-code-audit
description: "Use when triangulate PRD/product docs, prototype code, live implementation, static closure checks, and browser proof artifacts to find or close missing flows, default states, labels, permissions, PII controls, and monitoring gaps with evidence-first reporting."
---

# Product / Prototype / Code Audit

## Overview

Triangulate PRD/product docs, prototype code, live implementation, static closure checks, and browser proof artifacts to find or close missing flows, default states, labels, permissions, PII controls, and monitoring gaps with evidence-first reporting. This skill is maintained as a `reviewer`-shaped contract: it should guide evidence-grounded review, audit, critique, certification, or quality-gate work without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `product-prototype-code-audit` and requires evidence-grounded review, audit, critique, certification, or quality-gate work.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this skill when the user asks to:
- check whether implementation matches product docs or prototype
- find missing pages, fields, empty states, labels, default content, or monitoring hooks
- compare a current repo against a design/prototype repo
- audit a feature across multiple surfaces (app/admin/pad/backend)


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Core principle

Do not audit from filenames alone. Build evidence from three layers:
1. product/PRD requirements
2. prototype/reference implementation
3. current implementation

The result should say not just "missing" but "missing relative to which source, at which file/line, and why it matters in the business loop".

## Standard workflow

1. Locate the canonical evidence sources.
   - Identify the newest PRD/doc file.
   - Identify prototype/reference repo files for the feature.
   - Identify current implementation files.
   - If filename search fails, switch immediately to business vocabulary search.

2. Build the expected closed loop.
   - Map the user-entry surface, admin/ops surface, monitoring surface, and downstream/refund/reconciliation surface.
   - For money flows, explicitly map: initiation, confirmation, execution, downstream side effects, failure path, and operator visibility.

3. Compare prototype/reference vs current implementation.
   - Prefer page-to-page diff when the prototype repo contains matching files.
   - Use keyword backfill to prove presence/absence of specific UI elements, labels, statuses, filters, alerts, and explanatory text.
   - Treat route existence alone as insufficient; verify the default content actually surfaced to operators.

4. Audit defaults and operator legibility.
   Check for:
   - source/type tabs
   - purpose filters
   - status explanations
   - empty-state/default text
   - failure/refund wording
   - linked-record navigation
   - dashboard alerts / tiles
   - structured counterparty or actor rendering
   - monitoring / threshold / sync timestamps

5. Report by gap severity.
   - High: breaks operator understanding of the business loop or hides money state/risk.
   - Medium: feature exists but key context is missing.
   - Low: wording, polish, secondary discoverability.

## Search strategy

Start with business terms, not just technical names. Search for both:
- user-facing vocabulary: 兑换, 换汇, 汇率源, 通道储备金, 对手方, 退款, 失败, 钱包流向
- domain enums/contracts: EXCHANGE, REFUND_TO_BUY_CCY, PAYOUT_FAILED, channel_kind, liquidity_warn, liquidity_min, available

If `*exchange*`-style filename search is empty, do not conclude the feature is absent. Search by:
- page title text
- route path
- enum labels
- workflow step names
- alert copy

## Multi-repo comparison pattern

When a prototype/reference repo contains a matching page file:
- diff the prototype file against the live file first
- then run targeted keyword checks against both sides
- use the diff to generate hypotheses, and the keyword checks to turn them into explicit evidence

This is especially effective for catching:
- prototype-only tabs or pills
- explanatory copy that disappeared during real-data integration
- dashboard tiles not carried over
- structured renderers replaced by plain strings

## Money-flow audit checklist

For exchange / payout / topup / card / wealth flows, explicitly verify whether the admin UI exposes:
- source of funds / channel source
- purpose of the transaction
- where funds land on success
- where funds remain on failure
- downstream linked orders/transactions
- operator alerting when liquidity or execution risk exists

If the latest product spec changed failure semantics, the report must call out stale UI wording even when the feature technically works.

## Evidence format

For each gap, include:
- expected source: PRD/prototype file + line or exact string
- current source: implementation file + line or exact string
- why it matters operationally
- recommended landing point (which page/component should change)

## Implementation / closure mode

When the user moves from audit to "fix/落地/闭环", convert the audit findings into a regression harness before patching:
- write a small deterministic static check or focused test for the PRD gaps you are about to close
- confirm it fails against the current implementation (RED)
- implement the smallest coherent cross-surface slice (frontend render/search/export, service types/contracts, backend DTO/API, permission definitions)
- rerun the harness plus real build/test before claiming closure

For PII/admin modules, check every sensitive field at all exposure points: table cell, search predicate, CSV/export, modal copy, and backend DTO. Field-level permission logic is incomplete if it only hides the table cell while search/export still uses plaintext.

For admin list modules with privileged operations, close the action loop too: permission metadata → visible button → GA/modal confirmation → frontend service contract → backend endpoint permission/GA annotation → domain state mutation → security/audit event → list/detail DTO refresh fields. A list-page PRD repair is not closed if it only renders the column but the operator action (for example unbind/rebind/reset) has no backend contract or audit trail.

## Pitfalls

- Do not stop at route presence; inspect the page body.
- Do not assume a missing filename means a missing feature.
- Do not mix old PRD semantics with latest prototype semantics; explicitly prefer the newest source.
- Do not report a gap as product-critical unless you can show the missing operator-visible content.
- In financial flows, missing explanatory text about failure fund location is a real gap, not mere copy polish.
- Do not call a prototype/PRD repair "closed" until the closure harness and relevant frontend/backend builds have passed. If interrupted, say exactly which commands remain.

## Deliverable shape

Produce:
1. baseline sources used
2. current implementation surfaces found
3. missing/default-content gaps by severity
4. exact files to patch
5. any ambiguity or contract drift requiring backend confirmation

## References

- See `references/uvisa-admin-exchange-closed-loop.md` for a concrete multi-repo audit example covering PRD + prototype + live admin comparison.
- See `references/uvisa-admin-users-closed-loop.md` for a PRD-to-implementation repair pattern: static closure harness, PII field permissions, pagination, bound debit-card fields/actions, and validation commands.
- See `references/uvisa-admin-users-pii-action-closure.md` for the condensed checklist on PII exposure points plus privileged action closure: permission metadata → GA modal → service contract → backend permission/audit/state mutation → DTO refresh.
- See `references/uvisa-admin-users-prd-secondary-filter.md` for the secondary-filter pattern used when the user asks which uvisa-admin user-list/detail gaps are actually completable without changing Admin UI/function shape: prioritize PII audit productionization, KYC case decision flow, debit-card UNBINDING semantics, and real-service/mock-fallback cleanup; reject direct CNY force-unbind, new risk tabs, global audit pages, bulk actions, and contact-user buttons under a no-UI-change constraint.


## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Findings include evidence, severity/rubric calibration, and false-positive controls.
