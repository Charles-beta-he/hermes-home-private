# PWA Production Readiness Gate

Use when a local PWA/mobile web surface has passed UI/interaction gates and the user asks to push toward production, release readiness, or 可生产上线, but external deploy/push/real-device authority is not yet granted.

## Goal

Turn a visually accepted PWA into a locally production-ready artifact without crossing external release boundaries. The gate should be runnable as a single command (for example `make prod-verify`) and should fail closed before publish/deploy authority.

## Minimum local production bundle

1. Build gate
   - TypeScript/build passes.
   - Generated app shell assets are present.

2. PWA install metadata
   - `manifest.webmanifest` includes `name`, `short_name`, `start_url`, `scope`, `display`, `theme_color`, `background_color`, and maskable icon.
   - `index.html` includes viewport with `viewport-fit=cover`, theme color, manifest link, favicon, apple mobile web app meta, and apple touch icon.

3. Service worker app shell
   - Cache only an explicit app-shell allowlist: `/`, `/index.html`, built JS, manifest, icon, and SW itself if needed.
   - Do not broad runtime-cache all same-origin GETs.
   - Bypass API/WebSocket paths.
   - Cache only successful same-origin responses (`response.ok` and `response.type === 'basic'`).
   - Offline browser smoke should navigate to a fresh route not previously loaded (for example `/offline-smoke-route`) to prove fallback, not just reload the initially cached URL.

4. Production preview server
   - Serve only an explicit static asset allowlist when bound to LAN/`0.0.0.0`; do not expose `src/`, `e2e/`, package files, or `node_modules`.
   - Add security headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`.
   - CSP should include at least `default-src 'self'`, `object-src 'none'`, `base-uri 'none'`, and `frame-ancestors 'none'`. Keep `connect-src` scoped to intended local controller origins for local preview.

5. Readiness gate script
   - Check manifest/meta/icon/SW/server requirements statically.
   - Scan committed user-facing/source files for hardcoded credential shapes relevant to the project.
   - Fail closed if app-shell allowlist or security headers are missing.

6. Browser production smoke
   - Use the production-preview server, not a generic dev static server.
   - Verify actual response headers.
   - Verify manifest MIME/content.
   - Verify SW active.
   - Verify denylisted source/dev paths return 404.
   - Verify offline fallback from a new route.

7. Review and commit
   - Run full local bundle plus static secret/dangerous-code scans.
   - Ask an independent reviewer to probe SW caching, static-server exposure/path traversal, header false confidence, and offline false-pass paths.
   - If reviewer flags blockers and you patch them, rerun deterministic gates and ask for a final scoped review before committing.

## Human authority boundary

Local production-readiness does not authorize:

- `git push`
- CDN/server/domain deployment
- real HTTPS certificate or DNS changes
- real phone installation claims
- app-store/PWA distribution
- real hardware/camera long-run safety certification
- production safety/legal claims about the domain model

Emit a DecisionPacket/ContinuationPacket when the next step is one of those external or authority-bound actions.

## Common false passes

- Offline smoke reloads the URL visited online, so runtime cache hides a broken app-shell fallback.
- Production readiness script only searches source strings for header names but no browser smoke verifies actual headers.
- Preview server uses `SimpleHTTPRequestHandler` over the whole app directory and leaks development files on LAN.
- Service worker caches failed responses or arbitrary same-origin GETs.
- A reviewer passed before a non-blocking hardening edit; the final diff still needs another review.
