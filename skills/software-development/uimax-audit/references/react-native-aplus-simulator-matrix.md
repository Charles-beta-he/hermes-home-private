# React Native A+ Simulator UI Matrix

Use this reference when a React Native / mobile shell is already functionally reachable and the user asks for `A+`, `极限`, `全推A+`, or equivalent UI/UX closeout. Applicability: local/simulator UI delivery where external publish is not authorized. Anti-condition: do not claim App Store/TestFlight/production deployment from local simulator proof.

## A+ acceptance target

A+ is not a visual opinion. Require all of these before finalizing:

1. Code slice landed for the target UI improvement.
2. Regression tests cover the new interaction/negative state.
3. Production/UI gate checks the new anchors and accessibility contract.
4. Simulator/device app is rebuilt/reinstalled/launched.
5. Screenshot matrix covers every primary page plus any hidden/diagnostic disclosure surface.
6. Contact sheet is generated and visually audited.
7. Final verify command passes after screenshots/report updates.
8. Report and scoped project/profile/ledger are updated.
9. Boundaries are explicit: no external publish, no push, no real-device hardware claim, no cloud write-back unless actually authorized and verified.

## Recommended screenshot matrix

For a mobile assistant/avatar shell, capture at least:

- `00-home`: first screen with primary CTA/navigation visible.
- `01-release` or equivalent readiness/risk surface.
- `02-control` or main control room.
- `03-knowledge` or asset/library surface.
- `04-input` or text task composer.
- `05-voice` or voice/status surface.
- `06-settings` with preference controls such as reduced motion.
- `07-diagnostics-sheet` or equivalent secondary disclosure for engineering/operator diagnostics.

Generate a contact sheet so visual review covers the full matrix in one artifact. Do not call the matrix complete if one labeled screenshot is actually a duplicate/mis-hit of another page.

## Diagnostics containment pattern

Default product UI must not expose engineering terms such as internal flags, raw mode names, URLs, device IDs, blocked/internal statuses, authority chains, or sync/projection counters. Move them behind Settings → Diagnostics / 诊断详情, ideally as a bottom sheet or modal.

For A+ diagnostics disclosure:

- The default settings page states that diagnostics are hidden by default.
- The diagnostic surface is explicitly labeled and secondary.
- The sheet/modal has backdrop, handle or clear affordance, close button, and modal accessibility semantics.
- Tests assert default-hidden, open, and close behavior.
- It is acceptable for engineering terms to appear inside the diagnostic sheet if the default user flow stays clean.

## Reduced motion pattern

If the UI has an avatar/orb/particle animation, add a visible reduced-motion control or respect the platform setting. For local RN closeout, at minimum:

- Add a settings toggle with `accessibilityState` reflecting selected/on state.
- Pass `reducedMotion` into the animation component.
- Stop repeat animations and continuous renderer/profile intervals when reduced motion is enabled.
- Add a regression test for the toggle state and gate anchors.

## Simulator click fallback pattern

When screenshot navigation via coordinates is unreliable:

1. Prefer app/test route proof for behavior, then use simulator screenshots for pixels.
2. If background `computer_use` click is denied, use safe local macOS automation only if allowed by the environment and without clicking permissions/secrets.
3. Calibrate from a fresh screenshot; avoid assuming previous coordinates after scroll or simulator window movement.
4. Use the accessibility tree / AX button index as a fallback when coordinate clicks miss.
5. After every click, capture and visually verify page identity before labeling a screenshot.
6. If a click mis-hits, replace the screenshot and rebuild the contact sheet; do not silently accept a duplicate.

## Report template

A concise A+ report should include:

- Final grade and scope, with a local-vs-production boundary.
- Screenshot evidence paths.
- Page matrix table with PASS/FAIL per screen.
- Improvements completed: diagnostics containment, motion accessibility, navigation/discoverability, gates/tests.
- Final verification output summary.
- Explicit non-claims: no external publish/push/deploy/hardware/cloud write-back unless actually done.

## Verification checklist

- [ ] All screenshots are current and match their labels.
- [ ] Contact sheet visually audited.
- [ ] Final verification command ran after the last report/profile updates if those updates are part of the deliverable.
- [ ] Project/profile/ledger readback confirms status and grade.
- [ ] No claim exceeds the evidence boundary.
