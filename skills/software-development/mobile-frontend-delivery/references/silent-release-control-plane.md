# Silent Release / OTA Control Plane Pattern

Scope/applicability: class-level pattern for web, PWA, or WebView clients that need long-term silent hot update, per-user version alignment, or operator-governed rollback. Anti-condition: skip for ordinary release-note pages, simple native app-store upgrade prompts, or one-off cache-busting fixes.

## Decision

This is not primarily an SSR problem. SSR may help dynamic entry HTML, but the durable solution is a release control plane:

- Release Manifest decision service: user/platform/channel/region/app-shell/native-version -> release.
- Stable App Shell: fetch manifest, preload assets, activate at safe boundaries, report boot/chunk errors, rollback.
- Versioned assets: release-scoped directories on object storage/CDN.
- Admin governance surface: full release list, action candidate tables, rollback/health/audit.

## Admin interaction pattern

Do not make ordinary dropdowns the main release selector. Use:

1. Release List page as full governance view.
2. Release Detail drawer for assets, compatibility, rules, health, user hits, and audit.
3. Action drawer/modal candidate table for publish/gray/rollback/override.

Candidate table fields:

- release identifier, name, platform, runtime version
- status, health status, asset status
- API contract version, minimum shell/native version
- boot success, white-screen, chunk-load, and JS-error indicators
- selectable, recommended, disabled reason

The backend should provide candidate filtering by usage, for example rollback, publish, gray, user override, or channel policy.

## Rollback interaction

Rollback should not be a small confirm button. Use a gated flow:

1. Show current release and health/error context.
2. Choose target from candidate Release table.
3. Backend preview returns impact analysis: affected rules/users, state changes, activation semantics, risks.
4. Require reason type + reason text.
5. Require re-entering the target release identifier.
6. Require privileged confirmation or GA when available.
7. Execute backend transaction: status changes, rule changes, append-only audit with before/after.
8. Show observation panel: manifest return rate, boot success/fail, chunk errors, users still on old release.

## Data-model minimum

Use three conceptual ledgers:

- Release lifecycle/resource/compatibility/health records.
- Release decision rules for platform/channel/region/user/gray/hash matching.
- Append-only release audit with before/after and reason.

CDN/object storage must keep rollback targets and active releases. CDN cache is not the source of truth.

## Existing admin/version-management integration

Scope/applicability: use this when a product already has an admin release, maintenance, version notes, native upgrade, or OTA page and the task asks to add silent client release governance. Anti-condition: if the task is greenfield admin design, a separate top-level release console may be acceptable.

Do not assume the long-term release control plane must be a brand-new top-level menu. Prefer a small-surface integration when it preserves semantics:

- Reuse the existing admin module, permissions, privileged confirmation, toast/layout primitives, and audit entry points.
- Add a dedicated "Client Release" tab/panel under the existing release/maintenance page when operators already treat that page as the release center.
- Keep the release domain model independent: do not overload release notes, force-upgrade minimum version, native package version, or a single OTA payload URL as the web runtime release source of truth.
- Distinguish labels in the UI: release notes are user-facing changelog; force upgrade is a minimum-version gate; client release is the manifest/runtime decision surface.
- If first built as an isolated page for risk control, refactor it into the existing module before closeout when the user asks for small-surface admin changes or no duplicate entry.

## Evidence and no-fake-UI gate

Scope/applicability: use this for screenshots and visual acceptance evidence of admin release-control work. Anti-condition: explicit design-mockup requests may use mock data if clearly labeled as mock.

- Screenshots are acceptance evidence only when they come from the real target surface.
- Do not use route mocks, fake local data, fake permissions, or synthetic auth to prove an admin interaction unless the user explicitly asks for a mockup.
- If real admin login is blocked, report the blocker and the real backend response; do not substitute a mock screenshot. Continue landing non-visual layers that do not require the blocked credential.
- If login succeeds but create/list/read-back returns a structured not-found response, check whether the frontend dev proxy points at a backend that has not deployed the new release-control APIs. Treat this as a deployment alignment blocker, not as UI proof or a reason to add mock rows. See `references/release-control-plane-real-verification.md`.
- Avoid throwaway screenshot scripts with hard-coded absolute local imports. Prefer normal package resolution from the project context, such as project-local CLI execution or environment-based module resolution, rather than machine-specific import paths.
- Treat PRD/prototype documents as user-controlled artifacts: if the user says not to modify them, update only implementation/code or skill references, not project PRD/prototype files.

