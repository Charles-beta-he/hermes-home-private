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

## Auth / Credential Gate Flag Defaults

Scope: frontend auth stores or route guards that decide whether to send users into first-time setup, step-up verification, trusted-device checks, KYC completion, or other credential gates based on backend booleans.

Rule: missing credential-state flags must not be blindly synthesized into the permissive / already-complete state. Default according to the safer domain invariant for that gate, and add a regression test for both login-token normalization and profile-refresh normalization.

Checklist:

1. Separate explicit states from missing-contract states.
   - Prefer explicit backend booleans such as `hasPaymentPin`, `paymentPinSet`, `loginPasswordSet`, `currentDeviceTrusted`, or an explicit setup flag such as `needsPinSetup`.
   - If a flag is omitted, do not silently route into a downstream verification page that assumes the credential exists.
2. For first-time setup gates, fail toward setup rather than verification when the credential-exists contract is missing.
   - Example: if a newly opened account may not have a payment PIN, missing `hasPaymentPin` should behave like `false`, not like `true`, otherwise the user is sent to “enter payment PIN” before one exists.
3. Preserve known current-session state only after higher-priority explicit response fields are checked.
   - Good precedence: explicit login-token normalization → explicit profile fields / aliases → previous known state → safe default.
4. Cover both auth-token and profile-refresh paths in tests.
   - Login response omits the flag.
   - Profile `/me` response omits the flag.
   - Explicit `false` stays false and explicit `true` stays true.
5. Keep trusted-device / step-up verification separate from first-time setup.
   - “Credential exists but device is untrusted” is a different route than “credential does not exist yet”.

Anti-condition: if the backend contract is formally guaranteed and enforced to always include the flag on every relevant endpoint, frontend defaults may be narrower, but still keep a regression test proving omitted/malformed data does not route to an impossible user action.

## Shared Collection to Page View-Model Boundary

Scope: frontend applications where one shared store collection is consumed by multiple surfaces, especially financial, account, eligibility, inventory, notification, or compliance domains.

Rule: a shared store collection is not automatically a page-level view model. Before a page aggregates or displays a shared collection, encode the page's domain invariant in a selector/view-model layer.

## Truthful Runtime / Readiness Badge Model

