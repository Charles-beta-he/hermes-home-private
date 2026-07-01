# UVISA wallet transaction screenshot → backend contract tracing

Use when a UVISA wallet / transaction-list screenshot shows unexpected rows, missing rows, wrong transaction title, sign, status, or tab filtering and the user asks what backend change corresponds to it.

## Applicability

- UVISA C-side wallet/account pages backed by `GET /api/transactions` or `/api/transactions/recent`.
- Screenshots with transaction row evidence such as title, amount sign, status badge, internal badge, time, or filter tab.
- Backend changes in `TransactionController`, `TxAggregateQueryService`, rootType/type mapping, or frontend `transaction.service.ts` normalization.

Anti-conditions:

- Do not treat screenshot text alone as backend truth; it may be frontend `displayType` mapping rather than backend `description`.
- Do not assume a new backend scope is wired until the frontend call site is verified to send that param.
- Do not certify with Maven/test output if repo-local unrelated compile blockers prevent targeted tests; report the blocker separately from the semantic diff.

## Fast trace checklist

1. Extract visible screenshot fields:
   - page currency/title and selected tab;
   - row title;
   - amount sign and currency;
   - status badge;
   - extra badges such as `内部`;
   - timestamp.
2. Inspect backend diff around `TransactionController.list`:
   - request params (`currency`, `type`, `scope`, `page`, `size`);
   - default rootType whitelist;
   - any page/scope-specific whitelist;
   - `mapRootTypeToFeType` and `buildDescription`.
3. Map row title through frontend normalization before calling it a backend label:
   - `card_transfer` + negative amount → backend type `card-withdraw`;
   - frontend display text may become `卡余额返还`, even if backend description says `卡转出`.
4. Compare whitelist against all visible screenshot rows, not only the highlighted row:
   - if a new wallet scope includes `card_transfer` but excludes `admin_adjust`, a screenshot showing both `卡余额返还` and `系统调账` cannot be fully explained by that scope alone.
   - if default list includes `admin_adjust` but excludes `card_transfer`, it explains `系统调账` but not `卡余额返还`.
5. Verify frontend request construction:
   - service method forwards arbitrary params such as `scope` only if call sites pass it;
   - search for `scope: 'wallet-account'` / `wallet-account` / target page `transactionService.list(...)` usage.
6. Compare branch families before blaming a missing patch:
   - fetch both backend and frontend repos before conclusions;
   - compare `origin/<target>..origin/<source>` for the exact backend contract files (`TransactionController`, focused tests, `TxAggregateQueryService`) and the frontend call/normalization files (`AccountDetailScreen`, `transaction.service`, transaction store);
   - use key-string checks (`scope=wallet-account`, `CNY_WALLET_ACCOUNT_ROOT_TYPES`, `resolveRootTypes`) as semantic evidence only after confirming the files have no two-dot diff between branches.
7. Separate code branch truth from runtime/page truth:
   - if both branches contain the scope patch but the screenshot still shows a row that current code should filter (for example `系统调账` / `admin_adjust` on CNY wallet account), classify it as a runtime mismatch rather than a main-vs-test code diff;
   - next evidence should be Network response/request: missing `scope=wallet-account` means old frontend bundle/call path; present scope plus returned `admin_adjust` means old backend deployment or wrong service; response without `admin_adjust` but UI still shows it means store/session/PWA cache stale data.
8. Verification:
   - run focused backend test when compile graph is healthy;
   - if compile fails on unrelated duplicate/missing classes, state semantic conclusion + compile blocker separately;
   - add/expect a unit test for explicit type precedence over page scope.

## Reporting shape

- Start with the concrete backend change in one sentence.
- Then list: changed endpoint/param, added rootType set, how highlighted row maps, branch comparison result, mismatches against other visible rows, and verification result.
- When runtime output contradicts branch code, report the split explicitly: branch code state, deployed/runtime request evidence needed, and cache/store possibilities.
- Separate unrelated diffs such as release manifest security config from the screenshot-relevant transaction change.
