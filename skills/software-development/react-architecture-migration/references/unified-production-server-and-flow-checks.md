# Unified Production Server and Flow Checks

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:54:33.968451+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

### Unified Production Server (serve.js)

After building `dist/`, create a single Node.js server that handles both mock API and static files. Two variants:

**ESM variant (recommended for Vite projects)**:
```javascript
// serve.js — ESM, conditional mock loading
import express from 'express';
import cors from 'cors';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;
const ENABLE_MOCK = process.env.MOCK !== 'false';

app.use(cors());
app.use(express.json());

if (ENABLE_MOCK) {
  const { WALLETS, ... } = await import('./mock-server/data/mock.js');
  // ... mount all API routes
  console.log('[mock] API routes mounted at /api');
}

// Static files with caching
app.use(express.static(join(__dirname, 'dist'), {
  maxAge: '1y', immutable: true, index: false,
  setHeaders(res, path) {
    if (path.endsWith('.html')) res.setHeader('Cache-Control', 'no-cache');
  },
}));

// SPA fallback (MUST be last)
app.get('*', (_req, res) => {
  res.sendFile(join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 http://localhost:${PORT}`);
});
```

Key: HTML gets `no-cache`, JS/CSS get `1y immutable`. SPA fallback catches all non-API, non-static routes.

**CJS variant (for Expo/legacy projects)**:
```javascript
const http = require('http');
const fs = require('fs');
const path = require('path');
// ... see Unified Production Server Pattern above
```

### Docker Deployment

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY mock-server/package*.json ./mock-server/
RUN cd mock-server && npm ci --production
COPY serve.js ./
COPY mock-server/data ./mock-server/data
COPY dist ./dist
EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "serve.js"]
```

Add `.dockerignore`:
```
node_modules
src
mock-server/node_modules
*.md
.git
```

### Pitfalls for Unified Server
- **express not in root node_modules**: If express is only in `mock-server/node_modules`, either `npm i express cors` at root or symlink: `ln -sf mock-server/node_modules/express node_modules/express`
- **ESM imports**: Use `await import()` for conditional mock loading, not `require()`. ESM `await` at top level works in `.js` files with `"type": "module"` in package.json
- **SPA fallback must be LAST**: After `express.static()` and all API routes, `app.get('*', ...)` catches everything else
- **vite build without tsc**: When `tsc -b` fails on pre-existing errors, run `node node_modules/vite/bin/vite.js build` directly to skip type checking

### Key differences from dev mock server

- **Balance fields used in `.toFixed()` or `reduce((sum, x) => sum + x)`**: MUST be `number`, not `string`
- **ID fields used in routing (`product.ID`)**: MUST be uppercase `ID`, not `id`
- **Nested destructuring (`{trade: {...}}`, `{holding: {...}}`)**: MUST have the nesting wrapper
- **Array vs object**: Some endpoints return bare arrays `[{...}]`, others wrap in `{list: [...]}`
- **`.toFixed(2)` propagation**: If a value flows into `convert(amount, ...)` which calls `amount.toFixed(2)`, the value MUST be number at every point in the chain — including `total_earnings`, `total_amount`, `earnings[].amount`. One string in the chain breaks the entire page.
- **`reduce((sum, x) => sum + x, 0)` with strings**: If any `x` is a string like `"1500.00"`, the reduce produces string concatenation `"01500.002.5"` instead of `1502.5`. All values feeding into numeric reduce MUST be numbers.

### Parallel Subagent Strategy for 100+ Endpoints

When the project has 100+ API endpoints, use 3 parallel subagents to generate handlers by domain:
- Agent 1: Auth + User + KYC (40-50 endpoints)
- Agent 2: Wallet + UCard (60-70 endpoints)
- Agent 3: Investment + Notifications + Chat + Misc (40-50 endpoints)

Each agent writes to `/tmp/mock-{domain}.js`, the main server imports all three.

### Full Endpoint Self-Check (After Build)

After the mock server is built, run a programmatic self-test of ALL endpoints:

```python
import subprocess, json

BASE = "http://localhost:9969"

def test_get(path):
    try:
        result = subprocess.run(["curl", "-s", f"{BASE}{path}"],
            capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)
        return data.get("code") == 0 and data.get("data") is not None
    except: return False

def test_post(path, data=None):
    try:
        cmd = ["curl", "-s", "-X", "POST", f"{BASE}{path}",
               "-H", "Content-Type: application/json",
               "-d", json.dumps(data or {})]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        data = json.loads(result.stdout)
        return data.get("code") == 0 and data.get("data") is not None
    except: return False

# Group endpoints by domain, test each group
categories = {
    "AUTH": [("POST", "/api/auth/login", {"account":"test","password":"123"}), ...],
    "WALLET": [("GET", "/api/wallet/balances", None), ...],
    # ... all domains
}
for cat, endpoints in categories.items():
    passed = sum(1 for m, p, d in endpoints if (test_get if m=="GET" else test_post)(p, d))
    print(f"{'✅' if passed == len(endpoints) else '❌'} {cat} {passed}/{len(endpoints)}")
```

