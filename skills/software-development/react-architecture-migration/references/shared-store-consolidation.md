# Shared Store Consolidation Pattern

When multiple screens independently fetch the same API data with inconsistent fallback lists, consolidate into a single shared zustand store.

## Problem: Per-Screen Independent Fetches

```
HomeScreen → currencyService.list() → FIAT_ALL fallback → fiat[]
ExchangeScreen → currencyService.list() → ALL_CCYS fallback → mixed fiat+crypto ← BUG
```

Each screen has its own:
- Fetch logic (different error handling, different caching)
- Fallback lists (inconsistent: one has EUR/JPY, other doesn't; one mixes CRYPTO into FIAT)
- Loading states (screen A loads, screen B still shows stale fallback)

## Solution: Shared Zustand Store

```typescript
// src/stores/currency.store.ts
interface CurrencyMeta { symbol: string; name?: string; kind?: string; }

interface CurrencyRegistryState {
  all: Currency[];      // full list from API
  fiat: Currency[];     // filtered: kind === 'FIAT'
  crypto: Currency[];   // filtered: kind === 'CRYPTO'
  meta: Record<string, CurrencyMeta>;
  cnyEnabled: boolean;  // from platform config
  isLoading: boolean;
  error: string | null;
  fetchAll: () => Promise<void>;
}

export const useCurrencyRegistryStore = create<CurrencyRegistryState>()((set, get) => ({
  all: [], fiat: [], crypto: [], meta: {}, cnyEnabled: null, isLoading: false, error: null,
  fetchAll: async () => {
    if (get().isLoading) return;  // dedup guard
    set({ isLoading: true, error: null });
    try {
      const [currencyRes, topupRes] = await Promise.all([
        currencyService.list(),
        platformConfigService.getTopup().catch(() => null),  // fail-open
      ]);
      const items = currencyRes?.data?.items ?? [];
      const fiat = items.filter(c => c.kind === 'FIAT');
      const crypto = items.filter(c => c.kind === 'CRYPTO');
      const cnyEnabled = topupRes?.success && topupRes.data
        ? topupRes.data.domesticCnyTransferEnabled !== false
        : true;  // fail-open default
      set({
        all: items, fiat, crypto,
        meta: Object.fromEntries(items.map(c => [c.code, { symbol: c.symbol, name: c.name, kind: c.kind }])),
        cnyEnabled, isLoading: false, error: null,
      });
    } catch (e) {
      set({ isLoading: false, error: String(e) });
    }
  },
}));
```

### Backward-compat hook (gradual migration)

Keep the old hook signature working while delegating to the store:

```typescript
// src/hooks/useCurrencyRegistry.ts
export function useCurrencyRegistry() {
  const { all, meta, isLoading, error, fetchAll } = useCurrencyRegistryStore();
  useEffect(() => { fetchAll(); }, []);
  return { currencies: all, meta, loading: isLoading, error };
}
```

### Screen refactoring

```typescript
// BEFORE (ExchangeScreen — per-screen fetch + fallback)
const ALL_CCYS = ['USD','USDT','CNH','EUR','GBP','JPY','HKD','USDC']; // mixed fiat+crypto!
const [currencies, setCurrencies] = useState(ALL_CCYS);
useEffect(() => {
  currencyService.list().then(res => {
    const codes = res.data.items.filter(c => c.kind === 'FIAT').map(c => c.code);
    if (codes.length) setCurrencies(codes);
    // else keeps ALL_CCYS — mixes CRYPTO into FIAT picker ← BUG
  });
}, []);

// AFTER (ExchangeScreen — shared store)
const { fiat, crypto, fetchAll } = useCurrencyRegistryStore();
useEffect(() => { fetchAll(); }, []);
// Use fiat for receive picker, crypto for send picker — no fallback needed
```

```typescript
// BEFORE (HomeScreen — module-level cache + per-screen fetch)
let _cache: { list: Currency[]; at: number } | null = null;
const CACHE_TTL = 5 * 60_000;
const FIAT_ALL = ['CNH','CNY','USD','HKD','SGD','CHF','GBP','AUD'];
const CRYPTO_ALL = ['USDT','USDC'];
// ... fetch logic with cache, fallback, error handling

// AFTER (HomeScreen — shared store)
const { all, fiat, crypto, cnyEnabled, fetchAll } = useCurrencyRegistryStore();
useEffect(() => { fetchAll(); }, []);
// Use fiat/crypto directly, no module-level cache needed
```

## Test Isolation with Shared Stores (CRITICAL)

When a shared store exists, tests MUST pre-populate the store state — not just mock the service.

### ❌ WRONG: Reset store to empty, hope fetchAll completes in time

```typescript
beforeEach(() => {
  vi.mocked(currencyService.list).mockReset();
  useCurrencyRegistryStore.setState({
    all: [], fiat: [], crypto: [], meta: {}, cnyEnabled: null, isLoading: false, error: null,
  });
  // Store is empty → fetchAll runs async → test clicks picker before data arrives → FAIL
});
```

### ❌ WRONG: Mock service only, don't touch store

```typescript
beforeEach(() => {
  vi.mocked(currencyService.list).mockResolvedValue({ success: true, data: { items: [...] } });
  // Store might still have stale data from previous test if it's a module-level singleton
  // Different tests may see different store states depending on execution order
});
```

### ✅ CORRECT: Pre-populate store with same data as mock

```typescript
beforeEach(() => {
  vi.mocked(currencyService.list).mockReset();

  // Pre-populate store so picker is immediately available (no async wait)
  const items = [
    registryCurrency('CNY'), registryCurrency('CNH'), registryCurrency('USD'),
    registryCurrency('HKD'), registryCurrency('USDT', 'CRYPTO'),
  ];
  const fiat = items.filter(c => c.kind === 'FIAT');
  const crypto = items.filter(c => c.kind === 'CRYPTO');
  useCurrencyRegistryStore.setState({
    all: items as never[],
    fiat: fiat as never[],
    crypto: crypto as never[],
    meta: Object.fromEntries(items.map(c => [c.code, { symbol: c.symbol }])),
    cnyEnabled: true,
    isLoading: false,
    error: null,
  });

  // Also mock the service (for tests that trigger fetchAll explicitly)
  vi.mocked(currencyService.list).mockResolvedValue({
    success: true,
    data: { items: [...], total: items.length },
  });
});
```

### Why pre-populate?

1. Zustand stores are module-level singletons — state persists across tests in the same file
2. `fetchAll()` is async — tests that click UI elements before fetch completes see empty state
3. Pre-populating with `setState()` is synchronous — store has data before any `render()` call
4. The service mock is still needed for tests that explicitly test the fetch behavior

## Hook Export Naming Pitfall

When the hook name in the import doesn't match the call site, it's a silent error:

```typescript
// hooks/useCurrencyRegistry.ts
export function useCurrencyRegistry() { ... }  // exported as useCurrencyRegistry

// ExchangeScreen.tsx
import { useRegistry } from '../../hooks/useCurrencyRegistry';
const { currencies } = useRegistry();  // ← SILENT ERROR: useRegistry is undefined
// Runtime: "useRegistry is not a function" or hook returns undefined
```

Fix: always verify import name matches export name. TypeScript catches this, but if the import is destructured from a barrel export that re-exports with `as`, the mismatch can slip through.

## Migration Checklist

- [ ] Identify all screens that independently fetch the same API
- [ ] Compare fallback lists — find inconsistencies (missing currencies, mixed types)
- [ ] Create shared zustand store with `fetchAll()` + dedup guard
- [ ] Add backward-compat hook if needed (gradual migration)
- [ ] Refactor screens to use store instead of per-screen fetch
- [ ] Remove per-screen fallback lists (ALL_CCYS, FIAT_ALL, etc.)
- [ ] Remove module-level caches (`_cache`, `CACHE_TTL`)
- [ ] Update ALL tests: pre-populate store in `beforeEach` with `setState()`
- [ ] Verify: `tsc --noEmit` passes, all tests pass, no regressions
