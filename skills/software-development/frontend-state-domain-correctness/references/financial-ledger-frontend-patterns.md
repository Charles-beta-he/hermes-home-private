---
name: financial-ledger-frontend-patterns
description: 'Use when frontend optimistic transactions interact with double-entry financial ledgers — id alignment, deduplication, single-leg vs double-leg architecture, and composite key patterns. Triggered by: duplicate transaction records, fx_debit/fx_credit issues, optimistic update id mismatch, double-entry dedup, wallet showing wrong transaction legs.'
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - software
    - development
    - financial
    - ledger
    - optimistic-update
    - double-entry
    related_skills:
    - react-architecture-migration
    - systematic-debugging
    - development-closure-consensus
---

# Financial Ledger Frontend Patterns

## When to Use

- Duplicate transaction records appear after a financial operation (exchange, transfer, remit)
- Frontend optimistic transactions don't match backend authoritative records
- Double-entry ledger (debit/credit legs) causes confusion about which leg to display
- Composite IDs like `fx_debit:{orderId}` or `transfer_credit:{id}` cause dedup failures
- User reports "two records for one transaction" or "wrong amount shown"
- Exchange/transfer shows duplicate entries in wallet view
- Exchange history or order list API returns no fee data (fee fields missing from response)
- Backend has multiple endpoints serving same entity but with different field sets

## Core Problem: Optimistic Update ID Alignment

When a backend uses **double-entry bookkeeping** (one operation creates multiple ledger entries), the frontend must align optimistic transaction IDs with the **specific leg the current wallet will see** from the backend, not with a generic operation ID.

### The Failure Pattern

```
1. User exchanges CNY → USD
2. Backend creates:
   - Journal entry (operation-level): id = "journal_abc123"
   - FX Debit leg (CNY wallet): id = "fx_debit:order_xyz789"
   - FX Credit leg (USD wallet): id = "fx_credit:order_xyz789"
3. Frontend creates optimistic transaction: id = "journal_abc123"
4. Backend returns authoritative transactions with id = "fx_debit:order_xyz789"
5. Zustand/Redux merge: ids don't match → BOTH records persist → DUPLICATE
```

### The Fix Pattern

```typescript
// WRONG — uses journal/operation id
const optimisticTx = {
  id: journalId,           // "journal_abc123"
  rootType: 'journal',
  ...
};

// CORRECT — uses the debit leg's composite id (what the current wallet sees)
const optimisticTx = {
  id: `fx_debit:${quoteId}`,  // "fx_debit:order_xyz789" — matches backend
  rootType: 'fx_debit',        // matches backend leg type
  ...
};
```

**Rule**: The optimistic transaction `id` must match the `id` field of the authoritative transaction that the backend will return for the **same wallet view**. If the wallet view shows debit legs, the optimistic id must be the debit leg's id.

## Single-Leg vs Double-Leg Architecture

### Double-Leg (Recommended for multi-currency)

Backend creates separate entries per wallet:
- `fx_debit:{orderId}` in source currency wallet (e.g., CNY: -6739.30)
- `fx_credit:{orderId}` in target currency wallet (e.g., USD: +930.50)

**Pros**: Each wallet only sees its own currency's legs. Clean per-wallet view.
**Cons**: Frontend must know which leg to use for optimistic updates.

**Frontend approach**: Use the debit leg's composite id for optimistic updates in the source wallet view. The source wallet query filters by `currency=CNY`, so it only returns the debit leg.

### Single-Leg (Simpler but problematic)

Backend creates one entry with both currencies:
- `fx:{orderId}` with fromCurrency/toCurrency fields

**Pros**: No dedup issue — one operation = one record.
**Cons**: Both wallets see the same record. Source wallet shows a "from" amount, target wallet shows a "to" amount, but the same record appears in both views. Requires client-side filtering by amount direction.

**When single-leg fails**: If the wallet view filters by `currency` field, a single-leg record with `currency=CNY` won't appear in the USD wallet view, and vice versa. The user sees the exchange in one wallet but not the other.

## Decision Framework

| Scenario | Recommended Architecture |
|----------|------------------------|
| Multi-currency wallet with per-wallet views | Double-leg |
| Single wallet, no per-currency filtering | Single-leg |
| Need to show "sent" and "received" separately | Double-leg |
| Simplified transaction history (all-in-one) | Single-leg |

## Composite ID Patterns

Common composite id formats in financial backends:

```
fx_debit:{fx_order_id}        # Exchange debit leg
fx_credit:{fx_order_id}       # Exchange credit leg
transfer_debit:{transfer_id}  # Transfer debit
transfer_credit:{transfer_id} # Transfer credit
remit_debit:{remit_id}        # Remittance debit
remit_credit:{remit_id}       # Remittance credit
topup:{topup_id}              # Top-up (usually single-leg)
payout:{payout_id}            # Payout (usually single-leg)
```

