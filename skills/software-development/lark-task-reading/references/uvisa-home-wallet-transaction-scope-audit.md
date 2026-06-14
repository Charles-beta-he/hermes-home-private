---
title: UVISA Home Wallet Transaction Scope Audit
scope: "Project-scoped reference for UVISA / uvisa-app-2.0 Lark C-end transaction-display tasks only."
applicability: "Use when a UVISA Lark task mentions Home 最近交易 / 查看全部 / 钱包账户内交易记录, especially when the user narrows scope such as 仅检查 home 页面法币钱包板块."
anti_conditions: "Do not apply to unrelated projects, admin-only transaction tables, generic finance apps, or U-VISA card bill tasks unless the task explicitly includes the Home wallet-account surface."
description: Pattern for analyzing UVISA C-end Home wallet account transaction-list tasks without over-expanding into U-VISA card or global transaction surfaces.
---

# UVISA Home Wallet Transaction Scope Audit

Scope: this is a UVISA / `uvisa-app-2.0` project-scoped reference under the Lark task-reading workflow. It captures how to intake and analyze a specific class of UVISA C-end Home wallet transaction-list tasks. It is not a global transaction-ledger rule.

## Scope discipline

1. Read the Lark task by GUID and extract only the atoms matching the requested surface.
2. If the user narrows the scope to Home fiat wallets, do not analyze or implement U-VISA card bill tabs, card-only transaction pages, or global transaction history except as dependency evidence.
3. Map the visible surface before implementation:
   - `HomeScreen.tsx` fiat wallet card only links to `/account/:ccy`.
   - The actual wallet-account transaction list surface is `AccountDetailScreen.tsx`.
   - Home bottom “最近交易” uses `recentTransactions` and is a separate surface.

## Evidence path

For a Home wallet-account transaction task, inspect both FE and BE before judging compliance:

- Frontend:
  - `src/screens/home/HomeScreen.tsx` — wallet-row entry and link target.
  - `src/screens/home/AccountDetailScreen.tsx` — wallet account list, tabs, row labels, amount signs.
  - `src/services/transaction.service.ts` and `src/stores/transaction.store.ts` — query params, merge/cache behavior.
  - `src/components/transactionRowUtils.ts` / `TransactionRow.tsx` only if the task touches the generic Home recent row or shared row labeling.
- Backend:
  - `api/api-public/src/main/java/com/uvisa/api/pub/TransactionController.java` — `RECENT_ROOT_TYPES`, `DEFAULT_LIST_ROOT_TYPES`, `feTypeToRootTypes`, and `mapRootTypeToFeType`.

## Common finding: generic `/transactions?currency=` is not enough

Current-style wallet account pages often call `fetchList({ ccy })`, which becomes `GET /transactions?currency=<ccy>`. Backend default root-type whitelists may intentionally exclude `wealth_*` and `card_transfer`, so CNY wallet “全部” tasks that require fixed-wealth and U-VISA card-transfer rows cannot be satisfied by frontend filtering alone.

Do not declare the UI correct just because the current tests pass. Existing tests may encode older semantics, for example “转入 Tab includes wealth-redeem / wealth-interest”. If the Lark task says the CNY wallet 转入 tab should contain only 转入(+), the old test is now a regression fixture to update, not a truth source.

## Atom model for this task class

Split by currency family and tab:

- CNY / 全部: transfer-in, transfer-out, exchange in/out, fixed wealth buy/redeem/interest/early redeem, U-VISA card topup/withdraw.
- CNY / 转入: only transfer-in.
- CNY / 转出: only transfer-out.
- CNY / 兑换: exchange in/out.
- Non-CNY / 全部: only transfer-in, transfer-out, exchange in/out.
- Non-CNY / 转入: only transfer-in.
- Non-CNY / 转出: only transfer-out.
- Non-CNY / 兑换: exchange in/out.

## Recommended landing pattern

Prefer a backend-supported, surface-specific contract over aggregating many frontend calls when the scoped task includes CNY rows:

- Add/adjust a wallet-account transaction endpoint or query mode for the Home wallet account surface when the required rows exceed the generic `/transactions` default whitelist.
- Keep `/transactions` default semantics stable unless the task explicitly changes the global list; backend comments may document why certain root types are excluded.
- Make FE tab filters semantic, not just sign-based:
  - CNY all may include internal wealth/card rows.
  - CNY transfer-in/out tabs should not accidentally include every positive/negative internal row.
  - Non-CNY all should exclude CNY-only wealth/card rows unless product explicitly says otherwise.
- Prefer backend `description` for row title when it carries exact product wording; add targeted mapping for card-transfer signs (`U-VISA 卡充值` vs `U-VISA 卡提现`) and early redeem if backend does not already provide it.

