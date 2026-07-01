# React Native mobile extreme UI/UX closeout pattern

Applicability: class-level procedure for React Native mobile assistant/control-room shells that are already functionally reachable but fail visual, information-architecture, or user-facing polish expectations.

Anti-conditions: do not use this as proof of external release readiness, real-device microphone readiness, cloud-write readiness, or app-store distribution readiness. Project-specific paths, screenshots, bundle IDs, and one-off progress records belong in the project profile or ledger, not in this reference.

## Trigger signals

- User says the app is only functionally reachable, not visually acceptable.
- User says the UI optimization workflow was skipped.
- User asks to refine UI/UX “to the limit” or equivalent.
- Simulator screenshot shows a primary mobile surface dominated by branding/visual effects, debug copy, or generic explanation instead of clear next actions.

## Class-level rule

Do not claim UI/UX closeout from route tests alone. For mobile avatar/control-room apps, completion requires both:

1. Flow truth: tests for route transitions, action receipts, collapsed diagnostics, and accessibility labels.
2. Pixel truth: simulator screenshots showing first-screen hierarchy, text wrapping, task affordances, bottom-nav clarity, and absence of default engineering diagnostics.

## Extreme-pass checklist

1. Run a compact objective gate: success criteria, non-goals, boundaries, selected reversible path.
2. Audit screenshots for first-screen questions:
   - Is the assistant ready?
   - What can the user do next?
   - Where are knowledge, voice, settings, and release/readiness surfaces?
   - Is any engineering/debug copy visible by default?
3. Home surface must include more than brand/orb/status:
   - visible state/readiness
   - 2–3 high-priority action cards or chips
   - one direct composer/task CTA
   - explicit bottom navigation labels
4. Collapse diagnostics by default:
   - raw URLs, device IDs, dry-run/mode names, authority chains, repository details, projection/cache internals, and raw runtime status belong behind `诊断详情` or equivalent.
   - Add a regression test that the diagnostics panel is absent before toggling and present only after explicit action.
5. Productize copy:
   - Replace system-code/status words such as `RESTORE_SYSTEM_DEFAULTS`, `ACTIVE MONITORING`, `VERIFIED`, `PROCESSING`, and English placeholders with local-language user-facing labels.
   - Replace implementation terms such as `handoff`, `projection`, `canonical facts`, and `dry-run` with user-relevant state such as `回读确认`, `核心记录`, `草稿`, or `已保存` unless diagnostics are explicitly open.
6. Harden gates:
   - Add stable test IDs for home quick actions and diagnostics toggle/panel.
   - Count pressable accessibility labels/roles in production gate.
   - Add a copy guard for banned system/debug phrases.
7. Verify:
   - native lint + Jest
   - production gate
   - full workspace verify/build/security gate
   - simulator reinstall/launch
   - screenshot + UIMax re-audit for every touched user-facing surface, not only the Home/default route
   - mandatory mobile pixel checklist: top safe-area/header spacing, bottom-nav background/color/spacing/active state, chip row clipping/gaps, composer input+CTA grouping, contrast, and stale visual-system leftovers
8. Record boundaries honestly:
   - local-production UI prototype is not external distribution, real-device voice, or cloud-write production.

## Scoring guidance

- B/B+: Functionally reachable, clear labels, no obvious engineering copy, but weak first-screen action density.
- A-: First screen contains state, high-priority task affordances, direct CTA, explicit nav, collapsed diagnostics, and tests/gates/simulator screenshot evidence.
- A/A+: Adds screenshot automation for every secondary tab, reduced-motion/animation verification, bottom-sheet/modal diagnostics, and real-device interaction checks.