This catches missing handlers, wrong response shapes, and runtime errors in mock data before the browser test phase.

### Iterative Fix Loop

When the task is **syncing missing pages from a prototype/reference project** (not building service layers from scratch), use this focused workflow instead of the full migration:

### Trigger Conditions
- User points to a prototype directory (e.g. `uvisa-app-2.0`) and says "sync", "copy missing pages", "补充缺少页面"
- Two React projects need page-level reconciliation

### Quick Steps
1. **File diff**: `diff <(find proto/src/screens -name "*.tsx" | sed 's|.*/src/screens/||' | sort) <(find curr/src/screens ...)` — identify missing screens
2. **Copy + adapt**: Copy missing files, fix TS errors (type narrowing, unused params, import paths)
3. **Register routes**: Add lazy imports + `<Route>` entries in App.tsx following current patterns (lazy for default exports, direct import for named exports)
4. **Fix navigation links** (most commonly missed!): Diff `nav()` targets between prototype and current screens. Existing screens that should link to new pages often still point to old/wrong paths.
5. **Verify**: File diff = 0, route diff = 0, all nav targets have routes, all imports resolve, 0 new TS errors, tests pass

### Common Navigation Gaps
- SecurityCenterScreen: all sub-links point to `/me/security` (self) instead of `/me/security/phone`, `/email`, etc.
- HomeScreen "更多": points to `/remit` instead of `/more`
- PayeeListScreen "新建": points to `/remit` instead of `/remit/payees/new`
- PayoutHubScreen: USDT/USDC both point to `/payout/usdt` instead of `/payout/crypto/USDT` and `/payout/crypto/USDC`

### Pitfalls
- **Named vs default exports**: `lazy()` only works with default exports. Named exports (e.g. `PaymentVerifyScreens` exporting multiple components) need direct `import { X } from "..."`
- **i18n key gaps**: Prototype uses hardcoded strings, current uses `t("key")`. Either add keys to zh.json/en.json or use literals.
- **Missing data files**: Always trace imports from new screens — they may need `payeeStore.ts`, `securityStore.ts`, etc. that don't exist yet.
- **Pre-existing errors masking new issues**: Filter build output to only show errors from new files.
- **`tsc -b` fails on pre-existing errors**: When `npm run build` is `tsc -b && vite build` and tsc fails, run `node node_modules/vite/bin/vite.js build` directly to skip type checking. The build will still catch runtime import errors.
- **vite preview does NOT proxy**: `vite preview` uses the `preview` config section, not `server.proxy`. In Vite 5+, the proxy works in preview mode too, but verify with `curl http://localhost:4173/api/wallets`. If it returns HTML (index.html) instead of JSON, the proxy isn't working — use the dev server instead or configure `preview.proxy` separately.

### Multi-Dimensional Verification (10-Dimension Cross-Check)

When the sync is complete, run these additional cross-checks beyond file/route diff:

1. **File-level diff**: `diff <(find proto/src -name "*.tsx" -o -name "*.ts" | sed 's|proto/src/||' | sort) <(find curr/src ...)` — identify ALL missing files (screens + components + data + lib)
2. **Route-level diff**: Extract all `path=` from both App.tsx, sort, diff — should be identical (or curr has MORE)
3. **Navigation target coverage (dynamic)**: `grep -roh 'nav(\`/[^\`]*\`' src/screens/ | sed 's/nav(\`//;s/\`$//' | sort -u` — extract template-string nav targets
4. **Navigation target coverage (static)**: `grep -roh 'nav("/[^"]*"' src/screens/ | sort -u` — extract string nav targets
5. **Link to= static paths**: `grep -roh 'to="/[^"]*"' src/screens/ | sort -u` — compare `<Link>` targets
6. **Type export parity**: `diff <(grep "export" proto/src/types/index.ts | sort) <(grep "export" curr/src/types/index.ts | sort)` — ensures no type was lost
7. **Data file parity**: `diff <(ls proto/src/data/) <(ls curr/src/data/)` — ensures all data modules copied
8. **Component import resolution**: For every new file, resolve all relative imports and verify the target exists. Use a Python script to walk imports and check file existence.
9. **Missing nav targets**: Compare prototype nav targets against current routes — any nav target without a route = broken navigation
10. **Architecture diff**: Check if prototype uses different flows (e.g. centralized `/pay/verify/pin` vs per-screen PIN screens) — document the difference, don't force one pattern

- **Reference anchor unresolved during parity work**: If a Workpad or user request says “align with reference uvisa-app/prototype”, first verify the reference path exists and enumerate routes/screens. Do not claim parity against a missing path. If another candidate path exists (for example under Downloads), mark it provisional until the user confirms it.
