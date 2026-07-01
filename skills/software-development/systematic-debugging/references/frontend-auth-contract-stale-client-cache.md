# Frontend auth-contract changes vs stale browser/PWA clients

## Applicability

Use this when a browser/PWA client reports API `BAD_REQUEST`/`UNAUTHORIZED`/generic parameter errors immediately after an auth/session/OTP/PIN/payment-security contract change, while current source or current deployed bundle appears correct.

Typical signals:
- Screenshot/network panel shows an auth-sensitive endpoint failing, but current source sends the required field/header.
- A recent frontend change introduced an intermediate auth state (for example pending-login / step-up / MFA token) before a formal session token is written.
- Current live HTML or bundle contains the fix marker, but a user still reproduces old behavior.
- The app is a PWA or has a service worker/update prompt/cache layer.

Anti-conditions:
- Do not use this to excuse a real backend contract mismatch. First inspect the backend controller/service requirement and the actual request shape.
- Do not store project URLs, branch names, commits, or credentials in this generic reference. Resolve them from the active project each time.

## Debugging path

1. **Identify the failing contract boundary.**
   - From screenshot/network: endpoint, method, response code/message, timestamp, request body and headers if available.
   - Map visible page -> component/screen -> service wrapper -> store/state producer.

2. **Separate body parameters from auth/session headers.**
   - Auth endpoints may still expect an empty body but require a bearer header derived from a pending/step-up token.
   - Do not describe this as “missing body params” until request payload and headers have both been checked.

3. **Read git history for the contract split.**
   - Find the commit that introduced the intermediate state, e.g. storing `pendingToken` instead of formal `auth_token`.
   - Find the later commit that updated downstream calls to forward that token/header.
   - Check which remote branches contain both commits, and whether patch-equivalent hashes exist on the target branch.

4. **Verify current served artifact content, not only source.**
   - Fetch live HTML, extract hashed JS assets, download the active bundle, and search for robust markers: endpoint string plus required header/field/state key.
   - Fetch `/version.json` or the release manifest when present and record releaseId/createdAt/build metadata.
   - If build metadata is `unknown`, state that artifact proof comes from bundle-content markers, not commit metadata.

5. **Inspect service-worker/update posture.**
   - Check whether the SW is prompt-only vs auto-update, whether `skipWaiting`/`clientsClaim` are disabled, whether index/assets were historically precached or runtime-cached, and whether JS/CSS stale-while-revalidate caches existed in earlier versions.
   - A current SW fix only helps clients after the new SW/entrypoint is loaded and activated; already-open tabs or installed PWAs can continue old code.

6. **Classify the root cause.**
   - If current served bundle contains the required request shape, but user screenshot lacks it, classify as stale client runtime/cache/update activation — not current source/backend drift.
   - If served bundle lacks the marker, classify as deployment/branch/build mismatch.
   - If served bundle has marker and the live request still lacks it after a clean reload, inspect state production (token missing/expired/not persisted) before blaming cache.

## Verification checklist

- [ ] Current source call shape and backend required contract were both read.
- [ ] The introducing commit and fixing commit (or patch-equivalent commits) were identified.
- [ ] Remote branch containment was checked after fetch when branch freshness matters.
- [ ] Served HTML/bundle was fetched and searched for the fix marker.
- [ ] SW/update/cache behavior was checked for old-client persistence.
- [ ] The report distinguishes: current deployed behavior, stale client behavior, backend contract, and user remediation.

## User remediation patterns

For one affected browser/PWA client:
- Hard reload / close all tabs and reopen.
- DevTools Application -> Service Workers -> unregister, then Storage -> clear site data.
- If the app exposes a rescue script, use it to unregister service workers and clear Cache Storage, then reload.

For product hardening:
- Auth/session contract changes should be treated as release-boundary changes; use force/safe-boundary reload rather than relying only on optional update prompts.
- Ensure release metadata includes the build commit/sha so cache-vs-deploy investigations do not depend solely on minified bundle string search.
- Keep a rescue endpoint/script for installed clients trapped behind old service workers or removed hashed chunks.