### Narrow non-CNY-only ownership slice

If the user clarifies that CNY is being handled by another person/team and the current agent only owns “法币钱包非 CNY”:

1. Treat CNY as an explicit anti-scope. Do not change CNY fetch/query semantics, labels, or tab behavior in that slice.
2. A backend endpoint is usually not required for the non-CNY-only slice if `/transactions?currency=<non-CNY>` already returns transfer/exchange rows; the durable fix is a frontend semantic whitelist guarding against type leakage.
3. In `AccountDetailScreen.tsx`, branch on `wallet.ccy !== "CNY"` and allow only:
   - `transfer-in`
   - `transfer-out`
   - `exchange`
4. Non-CNY tabs should use explicit type checks, not generic signed amount direction:
   - all: transfer-in / transfer-out / exchange
   - in: `type === "transfer-in"`
   - out: `type === "transfer-out"`
   - swap: `type === "exchange"`
5. Within this UVISA-scoped Home wallet-account reference, non-CNY row titles should not leak backend channel-specific display labels into this surface. Applicability: only the UVISA C-end Home `/account/:ccy` wallet-account list when `wallet.ccy !== "CNY"`. Anti-condition: do not apply this to transaction detail/audit/admin surfaces, nor to the separate CNY wallet implementation path. Backend/service facts such as `rootType=inflow_hsbc`, `displayType=电汇入金`, or `displayType=电汇出金` may remain useful as detail facts, but this Home non-CNY surface should render product-level frontend i18n labels:
   - `transfer-in` → frontend i18n `tx.deposit` (`转入` in zh)
   - `transfer-out` → frontend i18n `tx.withdraw` (`转出` in zh)
   - `exchange` → amount-sign-aware `tx.exchangeIn` / `tx.exchangeOut` (`兑入` / `兑出`)
   Pass wallet/surface context into the title helper (for example `txDisplayTitle(tx, inflow, wallet.ccy, t)`) so the override remains scoped.
6. Keep CNY on the existing path until its owner lands the separate CNY contract, even if the old CNY path is imperfect.
7. Replace stale USD/non-CNY tests that expect `wealth-*` positive/negative rows in 转入/转出 tabs with RED tests proving `wealth-*`, `card-*`, and `admin_adjust`-like rows cannot pollute non-CNY wallet tabs.
8. Add a RED regression where a non-CNY `transfer-in` row carries `rootType: 'inflow_hsbc'` and `displayType: '电汇入金'`; it must render `转入`, not `电汇入金`. Add the symmetric `transfer-out` / `电汇出金` check. This catches the common “backend Chinese displayType bypasses frontend i18n/product wording” regression.

## Partial-implementation triage pattern

Scope: UVISA `uvisa-app-2.0` C-end Home wallet-account Lark tasks only. Applicability: when a pasted Lark task URL or screenshot suggests an existing PR/commit may have partially handled Home non-CNY wallet transaction rows. Anti-condition: do not apply this rule to admin tables, card-bill pages, generic transaction detail pages, or unrelated apps.

When a later session finds an existing PR/commit for this task class, do not classify the task as done from the PR title alone. Re-read the Lark task and comments, inspect the current diff/tests, and compare visible screenshots against every acceptance atom.

Common delta after a partial non-CNY wallet fix:

- A PR may already restrict non-CNY wallet account rows to `transfer-in` / `transfer-out` / `exchange` and pass tab-filter tests.
- The remaining UI bug can be row wording: backend/service `displayType` such as `电汇入金` / `电汇出金` still bypasses product-level wallet labels. On the Home non-CNY `/account/:ccy` surface, transfer rows should render `转入` / `转出`; exchange rows should still render `兑入` / `兑出` by amount sign.
- Treat this as `PARTIAL` / targeted delta, not a restart. Add RED tests for channel-specific `displayType` leakage before patching `txDisplayTitle` with wallet/surface context.
- If Lark comments contain only `[Image]` placeholders and native attachments are empty, use user-provided screenshots as triage evidence but require fresh online UI screenshots as native Lark attachments before final closeout.

## Closeout proof

A valid audit/implementation closeout should include:

1. Lark GUID and exact scoped atoms used.
2. FE surface mapping: Home wallet row → `/account/:ccy`.
3. Backend whitelist evidence for root types included/excluded.
4. Updated tests for CNY and non-CNY tab filtering, replacing stale tests that encoded old semantics.
5. Local targeted tests plus build if code changed.
6. For partial/stale Lark tasks, PR/commit evidence must be atom-matched; a merged PR title is not enough if screenshot/text evidence still shows a remaining atom gap.