Detailed `Truthful Runtime / Readiness Badge Model` guidance moved to `references/truthful-runtime-readiness-badge-model.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Common Pitfalls

1. **Using operation-level IDs in wallet-level lists.** Use the leg ID the backend returns to that view.
2. **Showing both ledger legs in global filters without product confirmation.** Dedup by root/operation when the UI intends one logical operation.
3. **Assuming fee fields mean the same thing everywhere.** Confirm current product definition and endpoint parity.
4. **Dropping concurrent SSE events.** A bare `syncInFlight` guard without a dirty bit loses data until the next poll.
5. **Persisting transient guard flags.** `syncPending` and `syncInFlight` are runtime state, not persisted store state.
6. **Changing backend field names without frontend fallback audit.** Optimistic objects, DTOs, and detail screens often read different fields.
7. **Collapsing business-error envelopes to `null`.** When an API client adapts backend envelopes such as HTTP 200 `{ code != 0, message, data: null }` into `{ success:false, code, message }`, do not let a store/action convert that result to plain `null` before the page-level toast/error handler. `null` should mean transport/unknown/no-entity fallback; business failures must carry `message` and `code` through store return types so the UI shows backend copy instead of generic `common.networkError`. Add regression tests at the store boundary for `success:false` message preservation, plus page-level checks that real exceptions still use the generic network fallback.
8. **Conflating broad backend stage with the concrete required action.** Auth/onboarding/payment flows may return both a coarse state (for example `authStage=PENDING_PIN`) and a specific next step (for example `requiredStep=SET_PAYMENT_PIN` vs `VERIFY_PAYMENT_PIN`). Route by the specific discriminator first; only use the broad stage as a fallback after checking setup/absence flags such as `hasPaymentPin=false`, `paymentPinSet=false`, or aliases. Add regression tests for both setup and verify variants so a new user is not sent to an existing-PIN verification screen.
8. **Reducing raw shared collections directly in page components.** A shared collection must pass through page eligibility, feature gates, and semantic conversion before display.
8. **Reducing raw shared collections directly in page components.** A shared collection must pass through page eligibility, feature gates, and semantic conversion before display.
8. **Treating UI wording as data-source authorization.** "Show these labels/sections" usually means preserve current business source and change presentation unless acceptance explicitly changes source, eligibility, or aggregation semantics.
9. **Collapsing multi-axis operational state into one green badge.** Labels such as "online · deliverable" may conflate connectivity, sync freshness, simulator/build proof, external release readiness, and authority gates. Replace with a selector that derives conservative copy from each axis and exposes missing proof/gates instead of implying production or external action readiness.
10. **Letting page-local transaction titles drift from shared list semantics.** When one surface (home/recent transactions, full transaction list, wallet-account detail) already has a shared transaction-row label priority, do not re-encode a different title ladder in a page component without a documented product exception. Prefer extracting/reusing the shared label helper, or at minimum lock parity tests across representative surfaces.
10. **Collapsing business failures into `null` makes real backend messages look like network errors.** In envelope-adapted APIs, HTTP 200 with `{ code != 0, message }` should become a typed business failure and keep `message` through service → store → screen. Store helpers that return `null` for `!res.success` force finish screens to fallback to `common.networkError`, hiding backend copy such as maintenance/payment/channel errors. Prefer a result union (`{ success:false, message, code }`) or throw/return an error object, and add tests for `200 + business code + message`.

## Auth Flow Stage vs Required Action Pattern

Use this when login/auth responses include both broad lifecycle stages and concrete next-action fields, especially in first-login, MFA, PIN, password-setup, or trusted-device flows.

Rule: do not route from a broad stage enum alone when a narrower required-action field exists. Treat fields such as `authStage=PENDING_*` as a state family, not as the user action. Route from the most specific contract first, for example:

1. Required setup action wins: `requiredStep=SET_PAYMENT_PIN`, `needsPinSetup=true`, `hasPaymentPin=false`, `paymentPinSet=false`, or equivalent aliases → setup screen.
2. Required verification action next: `requiredStep=VERIFY_PAYMENT_PIN` → verify-existing-secret screen.
3. Broad stage fallback only after excluding setup aliases: `authStage=PENDING_PIN` may mean either setup or verify depending on the action field.
4. Test mixed contracts explicitly: a response can contain `authStage=PENDING_PIN` and `hasPaymentPin=false`; this must not be sent to an “enter existing PIN” page.

When debugging this class of bug, capture and compare the full auth payload, not just the field that seems decisive. Check type definitions too: if the frontend union only includes `VERIFY_*` but the backend returns `SET_*`, TypeScript can hide the missing branch until runtime.

## API Envelope Business Error Propagation Pattern

Use this when a frontend API layer adapts backend envelopes such as `{ code, message, data }` into service/store results, especially when HTTP 200 can still mean business failure (`code !== 0`).

Rule: do not collapse a backend business failure into `null`, `false`, or a generic exception before the UI boundary has had a chance to display the backend `message`. Reserve generic “network error” copy for true transport/server failures or missing/unknown errors.

Checklist:

1. Identify the transport vs business-success boundary.
   - HTTP 200 + `code !== 0` is a business failure, not a network failure.
   - The adapter should preserve `success:false`, `code`, and `message`.
2. Audit every intermediate layer for message loss.
   - Service result → store action → page/finish screen.
   - Risky patterns: `if (!res.success) return null`, `catch { return null }`, `return res.success ? id : null`, or boolean-only store APIs.
3. Use typed result objects for post-verification side effects.
   - Good shape: `{ success: true, txId, ... } | { success: false, code, message }` or an equivalent existing project convention.
   - Keep `null` only for true local impossibility / transport fallback when no backend message exists.
4. At the UI boundary, prefer backend message and then fall back.
   - `toast(result.message || t("common.networkError"), "error")` on business failure.
   - Do not make the global network-error handler display arbitrary backend messages unless product explicitly wants 5xx/business copy there.
5. Add regression tests at the layer that previously swallowed the message.
   - Mock a 200/business-error adapted response with a concrete `code` and `message`.
   - Assert the store/page result preserves that message instead of returning `null` or generic network text.

Anti-conditions:
- If the backend formally uses non-2xx for all business failures and the API client resolves 4xx envelopes consistently, this pattern still applies at the first layer that receives `{ success:false, message }`, but the transport classification step differs.
- If the error is a true network outage, cancellation, timeout, or 5xx without product-owned business message, keep the generic network fallback.

## Cross-Surface Transaction Wording Parity Pattern

Use this when a wallet/account/transaction page displays the same logical transaction rows as a home or global transaction list, but has page-specific filtering, tabs, icons, or amount-direction semantics.

1. Identify the canonical row-title priority already used by the shared transaction row. Common financial-app priority is: backend `description` / scene text first, then explicit `displayType`, then type/i18n fallback, then counterparty/channel suffix if the canonical component does that.
2. Keep page-specific domain semantics outside the title-source priority unless product explicitly requires a different label.
   - Good page-specific logic: wallet tab eligibility, CNY scope parameters, ledger-leg amount sign, exchange “兑入/兑出” fallback when no description exists, internal badges, route targets.
   - Risky page-specific logic: hardcoding “定期申购” / “U-VISA 卡充值” ahead of backend `description`, or using `displayType` ahead of scene-specific `description` on only one surface.
3. If a page cannot reuse the shared component because layout differs, mirror the same helper/priority and document why the layout is custom.
4. Add parity tests, not just page-local screenshots:
   - A shared-row test proving `description` wins over generic type/display labels.
   - A page test for the affected wallet/account surface proving the same `description` priority.
   - A fallback test proving page-specific labels still work when `description` is absent.
5. Compare screenshots against both the target surface and the canonical surface when the user asks “是否一致 / same as home / same as transaction list”.

Anti-conditions:
- If the product document explicitly says a wallet page must show a normalized product label instead of backend scene text, record that exception near the helper and test the exception.
8. **Treating UI wording as data-source authorization.** "Show these labels/sections" usually means preserve current business source and change presentation unless acceptance explicitly changes source, eligibility, or aggregation semantics.
9. **Fixing one surface without comparing sibling renderers.** When a list/detail wording bug mentions "same as home", inspect the sibling component/helper that already renders the same entity before adding page-local logic. Prefer reusing or mirroring the same priority order (for example backend `description` > derived display label > generic type fallback) and add regression tests for both the canonical renderer and the page-specific renderer.

## Verification Checklist

- [ ] Domain invariant is stated in product/backend terms.
- [ ] Optimistic and authoritative IDs align for the same visible record.
- [ ] All relevant list/detail endpoints expose needed fields.
- [ ] Store merge/dedup handles optimistic replacement, not duplicate append.
- [ ] Async guard success and error paths both resync pending triggers.
- [ ] Regression tests cover rapid events and representative domain edge cases.
- [ ] Cross-surface transaction title tests prove backend `description` priority matches the canonical list row unless a product exception is documented.
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
## Support Files

- `references/financial-ledger-frontend-patterns.md` — FX/debit/credit IDs, fee semantics, transaction sign/description, DTO parity.
- `references/concurrent-async-guard.md` — dirty-bit guard implementation and Zustand examples.
