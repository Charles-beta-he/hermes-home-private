# Railway PWA production verification after PR merge

Scope: use for web/PWA frontends deployed on Railway where a GitHub PR merge is expected to update a public URL. This is not a rule for non-Railway deploys or repos whose CI/CD has a different release source of truth.

## Lesson

A green PR check and merged GitHub PR do not prove the public PWA URL is serving the new bundle. Verify the deployed HTML and JS assets directly.

## Procedure

0. Establish the canonical production origin before diagnosing PWA installability or cache headers.
   - Ask/confirm which URL is the user-facing online address if multiple domains exist (for example a Railway default domain plus a vanity/CDN domain).
   - Run installability, SW, manifest, and Android Chrome proof against that canonical origin.
   - Treat header/cache defects on non-canonical comparison domains as separate routing/CDN cleanup, not as blockers for the current online PWA verdict.
1. Confirm GitHub state:
   - PR is `MERGED`.
   - PR/push build checks are `SUCCESS`.
   - Note the merge commit SHA and PR URL.
2. Check any production-release dispatch workflow separately from PR checks.
   - A push-triggered workflow that queries `commits/{sha}/pulls` can race GitHub indexing immediately after squash merge and fail with a false "commit not associated with merged PR" error.
   - If the only failure is this race and the PR is now visibly merged, rerun the failed workflow and watch it to success.
3. Do not trust the locally linked Railway environment blindly.
   - `railway status` can be linked to one environment while the user-facing URL is on another.
   - Use `railway status --json` or `railway deployment list --environment <env> --service <service> --json` to identify which environment owns the public domain.
4. If deploying manually with `railway deployment up --ci` times out after upload, inspect `railway deployment list` before retrying.
   - The CLI may have created a `BUILDING` deployment even though the local request timed out.
   - Poll that deployment to `SUCCESS`/failure instead of immediately repeating the same upload.
5. Verify the public URL by reading deployed artifacts:
   - Fetch the HTML with a cache-busting query and no-cache headers.
   - Extract `/assets/*.js` bundle paths from HTML.
   - Fetch those bundles and search for deterministic markers from the change, e.g. new copy, enum keys, or debug labels.
   - For PWA work, also fetch `/manifest.webmanifest` and `/sw.js` to confirm installability-critical assets still respond correctly.
6. Browser smoke-check the real URL when UI/debug surface changed.
   - For debug-panel work, verify the expected text appears on the live page, not just in built assets.

## Local preview against the production backend

When the user asks to inspect a local build while using the Railway/production backend, prefer Vite proxy mode over direct cross-origin API calls:

```bash
VITE_DEV_API_PROXY_TARGET=https://<public-railway-app-host> \
  pnpm exec vite --host 0.0.0.0 --port 5179 --strictPort
```

Expected shape:

- `src/lib/api.ts` keeps `API_BASE = import.meta.env.VITE_API_BASE || '/api'`.
- Do **not** set `VITE_API_BASE=https://.../api` for this browser inspection path unless intentionally testing CORS; that makes the browser call the remote domain directly and changes the network shape.
- The browser Network panel should show local requests such as `http://127.0.0.1:5179/api/...`; Vite then proxies them to the Railway host.
- Verify proxy linkage with both sides:
  - fetch the transformed module, e.g. `curl http://127.0.0.1:5179/src/lib/api.ts`, and confirm `VITE_API_BASE` is absent while `VITE_DEV_API_PROXY_TARGET` is present.
  - call one harmless API through local `/api/...` and confirm response headers such as `server: railway-hikari` / `x-railway-edge`.
- Use `--strictPort` and clear stale Vite listeners before restarting. Delayed background watch notifications can mention old process IDs/ports; verify the live listener with `lsof -nP -iTCP:<port> -sTCP:LISTEN` or the current process handle instead of trusting late notifications.

Branch/environment alignment matters: if the user is testing a branch-backed environment such as `test`, start the local preview from `origin/test` plus the candidate patch (cherry-pick/reapply) rather than from `main`, then report the branch, HEAD, and whether `origin/test` is an ancestor.

For visual issues on tab bars or route-scoped chrome, first verify the current browser route actually renders that component. Flow pages such as remit/topup/payment may show bottom CTAs, not the main bottom TabBar.

## Evidence to report

- PR URL, merge commit, GitHub check status.
- Railway environment + deployment id + status for the public domain.
- Public URL asset filename currently served.
- Marker strings found in the live bundle.
- For local preview: exact branch/HEAD, proxy target, transformed `API_BASE` evidence, and one `/api/...` response header proving Railway backend proxying.
- Manifest/SW status if PWA install behavior is involved.

## Pitfalls

- Deploying to one Railway environment because the local link points there, then checking a URL served by another environment and thinking deploy failed.
- Treating a CLI timeout as failed upload without checking whether a deployment exists.
- Reporting PR merged as "live" before public HTML references the new asset hash.
