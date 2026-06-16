# UVISA wallet account transaction scope from Lark comments

Applicability: UVISA 2.0 C-side home wallet account transaction lists (`/account/:ccy`) when a Lark task/comment asks to classify wallet rows by CNY vs non-CNY and by tabs 全部/转入/转出/兑换. This is a scoped UVISA product reference, not a global wallet/accounting rule.

Anti-conditions:
- Do not apply to global `/transactions` default list, home recent transactions, card transaction detail pages, or admin wallet ledgers unless the task explicitly names those surfaces.
- Do not treat this as permission to include platform/internal rows such as `admin_adjust`, `platform_fee_*`, advisor commissions, or wealth pool topups.
- If a newer PRD/prototype/live Lark comment conflicts, use the project profile source-weighting policy and record the conflict.

## Acceptance matrix

### Home → CNY wallet account → 全部

Show:
- 转入 `+` (wallet account inflow)
- 转出 `−` (wallet account outflow)
- 兑入 `+`
- 兑出 `−`
- 定期申购 `−`
- 定期赎回 `+`
- 定期理财派息 `+`
- U-VISA 卡充值 `−` (wallet funds move into card)
- U-VISA 卡提现 `+` (card funds return to wallet)
- 提前赎回 `+` for fixed-term wealth only; flexible wealth has no early redeem row

### Home → CNY wallet account → 转入

Show only:
- 转入 `+`

### Home → CNY wallet account → 转出

Show only:
- 转出 `−`

### Home → CNY wallet account → 兑换

Show only:
- 兑入 `+`
- 兑出 `−`

### Home → non-CNY wallet account → 全部

Show only:
- 转入 `+`
- 转出 `−`
- 兑入 `+`
- 兑出 `−`

### Home → non-CNY wallet account → 转入 / 转出 / 兑换

- 转入 tab: 转入 `+`
- 转出 tab: 转出 `−`
- 兑换 tab: 兑入 `+`, 兑出 `−`

## Implementation notes

- **Recommended split:** backend should only provide the CNY wallet-account query set; frontend should own this comment's wallet-account display labels, signs, and tab filtering. Do not push comment-specific wording into backend `description` or global transaction type mapping.
- CNY wallet account list needs a scoped backend contract such as `scope=wallet-account` so the backend can include wallet, FX, wealth, and `card_transfer` roots without broadening the global transactions/default/recent list.
- The CNY scoped root set should include wallet inflow roots, `outflow`, `fx_debit`, `fx_credit`, `wealth_buy`, `wealth_redeem`, `wealth_interest`, and `card_transfer`; exclude `admin_adjust` and `card_spend` unless a newer task explicitly changes the surface.
- Keep backend generic transaction semantics stable: backend `buildDescription()` may remain generic (e.g. 卡转入/卡转出, 理财申购/赎回), and backend/global normalization does not need to adopt the home-wallet comment wording.
- Direction tabs should filter by explicit business type, not by generic amount sign. Wealth and card-transfer rows belong in CNY 全部 only, not CNY 转入/转出.
- Exchange labels are per-wallet ledger-leg labels: amount/sign relative to the current wallet decides 兑入 vs 兑出; do not display generic 兑换 on account rows.
- For CNY wallet **UI display only**, `card_transfer` sign is from the wallet perspective: negative amount is U-VISA 卡充值 / `card-topup`; positive amount is U-VISA 卡提现 / `card-withdraw`. Implement this in the account-page UI mapper from `rootType + amount`, so it still works if the backend/global `type` remains generic/legacy.
- For CNY wallet display labels, prefer the comment wording over backend generic labels: 定期申购, 定期赎回, 定期理财派息, 提前赎回, U-VISA 卡充值, U-VISA 卡提现.
- Preserve `wealthTxnType` (or equivalent backend subtype) through FE normalization so `EARLY_REDEEM` can render as 提前赎回.

## Verification checklist

- Unit test CNY 全部 includes all listed row classes and excludes system adjustments.
- Unit test CNY 转入/转出/兑换 are strict and do not admit wealth/card-transfer rows.
- Unit test non-CNY 全部/方向/兑换 remain limited to transfer-in, transfer-out, exchange.
- Unit test the account-page UI mapper with backend-generic `card_transfer` rows: negative amount renders `U-VISA 卡充值` with `−`; positive amount renders `U-VISA 卡提现` with `+`, even if backend `type/displayType` use generic labels.
- Unit test backend only for the scoped root-type set and explicit type precedence; do not require backend to emit comment-specific labels.
- Build/typecheck the frontend and run a Java/JUnit or at least scoped javac check for backend scope changes.
