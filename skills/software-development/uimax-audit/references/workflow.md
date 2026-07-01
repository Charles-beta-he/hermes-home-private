# Workflow

Extracted from `/Users/charles/.hermes/skills/software-development/uimax-audit/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Workflow

### Phase 1: Visual Audit (browser tools)

For each page/component:

0. **Classify the surface before scoring**: is it user-facing product UI, secondary diagnostics, or engineering/operator UI? Do not let engineering diagnostics (Monorepo, authority chain, dry-run, device IDs, internal alpha, raw URLs) count as acceptable default mobile UX. If they appear on a primary mobile user page, score information architecture as D/F until they are moved behind Settings/诊断 or a secondary disclosure.
1. **Read the UI test ledger first** (`docs/UI_TEST_CASES.md`, project Workpad, or equivalent) and choose the exact flow/status to verify.
2. **Navigate** to the page in browser-harness / a real browser at the target viewport.
3. **Actually perform the documented flow**: click, type, submit, back/interrupt, switch theme/language, and confirm finish/error states. Do not score from screenshots alone.
4. **Check console** for JS errors: `browser_console(clear=true)`
5. **Inspect network/storage where relevant**; redact tokens/passwords/private values in reports.
6. **Screenshot + analyze**: `browser_vision(question="Analyze UI quality...", annotate=true)`
7. **Test interactions**: touch target size, press feedback, loading/error states, fixed header/bottom-nav safe-area, keyboard/focus/ARIA, reduced-motion, dark/i18n contrast.
8. **Note issues** with severity and category, and link each issue to the test case ID and evidence path.

**Important**: React CSR apps may show "Empty page" in browser_snapshot. Use browser_vision screenshots instead.

**Acceptance rule**: UIMax scoring is secondary to flow truth. A visually polished screenshot is not a pass if the documented business flow was not actually completed through the browser.

**Mobile/RN readiness rule (hard gate)**: Do not claim `A+`, `production-ready`, or `local-production ready` UI from lint/Jest/production gates alone. For each user-facing surface touched by the change, require fresh simulator/device pixel evidence and explicitly audit: top safe-area/header spacing, bottom tab color/height/item spacing/active state, chip wrapping/clipping, composer input+CTA layout, contrast, and default engineering-copy leakage. If any surface cannot be captured because of OS permissions or tooling, report a human gate instead of downgrading the evidence requirement or claiming UI readiness. For RN simulator work, prefer native UI-test-driven route navigation plus screenshot capture during a deliberate hold window; see `references/react-native-simulator-uimax.md`.

**No oral pass rule**: If the user says “严格验收”, “不要口头”, or challenges why UIMax was not used, stop summarizing intentions and produce hard evidence only: failing screenshot = continue fixing; wrong-route/loading/home-screen screenshot = invalid evidence; final answer must cite the actual commands, screenshot paths, and report/profile updates.

**PWA/mobile bottom-tab A+ rule**: For tabbed mobile/PWA surfaces, a visible screenshot of the tab bar is insufficient. The gate must explicitly verify fixed/sticky placement intent, active tab visibility, content-to-nav gap, fixed-nav overlap (`contentOverlapNav === 0` or equivalent), horizontal overflow, touch targets, console health, and at least one narrow viewport. If the task uses thresholds, document the threshold and actual metrics; do not claim `100%`/perfect coverage unless the code enforces and the report proves exactly that. See `references/pwa-mobile-tab-uimax.md`.

**RN global-tab hard gate**: When a React Native app has bottom navigation, do not accept a Home-only tab as a pass. The tab belongs in the shared app shell/layout, with stable `testID`s and unique button-level `accessibilityLabel`s. Native UI tests should assert `app.buttons["底部导航：…"]` instead of inner text `StaticText`s, because Pressable labels may not be exposed as standalone text. Prefer a non-overlay bottom layout slot; if a floating/absolute tab is used, prove it does not cover composers, cards, or list endings. Capture Home, Input/composer, Settings/detail, and modal/diagnostics states in the screenshot matrix. See `references/react-native-global-bottom-tab-closeout.md`.

### Phase 2: Code Audit (terminal/file tools)

Scan source code for quality metrics:

```
# Inline styles count per file
search_files(r'style=\{', target='content', path='src/', file_glob='*.jsx')

# ARIA attributes
search_files(r'aria-', target='content', path='src/', file_glob='*.jsx')

# tabIndex usage
search_files(r'tabIndex', target='content', path='src/', file_glob='*.jsx')

# Focus styles in CSS
search_files(r':focus', target='content', path='src/', file_glob='*.css')

# Hardcoded colors (not CSS vars)
search_files(r"(?:color|background|border).*#[0-9a-fA-F]{3,8}", target='content', path='src/')

# prefers-reduced-motion
search_files(r'prefers-reduced-motion', target='content', path='src/')

# CSS variable coverage
# Count defined vs used in CSS files
```

### Phase 3: Generate Report

Write `UIMAX_REPORT.md` with:
1. Overall scores per dimension (table)
2. Per-page/component grades
3. Code quality statistics
4. Prioritized issue list (P0/P1/P2)
5. Optimization roadmap for next loop iteration

### Phase 4: Optimization (P10 strategy)

Based on scores, prioritize:
1. **P0 (blocking)**: Accessibility gaps — tabIndex, :focus, ARIA
2. **P1 (important)**: Static inline style migration, hardcoded colors
3. **P2 (nice-to-have)**: CSS variable coverage, responsive polish

After fixes: `pnpm test && pnpm build` → re-run Phase 1-3 to verify improvement.

### Taste rejection after a green audit

If tests, gates, and screenshots pass but the user says the UI is still ugly, do **not** keep defending the grade or endlessly micro-tune the same visual language. Treat this as a design-direction failure, not a QA failure:

1. Separate evidence quality from taste acceptance: A/A+ verification means the implementation is well-evidenced, not that the design direction is approved.
2. Stop changing production/RN code unless the user explicitly asks for direct implementation.
3. Build a short redesign PRD that states the visual problem, target product feeling, non-goals, information architecture, and acceptance criteria.
4. Produce a browser-viewable prototype with a new design thesis and a small number of meaningful variants.
5. Verify the prototype opens cleanly and key interactions work, then ask the user to pick a direction before implementation.

For RN/mobile shell cases, see `mobile-frontend-delivery` reference `references/rn-redesign-prd-before-implementation.md`.
