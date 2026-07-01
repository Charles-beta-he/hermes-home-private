---
name: react-architecture-migration
description: 'Use when you need to migrate React app from hardcoded mock data to production architecture: API client → Services → Zustand stores → Mock server.'
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - software
    - development
    - react
    - architecture
    - migration
    related_skills:
    - brand
    - design
    - domain
    - email
    - loop
    - p10
    - p10-architecture-self-check
    - subagent-driven-development
---

# React Architecture Migration — Mock Data → Production

## Overview


> Complete migration workflow for React+TypeScript apps from hardcoded mock data to production architecture with services, stores, mock server, i18n, dark mode, PWA, and monitoring.

## When to Use

- React app has hardcoded mock data in `data/mock.ts` or inline in screens
- Need to build API/service/store layer from scratch
- Need i18n, dark mode, PWA, error tracking, analytics
- User wants "loop until 99% complete"
- Need to build a mock server from existing service files (Expo or Vite)
- User says "mock server", "模拟服务器", "本地API", "loop until flow closed", "页面流程闭环"
- User asks to browser-test login/auth/security flows where mock demo credentials may differ from real/staging backend behavior
- **Prototype sync**: User points to a prototype directory and says "sync", "copy missing pages", "补充缺少页面", "同步后填充"
- **Unified deployment**: User wants to deploy mock server + dist as one process, "打包部署", "serve.js", "docker部署"


Don't use for:
- simple UI copy/styling changes with no data-source or architecture migration;
- backend-only API work where the frontend integration path is not in scope;
- replacing product/API evidence with mock data or localStorage behavior after production endpoints exist.

## Architecture Pattern

Detailed mock-to-production architecture pattern moved to `references/architecture-pattern.md`.

Load it when mapping mock/localStorage state to API-backed services, auth/session, React Query, and production data contracts.

Minimum in-root rule: identify the live backend contract and preserve existing behavior before replacing mock paths.

## Project Workpad Preflight (Long-running Frontend Loops)

Detailed project Workpad preflight moved to `references/project-workpad-preflight.md`.

Load it before long frontend closure loops when a project Workpad/SSOT exists.

Minimum in-root rule: Workpad north star, red lines, anchors, and evidence ledger override ad-hoc session memory.

## Execution Sequence (Loop with P10 Self-Check Each Round)

Detailed execution sequence moved to `references/execution-sequence-p10-loop.md`.

Load it for long-running frontend migration loops that need repeated self-check, adoption scans, test/build runs, and route-by-route proof.

Minimum in-root rule: migrate in verifiable slices and re-run focused checks after each slice.

## "未动" Audit Pattern

Use `execute_code` to programmatically find gaps:

```python
app = open("src/App.tsx").read()
for c in ["ErrorBoundary", "Suspense", "useAppBootstrap", "AnalyticsTracker"]:
    print(f"  {'✓' if c in app else '✗'} {c}")

for root, dirs, files in os.walk("src/screens"):
    for f in files:
        if not f.endswith('.tsx'): continue
        c = open(os.path.join(root, f)).read()
        # Count: stores, services, i18n, loading, dark: adoption
```

## Vite Mock vs Real Backend Flow Verification

When browser-verifying auth/security flows in Vite apps, apply `references/vite-mock-real-backend-flow-verification.md`: inspect `vite.config.ts` and `VITE_API_BASE`, run both default dev and forced-mock routes when docs/demo fixtures disagree with behavior, inspect response bodies rather than HTTP status alone, capture screenshots/network/console evidence, and record split results such as `FAIL(default dev) / PASS(forced mock)` instead of flattening them into one verdict.

## Playwright E2E Testing for Financial Apps

After all architecture is in place, add E2E tests for flow closure:

```bash
npm install -D @playwright/test
npx playwright install chromium
```

### Key Test Patterns

```typescript
// tests/flow-closure.spec.ts
// Test PIN error recovery
test('wrong PIN → error → clear → retry → success', async ({ page }) => {
  await page.goto('/card/topup/pin?amt=100');
  // Enter wrong PIN via numbered buttons
  for (const d of '111111') {
    await page.click(`button:has-text("${d}")`);
  }
  await expect(page.locator('.text-danger')).toBeVisible();
  await page.waitForTimeout(500); // wait for auto-clear
  // Enter correct PIN
  for (const d of '888888') {
    await page.click(`button:has-text("${d}")`);
  }
  await page.waitForTimeout(2000);
  expect(page.url()).toContain('/order/');
});

// Test state leak on navigation
test('navigate away during flow does not crash', async ({ page }) => {
  await page.goto('/exchange');
  await page.fill('input', '5000');
  await page.goto('/home');
  // No JS errors
});

// Test double-submit protection
test('double-click does not duplicate transaction', async ({ page }) => {
  // ... verify debounce works
});
```

