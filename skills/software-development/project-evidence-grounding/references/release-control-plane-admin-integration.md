# Release Control Plane Admin Integration

Scope/applicability: class-level pattern for admin/product tasks where an existing version-management, maintenance, force-update, APK/package, or release-notes page already exists and a new client runtime release-control plane must be added. Anti-condition: skip this reference for greenfield admin consoles with no existing release/version surface, or for pure documentation-only planning.

## Lesson

Do not default to a brand-new standalone admin entry just because the release-control model is new. First inspect the existing admin version-management surface and decide whether the new control plane should be integrated as a tab/panel there.

Preferred landing shape when an existing admin version page exists:

1. Keep the existing sidebar/menu entry.
2. Add a scoped tab/panel for client runtime releases inside that page.
3. Preserve existing maintenance, force-update, native package, and release-note behavior untouched.
4. Keep the runtime release-control domain model independent: release records, rules, candidates, rollback preview, rollback execution, and append-only audit.
5. Do not overload release notes, force-update minimum-version fields, or raw OTA payload URL fields as the runtime release source of truth.

This gives small-surface product integration without corrupting domain boundaries.

## Anti-patterns

- Adding a separate sidebar entry before checking whether the current admin version page should own the feature.
- Treating release notes as runtime releases.
- Treating “mark release note rolled back” as real client runtime rollback.
- Replacing candidate selection with a simple dropdown when the action requires resource, health, API-compatibility, or eligibility evidence.
- Shipping fake UI with hardcoded demo rows, fake ids, or local fallback data after the backend contract exists.
- Modifying PRD/prototype docs when the user only asked to implement/admin-integrate an already accepted interaction.

## Real-UI gate

For release-control admin surfaces, every visible row/action should come from a real service call or a real empty/error state. Screenshot fixtures may intercept APIs for visual review, but fixture scripts must stay outside production code or be explicitly test-only and must not introduce local absolute imports or local machine paths into tracked code.

## Verification checklist

- Existing admin version-management surface was inspected before adding navigation.
- Final navigation matches product scope: tab/panel in existing page unless there is a strong reason for a standalone entry.
- Existing version-note, package, force-update, and maintenance controls still build and remain reachable.
- Candidate release selection is table/drawer based when eligibility matters.
- Backend has real persistence/API/audit; frontend service calls those APIs directly.
- No PRD/prototype docs were changed unless explicitly requested.
- Build/compile was rerun after moving the integration point.
