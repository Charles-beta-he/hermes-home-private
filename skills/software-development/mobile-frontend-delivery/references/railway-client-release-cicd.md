# Railway Client Release CI/CD for Silent PWA/H5 Updates

Use when a mobile H5/PWA is deployed by Railway Docker services and must support silent, per-user release manifests rather than simple container-overwrite deploys.

## Key Lesson

Railway can remain the CI/CD trigger, but a plain `Dockerfile -> build dist -> nginx serves current dist` deploy does **not** close a silent hot-update loop. Each deploy replaces the container image, so old chunks disappear unless assets are also copied into a versioned, retained release store. That breaks old pages doing dynamic imports and causes chunk 404 / white screens.

## Target Shape

Keep Railway services:

1. `backend`: DB migrations, release/rule/audit/event/asset APIs, manifest decision.
2. `admin`: governance UI only; operators publish/gray/rollback registered releases.
3. `app`: static H5/PWA service plus `/api` proxy and `/releases/{releaseId}/...` release asset serving.

For test environments, use a Railway Volume mounted at `/data/releases` for retained release assets. Long-term production should prefer OSS/S3/R2 + CDN, with Railway only serving current shell/proxy.

## Required App Changes

1. Add `scripts/generate-client-release-manifest.mjs`.
2. Add package script:
   - `build:release = tsc -b && vite build && node scripts/generate-client-release-manifest.mjs`
3. Generate `dist/release-manifest.json` with:
   - `releaseId`, `runtimeVersion`, `platform`, `buildNumber`, `gitSha`, `createdAt`
   - `assetBaseUrl`, `manifestUrl`
   - `entrypoints` (`index.html`, `sw.js` if applicable)
   - `assets[]`: path, type, size, sha256/integrity, cacheControl
   - `apiContractVersion`
4. Docker build should use `pnpm run build:release` and pass build args/env such as `RELEASE_ID`, `RUNTIME_VERSION`, `API_CONTRACT_VERSION`, `PUBLIC_APP_BASE_URL`.
5. App container entrypoint should copy built `dist/**` into `/data/releases/{releaseId}/` and then start nginx.
6. Nginx should serve:
   - `/` and `/index.html`: `no-cache, must-revalidate` / no-store as appropriate
   - `/sw.js`: `no-cache, no-store, must-revalidate`
   - `/releases/{releaseId}/release-manifest.json`: `no-store`
   - `/releases/{releaseId}/assets/*`: `public, max-age=31536000, immutable`

## Required Backend Changes

1. Add `client_release_asset` table. The manifest controller must not reference a table that the migration does not create.
2. Add an internal idempotent registration endpoint, e.g. `POST /api/internal/client-releases/register`.
3. Authenticate internal registration with `X-Internal-Token`, not admin JWT and not `permitAll`.
4. Registration should upsert:
   - `client_release`: default `BUILT` or `VERIFIED`, not auto-`ACTIVE`
   - `client_release_asset`: `manifest_json`, asset hashes, cache headers, status
   - append-only audit operation such as `ci_register`
5. Public `GET /api/client-release/manifest` should return release metadata plus `assetManifest` from `client_release_asset`.

## Railway Variables

App service:

- `BACKEND_INTERNAL_URL=http://<backend-service>.railway.internal:8080`
- `CLIENT_RELEASE_INTERNAL_TOKEN=<shared-secret>`
- `RELEASE_PLATFORM=H5`
- `API_CONTRACT_VERSION=api-v1`
- `RUNTIME_VERSION=web-<git-sha-or-timestamp>`
- `PUBLIC_APP_BASE_URL=https://<app-test>.up.railway.app`
- `RELEASES_DIR=/data/releases`

Backend service:

- `CLIENT_RELEASE_INTERNAL_TOKEN=<same-shared-secret>`
- DB/Redis/Flyway profile vars as usual

Admin service:

- `BACKEND_INTERNAL_URL=http://<backend-service>.railway.internal:8080`

Prefer leaving frontend `VITE_API_BASE` empty so nginx `/api` same-origin proxy is used.

## Deployment Order / Retry

Railway may not strictly order multi-service deploys. Make app registration resilient:

1. backend deploys and healthcheck passes;
2. app deploys, waits for backend `/health`, then registers release;
3. registration retries for several minutes and is idempotent;
4. nginx may start even if registration fails, but logs must clearly show the failed registration;
5. admin lists registered `BUILT/VERIFIED` releases and operators publish/gray/rollback.

Do **not** automatically make every Railway build `ACTIVE`; Railway deploy is artifact registration, not release decision.

## Client Runtime Follow-up

After Railway manifest generation/registration exists, the client runtime must not mark a new release `pending` until assets are ready:

1. fetch `/api/client-release/manifest`;
2. fetch `manifestUrl` with `cache: no-store`;
3. preload/verify listed assets (HTTP 200 and optional sha256/integrity);
4. only then mark `assetReadyReleaseId` and `pendingReleaseId`;
5. activate only at safe boundaries.

## Verification Evidence

Minimum proof of closure:

- Railway app build log shows `build:release` and generated `release-manifest.json`.
- `/releases/{releaseId}/release-manifest.json` returns `200` with `Cache-Control: no-store`.
- hashed assets return `200` with immutable cache headers.
- backend registration returns accepted/upserted and DB read-back shows `client_release` + `client_release_asset`.
- admin lists the release without mock data.
- manifest endpoint returns the expected release and non-empty `assetManifest`.
- client runtime preloads assets, then activates at a safe boundary.
