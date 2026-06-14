# Local Vite frontend against online backend

Scope: mobile/PWA frontend UI verification where the UI must run locally but API calls should hit the deployed backend through the same-origin Vite dev server. This avoids browser CORS/preflight drift and matches the user's expectation that Network shows local `/api/...` requests while the proxy forwards to the online domain.

## Rule

Prefer Vite proxy for local UI + online backend checks:

```bash
VITE_DEV_API_PROXY_TARGET=https://<online-app-or-api-host> \
  pnpm exec vite --host 0.0.0.0 --port 5179 --strictPort
```

Do **not** set `VITE_API_BASE=https://.../api` for this verification mode unless the user explicitly wants direct cross-origin browser calls. Setting `VITE_API_BASE` makes browser requests go directly to the online domain and can trigger CORS/preflight differences; it also prevents the expected local `/api/...` Network trace.

## Required cleanup before starting

Vite can silently move to another port when the requested port is occupied. Before presenting a URL to the user:

```bash
lsof -nP -iTCP:5179 -sTCP:LISTEN || true
lsof -nP -iTCP:5180 -sTCP:LISTEN || true
# kill stale node PIDs that belong to older Vite previews/dev servers if needed
```

Then start with `--strictPort` so stale processes fail fast instead of producing confusing delayed watch notifications on `5180`.

## Verification

1. Verify the transformed client still uses proxy mode:

```bash
curl -sS http://127.0.0.1:5179/src/lib/api.ts \
  | grep -E "VITE_API_BASE|const API_BASE"
```

Expected: no concrete online `VITE_API_BASE`; `const API_BASE = import.meta.env.VITE_API_BASE || "/api"` remains.

2. Verify the proxy actually reaches the online backend:

```bash
curl -i -X POST http://127.0.0.1:5179/api/auth/send-code \
  -H 'Content-Type: application/json' \
  -d '{"email":"<test-email>"}'
```

Expected request URL from the browser/user's Network panel: `http://127.0.0.1:5179/api/...`.
Expected response evidence: upstream headers such as `server: railway-hikari`, `x-railway-edge`, or the deployed backend's canonical JSON envelope.

For endpoints with side effects such as `send-code`, tell the user if the verification may send an email/SMS before or immediately after doing it.

## Pitfalls

- `VITE_API_BASE=https://.../api` is direct browser cross-origin, not Vite proxy.
- `VITE_DEV_API_PROXY_TARGET` only works when the app's runtime API base stays `/api`.
- Delayed background watch notifications can mention old processes/ports after they were killed. Check live listeners with `lsof` before trusting the notification.
- If a proxy target returns 502, do not conclude the online backend is down until checking whether the target host/path is the correct backend owner for `/api` and whether the dev server is the current process/port.
