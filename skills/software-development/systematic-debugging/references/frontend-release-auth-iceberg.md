# Frontend release/auth iceberg scan

Use when a frontend change adds app-wide runtime checks, release manifests, auth interceptors, public routes, or payment verification side effects. The visible bug may be a single 401 or duplicate request, but the hidden failures are usually at route/auth/telemetry boundaries.

## Pattern A — pre-auth release/runtime checks

Symptom: login/verification/public page shows 401 for a runtime endpoint such as `/api/client-release/manifest`.

Scan boundaries:
1. Route model: compare the runtime hook's public-route predicate against the app's canonical public route gate. Do not duplicate an exact route list if the app uses prefix matching or public support routes.
2. Transport: pre-auth checks must use a static/public read path (for example `fetch('/version.json', { cache: 'no-store', credentials: 'omit' })`) instead of the authenticated API client.
3. Telemetry: static pre-auth sync must not report through authenticated API event endpoints. A stale `auth_token` in localStorage can otherwise turn a fixed manifest call into a new `/events` 401/auth-expired loop.
4. Serving config: every deploy/static-server config used by the project must serve the static manifest explicitly with JSON content type and no-store, not just the Docker template. Check for config drift between template nginx config, root nginx config, local static server, and CDN rules.
5. Activation semantics: authenticated users on post-login setup routes may still need the authenticated manifest API; unauthenticated public routes should use the static manifest.

Regression tests to add:
- unauthenticated `/login` and prefix public routes read `/version.json` and do not call the authenticated manifest API;
- stale local `auth_token` during pre-auth static sync does not call authenticated telemetry/events;
- authenticated post-login setup routes still use the authenticated manifest API.

## Pattern B — OTP success followed by downstream submit failure

Symptom: `/auth/otp/verify` succeeds, but an inline payout/remit submit rejects; the UI then re-verifies the same 6-digit OTP and shows "code expired" instead of the real business failure.

Root cause pattern: a broad `.catch()` wraps both the OTP verify promise and the async downstream submit. If it resets the in-flight lock after OTP success, the consumed OTP can be submitted again when React effects rerun with the same code state.

Fix shape:
- distinguish "OTP verify failed before success" from "downstream business submit failed after OTP success";
- keep the OTP verify lock after a successful OTP response;
- only reset the lock for OTP verification failures or failed OTP responses;
- surface downstream submit errors as business/network submission errors, not OTP errors.

Regression test:
- mock OTP verify success;
- mock inline remit/payout submit rejection;
- assert `/auth/otp/verify` is called exactly once and the consumed OTP is not re-opened for retry.

## Pattern C — online public-page verification after release/runtime fixes

After merging a pre-auth release/runtime fix, verify the deployed public page, not just local tests:
1. Open the real acceptance URL on a cache-busting public auth route (for example `/login?<probe>`).
2. Inspect resource timing for `client-release`, `version.json`, `manifest`, and auth-related URLs.
3. Expected pre-auth shape: `/version.json` returns 200/no-store, `manifest.webmanifest` may load, and protected `/api/client-release/manifest` / `/api/client-release/events` must not appear.
4. Trigger foreground paths (`focus`, `visibilitychange`) and re-check resource timing; they should still read only the static manifest while unauthenticated.
5. Check console errors and JS exceptions are empty.
6. Read local release-runtime state: `currentReleaseId` may be set from static version; `userBoundReleaseId` should remain null; no auth token should be required.

Anti-conditions:
- Do not treat project-specific URLs, release IDs, or branch names as class-level facts; keep those in a project profile or final report only.
- Do not login with real credentials unless explicitly requested; pre-auth verification should prove the public surface without secrets.
