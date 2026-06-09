# UVISA Currency Architecture

## Overview

UVISA currency data flows from a single admin registry through `currencyService.list()` to all consumer pages. The key architectural principle: **all pages must derive their currency lists from the same admin registry, never from hardcoded fallback arrays.**

## Data Flow

```
Admin Registry (backend)
  → currencyService.list() (API)
    → useCurrencyStore.hydrateFromBalances() (Zustand store)
      → useRegistry() hook (fiat, crypto, byCode, byKind)
        → HomeScreen, TopupHubScreen, PayoutHubScreen, ExchangeScreen
```

### Key Files

| File | Role |
|------|------|
| `src/stores/useCurrencyStore.ts` | Zustand store, single source of truth. `hydrateFromBalances()` populates from API. |
| `src/hooks/useCurrencyRegistry.ts` | Derives `fiat`, `crypto`, `byCode`, `byKind` from store. Exports `FALLBACK_CURRENCY_UI` for offline. |
| `src/services/currency.service.ts` | API client for `/api/currency/list`. |
| `src/lib/customerCurrencyVisibility.ts` | `filterDomesticCnyItems()` — hides CNY when domestic transfer gate is off. |

### Consumer Pages

| Page | How it gets currencies | Special rules |
|------|----------------------|---------------|
| HomeScreen (资产首页) | `useRegistry().fiat` + `.crypto` | Split into 法币钱包 + 加密钱包 sections |
| TopupHubScreen (转入) | `currencyService.list()` direct | Sections: DOMESTIC(CNY), SWIFT(fiat), ONCHAIN(crypto) |
| PayoutHubScreen (转出) | `currencyService.list()` direct | Sections: DOMESTIC(CNY), CROSS_BORDER(fiat), ONCHAIN(crypto) |
| ExchangeScreen (兑换) | `useRegistry().fiat` | Receive-currency picker is **FIAT-only** — no USDT/USDC |

### FIAT vs CRYPTO Kind

Every currency from the admin registry has a `kind` field:
- `"FIAT"` — traditional currencies (USD, CNH, CNY, HKD, EUR, JPY, GBP, etc.)
- `"CRYPTO"` — blockchain tokens (USDT, USDC)

The `kind` field drives section routing in topup/payout hubs and filters in the exchange picker.

## Anti-Pattern: ALL_CCYS Fallback

**Problem**: A hardcoded `ALL_CCYS` array mixing FIAT and CRYPTO codes acts as a fallback when the admin registry is unreachable. This causes:
1. CRYPTO codes (USDT, USDC) appearing in FIAT-only pickers (exchange receive-currency)
2. FIAT codes (EUR, JPY, GBP) missing if not in the hardcoded list
3. Currency list divergence between pages when some use the fallback and others use the registry

**Fix**: Remove `ALL_CCYS` from consumer pages. All pages must derive currencies from:
- `useRegistry()` hook (preferred, store-backed)
- `currencyService.list()` direct (acceptable for hub screens that need raw data)

**Verification**: After any currency change, screenshot all 4 pages and verify currency counts match:
- Home: all enabled fiat + all enabled crypto
- Topup: same currencies, split by section
- Payout: same currencies, split by section
- Exchange picker: FIAT only, same fiat count as home

## Adding a New Currency

1. Admin registry: add currency with correct `kind` (FIAT/CRYPTO), `enabled=true`
2. All consumer pages automatically pick it up via the shared store
3. If the currency needs a custom icon, add to `CurrencyAvatar` component
4. If it needs custom sub-text in topup/payout, add i18n key `topup.sub.<code>` / `payout.sub.<code>`
5. Verify: all 4 pages show the new currency in the correct section

## Common Pitfalls

1. **Exchange picker showing USDT/USDC**: The receive-currency picker must use `useRegistry().fiat`, not `useRegistry().all` or a mixed list. Crypto-to-crypto exchange is not supported.
2. **CNY hidden when it shouldn't be**: Check `domesticCnyTransferEnabled` gate from `platformConfigService.getTopup()`. CNY is filtered by `filterDomesticCnyItems()`.
3. **Stale currency list after admin change**: The Zustand store persists across navigations. Force re-hydration by navigating away and back, or by calling `hydrateFromBalances()` with fresh API data.
4. **Different currency counts across pages**: Root cause is almost always one page using a hardcoded fallback while others use the registry. Search for `ALL_CCYS`, `FALLBACK_CODES`, or inline currency arrays.
