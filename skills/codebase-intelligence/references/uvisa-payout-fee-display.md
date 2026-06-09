# UVISA Payout Fee Display Architecture

## Two Payout Screens

| Screen | Route | Fee Strategy |
|--------|-------|-------------|
| `PayoutUsdtScreen` | `/payout/usdt` (legacy) | Hardcoded `≈ 0.10 USDT` in JSX |
| `PayoutCryptoScreen` | `/payout/crypto/:asset` AND `/payout/usdt` | Dynamic from backend via `feeDisplay()` |

Both routes `/payout/usdt` and `/payout/crypto/:asset` now render `PayoutCryptoScreen` (App.tsx:351-352).

## feeDisplay Function (PayoutCryptoScreen.tsx:95-99)

```typescript
function feeDisplay(fee: string | undefined, asset: string): string {
  if (!fee) return `≈ 0.10 ${asset}`;
  const numericOnly = /^[\d.,\s]+$/.test(fee);
  return numericOnly ? `≈ ${fee.trim()} ${asset}` : `≈ ${fee}`;
}
```

Logic:
1. No fee → default `≈ 0.10 {asset}`
2. Fee is pure numeric (e.g. "4.70") → append asset: `≈ 4.70 USDT`
3. Fee already contains text/symbols (e.g. "≈ 0.5") → pass through as-is (no double-append)

## feeOf Function (PayoutCryptoScreen.tsx:86-91)

```typescript
function feeOf(config: PayoutNetworkConfig): string | undefined {
  const raw = config.networkFeeEstimate ?? config.fee;
  if (raw == null || raw === "") return undefined;
  if (typeof raw === "object") return pickI18nText(raw) || undefined;
  return String(raw).trim();
}
```

Priority: `networkFeeEstimate` > `fee`. Both can be number|string|i18n-object.

## Backend Data Flow

- `ChainNetwork.networkFeeEstimate` is `BigDecimal` (Java), serialized as JSON number
- Frontend receives as number, `feeOf` converts via `String(raw)` → "0.5"
- `feeDisplay` detects numeric-only → appends asset unit

## Known Issue: Lark 401531e0

**Title**: 预计网络费右侧必须带币种单位(USDT/USDC),不能只显示裸数字

**Test coverage** (PayoutCryptoContactPicker.test.tsx:155-168):
- Mocks `networkFeeEstimate: '4.70'` (string, numeric-only)
- Asserts `≈ 4.70 USDT` present
- Asserts `≈ 4.70` (bare number) NOT present

## Debugging: Fee Shows Without Unit

If fee displays as bare number (e.g. "≈ 0.5" instead of "≈ 0.5 USDT"):

1. **Check deployment staleness** — code may be correct locally but not deployed. Compare Railway build timestamp vs local git HEAD.
2. **Check backend response** — if `networkFeeEstimate` already contains "≈" or non-numeric chars, the regex won't match and asset won't be appended. Inspect network tab for raw API response.
3. **Check `asset` param** — on `/payout/usdt` route, `useParams()` returns `{}`, so `asset` defaults to `"USDT"`. If the default is missing, the string would be "≈ 0.5 " (trailing space).

## Static Fallback (NETWORKS array)

When `getNetworks()` API fails, falls back to static `NETWORKS` (PayoutCryptoScreen.tsx:38-44). These have NO `fee` field → `feeOf` returns `undefined` → `feeDisplay` returns `≈ 0.10 USDT`.
