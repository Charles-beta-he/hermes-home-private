# Core Workflow

Extracted from `/Users/charles/.hermes/skills/software-development/browser-harness-integration/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Core Workflow

```
Task Execution Complete
    ↓
Build Verification Passes
    ↓
Start Dev Server
    ↓
┌─────────────────────────────────────┐
│ 0. Test Ledger Walkthrough          │
│    - Read project UI test cases     │
│    - Open real browser/harness      │
│    - Actually click/type/navigate   │
│    - Inspect console/network/storage│
├─────────────────────────────────────┤
│ 1. Dogfood Testing (per page)       │
│    - Page screenshot                │
│    - Console error check            │
│    - Interactive element testing    │
│    - Issue collection               │
├─────────────────────────────────────┤
│ 2. Visual Regression Check          │
│    - Current vs baseline screenshot │
│    - AI difference analysis         │
│    - Regression detection           │
├─────────────────────────────────────┤
│ 3. UIMax / UI Skill Audit           │
│    - 6-dimension scoring (A-F)      │
│    - ui-ux-pro-max constraints      │
│    - baseline/a11y/motion checks    │
│    - Optimization suggestions       │
└─────────────────────────────────────┘
    ↓
Generate Verification Report
    ↓
Stop Dev Server
```

### User/Project Preference: Real Browser Walkthrough First

For projects with an existing UI test ledger (for example `docs/UI_TEST_CASES.md`), treat browser-harness / real-browser walkthrough as the primary UI acceptance evidence. Automated screenshot scripts such as `npm run ui:regression` are guardrails, not substitutes for opening the app and truly walking the flow.

Required sequence for UI work:
1. Read the project Workpad and UI test-case ledger before testing.
2. Start the dev/mock environment and verify health.
3. Open the page in browser-harness/real browser at the target viewport (mobile 375/390 for H5 apps unless specified).
4. Follow the documented test case step-by-step: click, type, submit, go back, interrupt flows, switch theme/language, and verify completion state.
5. Capture screenshots plus console, network, and storage observations; redact tokens/passwords/private data.
6. Apply UI quality constraints from `ui-ux-pro-max`, `uimax-audit`, `baseline-ui`, accessibility, and motion/performance skills: touch targets, safe-area/bottom-nav avoidance, no horizontal overflow, dark/i18n contrast, feedback/loading/error states, animation timing, focus/ARIA, and recovery paths.
7. For auth-gated frontend-only UI validation, if the task does not require real account/backend semantics and unit/build gates already prove the logic, it is acceptable to inject a clearly labeled test auth state into localStorage/sessionStorage to reach protected routes. Record this as `browser UI with mocked auth state`, not as full product/business acceptance. Still inspect console errors and verify rendered user-facing text/DOM state.
8. Run automated guards (`ui:regression`, Playwright, unit/build) after the real walkthrough to catch deterministic regressions.
8. Deposit evidence paths and verdicts back into the UI ledger / Workpad.

Pitfall: Do not declare UI acceptance from script screenshots alone. A script can prove selected pages render, but it may miss wrong flow semantics, broken back behavior, missing feedback, stale storage, or a visually acceptable screen reached through an invalid path.

### UI Evidence Closeout Rule

When the user provides a live UI reference surface (for example a local built-in dashboard URL and start command), treat it as the primary visual/interaction source before guessing from filenames or generic patterns. Open the reference in the browser, extract actual DOM/computed-style evidence for scroll containers, bounded panes, overflow behavior, and interaction affordances, then mirror the class-level pattern in the target UI. For Hermes-style dashboards, the durable pane pattern is `min-height: 0`, bounded flex/grid children, `overflow-y: auto`, `overflow-x: hidden`, `scrollbar-gutter: stable`, and contained overscroll; verify with browser harness/DOM probes that long lists scroll internally and do not create horizontal overflow.

For dense control consoles/inboxes, a browser harness PASS is not enough unless the harness targets the changed surface. Build a surface-specific Playwright/DOM probe that asserts both positive and negative UI contracts: required lead/list/detail panes exist, unwanted panels (for example permission matrices that burden the workflow) are absent, page horizontal overflow is zero, scroll panes are bounded, readable widths/heights hold across desktop-short and breakpoint-band viewports, and cards are not vertically clipped. Always inspect the generated screenshot after the script passes; if text is vertical, cramped, or visually unusable, the UI regression remains open even if issueCount is 0.

When a capability/safety model exists behind a control panel, do not automatically render it as a visible permission matrix. Verify the user's intended experience: control panels should reduce manual intervention by presenting next actions; safety belongs at the action point, audit receipt, or secondary diagnostics/safety panel unless the user explicitly asks to see the permission model. For a concrete Human Inbox regression and harness checklist, see `references/control-console-human-inbox-ux-regression.md`.

For Hermes-style local control consoles where writable buttons depend on a generated dashboard snapshot plus a live localhost API, use `references/control-console-live-session-readback.md`. Do not close the browser verification after seeing that a button is enabled; prove the actual click, API write, local ledger row, regenerated snapshot projection, and UI readback receipt all agree. Short-lived capability/session state should come from live API health/status, not only from a potentially stale generated snapshot.

When closing a frontend/UI-affecting task, distinguish these evidence levels explicitly:

- Unit/store/service tests prove mapping/logic only.
- Multi-model review can suggest missing cases, but model agreement is not UI evidence.
- Playwright/browser-harness evidence is required before saying “UI 回测已通过” or “browser verified”.
- Target-surface proof is mandatory: before capturing evidence, identify the exact page/tab/modal/filter state named by the task, navigate to it, and record visible anchors in the screenshot/report (active tab text, URL/route, breadcrumb, selected filter, table header, or modal title). If a task says “业绩统计 tab 下” or names specific columns, a screenshot from the default sibling tab (for example “理财师管理”) is invalid even if the surrounding module is correct. Treat wrong-tab/wrong-filter screenshots as `UI evidence invalid / rerun required`, not as partial pass.
- Default Lark/admin UI evidence viewport: capture screenshots as a 14-inch desktop browser interface (use a 1512×982 CSS viewport unless the project has a more specific 14-inch profile). Do not use narrow/mobile screenshots for admin evidence unless the task explicitly targets mobile H5. Label the viewport in the report and screenshot filename.
- User preference: 验收严禁 mock，除非用户明确允许。Do not use mocked-auth, mocked API, mock-server, synthetic fixtures, or intercepted browser routes as acceptance evidence unless the user explicitly asked for/allowed mocks. If only mock evidence exists, label it as a non-acceptance developer check and continue to real auth + real backend + real interface data, or report that true acceptance is not yet done.

### Playwright Script + Screenshot + Log Evidence Chain

When borrowing or evaluating an external “webapp testing” pattern, do not import the external skill until source and license are verified. Map the useful pattern into this harness instead:

1. Use only an existing project dependency (`@playwright/test`/`playwright`) unless installation is explicitly in scope.
2. Produce a stable evidence bundle outside ephemeral `test-results/`: script path, exact command, URL, viewport, environment/dependency source, screenshot, console/pageerror/requestfailed log, storage assertions when relevant, and machine-readable summary.
3. Include a dry-run mode that prints planned checks/artifact paths without launching the browser.
4. Label scope precisely: a script+screenshot guard proves the selected page/interaction, not full product semantics or backend contract closure.
5. When an external verification-loop product or CLI is the source of the pattern, absorb only the class-level contract first: self-consistent failure bundle, run/snapshot/code-version integrity, partial marker, resumable timeout, exit-reason taxonomy, and explicit external-service gates. See `references/optional-external-verification-loop-backend.md`.
6. Keep any project-specific example reports in the project/Workpad evidence surface rather than treating them as global requirements.

### Prototype URL Comparison / Project Memory Capture

When the user provides a frontend prototype URL (for example a design demo or clickable product prototype) and asks whether implementation matches it:

1. Treat the URL as a durable project fact if it is project-specific: add it to the project Workpad/project memory, not global memory, and label it as `prototype/design reference` rather than a real backend/test environment unless proven otherwise.
2. Open the prototype route in browser-harness and walk the target flow, recording exact visible step labels, CTA labels, warning copy, default factor/channel, demo codes/password hints, and final state.
3. Compare against the current implementation at the same route/flow using real browser evidence plus code/test evidence when available.
4. Classify differences by source-of-truth:
   - `matches prototype`: visual/interaction semantics align.
   - `intentional task-driven divergence`: current task/PRD/security requirement supersedes prototype (e.g. replacing old-phone OTP with current-account email/SMS step-up). Do not call this a bug; explain why it is safer/better and task-compliant.
   - `prototype drift / implementation gap`: no task/PRD reason supports the mismatch; record follow-up.
5. Do not let a prototype demo path certify backend semantics. A prototype can validate UI copy/flow shape only; auth/OTP/PIN/security contracts still require real backend or inspected controller/service evidence.

For i18n/toast/error-state fixes, add at least one browser-level assertion that drives the user flow and checks the rendered user-facing text in the active language, including a negative assertion that the raw backend message in the wrong language is not visible. Prefer running both desktop Chromium and mobile viewport projects when the app is H5/mobile-first.

If auth-gated local UI verification is blocked because the app bootstrap/profile fetch clears your injected storage session and bounces back to `/login`, use the deterministic mocked-auth + mocked-API Playwright pattern in `references/mocked-auth-mocked-api-local-ui-verification.md`. This is the preferred fallback for local UI evidence when the task scope is frontend rendering/interaction verification rather than real auth or backend business acceptance.

Evidence path durability: Playwright may clean or overwrite `test-results/` during later runs. For evidence that will be referenced in docs/Workpad/TG closeout, write reports/screenshots to a stable temp path such as `/tmp/<project>-<scope>-<date>/...` or copy them there before running additional Playwright commands.