### Playwright Config
```typescript
// playwright.config.ts
export default defineConfig({
  use: { baseURL: 'http://localhost:5173' },
  webServer: {
    command: 'npm run mock',
    url: 'http://localhost:3001/api/wallets',
    reuseExistingServer: true,
  },
});
```

### Flow Closure Test Matrix
```
Flow         Steps                                    Verify
PIN verify   enter wrong → error → clear → retry     State resets, can retry
Exchange     select → amount → confirm → execute      Navigates to /order/
Remit        payee → amount → preview → PIN → SMS     Timeline loads
Card freeze  confirm → processing → frozen → unfreeze Status toggles
Wealth       browse → select → buy → confirm          Holding created
```

## Expo / React Native Mock Server Setup (Non-Vite)

Detailed Expo/React Native mock-server setup moved to `references/expo-react-native-mock-server.md`.

Load it only when the target is Expo/RN rather than Vite web and local API emulation is required.

Minimum in-root rule: keep mock server paths aligned with production API paths before claiming integration parity.

## Mock Data Format Discovery (Critical Pattern)

When building a mock server, the #1 failure mode is **wrong data format**. Frontend hooks/components destructure response data in specific ways that are NOT obvious from the service layer. You must read the hooks and page components to discover the exact expected shape.

### Discovery Method

1. **Read the hook** (e.g., `useBalances.ts`, `useUCard.ts`) — find `formatData()` or `map()` calls
2. **Read the page component** — find destructuring patterns like `({trade}) =>` or `res.list.map()`
3. **Check field names** — `item.coin_name` not `item.currency`, `product.ID` not `product.id`
4. **Check types** — `.toFixed()` and `reduce((sum, x) => sum + x, 0)` require numbers, not strings

### Common Format Mismatches (Expo/React Native)

| Endpoint | WRONG (naive mock) | RIGHT (frontend expects) |
|----------|-------------------|--------------------------|
| wallet/balances | `{fiat:[{currency:'USD'}], crypto:[...]}` | `{list:[{coin_name:'USD', balance:'5000.00'}]}` |
| wallet/sec-balances | `[{symbol:'USDT', balance:'1500'}]` | `{list:[{coin_name:'USDT', balance:1500}]}` — balance MUST be number |
| wallet/fiat/fee | `{deposit_fee_rate:'0.01'}` | `{fb:{recharge_fee:0.01,...}, sec:{network_fee:0.0005,...}}` |
| ucard/trades | `{list:[{id:'t1', type:'payment', amount:-50}]}` | `{list:[{trade:{ID:'t1', action:'payment', status:'success', amount:-50, mask_id:'****1111'}}]}` |
| investment/products | `{list:[{id:'prod001', apy:'8.5%'}]}` | `{list:[{ID:'prod001', expected_return:'8.5', min_amount:100}]}` |
| investment/holdings | `{list:[{id:'hold001', amount:'5000'}]}` | `[{holding:{ID:'hold001', product_id:'prod001', amount:5000}}]` |
| investment/today-earnings | `{today_earnings:'12.50'}` | `{earnings:[{amount:12.50, product_name:'Fund'}]}` |
| investment/holding/:id/chart | `{chart:[{date:'...', value:5000}]}` | `[{date:'...', value:5000}]` — array directly, not wrapped |
| wallet/sec-balances (type) | `{list:[{coin_name:'USDT', balance:'1500.00'}]}` | `{list:[{coin_name:'USDT', balance:1500}]}` — string balance causes `toFixed is not a function` in `reduce((sum, x) => sum + x, 0)` |
| investment/today-earnings (type) | `{earnings:[{amount:12.50}], total_earnings:'425.00'}` | `total_earnings` MUST be number — `convert(amount)` calls `.toFixed(2)` on it |

### `.toFixed()` Type Chain Rule

Any value that flows through `CurrencyContext.tsx` → `convertAmount(amount, ...)` → `amount.toFixed(2)` MUST be a number at every point in the chain. One string breaks the entire page. This affects:
- `portfolioData.totalAssets`, `totalReturn`, `todayReturn`
- `walletBalances[].balance`, `cryptoBalances[].balance`
- `holdings[].amount`, `holdings[].earnings`
- `total_earnings`, `total_amount` from API responses

**Detection**: If a page crashes with `toFixed is not a function`, trace the value back through hooks/stores to the API response. The root cause is always a string where a number is expected.

### Unified Production Server (serve.js)

Detailed unified production server, Docker, endpoint self-check, iterative fix loop, navigation gaps, and multidimensional verification moved to `references/unified-production-server-and-flow-checks.md`.