### Extracting the Operation ID from a Composite ID

```typescript
function extractOperationId(compositeId: string): string {
  // "fx_debit:order_xyz789" → "order_xyz789"
  const parts = compositeId.split(':');
  return parts.length > 1 ? parts.slice(1).join(':') : compositeId;
}

function getLegType(compositeId: string): string {
  // "fx_debit:order_xyz789" → "fx_debit"
  return compositeId.split(':')[0];
}
```

## Zustand Store Dedup Pattern

When merging optimistic and authoritative transactions:

```typescript
// In Zustand store
addTransaction: (tx) => set((state) => {
  const existing = state.transactions.find(t => t.id === tx.id);
  if (existing) {
    // Replace optimistic with authoritative (same id)
    return {
      transactions: state.transactions.map(t =>
        t.id === tx.id ? { ...t, ...tx, _isOptimistic: false } : t
      )
    };
  }
  // New transaction
  return { transactions: [tx, ...state.transactions] };
}),
```

This only works when optimistic and authoritative ids match. If they don't, you get duplicates.

## Pitfalls

1. **Using operation/journal id for optimistic tx**: The most common mistake. Always use the leg-specific composite id.

2. **Reverting to single-leg to "fix" dedup**: Single-leg has its own problems (see above). Fix the id alignment instead of changing the ledger architecture.

3. **Not checking which leg the current wallet sees**: The optimistic id must match the leg that the current wallet's query returns. If the wallet shows all legs (debit + credit), you may need different logic than if it filters by currency.

4. **Backend returning different leg types for different operations**: Exchange uses `fx_debit/fx_credit`, transfer uses `transfer_debit/transfer_credit`. The optimistic id prefix must match the specific operation type.

5. **Mockito cannot mock nested class method references**: In Java/Spring backends, testing composite id generation in nested classes requires actual instantiation, not mocking. Use `@SpringBootTest` or extract to a standalone service.

6. **`gh pr merge --delete-branch` fails with git worktree**: When multiple worktrees reference the same branch, `--delete-branch` fails even for remote branches. Use `--squash` without `--delete-branch`, or use the GitHub API directly.

7. **Global transaction list showing both legs**: When a unified `/tx` page filters by `type === "exchange"` (or `type === "transfer"`), it shows BOTH legs (debit + credit) per operation because both legs map to the same frontend type. This is visually confusing — user sees "+6739" and "-6739" for one exchange. Fix options: (a) filter by `rootId` dedup in the global view, (b) show only debit leg in global "兑换" filter and credit leg in "入金" filter, or (c) confirm with product whether dual-leg in global view is intentional. Wallet-level views are NOT affected because they filter by `currency`, which naturally isolates legs.

