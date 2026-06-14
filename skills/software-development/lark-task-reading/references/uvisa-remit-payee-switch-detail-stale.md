# UVISA remittance amount-page payee switch detail stale data

Scope: UVISA C-end remittance amount page bugs where the user reports that after tapping the in-page `切换` button and choosing another payee, tapping `详情` still shows the previous payee's detail.

Session-derived pitfall:
- Do not assume a commit that fixes `PayeeViewScreen` (`/remit/payees/:id/view`) covers the amount-page embedded detail sheet.
- The screenshot surface is `RemitAmountScreen` (`/remit/:payeeId/amount`), specifically the top `PayeeBar` with `切换` and inline `详情`.
- In the unified flow (`/remit/new/amount?ccy=...`), switching payees may only call `setPayee(p)` without changing the route `payeeId`; effects keyed only on route params will not run.

Root-cause checklist:
1. Open `src/screens/remit/RemitAmountScreen.tsx`, not only `PayeeViewScreen.tsx`.
2. Inspect `PayeeBar` wiring:
   - `onSwitch={() => isNew ? setPicker("payee") : nav("/remit")}`
   - payee picker item click often does `setPayee(p); setPicker(null);`
3. Inspect embedded detail state. A stale bug exists if detail state stores only status/data, e.g. `status: "ok", data`, without the owning `payee.id`.
4. Inspect `openDetailSheet`. A stale bug exists if it only checks `detailState.status !== "ok"`; old payee detail with `status === "ok"` will suppress a new fetch.
5. Inspect render handoff to `PayeeDetailRows`. It must only pass detail/loading/error when the state `id` equals current `payee.id`.

Safe fix pattern:
- Bind detail state to payee id:
  - `loading`: `{ status: "loading", id }`
  - `ok`: `{ status: "ok", id, data }`
  - `error`: `{ status: "error", id, message }`
- Derive `currentPayeeId = payee?.id ?? ""` and `detailPayeeId = detailState.status === "idle" ? "" : detailState.id`.
- Fetch when `currentPayeeId` changes and no current-id detail is already loading/ok/error.
- In `openDetailSheet`, reuse cached detail only when `detailPayeeId === currentPayeeId`; otherwise call `fetchPayeeDetail(currentPayeeId)`.
- Render with id guard:
  - `detail={detailState.status === "ok" && detailState.id === payee.id ? detailState.data : null}`
  - same id guard for loading/error.

TDD regression shape:
1. Seed two wallet payees, e.g. `Mill` and `自己`.
2. Mock `remitService.getPayee(id)` to return distinct account/realName values for each id.
3. Render `/remit/new/amount?ccy=USD`.
4. Select `Mill`, tap inline `详情`, assert `ROLA MILL` is shown.
5. Close sheet, tap `切换`, select `自己`, tap inline `详情`.
6. Assert `getPayee('wallet-self')` was called, `SELF USER` is shown, and old `ROLA MILL` / old account are absent.

Verification commands used successfully:
```bash
pnpm exec vitest run src/screens/remit/__tests__/RemitSwiftFee.test.tsx
pnpm exec eslint src/screens/remit/__tests__/RemitSwiftFee.test.tsx
pnpm run build
 git diff --check -- src/screens/remit/RemitAmountScreen.tsx src/screens/remit/__tests__/RemitSwiftFee.test.tsx
```

Notes:
- Project full scoped eslint on `RemitAmountScreen.tsx` may surface pre-existing React compiler/hook lint debt unrelated to this fix. Do not treat old lint debt as proof the stale-detail fix failed; rely on targeted regression + build + diff check unless the new change introduces a new lint error.
- This is a target-surface lesson: map screenshot UI to route/component before claiming an existing commit covers the task.
