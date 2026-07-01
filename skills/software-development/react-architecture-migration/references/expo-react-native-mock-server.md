# Expo / React Native Mock Server Setup

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Expo / React Native Mock Server Setup (Non-Vite)

When the project uses **Expo** (metro bundler) instead of Vite, the proxy and mock server setup differs:

### Step 1: Extract All API Endpoints from Service Files

Use `execute_code` to scan all service files for API patterns:

```python
import re
from pathlib import Path

api_calls = []
services_dir = Path('/path/to/project/services')
for file_path in services_dir.glob('*'):
    if file_path.suffix not in ['.ts', '.js']:
        continue
    content = file_path.read_text(encoding='utf-8')
    patterns = [
        (r'get\(`\$\{BASE_URL\}([^`]+)`', 'GET'),
        (r'post\(`\$\{BASE_URL\}([^`]+)`', 'POST'),
        (r'put\(`\$\{BASE_URL\}([^`]+)`', 'PUT'),
        (r'del\(`\$\{BASE_URL\}([^`]+)`', 'DELETE'),
    ]
    for pattern, method in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            api_calls.append({
                'file': file_path.name,
                'method': method,
                'path': f'/api{match}',
            })
```

This finds all endpoints including parameterized ones like `/api/ucard/${id}/details`.

### Step 2: Identify Response Format

Read the axios interceptor or service error handling to determine the response contract:
- Expo projects often use `{ code: 0, data: {...} }` for success
- Some use `{ success: true, data: {...} }`
- Token failure is typically `code === -4` (redirect to login)
- Account disabled is `code === -6`

### Step 3: Mock Server (Node.js built-in http module)

**Do NOT install Express** — npm peer dep conflicts are common in Expo projects. Use Node.js built-in `http` module:

```javascript
// scripts/mock-server.js
const http = require('http');
const url = require('url');

const PORT = 9999;

// Route handlers grouped by domain
const routes = {
  // Auth — return success directly (API key related)
  'POST /api/auth/login': () => ({ code: 0, data: { token: 'mock_token_abc123', user: { id: '1', email: 'test@test.com', name: 'Test User' } } }),
  'POST /api/auth/register': () => ({ code: 0, data: { message: '注册成功' } }),
  'POST /api/auth/send-code': () => ({ code: 0, data: { message: '验证码已发送' } }),
  // ... all 174 endpoints
};

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  const key = `${req.method} ${parsed.pathname}`;
  const handler = routes[key] || routes[`GET ${parsed.pathname}`];

  if (handler) {
    const body = [];
    req.on('data', chunk => body.push(chunk));
    req.on('end', () => {
      const data = handler(parsed.query, body.length ? JSON.parse(Buffer.concat(body).toString()) : {});
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(data));
    });
  } else {
    // Fallback: return generic success for unmatched routes
    console.log(`⚠️  Unmatched: ${key}`);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ code: 0, data: {} }));
  }
});

server.listen(PORT, () => console.log(`Mock server on http://localhost:${PORT}`));
```

### Step 4: Configure metro.config.js Proxy

Expo uses `metro.config.js` with `http-proxy-middleware`. Change the proxy target to local mock server:

```javascript
// In metro.config.js, find the proxy configuration
// Change url[index] to point to mock server
const url = [
    'http://localhost:9999',  // ← Mock server (was remote API)
    'https://realtest.hmalls.cn:9998/ucard',
    'https://app.denatrust.com',
];
const index = 0;  // ← Changed from 2 to 0

// The proxy uses enhanceMiddleware pattern:
apiProxy = createProxyMiddleware({
    target: url[index],
    changeOrigin: true,
    secure: false,
    pathRewrite: { '^/api': '/api' },
});
```

**Key difference from Vite**: Expo uses `defaultConfig.server.enhanceMiddleware` to intercept requests, not `server.proxy` in vite.config.ts.

### Step 5: Run Both Servers

```bash
# Terminal 1: Mock server
node scripts/mock-server.js

# Terminal 2: Expo dev server
EXPO_NO_TELEMETRY=1 expo start --web
```

### Expo / React Native Route Auth Gate Pattern

When an Expo/RN migration branch has static route/auth guard scripts (for example `check-rn-route-auth.mjs`), treat them as contract tests as well as behavior tests. They may enforce explicit source patterns so future agents cannot bypass auth by accident.

1. Keep route metadata explicit: every mobile route object should declare `requiresAuth`, login/public auth routes must be `false`, and bottom-tab routes must all be protected routes.
2. Resolve rendering through the gated route object (`getMobileRoute(activeTab)` → `currentRoute` → `currentRoute.component`), not directly from tab state.
3. Hide bottom tabs on login/public auth routes with a source-visible guard such as `currentRoute.id !== 'login' && (...)`; if an additional auth flow or selected feature is active, put that condition inside the guarded expression rather than obscuring the login guard.
4. Pass a bounded session setter into `LoginScreen` (`onAuthenticated={setAuthSession}`) and run post-login profile/security synchronization in `App` via a token-keyed effect. This keeps LoginScreen from mutating broader global/auth-flow state while still allowing App to enter setup-login-password, PIN setup, device trust, or protection flows after `refreshAuthProfile()`.
5. Prevent profile-sync loops by recording the last access token synced; skip profile sync for dev visual/auth-bypass sessions used only for screenshot parity.

### Pitfalls for Expo Mock Server

1. **npm install fails in Expo projects**: Use Node.js built-in `http` module, not Express. Expo's dependency tree has strict peer dep constraints.

2. **metro.config.js proxy structure**: The proxy is NOT in `server.proxy` like Vite. It's in `defaultConfig.server.enhanceMiddleware` which wraps the middleware function.

3. **FormData handling**: Expo's axios interceptor sends `multipart/form-data` with FormData. Mock server must handle multipart parsing or accept any Content-Type.

4. **BASE_URL is conditional**: `process.env.NODE_ENV === 'development' ? '/api' : 'https://app.denatrust.com/api'`. Mock server only works in dev mode because that's when requests go through `/api` proxy. **FIX for production builds**: Change to `Platform.OS === 'web' ? '/api' : (process.env.NODE_ENV === 'development' ? ... : ...)`. This makes web always use relative paths (works with both proxy in dev and same-origin in prod). Native keeps full URLs. Without this fix, production builds will call the remote API instead of the local mock server.

5. **Path parameters**: Endpoints like `/api/ucard/${id}/details` need regex matching in mock server, not exact string match. Use a route matcher that handles `:id` patterns.

6. **Token in headers**: The app sends `Authorization` header with stored token. Mock server should accept any token value — don't validate.

7. **Fallback handler is critical**: Unmatched routes should return `{ code: 0, data: {} }` not 404. This prevents the app from crashing on endpoints you haven't mocked yet. Log unmatched routes to build the complete list iteratively.

8. **Loop until flow closed**: Run the app, navigate every screen, watch mock server logs for unmatched routes → add handlers → repeat until zero unmatched.
