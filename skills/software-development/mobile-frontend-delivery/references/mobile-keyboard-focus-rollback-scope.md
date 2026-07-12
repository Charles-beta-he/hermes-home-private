# Mobile keyboard-focus rollback scope

Applicability: mobile web/PWA/WebView money, transfer, remit, payout, auth, or short form pages where a recent change caused focused inputs to push the whole page, CTA/footer/header movement, icon/card displacement, or scroll snapping. Use when the user asks to inspect history or roll back page-specific keyboard/focus changes.

Anti-conditions:
- Do not apply as a blanket revert recipe for unrelated UI or business logic changes.
- Do not assume the visible checkout/working branch contains the reported screen; first verify whether the screen exists on the active branch or another worktree/feature branch.
- If the user says “先别改”, “只检查”, or “先整理”, make no patches, restores, commits, or generated files until they explicitly authorize the write step.

Procedure:
1. Establish the target route/screen from screenshot text and source strings, then verify the actual branch/worktree that contains that screen.
2. Separate three buckets before changing anything:
   - page files: the concrete screen(s), icons/cards, tests;
   - keyboard/focus infrastructure: keyboard shell, visualViewport, focus-visibility, scroll-inset helpers, global CSS/app shell;
   - unrelated dirty worktree changes.
3. Inspect history with path-scoped git commands, not repository-wide revert assumptions: `git log --since=<day> -- <screen> <keyboard-shell> <tests>` and `git show --stat --name-only <commit> -- <paths>`.
4. Summarize first in user-facing terms: which commits/files touched the page, which are likely tied to focus/page-push, which are likely tied to icon/card displacement, and which files should not be touched.
5. For rollback, prefer an isolated worktree/branch based on the affected feature branch. Restore only the scoped page + keyboard/focus/test files from the commit before the first relevant change; do not mutate the user’s current dirty checkout unless that is the explicit target.
6. After rollback, run narrow tests for the affected screens and shared keyboard/layout tests. If dependencies are missing in the isolated worktree, install from the lockfile there rather than borrowing partial binaries from another checkout.
7. Report exact rollback branch/worktree/commit, file list, diff stat, and real test output. If UI acceptance is required, still obtain real mobile/PWA screenshot evidence; unit tests are not enough for final visual acceptance.

Pitfalls:
- A focused-input page-push bug often comes from an interaction between a page wrapper, keyboard shell marker, visualViewport height, nested scroll owner, and manual focus scroll. Reverting only one event handler may leave the bad shell/scroll-owner split intact.
- Icon/card displacement on a transfer page may be a symptom of container/scroll/viewport changes rather than an avatar/icon component bug. Check layout history before rewriting icon components.
- Do not preserve accidental mid-investigation edits as part of the rollback. If you changed code before realizing the user wanted inspection-only, revert your own edit first or keep the rollback in a clean isolated worktree.
