# UVISA non-CNY wallet transaction closeout pattern

Scope: UVISA C-end frontend tasks only, specifically wallet-account transaction-list work under `首页 > 法币钱包区域 > 非 CNY 钱包账户内交易记录` in `uvisa-app-2.0` / `uvisa-app`.

Applicability: use when a Lark task asks which transaction records and display labels should appear inside non-CNY fiat wallet account pages or their tabs.

Anti-condition: do not apply this rule to CNY wallet pages, card bill pages, wealth pages, home recent-transactions modules, backend ledger semantics, or other products unless a task explicitly says their acceptance should match this surface.

## Durable lesson

Do not treat frontend-normalized `tx.type` as the product scope source of truth for non-CNY wallet account lists. Backend/service normalization can turn records that are not product wallet flows into `transfer-in` / `transfer-out`, especially:

- `rootType=admin_adjust` normalized as `transfer-in` / `transfer-out`.
- Legacy/system rows whose `displayType` / description is `系统调账` / `系统入账` / `系统扣款`.
- Card and wealth rows that share the same currency and amount direction.

For this scoped surface, product scope should be an explicit allowlist:

- transfer-in: `inflow_hsbc`, `inflow_cobo`, `inflow_debit`
- transfer-out: `outflow`
- exchange: `fx`, `fx_debit`, `fx_credit`

Then add an explicit exclude guard for admin/system adjustment markers before any fallback compatibility path:

- `rootType === admin_adjust`
- display labels/descriptions equivalent to `系统调账`, `系统入账`, `系统扣款`

Display title should be product-level, not backend-channel-level, on this surface:

- transfer-in -> `转入`
- transfer-out -> `转出`
- exchange -> `兑入` / `兑出` by amount sign

## Verification recipe

1. Add regression fixtures for both classes:
   - normal rootType allowlisted rows for in/out/exchange.
   - `admin_adjust` rows with positive/negative amounts.
   - legacy adjustment row missing rootType but carrying system display text.
2. Assert non-CNY tabs:
   - 全部: only allowed product rows, no system/card/wealth rows.
   - 转入: only allowed transfer-in rows.
   - 转出: only allowed `outflow` rows; if no real outflow exists it must show empty state, not a system adjustment.
   - 兑换: only `fx*` rows, rendered as `兑入` / `兑出`.
3. Build and deploy the actual frontend service that backs the public URL. For Railway-backed UVISA app environments, confirm which environment serves the URL by checking the deployed asset hash from `index.html`; a successful deploy to another environment is not proof.
4. In browser verification, capture both DOM/tab assertions and the `/api/transactions?currency=<CCY>` response. A strong proof is: backend still returns `rootType=admin_adjust` for the currency, but the account page tabs do not render it.
5. For final Lark closeout, attach native screenshots to the Lark task; local screenshot paths or text-only evidence are not enough.

## Railway/public URL pitfall

A Railway service may have multiple environments while the public domain name can be misleading. Do not infer environment from the hostname. After deployment, fetch `index.html` and verify the `assets/index-*.js` hash matches the build logs for the environment you deployed. If not, deploy the same commit/message to the environment that actually serves the public URL, then rerun online UI proof.

## Lark native attachment closeout

Use Task attachment upload, not local paths in comments:

- `POST /task/v2/attachments/upload`
- multipart fields: `resource_type=task`, `resource_id=<task_guid>`, file field `file`
- verify via `GET /task/v2/attachments?resource_type=task&resource_id=<task_guid>`

Then run `lark_task_closeout_guard.py --phase online-ui-retest` with target-bound atoms/proofs before `PATCH /task/v2/tasks/{guid}` with wrapped `task` object and `update_fields`.