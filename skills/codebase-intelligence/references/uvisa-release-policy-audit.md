# UVISA-scoped release policy backend audit checklist

Scope/applicability: use only for UVISA backend / UVISA H5/APK/OTA release-policy reviews. This is a project-scoped reference under the broader codebase-intelligence skill, not a global API rule.

Anti-conditions: do not apply these file paths, enum names, permissions, or schema assumptions to non-UVISA projects. For UVISA, always re-check current code before citing an observed path or migration as still true.

## Core risk model

Client release policy is a high-impact operational control plane. Treat it as production config, not as normal content:

- One wrong ACTIVE/current policy can force-update or unblock all clients.
- Rollback is itself a publish event and must be audited as strongly as publish.
- Static config, `SystemEvent`, admin page state, and public `/api/app/version` must not become competing sources of truth.
- Public response caching can make a correct DB write ineffective.

## UVISA evidence anchors from 2026-06 review

Re-verify before reuse:

- `api/api-public/.../AppVersionController.java` returned static config fields only: `latest`, `forceUpdate`, `releasedAt`.
- `app/.../SecurityConfig.java` publicly permitted `/api/app/version`.
- `api/api-admin/.../system/AdminMaintenanceController#pushRelease` wrote only `SystemEvent RELEASE_PUSH` and did not update a client-readable release-policy SSOT.
- `ReleaseNote` Java code supported `ROLLED_BACK`, while migration `V613__release_note.sql` constrained `status IN ('DRAFT','PUBLISHED')`.
- `RequiresPermission#gaRequired` enforcement depended on `uvisa.security.ga-enforce`; prod should fail closed if false/missing.

## P0 checks

1. SSOT
   - There must be exactly one authoritative client-readable source for active release policy, preferably DB-backed `client_release_policy_current` or equivalent.
   - `SystemEvent` is audit/event evidence, not the public source of truth.
   - Config fallback must be bootstrap-only; DB/read failure should not silently return stale static config in prod.

2. Single ACTIVE/current invariant
   - Enforce at DB level that only one active/current policy exists per `(platform, channel)`.
   - Service-level “check then insert/update” is insufficient under concurrent publish.
   - Preferred shape: immutable `policy_revision` table plus unique `policy_current(platform, channel)` pointer.
   - Alternative MySQL pattern: generated nullable active key with unique index for ACTIVE rows.

3. Concurrent publish / rollback
   - Publish and rollback must lock or CAS the current `(platform, channel)` pointer.
   - Mutations should accept `expectedCurrentPolicyId` and return 409/conflict if stale.
   - Rollback should create a new rollback revision or atomically move the current pointer with audit; avoid blindly “reactivating previous_policy_id”.

4. GA / permission
   - Publish, rollback, force update, and minimum-supported-version mutations require `@RequiresPermission(..., gaRequired=true)`.
   - Verify prod `uvisa.security.ga-enforce=true`; if prod can start with false, call it P0.
   - Tests should prove missing/wrong `X-GA-Code` rejects these endpoints.

5. DB constraint mismatch
   - Compare Java state machines against Flyway CHECK constraints.
   - For release notes, either DB allows `ROLLED_BACK` or code/API must remove that state.
   - Add FK and status/platform validation for `release_note_id` referenced by release policy.

## P1 checks

1. Version comparison
   - Do not compare version strings lexicographically.
   - Store/derive sortable fields: build code, semver parts, or monotonic H5 build id.
   - Public API should accept current client version/build and return server-authoritative `updateRequired` / `forceUpdate` instead of forcing clients to infer.

2. Platform enum consistency
   - Normalize H5 naming (`WEB`, `WEB_H5`, `APP`, `H5`) across DB CHECK, Java enum, admin form, and public API.
   - Explicitly define how native shells loading H5 map to policy: `ANDROID/IOS` app policy vs `WEB` bundle policy.
   - Response should include `resolvedPlatform`/`platform` and `channel`.

3. Rollout percent
   - DB CHECK `0 <= rollout_percent <= 100`, default 100.
   - Use deterministic bucketing: hash stable user/device/install id + policy id.
   - Minimum-supported hard block must not be bypassed by rollout.

4. Audit
   - Add explicit `@OpLog` with action names such as `release.policy.publish` and `release.policy.rollback`.
   - Capture old/new policy ids, reason, expected current id, admin id, trace id, IP/UA, and GA result.
   - Keep `SystemEvent` as business event if useful, but admin accountability belongs in structured admin op log.

5. Cache consistency
   - All reads should go through a release-policy service, not direct controller/repository ad hoc queries.
   - Evict/update Redis/local cache after transaction commit on publish/rollback.
   - Public response should include `policyId`, `publishedAt`, `source`, and optionally `etag`.
   - Admin publish should read back through the same service before returning success.

## Suggested review output shape

Report material blockers only:

```text
P0
- [Title]
  Evidence: file/path or schema/API fact
  Risk: concrete failure mode
  Fix: DB/service/API/test changes

P1
- ...
```

Avoid listing generic best practices unless tied to a UVISA evidence point or a specific proposed schema/API gap.