8. **Exchange sign wrong on HomeScreen/global tx list (t104043)**: `txInflow()` treats `"exchange"` as outflow (it's in `OUTFLOW_TYPES`), making `fx_credit` legs show `-` instead of `+`. The `AccountDetailScreen` has its own `accountRowInflow()` that bypasses this with `amount > 0`, but `TransactionRow` (HomeScreen, global list) uses `txInflow()`. Fix: add `if (tx.type === "exchange") return (tx.amount ?? 0) > 0;` before the OUTFLOW_TYPES check in `txInflow()`. See `references/tx-sign-determination-chain.md` pitfall #4.

9. **Fee quote vs actual mismatch across screens**: The optimistic transaction stores the `confirm` API response's `fee` (quote estimate, e.g., 0.04 USDT), while the order detail screen reads the `fx_order`'s actual executed fee (e.g., 0.01 USDT). User sees different fees on transaction details vs order details. This is inherent to optimistic updates — the fee normalizes after refresh. See `references/exchange-fee-sourcing.md` for full sourcing chain.

10. **Redundant symbol in fee display**: The `{SYMBOL} {amount} {ccy}` format produces "USDT 0.01 USDT" when SYMBOL[ccy] is the ccy code itself (e.g., SYMBOL['USDT'] = '₮' gets replaced to 'USDT'). Even for currencies with real symbols (¥, $), the format `¥ 0.50 CNY` is redundant. Fix: use `{ccy} {amount}` uniformly for fee display. This applies to both `exchangeFeeText()` in PaymentDetailScreen and optimistic `feeText` in PaymentFinishScreens.

11. **Exchange history endpoint missing fee fields**: The `ExchangeController.history()` endpoint uses a simpler SQL query than `TxAggregateQueryService`. It was missing `channel_fee_amount` and `platform_spread_amount` columns, so the history API returned no fee data. When multiple endpoints serve the same entity, audit field parity — the simpler/older endpoint is usually the one missing fields. See `references/exchange-fee-sourcing.md` for the fix pattern.

12. **Platform spread fee definition — explicit UI fee must NOT include spread (supersedes t104026 reconciliation)**: The codebase has used two interpretations of `fee`. The current product/operator correction (2026-06-02) is: **C-end displayed "兑换手续费" = explicit channel fee only**. Platform spread is already embedded in the applied rate and must stay as a separate revenue/spread field, not be added to the visible fee line.

   **Correct explicit-fee approach — Fee = channelFee only:**
   Platform spread is the platform's profit margin already embedded in `appliedRate` (user sees a worse rate than midRate). User-visible `fee` / `fee_amount` should be `channel_fee_amount` only. Quote/confirm/frontend fallback should not add `platformSpread` into the line item labelled "手续费". Showing spread as part of "手续费" double-counts/confuses because the rate already reflects it.

   **Historical wrong-for-current-product approach — Fee = channelFee + platformSpread:**
   t104026 aligned quote/confirm to `fee = channelFee + platformSpread` to match a then-observed `/transactions` mismatch. This produced symptoms like HKD 11, fixed fee 4, channel fee 0.1%, spread 0.3% → backend `channelFee=4.011`, `platformSpread=0.021`, `fee=4.032`, C-end displays HK$4.03. Per 2026-06-02 correction, the visible fee should be channel fee only (HK$4.01 after 2dp), while platform spread remains informational/accounting.

   **Fix scope when encountered:** update all surfaces simultaneously: `ExchangeController.createQuote()` / `confirmExchange()` / idempotency responses `fee=channelFee`; frontend `totalExchangeFee()` fallback and `ExchangeConfirmScreen` split fallback use `channelFee` only; keep `platformSpread` as separate field. Also check `TxAggregateQueryService`: if already using `COALESCE(f.channel_fee_amount, 0) AS fee_amount`, do not regress it back to combined fee.

   See `references/exchange-fee-sourcing.md` and `references/t104026-fee-alignment.md` as historical context, but treat this 2026-06-02 correction as the current product rule.

13. **Wallet currency filter is the natural dedup boundary**: `AccountDetailScreen` filters `transactions.filter(t => t.ccy === wallet.ccy)`. For cross-currency exchanges (CNY→USD), each wallet only sees its own leg. For edge cases like CNY→CNH (different codes, same underlying currency), the filter still works because the codes differ. The only failure case would be a literal same-currency exchange, which the frontend blocks via `sameCcy` check.

14. **Backend DTO field completeness for confirm/quote responses (t104020)**: When the frontend reads fields from a confirm/quote response (e.g., `fee`, `rate`, `feeCcy`), verify the backend DTO actually includes them. A common pattern: the `confirmExchange()` method returns a manually constructed `Map` — if a field was added to the quote response but not the confirm response, the frontend gets `undefined`. **Audit rule**: quote and confirm responses must have identical field sets. If quote returns `{fee, rate, channelFee, platformSpread, feeCcy}`, confirm must too. Check both the primary path AND the idempotency path (when the order already exists).

15. **Scientific notation in URL params for small decimals (t104045)**: `String(number)` in JavaScript produces scientific notation for very small values (`1.234e-7`). When passing exchange amounts/rates/fees as URL params (e.g., `?out=${String(amount)}`), use `toFixed(8)` instead to guarantee pure decimal format. This affects `ExchangeConfirmScreen` URL param construction and any screen that passes financial amounts via URL query strings. **Pattern**: `String(0.00000012)` → `"1.2e-7"` (broken), `(0.00000012).toFixed(8)` → `"0.00000012"` (correct).

16. **fx_debit/fx_credit description differentiation (t104052)**: When both legs of an exchange share the same frontend `type` (e.g., `"exchange"`), the backend `buildDescription()` must return distinct labels per leg. A `case "fx_debit", "fx_credit" -> "货币兑换"` produces two identical rows in the transaction list. Fix: `case "fx_debit" -> "兑出"` and `case "fx_credit" -> "兑入"`. The frontend `TransactionRow` uses `tx.description` when available (line 180-181), so the backend description is authoritative. For the non-home variant, ensure it also prefers `tx.description` over the type-based `LABEL_MAP` fallback — otherwise the list view still shows the generic type label.

## References

- `references/fx-dedup-fix.md` — Specific uvisa fx_debit/fx_credit fix walkthrough
- `references/fx-investigation-methodology.md` — Full-stack investigation pattern for FX duplicate/wrong transaction issues (4-layer checklist)
- `references/tx-sign-determination-chain.md` — `txInflow()` priority chain, direction/amount/ccy mapping for optimistic exchange transactions
- `references/exchange-fee-sourcing.md` — Fee definition (Approach B: channelFee + platformSpread), `exchangeFeeText()` formatting, USDT symbol ambiguity, endpoint field parity audit
- `references/t104026-fee-alignment.md` — Specific t104026 fix: aligning quote/confirm/transactions endpoints to use consistent fee definition
- `references/batch-exchange-fixes-t104020-t104052.md` — Batch of 6 exchange fixes: confirm DTO completeness, receive picker currency universe, scientific notation in URL params, description differentiation
