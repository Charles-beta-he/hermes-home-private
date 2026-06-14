# UVISA C-end linked UI issue implementation pattern

Scope: UVISA `uvisa-app-2.0` user-end Lark tasks pasted as Task Center URLs where the user asks to “分析解决问题” / solve the issues, and the task surfaces are UI/i18n/PWA rather than backend money/auth semantics.

## Pattern from session: grouped C-end UI fixes

When several linked tasks touch adjacent C-end UI surfaces, still keep each acceptance atom explicit:

- Tab/nav visual issue: assert the rendered component uses a dedicated class or token, not a generic shared surface class that may affect other chrome. For bottom tab bar opacity/background fixes, a test can assert `TabBar` uses `tabbar-glass` and does not use generic `.glass`.
- FAQ/i18n issue: static knowledge-base data is not covered by ordinary `i18n/*.json` keys. Add a language-aware adapter layer for question/answer/category labels and update search to operate on localized entries. Test the actual screen in English and assert English categories/questions are visible while Chinese source strings are absent.
- PWA install waiting issue: browser/native install prompts are outside app control, but the app can show a loading toast before invoking the prompt/description-profile navigation. For iOS/profile and browser install branches, render loading text, wait for next paint, then call the native/browser handoff. Tests that assert `location.assign` or prompt calls must `await waitFor(...)` after next-paint logic is introduced.
- Android/PWA theme-chrome issue: when system theme and app theme disagree, do not let static `theme-color` metas keep following `prefers-color-scheme`; synchronize system chrome color to the app's resolved theme at first paint and runtime theme changes. See `references/uvisa-cend-theme-chrome-and-dark-panel-closeout.md`.
- Dark-mode detail-panel issue: if text tokens invert but a nested card keeps a hardcoded light background, replace that background with semantic surface tokens and test the exact routed screen. See `references/uvisa-cend-theme-chrome-and-dark-panel-closeout.md`.

## Verification sequence

1. Write or update targeted RED tests for each atom before implementation.
2. Run the narrow Vitest command and confirm failures are atom-specific, not syntax/setup errors.
3. Implement the minimal UI/i18n/PWA changes.
4. Re-run the narrow tests.
5. Run `pnpm run build`; TypeScript often catches test fixture shape drift, e.g. mocked `CustomerServiceConfig` must include all required fields.
6. Run `git diff --check` before commit.
7. If the working tree has unrelated pre-existing changes or the current upstream branch is gone, make a scoped local commit with only the task files. Do not push or mix unrelated dirty files unless the user explicitly authorizes branch/push cleanup.

## Closeout boundary

For UVISA/Lark C-end tasks, local code/test/build + scoped commit is only implementation-sendback evidence. Do not mark Lark complete from local proof alone. Final Lark completion still needs deployed/online UI retest evidence and, where UI closeout rules require it, task-relevant native screenshot attachment.

## Pitfalls

- Do not treat `[Image]` comment placeholders from Lark API as absence of visual evidence; classify them as API-limited inline screenshot evidence and rely on native attachments or online UI screenshots.
- Do not overfit FAQ English proof to title i18n only. The failure can be in static data arrays that remain Chinese even when the screen chrome is translated.
- Do not assert async native handoff calls synchronously after adding `requestAnimationFrame`/next-paint guards.
- Do not let a generic glass/style class change leak into unrelated UI components just to fix TabBar opacity.
