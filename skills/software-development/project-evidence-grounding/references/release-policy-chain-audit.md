# Release / Version Policy Chain Audit Pattern

Scope: class-level pattern for product-grounded audits of app/admin release or version-update flows.
Applicability: use when an admin release/version control is expected to change client runtime behavior.
Anti-conditions: do not use for ordinary code deployment checklists, marketing release notes with no client gate, or project-specific facts that should live in a project profile.

## Why this matters

A release button is not a release chain unless it closes the loop from admin intent to client behavior. A UI action that only writes an audit/event row can look successful in admin while the client continues reading static config or another source of truth.

## Evidence map to build

1. Product contract
   - Startup/version gates: strong update vs optional update, dismiss rules, maintenance pages.
   - Admin surface requirements: release notes, per-platform release, permissions, second-factor approval, rollback.
   - Status model: draft/published/rolled-back; remove obsolete states if product says no scheduled release.

2. Admin implementation
   - Page handlers and service calls for publish/push/rollback.
   - Whether the action writes business state or only system/audit events.
   - Permission and second-factor gates.
   - Platform enum translation in UI vs backend.

3. Backend write path
   - Controller endpoint called by admin.
   - Service/repository/entity/migration behind it.
   - Whether it updates a client-readable single source of truth, such as a release-policy/config table, or just logs an event.
   - Database constraints vs code status transitions.

4. Public client read path
   - Public version endpoint and data source.
   - Static config fallbacks vs admin-managed state.
   - Client comparison logic and route gate location.

5. Client activation mechanism
   - For browser/PWA apps, the actual new code is delivered by deployed assets plus Service Worker; admin policy only decides prompt/blocking semantics.
   - Verify cache headers, Service Worker registration, and prompt behavior when relevant.
   - Avoid treating a standalone payload URL as real unless a client consumer exists.

## Red flags

- Admin publish endpoint returns success but only writes an audit/system event.
- Public version endpoint reads static environment/config while admin edits another table/event stream.
- Version check exists only in About/Settings, not at startup before auth routing.
- Product has force/optional update semantics, but client only displays an informational toast.
- Platform enums differ silently across product docs, admin UI, backend, and database.
- Database constraints lag code transitions, such as code writing rolled-back states while migrations allow only draft/published.
- Browser/PWA release flow exposes a payload URL without any frontend downloader/consumer.

## Recommended closure shape

- Establish a client-readable release policy SSOT, such as a release-policy or runtime-config table.
- Admin publish writes policy plus audit event; audit event is not the state source.
- Public version endpoint reads active policy with config fallback only for bootstrap.
- Client startup gate enforces force/optional decisions before normal routing.
- Browser/PWA update activation remains user-triggered via Service Worker; force update blocks business access but does not silently reload active tabs.
- Rollback restores a previous active policy rather than deleting history.

## Minimal verification checklist

- Admin publish changes the public version endpoint response without backend redeploy.
- Optional update is dismissible and suppression is keyed by target version.
- Force update cannot be bypassed into protected routes.
- Rollback changes public response back to prior policy.
- Release note text displayed on the client comes from the same release/policy record.
- Platform/status enums and database constraints match the product contract.
