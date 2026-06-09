# Financial Field Authority Pattern

## Problem: Client-Side Reverse-Calculation of Fees/Rates

When a backend endpoint computes derived financial values (fee, applied rate, net amount) but only returns the transaction ID and status, the frontend must reverse-calculate these from inputs and display values. This causes precision mismatches.

### UVISA Exchange Confirm Case (2026-05-30)

**Symptom:** Fee deduction invisible to users in exchange confirmation screen.

**Root cause chain:**
1. `ExchangeController.confirmExchange()` returned only `txId`, `rootId`, `status`, `converted` (amountOut), `journalId`
2. Frontend `ExchangeFinishScreen` had to reverse-calculate fee: `fee = amountIn - (amountOut / rate)`
3. Display rate was rounded to 4dp (e.g., `0.1472`) while backend used 8dp (e.g., `0.14724000`)
4. `106.91 - (15.74 / 0.1472) = 0.02` but `106.91 - (15.74 / 0.14724) = 0.00` — fee appeared to vanish

**Fix (backend):** Return `channelFeeAmt` as `fee`, `feeCcy` (fromCcy), and `appliedRate` as `rate` in the confirm response. Frontend already mapped these fields with `!= null` guards.

**Files changed:**
- `api/api-public/src/main/java/com/uvisa/api/pub/ExchangeController.java`
  - Primary response path (line ~589): added `.put("fee", channelFeeAmt).put("feeCcy", fromCcy).put("rate", appliedRate)`
  - Idempotency return path (line ~404): expanded SQL to select `channel_fee_amount` + `rate`, added same fields to response

**Frontend already compatible:** `exchange.service.ts` lines 112-116 map `fee`, `rate`, `feeCcy`, `appliedRate`, `channelFee`. `ExchangeFinishScreen` lines 863-866 prefer backend values over URL params.

### General Pattern

**Anti-pattern:** Backend mutation returns only ID + status for financial operations.

**Correct pattern:** Backend mutation returns all authoritative computed values:
```json
{
  "txId": "...",
  "status": "COMPLETED",
  "amountOut": 15.74,
  "fee": 0.02,
  "feeCcy": "USD",
  "rate": "0.14724000"
}
```

**Why clients can't reverse-calculate:**
- Display rates are rounded; applied rates carry full precision
- Fee structures involve tiering, minimums, channel-specific logic
- Rounding direction varies by currency pair and amount

**Idempotency rule:** Retry responses must include the same computed fields as first-time responses. Expand the idempotency query SQL to include fee/rate columns.