Load it when deploying mock server + dist as one process or validating 100+ endpoint/frontend-flow closure.

Minimum in-root rule: deployment parity requires endpoint grouping, flow checks, and runtime evidence.

## TypeScript Build Error Triage

When `tsc -b` fails with many errors during migration, don't fix file-by-file. Categorize first:

### Category: Missing Test Framework Types (TS2593)
`Cannot find name 'beforeEach'/'describe'/'vi'` → Add `"vitest/globals"` to `tsconfig.app.json` types array.

### Category: Plugin API Drift (TS2561/TS2322)
- `vite-plugin-compression2` v2: `algorithm` → `algorithms` (array: `['brotliCompress']`)
- Vitest `test` config: `import { defineConfig } from 'vitest/config'` (not from `'vite'`)

### Category: Variable Shadowing → "Not Callable"
When `t('...')` errors as "Type 'Number' has no call signatures":
- `const t = setTimeout(...)` shadows `useTranslation()`'s `t` → rename timer
- `.map((t) => { t('...') })` shadows translation `t` → rename param to `tx`

### Category: Implicit `any` in Zustand Selectors (TS7006)
`useXxxStore((s) => s.field)` where `s` is `any`:
1. Export state interfaces: `export interface WalletState { ... }`
2. Import types: `import type { WalletState } from '../stores/wallet.store'`
3. Annotate: `useWalletStore((s: WalletState) => s.wallets)`

Same for `.filter((t) => ...)` and `.map((tx, i) => ...)` callbacks — add explicit parameter types.

### Category: Zustand v5 Persist Changes
- `onFinishHydration` removed → use `onRehydrateStorage` in persist config instead
- `transactions: []` inferred as `never[]` → `[] as Transaction[]`
- `useXxxStore.getState()` circular ref → use `(set, get)` store creator param, call `get()`

### Category: Test Mock Type Mismatches
Use `as any` for test mock data objects. Tests verify behavior, not type correctness.
For `ApiResult<T>` mocks missing `data` field: `mockResolvedValue({ success: false } as any)`.

### Verification
After each fix batch:
```bash
npx tsc -b 2>&1 | grep -c 'error TS'             # count remaining
npx tsc -b 2>&1 | grep '^src/' | grep -v '__tests__' | grep -v 'src/test/'  # source only
```

## Financial Ledger Dedup (Double-Entry)

When the app uses double-entry bookkeeping (exchange/transfer creates debit+credit legs), optimistic transaction ids must match the backend's composite leg id (e.g., `fx_debit:{orderId}`), not the operation/journal id. See `financial-ledger-frontend-patterns` skill for the full pattern, decision framework, and case study.

## Shared Store Consolidation

When multiple screens independently fetch the same API with inconsistent fallback lists, consolidate into a single shared zustand store. See `references/shared-store-consolidation.md` for the full pattern, test isolation strategy (pre-populate with `setState()`, don't reset to empty), and migration checklist.

## Common Pitfalls

Detailed migration pitfalls and mid-round fix patterns moved to `references/migration-pitfalls-and-midrounds.md`.

Load it when adoption scans find remaining mocks, format mismatches, stale stores, ledger dedup issues, or repeated build/test failures.

Minimum in-root rule: do not declare migration complete until source searches and runtime checks prove mock paths are gone or intentionally isolated.

## Round 7: Security Hardening (CRITICAL for financial apps)

Detailed security, architecture protection, PWA, API alignment, multimodel gap-analysis, H5 conversion, BottomSheet, and PIN recovery rounds moved to `references/security-h5-pwa-and-final-rounds.md`.

Load it when the migration touches financial/security-sensitive surfaces, H5 conversion, PWA update flows, or final gap analysis.

Minimum in-root rule: security/H5/PWA claims require real runtime/build evidence, not static copy edits.

## Completion Checklist

Detailed completion checklist moved to `references/completion-checklist.md`.

Load it before claiming migration completion or A+/loop closure.

Minimum in-root rule: every completed item needs source or runtime evidence from the current slice.

## Programmatic Completeness Audit

Detailed programmatic completeness audit moved to `references/programmatic-completeness-audit.md`.

Load it when scanning infrastructure files, store middleware, screen adoption, route parity, and remaining mock usage.

Minimum in-root rule: source search/readback must support any claim that mocks were removed or isolated.

## Deployment

Detailed deployment notes moved to `references/deployment.md`.

Load it when deploying the migrated frontend to Cloudflare Pages, Vercel, Netlify, VPS, Railway, or production env files.

Minimum in-root rule: deployment/publish requires exact target authority and post-deploy readback.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
