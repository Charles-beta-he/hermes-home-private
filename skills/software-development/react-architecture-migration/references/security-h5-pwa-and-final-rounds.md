# React Migration Security, H5/PWA, and Final Rounds

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Round 7: Security Hardening (CRITICAL for financial apps)

### Route Guards
```
src/components/ProtectedRoute.tsx:
- Checks useAuthStore((s) => s.isAuthenticated)
- Redirects to /login via <Navigate> if not authenticated
- In App.tsx: wrap all non-auth routes in ProtectedLayout (Outlet pattern)
```

### PIN Attempt Limiting
```
src/lib/pinGuard.ts:
- trackAttempt(key): { blocked, remaining, lockoutUntil }
- Max 5 attempts per 10-min rolling window, 5-min lockout
- Stored in sessionStorage (resets on tab close)
- usePinGuard(key) hook for React components
```

### Session Timeout
```
src/hooks/useSessionTimeout.ts:
- Tracks lastActivity, resets on click/keydown/touchstart/mousemove
- Checks every 60s: idle > 15 min → authStore.logout() + redirect
- visibilitychange: tab hidden > 30 min → logout on return
- Call useSessionTimeout() in App.tsx ShellLayout
```

### Token Refresh with Request Queuing
```
In src/lib/api.ts response interceptor:
- On 401: try POST /auth/refresh with stored refresh_token
- Queue concurrent 401s in failedQueue
- If refresh succeeds: replay all queued requests
- If refresh fails: clear tokens, redirect to /login
- Add refreshToken() to auth.service.ts
```

### Replace Hardcoded PINs
```
src/lib/pinVerify.ts:
- verifyPin(pin) → calls POST /auth/pin/verify if API available
- Falls back to VITE_DEMO_PIN env var (default "888888")
- All 5 PIN screens use this + pinGuard instead of const CORRECT = "888888"
```

### Shared Validators
```
src/lib/validators.ts:
- isWeakPin(pin): checks 18 common PINs + all-same-digit
- isValidAmount(val, min, max, decimals): range + precision check
- isValidEthAddress(addr): 0x + 40 hex chars
```

### i18n Security Fix
```
In src/i18n/index.ts: change escapeValue: false → true
(Financial apps MUST escape HTML in translations)
```

## Round 8: Architecture Protection

### Zustand Middleware (all 7 stores)
```typescript
import { create } from 'zustand';
import { persist, devtools, createJSONStorage } from 'zustand/middleware';

export const useStore = create<State>()(
  devtools(
    persist(
      (set, get) => ({ /* state & actions */ }),
      {
        name: 'store-name',
        storage: createJSONStorage(() => sessionStorage),
        partialize: (state) => ({ /* critical fields only */ }),
      }
    ),
    { name: 'StoreName' }
  )
);
```

### Request Cancellation
```
src/lib/useApiEffect.ts:
- useApiEffect(url, deps, onData) — auto-cancels on unmount
- useCancelScope() — low-level AbortController wrapper
```

### Financial CTA Debounce
```
src/hooks/useDebounceAction.ts:
- Wraps callback to ignore rapid repeated calls within delay ms
- Use on all financial operation buttons (1000ms default)
```

### Offline Detection
```
src/hooks/useOnlineStatus.ts: navigator.onLine + events
src/components/OfflineBanner.tsx: sticky yellow warning bar
Wire <OfflineBanner /> in App.tsx ShellLayout
```

### Feature Flags
```
src/lib/featureFlags.ts:
- Static config with isEnabled(flag) + useFeature(flag) hook
- Can be swapped for remote config later
```

### Retry Logic
```
src/lib/retry.ts:
- withRetry<T>(fn, maxRetries=3, delay=1000) with exponential backoff
```

### Transaction Export
```
src/lib/exportUtils.ts:
- exportToCsv(transactions, filename) using Blob + URL.createObjectURL
- BOM prefix for Excel CJK compatibility
```

## Round 9: PWA Update Notification

### Problem
With `registerType: 'autoUpdate'`, users don't see updates because SW silently caches old assets.

