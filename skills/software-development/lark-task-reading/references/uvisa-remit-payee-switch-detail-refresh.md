# UVISA remit payee switch detail-refresh pitfall

Scope: UVISA C-end remittance amount flow tasks where the requirement says that switching the recipient from the visible `切换` button must refresh the currently selected payee's authoritative details.

## Durable lesson

Do not assume a fix in `PayeeViewScreen` covers the remittance amount screen. The visible `切换` button on the screenshot-style amount page belongs to `RemitAmountScreen` / `PayeeBar`, not `PayeeViewScreen`.

Relevant surfaces:

- `src/screens/remit/PayeeViewScreen.tsx`: `/remit/payees/:id/view` standalone payee detail page.
- `src/screens/remit/RemitAmountScreen.tsx`: `/remit/:payeeId/amount`, including the top payee bar, `详情`, and `切换` button.
- `src/screens/remit/RemitPayeeScreen.tsx`: `/remit` payee picker route used by some switch paths.

## Audit checklist

When auditing or fixing this class of task:

1. Locate the exact UI control from the screenshot/text. For the top-card `切换` button, inspect `RemitAmountScreen` and `PayeeBar` first.
2. Distinguish the two routing modes:
   - `/remit/:payeeId/amount`: route id changes can trigger `useEffect(... [payeeId])`.
   - `/remit/new/amount?ccy=...`: `payeeId === "new"`; selecting another payee often only calls `setPayee(p)` and will not trigger effects keyed only on URL `payeeId`.
3. Search for `getPayee` and verify it is called on the state transition that the user actually described: switching selected payee, not only opening a standalone detail page.
4. Ensure detail state is bound to the payee id. A bare `detailState.status === "ok"` check can reuse stale detail from the previous payee.
5. If the main amount page displays payment method/account from local `payeeStore`, decide whether the requirement requires only the detail sheet to refresh or also the top-card/payment-method rows to use authoritative detail data.

## Safe implementation pattern

Use id-bound detail state:

```ts
type DetailState =
  | { status: "idle" }
  | { status: "loading"; id: string }
  | { status: "ok"; id: string; data: PayeeDetailDto }
  | { status: "error"; id: string; message?: string };
```

Trigger the detail fetch from the selected payee, not only from the URL param:

```tsx
useEffect(() => {
  if (!payee?.id) {
    setDetailState({ status: "idle" });
    return;
  }
  void fetchPayeeDetail(payee.id);
}, [payee?.id, fetchPayeeDetail]);
```

When opening the detail sheet, require the cached detail to match the current payee:

```tsx
const hasCurrentDetail =
  detailState.status === "ok" && detailState.id === payee.id;

if (!hasCurrentDetail) void fetchPayeeDetail(payee.id);
```

## Regression tests to add

At minimum, add tests for `RemitAmountScreen` that prove:

- clicking the top `切换` button opens recipient selection;
- selecting a different payee in `/remit/new/amount?ccy=...` calls `remitService.getPayee(newId)`;
- opening `详情` after switching uses the new payee's detail, not the old detail;
- stale/slow response from the previous payee cannot overwrite the new payee's detail.

## Closeout evidence

For Lark closeout, report this as an amount-flow fix, not a standalone payee-detail-page fix. Evidence should name `RemitAmountScreen` / top `切换` flow and include targeted test output plus, when UI acceptance is required, a screenshot or browser proof of the exact amount page route and switch flow.