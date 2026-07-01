# React Native Mobile UI Production Closeout

Use when an RN/mobile avatar or assistant shell is functionally implemented but the user says it feels ugly, Home-only, generic, debug-like, or not production-grade.

## Applicability

- React Native/mobile shells with Home plus secondary product surfaces.
- Stitch/design-tool artifacts have been mapped into runtime surfaces, but UX still feels like a prototype.
- Simulator demo shows routes exist, but navigation discoverability or page identity is weak.
- User asks for enterprise/production-grade delivery or explicitly says the UI workflow was skipped.

Anti-conditions:
- Pure backend/API work.
- One-off visual copy changes without mobile delivery or simulator proof.
- External release gates such as App Store/TestFlight/MDM unless explicitly authorized.

## Required Sequence

1. **Do not defend route availability as usability.** If the user says it feels Home-only or ugly, treat that as a UX failure even if tests pass.
2. **Run a UI audit before more feature fill.** Inspect simulator screenshots for hierarchy, wrapping, CTA clarity, navigation labels, touch targets, and debug/engineering copy.
3. **Separate primary UX from diagnostics.** The default user surface should show status, next useful action, and clear action cards. Move Monorepo, authority chain, dry-run, device IDs, internal alpha, canonical facts, URLs, and raw projection status to Settings/Diagnostics or hide them behind a secondary affordance.
4. **Make navigation visible and cross-surface.** Home controls need text labels, not only abstract icons. Secondary pages should have a visible segmented switcher/tab row so users can move between Release, Control, Knowledge, Text, Voice, and Settings without returning Home.
5. **Productize copy.** Block system-code strings in user-facing UI: examples include `RESTORE_SYSTEM_DEFAULTS`, `ACTIVE MONITORING`, `VERIFIED`, `FINALIZED`, `PROCESSING`, `Ask Hermes anything`, `canonical facts`. Replace with localized product language.
6. **Add negative and positive regression tests.** Verify the productized page title/actions exist and engineering/debug copy is absent by default. Keep route tests for every visible tab or CTA.
7. **Harden the production gate.** Add a user-facing-copy guard to the local gate if the project has one, so future changes cannot reintroduce raw system/debug copy.
8. **Verify on simulator after reinstall.** Run native lint/Jest, the project production gate, reinstall to the simulator, capture screenshots, and visually compare before/after.
9. **Write closeout evidence.** Produce a UIMax-style report with before/after grades, screenshot paths, final verification command output, remaining P2 issues, and release boundaries.

## Verification Checklist

- Native lint/Jest passes.
- Production gate passes, including accessibility and user-facing-copy checks.
- Workspace tests/build pass if the project is a monorepo.
- Simulator build/install/launch succeeds after the UI changes.
- At least Home screenshot is captured and inspected; route tests cover secondary screens.
- UIMax/report/ledger explicitly state external release boundaries: no App Store/TestFlight/MDM/real-device voice/cloud-write claim unless separately verified.

## Pitfalls

- **Functional route ≠ acceptable UX.** A technically reachable secondary page can still feel like Home-only if the user sees icon-only controls or every destination opens the same generic detail frame.
- **Engineering copy is not transparency.** Diagnostic truth belongs behind Settings/Diagnostics, not in the main product surface.
- **A beautiful screenshot can still fail flow truth.** Keep tests for route transitions, action receipts, and return paths.
- **Do not fake full production release.** Local production-grade prototype is a valid closeout category distinct from external distribution readiness.
