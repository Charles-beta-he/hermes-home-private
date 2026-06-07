---
name: frontend-state-domain-correctness
description: "Use when frontend state management must preserve domain correctness under async refreshes, optimistic updates, realtime invalidation, category filters, or backend ledger/API semantics. Covers dirty-bit async guards and financial ledger transaction display/dedup patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [frontend, state-management, zustand, optimistic-updates, financial-ledger, realtime]
    related_skills: [systematic-debugging, react-architecture-migration, test-driven-development]
---

# Frontend State and Domain Correctness

## Overview

This umbrella covers frontend stores and UI data models where correctness depends on backend/domain semantics: optimistic updates, double-entry financial ledgers, realtime invalidation, guarded async sync, category-filtered lists, and API field parity.

## When to Use

- Duplicate, missing, or wrong transaction records after optimistic updates
- Double-entry debit/credit ledger records must be displayed as one logical operation or the correct wallet leg
- Zustand/Redux/Vue stores drop rapid SSE/polling/visibility refreshes due to an in-flight guard
- Category-filtered lists or pickers show items from the wrong business universe
- Backend endpoints serve the same entity with mismatched field sets

Don't use for:
- Pure CSS/display-only bugs with no state/domain semantics
- Backend-only ledger accounting with no frontend representation issue
- Simple one-shot fetches where concurrency cannot overlap

## Default Debugging Flow

1. **Name the domain invariant**: e.g., one visible transaction per wallet leg, fee means channel fee only, category list excludes business-ineligible currencies.
2. **Trace source layers**: optimistic client object → store merge → API response → backend DTO/query → ledger/domain model.
3. **Compare IDs and keys**: optimistic id, authoritative id, operation id, composite leg id, root id, and dedup key.
4. **Check async guard behavior**: whether rapid triggers are dropped, coalesced, or resynced.
5. **Verify all user surfaces**: detail pages, global lists, wallet lists, history endpoints, and confirm/quote responses.

## Financial Ledger Frontend Pattern

- Match optimistic transaction IDs to the exact authoritative record the current wallet view will receive.
- For double-entry systems, `fx_debit:{orderId}` and `fx_credit:{orderId}` are distinct records. The source wallet likely sees the debit leg; target wallet sees the credit leg.
- Do not switch to a single-leg architecture just to hide frontend duplicates; fix ID alignment and list dedup boundaries.
- Distinguish explicit UI fee from embedded spread/rate economics according to current product semantics.
- Audit quote, confirm, idempotency, history, and aggregate endpoints for field parity.

## Async Guard Dirty-Bit Pattern

When a one-at-a-time sync guard drops rapid triggers:

```ts
if (get().syncInFlight) {
  set({ syncPending: true });
  return;
}
set({ syncInFlight: true, syncPending: false });
// fetch/process
let pending = false;
set((s) => {
  pending = s.syncPending;
  return { ...resultFields, syncInFlight: false, syncPending: false };
});
if (pending) void get().syncNotifications('sync-pending');
```

Use the updater form for atomic capture-and-clear. Do not read `get().syncPending` and then clear it in a separate write.

## Shared Collection to Page View-Model Boundary

Scope: frontend applications where one shared store collection is consumed by multiple surfaces, especially financial, account, eligibility, inventory, notification, or compliance domains.

Rule: a shared store collection is not automatically a page-level view model. Before a page aggregates or displays a shared collection, encode the page's domain invariant in a selector/view-model layer.

Checklist:

1. State the page invariant in business terms before deriving numbers or visibility.
   - Example shapes: placeholder-only surface, active-items-only list, historical ledger, balance fallback, compliance-gated summary.
2. Put feature gates and placeholder rules before aggregation.
   - If a surface is intentionally disabled, not launched, or placeholder-only, return the placeholder view model before reading raw entities.
3. Filter by page eligibility before `reduce`/`map`.
   - Do not assume "nothing user-visible" means the raw collection is empty.
   - Check status, ownership/session freshness, lifecycle state, product type, visibility flag, and other domain-specific eligibility.
4. Centralize semantic conversion.
   - Currency conversion, precision, status mapping, earnings/revenue field choice, and type splits belong in selectors/domain helpers, not ad-hoc page reducers.
5. Preserve raw vs derived boundaries.
   - Service normalization handles transport compatibility; selectors handle page display semantics.
6. Test negative cases.
   - Raw entities exist but the feature is disabled.
   - Raw entities are non-displayable for this page.
   - Persisted cache or failed refresh would otherwise leak stale/cross-context data.

Anti-conditions: this pattern is unnecessary for a truly page-local collection whose API contract already returns exactly the page view model and has no shared reuse, lifecycle filtering, feature gate, or cross-surface aggregation.

Falsifier: if the backend contract explicitly guarantees the endpoint returns only entities eligible for that exact page surface and the collection is not reused elsewhere, page-level selectors may be minimal pass-throughs.

## Common Pitfalls

1. **Using operation-level IDs in wallet-level lists.** Use the leg ID the backend returns to that view.
2. **Showing both ledger legs in global filters without product confirmation.** Dedup by root/operation when the UI intends one logical operation.
3. **Assuming fee fields mean the same thing everywhere.** Confirm current product definition and endpoint parity.
4. **Dropping concurrent SSE events.** A bare `syncInFlight` guard without a dirty bit loses data until the next poll.
5. **Persisting transient guard flags.** `syncPending` and `syncInFlight` are runtime state, not persisted store state.
6. **Changing backend field names without frontend fallback audit.** Optimistic objects, DTOs, and detail screens often read different fields.
7. **Reducing raw shared collections directly in page components.** A shared collection must pass through page eligibility, feature gates, and semantic conversion before display.
8. **Treating UI wording as data-source authorization.** "Show these labels/sections" usually means preserve current business source and change presentation unless acceptance explicitly changes source, eligibility, or aggregation semantics.

## Verification Checklist

- [ ] Domain invariant is stated in product/backend terms.
- [ ] Optimistic and authoritative IDs align for the same visible record.
- [ ] All relevant list/detail endpoints expose needed fields.
- [ ] Store merge/dedup handles optimistic replacement, not duplicate append.
- [ ] Async guard success and error paths both resync pending triggers.
- [ ] Regression tests cover rapid events and representative domain edge cases.
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
## Support Files

- `references/financial-ledger-frontend-patterns.md` — FX/debit/credit IDs, fee semantics, transaction sign/description, DTO parity.
- `references/concurrent-async-guard.md` — dirty-bit guard implementation and Zustand examples.