### Solution: `registerType: 'prompt'` with Forced Countdown
```
vite.config.ts:
  VitePWA({ registerType: 'prompt', ... })
  → SW installs but waits for user confirmation before activating

src/hooks/useServiceWorkerUpdate.ts:
  → Detects 'updatefound' event on SW registration
  → When new SW state === 'installed' && controller exists → isUpdateAvailable = true
  → Modes: 'prompt' (user clicks) or 'forced' (30s countdown then auto-update)
  → updateApp() sends { type: 'SKIP_WAITING' } to waiting SW
  → 'controllerchange' event fires → page.reload()
  → checkForUpdate() for manual version check (wire to MeScreen version card)

src/components/UpdateBanner.tsx:
  → Shows sticky banner: "发现新版本  28s  [立即更新]"
  → In 'forced' mode: countdown timer, auto-updates when 0
  → In 'prompt' mode: user clicks to update
  → Calls updateApp() on click or countdown expiry
  → Dark: mode support
```

### Manual Version Check (MeScreen Integration)
Wire `checkForUpdate()` from useServiceWorkerUpdate to MeScreen version card:
```tsx
const { checkForUpdate, updateStatus } = useServiceWorkerUpdate();
// onClick={checkForUpdate} on version card button
// updateStatus: 'idle' | 'checking' | 'available' | 'up-to-date'
// Show spinner when checking, green check when up-to-date
```

### Update Flow
```
SW registers → checks every 60 min + on mount
New version found → installs in background
isUpdateAvailable = true → banner shows with countdown
User clicks OR countdown hits 0 → SKIP_WAITING → new SW activates → page reloads
Fresh assets from new cache
```

### Dynamic Version Display
Create `src/lib/version.ts`:
```typescript
export const APP_VERSION = '1.0.0';
export const BUILD_NUMBER = '24042701';
export const FULL_VERSION = `v${APP_VERSION} (build ${BUILD_NUMBER})`;
```
Reference in MeScreen and AboutScreen instead of hardcoded 'v1.0.0'.

## Round 9.5: Mock Server API Path Alignment (CRITICAL)

After all services are created, verify frontend paths match mock server endpoints:

```bash
# Check POST endpoints match
for svc in src/services/*.service.ts; do
  paths=$(grep -o "'/[^']*'" $svc | tr -d "'" | sort -u)
  for p in $paths; do
    status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:3001/api$p" -H "Content-Type: application/json" -d '{}' 2>/dev/null)
    if [ "$status" = "404" ] || [ "$status" = "000" ]; then
      echo "❌ $svc → $p (HTTP $status)"
    fi
  done
done
```

Common mismatches (service → mock server):
- `exchange/execute` vs `exchange/confirm` — service uses execute, tests may use confirm
- `remit/preview` vs `remit/quote` — service uses preview, tests may use quote
- `auth/pin/setup` vs `auth/verify-pin` — service uses pin/setup
- `wealth/holdings/:id/redeem` vs `wealth/redeem` — service uses nested path

Fix: Add missing endpoint aliases to mock server (not change services).

### Browser-Based Flow Verification

Use `browser_console` to test all API endpoints directly in the running app:

```javascript
// Run in browser_console to verify all flows
async function fullAcceptanceTest() {
  const tests = [
    {name: 'Login', url: '/api/auth/verify', method: 'POST', body: {phone: '13856785678', code: '123456'}},
    {name: 'Wallets', url: '/api/wallets', method: 'GET'},
    {name: 'Exchange Quote', url: '/api/exchange/quote', method: 'POST', body: {from: 'USD', to: 'CNH', amount: 100}},
    {name: 'Exchange Confirm', url: '/api/exchange/confirm', method: 'POST', body: {from: 'USD', to: 'CNH', fromAmount: 100, toAmount: 720, rate: 7.2}},
    // ... all 17+ POST endpoints + 18 GET endpoints
    {name: 'Wrong PIN', url: '/api/auth/verify-pin', method: 'POST', body: {pin: '000000'}, expectFail: true},
  ];
  // Each test: fetch → check success field → log ✅ or ❌
}
```

This catches path mismatches, missing endpoints, and error handling gaps before they reach production.

## Round 10: Multi-Model Gap Analysis (Final)

