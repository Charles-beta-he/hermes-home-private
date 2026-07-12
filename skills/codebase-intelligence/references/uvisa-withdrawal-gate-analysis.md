# UVISA withdrawal gate analysis

Use this scoped reference when asked how the C-side/user app decides whether withdrawal is forbidden/disabled. Re-verify current code before making product claims.

Applicability:
- UVISA 2.0 frontend repo: `src/screens/card`, `src/screens/payout`, `src/services/card.service.ts`.
- UVISA backend repo: `api/api-public/src/main/java/com/uvisa/api/pub/CardController.java`.
- Questions about C-side card withdrawal, CNY wallet payout, crypto payout, or frontend/backend gate alignment.

Anti-conditions:
- Do not apply to admin withdrawal approval/risk review without inspecting admin/backend payout services.
- Do not treat frontend disabled state as authority; backend status/PIN/limit/balance checks remain authoritative.
- Do not infer product semantics from stale local comments alone; read current controller/service code.

## Fast trace checklist

1. Determine which withdrawal surface the user means:
   - U-VISA card withdrawal: `/card/withdraw` → `CardWithdrawScreen.tsx`.
   - CNY wallet payout: `/payout/cny` → `PayoutCnyScreen.tsx`.
   - Crypto payout: `/payout/:asset` or legacy `/payout/usdt` → `PayoutCryptoScreen.tsx` / `PayoutUsdtScreen.tsx`.
2. Read the entry screen and service normalization before answering:
   - `card.service.ts` maps backend `ACTIVE/FROZEN/CANCELLED` to frontend `normal/frozen/none`; preserves `rawStatus`.
   - `CardScreen.tsx` computes effective status and disables card topup/withdraw actions when frozen/freezing.
3. For card withdrawal, inspect `CardWithdrawScreen.tsx`:
   - `frozen = card?.status === "frozen"`.
   - Withdrawable cap = card ledger balance + flexible/daily wealth holdings; fixed holdings are locked and excluded.
   - Limits come from `cardService.getGlobalLimits('WITHDRAW')` → `/api/cards/limits/global?direction=WITHDRAW`.
   - CTA disabled when `valid` is false: frozen, below min, above card+flex balance, or above single max.
   - Cent-quantized comparisons are intentional to avoid float-boundary false insufficiency.
4. For CNY payout, inspect `PayoutCnyScreen.tsx`:
   - Domestic transfer gate via `useDomesticCnyTransferGate()` / platform config (`domesticCnyTransferEnabled`).
   - Bound bank card last4 must exist.
   - Amount must satisfy min/max/balance.
   - Dynamic payout preview must succeed (`feeState.status === "ok"`) before CTA enables.
5. For crypto payout, inspect `PayoutCryptoScreen.tsx`:
   - Network config from backend is authoritative for min amount; fallback only preserves network choices.
   - CTA requires positive amount, optional min satisfied, amount <= balance, and address valid for network.
   - Legacy `PayoutUsdtScreen.tsx` hardcodes `num >= 50` and EVM address regex; verify whether route still points there.
6. Backend authority check for card withdrawal:
   - `POST /api/cards/{id}/withdraw` in `CardController` requires card status `ACTIVE`.
   - Payment PIN is verified server-side.
   - USD-equivalent cap, GSalary card readiness, GSalary balance modify, ledger journal, and active flexible holdings shortfall checks happen backend-side.
   - Insufficient card+active flexible principal becomes `INSUFFICIENT_BALANCE`.

## Reporting shape

When answering, separate:
- Frontend pre-disable rules (what blocks the button/navigation).
- Backend definitive rejection rules (what rejects even if frontend is bypassed).
- Surface-specific differences (card vs CNY payout vs crypto payout).
- Evidence paths and line anchors from current reads.