## Full-stack landing checklist for silent release work

When the user asks to fully land silent client hot-update / release-control work, do not stop at admin screens or a manifest endpoint. Carry the implementation across these real layers unless an authority boundary blocks it:

1. Admin integration: prefer the existing release/maintenance/version-management module as a tab/panel; avoid duplicate top-level entries unless greenfield.
2. Admin rule control: release detail should expose rule list and real create/enable/disable APIs for `GRAY`, `PERCENTAGE`, `WHITELIST`, `BLACKLIST`, `USER_OVERRIDE`, `CHANNEL`, and `REGION`; writes should append audit records.
3. Backend SSOT: keep release, rule, event, and audit ledgers separate from version notes, native package records, force-upgrade minimums, or a single OTA payload URL.
4. Manifest decision: backend chooses by platform/status/resource/health, rollback priority, rule priority, black/white/user override/channel/region rules, and stable user hash buckets. The frontend must not randomly choose gray users.
5. Client runtime: fetch manifest on boot/login/logout/user-switch/foreground/safe route, track `currentReleaseId`, `pendingReleaseId`, `userBoundReleaseId`, and `lastKnownGoodReleaseId`, activate only at safe boundaries, and never show a version-update toast for this silent path.
6. Failure rollback: report boot success, detect boot-watchdog timeout and chunk/dynamic-import errors, mark bad releases locally, and fall back to last-known-good. Event reporting must never block user flows.
7. Verification: run backend compile, admin build, client tests/build, and at least one real read-back/API/browser check when credentials and local services allow it. If admin auth is blocked, state the exact blocker and the seed/account needed; do not mock acceptance evidence.

## Product/PRD notes

Scope/applicability: use this when an admin/backend release control plane must be connected to a web/PWA/WebView user client for silent hot update. Anti-condition: skip for ordinary changelog pages, app-store-only native upgrades, or design-only prototypes.

When continuing from release governance into the actual user client, do not stop at an admin-only control plane. Wire a stable client runtime at app-shell level:

1. Install global handlers before React/app render for previous-boot watchdog and chunk/dynamic-import failures.
2. Add a shell hook near auth/router state, not inside individual business pages. It should sync manifest on boot, login success, logout, user switch, route safe-boundary, and foreground/focus.
3. Keep local state explicit: `currentReleaseId`, `pendingReleaseId`, `userBoundReleaseId`, `lastKnownGoodReleaseId`, `runtimeVersion`, and bad-release markers.
4. Treat manifest fetch failure as non-blocking: continue with current/last-known-good release and never show a version-update toast.
5. Make manifest readable before login/cold start, but keep event/reporting endpoints authenticated or protected by signing/rate limits if anonymous reporting is required.
6. Safe-boundary activation should be conservative: main tabs/login surfaces only, no dirty forms (`[data-dirty="true"]` / `[data-form-dirty="true"]` or project equivalent), and no transaction/KYC/payment/confirm/password routes.
7. On activation, write a boot marker and use `location.replace`; report activation. On successful mount, clear the marker and report boot success. If a later boot sees an expired marker, mark the release bad and roll back to `lastKnownGoodReleaseId`.
8. Chunk-load or dynamic-import errors should mark the current release bad and report evidence, but must not interrupt the current user flow beyond the browser/runtime failure already happening.

## Evidence and no-fake-UI gate additions

Scope/applicability: use this for screenshots and UI acceptance evidence of release-control work. Anti-condition: explicit design-mockup requests may use mock data if clearly labeled as mock.

- For release-control screenshots, never use route interception, fake auth, fake permissions, or local mock release data as acceptance evidence unless the user explicitly asks for a mockup. If real auth fails, report the exact backend response and continue implementable backend/client work instead of fabricating screenshots.
- Avoid temporary screenshot helpers that import project packages through machine-specific absolute paths. Prefer project-local execution or environment-based module resolution. If a temporary helper is needed, keep it outside the repository and do not present it as product code.

## Product/PRD notes

PRD/prototype should define operator roles, permissions, safe activation boundaries, release states, rollback/fuse thresholds, and audit expectations. It should not present a version dropdown as the whole product requirement. If the user says not to modify PRD/prototype artifacts, update implementation and skills only; do not create or edit project PRD/prototype files.
