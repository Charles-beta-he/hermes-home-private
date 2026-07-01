# UVISA C端资金保护期本地状态闭环

Scope: UVISA C端 Lark tasks where `fundProtectionFrom` / `fundProtectionUntil` or a local `protectionUntil` fallback blocks payout/remit/withdrawal even though backend `/api/me` says the fund-protection window has been reset or lifted.

Applicability:
- Symptoms mention reset fund-protection period, payout/remit still blocked in App, web works, reinstall fixes it, or About → clear cache does not help.
- The task touches external outflow gates: payout, remittance, or payment PIN verification before outflow.

Anti-conditions:
- Do not use this for wealth product lockup, card fixed-deposit lockup, payment-PIN account lockout, OTP rate limits, or backend risk-policy enforcement unless the task explicitly names fund protection.
- Do not solve by deleting the protection UI/route or by ignoring backend `FUND_PROTECTION_ACTIVE`; the backend remains authoritative.

## Procedure

1. Read the live Lark task and preserve API evidence:
   - `/api/me` payload status for `fundProtectionFrom` / `fundProtectionUntil`.
   - Any comment image or curl evidence. If Lark only returns `[Image]`, classify it as a Lark API evidence gap, not absence of screenshot evidence.

2. Classify as cross-cutting state-source bug, not a point fix:
   - The source of truth is backend `/api/me`.
   - Zustand/session fallback (`auth-store.protectionUntil`) is only an optimistic bridge after sensitive in-app changes.
   - Any route that gates payout/remit from local state must refresh profile before enforcing the local fallback.

3. Implement globally in auth state:
   - Add/verify a helper that derives `protectionUntil` from `user.fundProtectionUntil` and returns `null` when backend field is absent, invalid, or expired.
   - On login-token consumption and `fetchProfile()`, set both `user` and local `protectionUntil` from the normalized profile.
   - When fresh `/api/me` says `fundProtectionUntil: null`, clear local stale `protectionUntil` so reinstall is not required.

4. Harden outflow gates:
   - Before PIN verification for protected outflow destinations (`/payout/*`, remit timeline/pay/finish surfaces), call `fetchProfile()` and wait for it to settle before redirecting to `/protection` based on local `protectionUntil`.
   - Keep backend submit error handling for `FUND_PROTECTION_ACTIVE` as a second-line guard; it should still route to `/protection` when the backend actively rejects.

5. Fix clear-cache semantics if task mentions About → 清除缓存:
   - Clear session-scoped app state (at minimum `sessionStorage.clear()` or exact persisted app-state keys) before unregistering Service Worker / deleting Cache Storage / reload.
   - Update copy so “清除缓存” honestly says it clears app-local state, not only SW/cache files.

6. Tests:
   - Auth store: stale local protection is cleared when fresh profile says lifted.
   - Auth store: active backend profile window syncs to local fallback.
   - Clear cache: clears session-scoped persisted app state before reload.
   - Existing payment verify / outflow route tests still pass.
   - Run targeted Vitest plus `pnpm run build`.

## Pitfalls

- Reinstall fixing the issue strongly indicates persisted frontend state, but the durable fix is still to make backend `/api/me` authoritative and refresh before protected outflow gates.
- Do not keep `protectionUntil` in persisted state without a profile refresh path that can clear it; stale persisted future timestamps will repeatedly block PIN/outflow screens.
- Do not rely on About → clear cache if it only deletes Cache Storage and unregisters Service Worker; Zustand persisted snapshots can live in session/local storage outside HTTP caches.
- If backend `/api/me` is already correct, avoid backend changes unless submit APIs still return `FUND_PROTECTION_ACTIVE` after profile proof.
