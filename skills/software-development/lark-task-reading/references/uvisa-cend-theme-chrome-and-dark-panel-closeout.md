# UVISA C-end theme chrome + dark-panel UI closeout notes

Scope: UVISA `uvisa-app-2.0` C-end UI Lark tasks where screenshots show Android/PWA status bar, navigation bar, safe-area strips, or dark-mode detail panels with poor contrast.

Applicability:
- The task is user-end UI/PWA presentation, not backend money/auth semantics.
- The app supports an explicit in-app light/dark/system theme choice.
- The symptom involves OS theme and app theme disagreeing, or a nested detail panel remaining light while dark-mode text tokens are applied.

Anti-conditions:
- Do not apply this to backend/API data correctness, payment/PIN/security semantics, or admin UI without separately checking that surface's theme architecture.
- Do not hardcode these colors into global skills for other projects; use the current project's surface tokens.
- Do not close Lark final from local tests/build alone; online UI retest remains required for `uvisa-app-2.0`.

## Pattern: app theme must own system chrome color

Symptom:
- Android/system is dark, but the app is explicitly set to light/day mode.
- Top status bar or bottom navigation/safe-area region still renders as a black block.

Likely cause:
- Static `<meta name="theme-color" media="(prefers-color-scheme: dark)">` still follows OS preference, not the app's resolved theme.
- Android PWA/WebView/system chrome can pick the dark theme-color even when the app DOM is `data-theme="light"`.

Fix pattern:
1. Keep first paint aligned: in `index.html` bootstrap, after resolving the persisted/system app theme, set `data-theme` and update every `meta[name="theme-color"]` content to the app-resolved color.
2. Keep runtime changes aligned: in the theme store/applyTheme path, update all existing theme-color metas when the app theme changes or rehydrates.
3. Use product surface tokens, e.g. light `surface.base`, dark `surface.dark`, matching existing design tokens.
4. Add a regression test that inserts both light/dark `theme-color` metas, sets app theme to light, and asserts both metas now contain the light app chrome color. This catches OS-dark/app-light mismatch.

Pitfall:
- Do not rely only on `media="(prefers-color-scheme: light|dark)"` when the product lets users choose an explicit theme. OS preference and app theme are separate authorities.

## Pattern: hardcoded light panels fail dark text-token inversion

Symptom:
- Dark-mode detail page has labels/values such as recipient/account rows present but visually unreadable.

Likely cause:
- A nested detail panel uses a hardcoded light background while dark-mode text tokens invert globally.

Fix pattern:
1. Replace hardcoded light backgrounds with semantic surface tokens, e.g. `bg-surface-alt dark:bg-surface-elevated` in this project.
2. Keep label/value text on existing ink tokens (`text-ink-400`, `text-ink-900`) so global dark-mode overrides remain consistent.
3. Add a focused UI test for the exact detail panel: assert semantic panel classes and row text classes. Prefer testing the existing screen route/state rather than a detached component.

## Verification sequence

- First write a failing targeted test for each atom.
- Run the narrow Vitest command and confirm the failures are atom-specific.
- Implement minimal theme/panel changes.
- Re-run narrow tests, then `pnpm run build`, then `git diff --check`.
- If there are unrelated dirty files, stage only the task files and review/commit the staged diff.

## Closeout boundary

For UVISA `uvisa-app-2.0` Lark tasks, this proves implementation-sendback only. Final Lark completion still needs deployed/online UI retest evidence and any required screenshot/native attachment gate.
