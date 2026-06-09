# UVISA FX Exchange Fee Architecture

## Overview

UVISA currency exchange (CNY ↔ USDT) uses a dual-fee model: **channel fee** (explicit, displayed) and **platform spread** (implicit, embedded in rate). This reference documents the full flow, known bugs, and debugging checklist.

## Exchange Flow

### 1. Quote Phase (`POST /api/exchange/quote`)

**Controller:** `ExchangeController.createQuote()` (api-public)

Fee calculation:
```
channelFeeFixedAmt  = pair.getFeeFixed()                    // 固定费
channelFeePercentRate = pair.getChannelFeePct()             // 百分比费率
channelFeePercentAmt  = amountIn × channelFeePercentRate    // 百分比费额
channelFeeAmt         = channelFeeFixedAmt + channelFeePercentAmt  // 合计通道费

spreadBase        = amountIn - channelFeeAmt                // 扣费后本金
platformSpreadAmt = spreadBase × platform_spread_pct%       // 汇率加点收益（隐性）

effectiveIn = amountIn - channelFeeAmt                      // 实际换汇本金
amountOut   = effectiveIn × appliedRate                     // 到账金额（扣费后计算）
```

**Critical branching (line 250-252):**
```java
BigDecimal amountOut = pairOpt.isPresent()
    ? effectiveIn.multiply(appliedRate)   // 有 pair → 从扣费后金额计算
    : amountIn.multiply(appliedRate);     // 无 pair → 从未扣费金额计算（BUG 源头）
```

### 2. Confirm Phase (`POST /api/exchange/confirm`)

**Controller:** `ExchangeController.confirmExchange()` (api-public)

- Reads quote from `fx_quote` table (all fields: amount_in, amount_out, channel_fee_amount, etc.)
- Validates: used flag, expiry (2s safety buffer), balance, large-amount MFA
- Submits to GSalary upstream (if gsalaryQuoteId exists)
- Creates 4-entry ledger journal:
  - DEBIT user wallet: `amountIn` (full amount)
  - CREDIT equity.fee.fx: `channelFeeAmt` (fee portion, only if > 0)
  - CREDIT FX bridge: `effectiveIn` (amountIn - fee)
  - DEBIT FX bridge toCcy: `amountOut`
  - CREDIT user wallet toCcy: `amountOut`

**Response shape (line 578-587):**
```json
{
  "journalId": "...",
  "status": "COMPLETED",
  "fromCcy": "CNY",
  "toCcy": "USDT",
  "amountIn": "106.91",
  "amountOut": "15.74",
  "gsalaryOrderId": "..."
  // ❌ NO fee / channelFee fields in response
}
```

### 3. Frontend Display

**ExchangeConfirmScreen:**
- Calculates `feeInFromCcy` from quote data: `amountIn - (amountOut / settlementRate)`
- Passes as URL param `fee` to finish screen

**ExchangeFinishScreen:**
- Reads `feeParam` from URL params
- After execute, checks `res.data.fee ?? res.data.channelFee` → both undefined
- Falls back to `feeParam` from URL

## Known Bug Pattern: Fee Displayed But Not Deducted

**Symptom:** Order details show fee (e.g., ¥0.02) but `amountOut = amountIn × rate` (fee not deducted)

**Math verification:**
- If fee deducted: `(amountIn - fee) × rate = amountOut` → amountOut < amountIn × rate
- If fee NOT deducted: `amountIn × rate = amountOut` → matches exactly

**Root cause chain:**
1. `pairOpt.isPresent()` returns false → `amountOut` calculated from `amountIn` (not `effectiveIn`)
2. `channelFeeAmt` is still calculated and returned in quote response
3. Frontend displays the fee, but actual `amountOut` didn't have fee deducted
4. `confirmExchange` response omits `fee` field → frontend can't verify

**Fix options:**
- **Backend (recommended):** Ensure `amountOut` always uses `effectiveIn`; add `fee`/`feeCcy` to confirm response
- **Frontend (temporary):** Recalculate fee from `amountIn - (amountOut / rate)`

## Known Bug Pattern: Precision Masking (t104020, 2026-05)

**Symptom:** Fee IS correctly deducted from `amountOut`, but the displayed rate (4dp) and `amountOut` (2dp) make it look like fee was NOT deducted.

**Example (real case):**
```
兑出:     ¥106.91 CNY
兑入:     ₮15.74  USDT        (2dp display)
成交汇率: 1 CNY = 0.1472 USDT  (4dp display)
手续费:   ¥0.02   CNY

User checks: 106.91 × 0.1472 = 15.737 → rounds to 15.74  ← looks like no fee deducted!
Actual calc: 106.89 × 0.14724 = 15.738 → rounds to 15.74  ← fee WAS deducted, same result!
```

**Root cause:** The displayed rate has only 4dp precision. The actual `appliedRate` has 8dp. When `(amountIn - fee) × actualRate` and `amountIn × displayedRate` both round to the same 2dp `amountOut`, the fee deduction becomes **invisible to the user**.

**Key insight:** This is NOT a backend bug — the fee IS deducted. It's a **display precision problem** that makes the order detail page unverifiable.

**Distinguishing from real fee-not-deducted bug:**
- Precision masking: `amountOut` from backend = `(amountIn - fee) × appliedRate_8dp` → both check equations pass at display precision
- Real bug: `amountOut` from backend = `amountIn × appliedRate` → exact match, fee never deducted

**Fix:** Add "实际兑换金额" (effective conversion amount = amountIn - fee) row to order detail, OR show rate at 6dp instead of 4dp. Backend confirm response should also include `fee`/`feeCcy`/`rate` fields for authoritative values.

## Debugging Checklist

When fee display is wrong:
1. Check `pairOpt.isPresent()` in createQuote — is the pair configured?
2. Verify `amountOut` formula: should be `effectiveIn × rate`, not `amountIn × rate`
3. Check confirm response for `fee`/`channelFee` fields (currently missing)
4. Compare frontend `feeParam` (URL) vs `executedFee` (response) — if response has no fee, frontend uses stale URL param
5. **Precision-aware math check (critical):**
   - Get the `appliedRate` at full 8dp precision (from DB `fx_quote` or backend log), NOT from the 4dp display
   - Compute: `(amountIn - fee) × appliedRate_8dp` → should equal backend's `amountOut`
   - Compute: `amountIn × appliedRate_8dp` → should NOT equal backend's `amountOut` (if fee > 0)
   - If both round to the same 2dp value, you have **precision masking**, not a fee-deduction bug
6. **Check both exchange methods:** `createQuote()` AND `confirmExternalExchange()` share the same `pairOpt.isPresent()` branching

## Key Files

| File | Role |
|------|------|
| `api/api-public/.../ExchangeController.java` | Quote + Confirm logic (lines 126-590); `confirmExternalExchange()` shares same `pairOpt` branching |
| `domain/fx/.../FxOrder.java` | Order entity (fee/spread fields) |
| `domain/fx/.../FxPair.java` | Pair config (feeFixed, channelFeePct, platformSpreadPct) |
| `uvisa-app-2.0/src/screens/exchange/ExchangeConfirmScreen.tsx` | Fee calculation + URL param |
| `uvisa-app-2.0/src/screens/exchange/ExchangeFinishScreen.tsx` | Fee display + execute response handling |

## Related References

- `references/uvisa-payout-fee-display.md` — Payout screen fee display patterns (similar architecture)
- `references/uvisa-currency-architecture.md` — Currency data flow (exchange picker, FIAT-only rule)