After all rounds, run 3 parallel subagents (5-8 files each):
- Agent 1: Auth & Security audit (token, session, PIN, validation)
- Agent 2: Business Logic audit (exchange countdown, payout wiring, export, limits)
- Agent 3: Architecture Protection audit (persist, cancel, retry, feature flags)

16. **browser_console for flow verification**: Can test all API endpoints directly in the browser without Playwright. Faster than E2E tests for verifying endpoint existence and error handling.

17. **vite-plugin-pwa registerType 'prompt'**: Must NOT have `skipWaiting: true` or `clientsClaim: true` in workbox config. The 'prompt' mode handles SKIP_WAITING via the useServiceWorkerUpdate hook.

18. **PWA icons must be real PNG**: Generate with Pillow (`from PIL import Image`) if design tools unavailable. SVG icons don't work for PWA manifest.

19. **Mock server not in build**: `npm run build` only bundles frontend. Mock server deploys separately (Railway/Render/VPS). **EXCEPTION**: You can create a unified `serve.js` that serves both `dist/` static files AND mock API in one Node.js process (see Unified Production Server pattern below).

20. **Mock server API path mismatch**: Frontend services may call different paths than mock server endpoints. Always run the path alignment check (Round 9.5) before declaring "done".

21. **PWA Update Banner i18n keys**: Add `update.available` and `update.button` to zh.json/en.json. Use nested key structure (i18next supports it alongside flat keys).

22. **BottomSheet portal after PhoneCanvas removal**: When converting from PhoneCanvas prototype to real H5, BottomSheet portals into `#phone-portal` which no longer exists. Change to `document.body` with `fixed` positioning.

23. **Build gzip verification**: `du -sh dist/` shows uncompressed size. Always verify gzipped: `for f in dist/assets/*.js dist/assets/*.css; do gzip -c "$f" | wc -c; done | awk '{s+=$1} END {print s/1024 " KB"}'`

24. **web-vitals API change**: `onFID` removed in v5, use `onINP` instead.

## Round 11: H5 Conversion (Prototype → Production)

When the app uses PhoneCanvas for prototype display, convert to real H5:

1. Remove `<PhoneCanvas>` wrapper from App.tsx — render ShellLayout directly
2. Delete PhoneCanvas.tsx file
3. Replace fake StatusBar (9:41 + signal icons) with safe-area spacer:
   ```tsx
   export default function StatusBar() {
     return <div className="w-full shrink-0" style={{ height: 'env(safe-area-inset-top, 0px)' }} />;
   }
   ```
4. Fix BottomSheet: change portal target from `#phone-portal` to `document.body`, use `fixed` instead of `absolute`
5. Update index.html viewport: remove `maximum-scale=1.0, user-scalable=no`
6. Verify with tsc --noEmit

## BottomSheet Portal Fix (H5 Conversion)

When removing PhoneCanvas, BottomSheet portals into `#phone-portal` which no longer exists:

```typescript
// BEFORE (PhoneCanvas mode)
const host = document.getElementById("phone-portal");
// Uses absolute positioning relative to phone canvas

// AFTER (H5 mode)
// Portal into document.body with fixed positioning
return createPortal(
  <div className="fixed inset-0 z-[1000] ...">...</div>,
  document.body,
);
```

Key changes: `absolute` → `fixed`, `#phone-portal` → `document.body`, add `aria-modal` + `role="dialog"`.

## PIN Error Recovery Pattern

When PIN verification fails, the error state and input must be cleared in separate steps:

```typescript
// WRONG — race condition, both cleared simultaneously
setTimeout(() => { setPin(""); setError(null); }, 480);

// CORRECT — clear pin first, then error, with verifying guard
const [verifying, setVerifying] = useState(false);

useEffect(() => {
  if (pin.length !== 6 || error || verifying) return;
  setVerifying(true);
  verifyPin(pin).then((ok) => {
    setVerifying(false);
    if (ok) { /* success */ }
    else {
      // Track failure, show error
      setError({ key: Date.now(), msg: errorMsg });
      // Separate clearing: pin first, then error
      setTimeout(() => { setPin(""); }, 300);
      setTimeout(() => { setError(null); }, 480);
    }
  });
}, [pin, error, verifying]);
```

The `verifying` guard prevents double-triggering while async verification is in progress.
