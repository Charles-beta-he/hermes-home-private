# UVISA Lark linked-issue triage from task URLs

Use when the user pastes one or more Lark Task Center URLs and asks to “查看/分析这些问题” before explicitly asking to implement.

## Goal

Produce a live, evidence-backed issue readout without prematurely editing code or closing Lark. Many UVISA Lark items are stale by the time they are re-shared: the current code may already contain a fix, but Lark still needs online UI retest evidence.

## Procedure

1. Extract both identifiers from each URL:
   - `guid=<task-guid>` for direct API fetch.
   - `suite_entity_num=t104xxx` for human reporting and git/evidence search.
   Deduplicate repeated URLs before reporting.

2. Fetch each task directly by GUID with the Task v2 single-task endpoint:
   - `GET /task/v2/tasks/{guid}?user_id_type=open_id`
   - Record `summary`, `completed_at`, `url`, `members`, `tasklists`, `attachments`.
   - Enrich the tasklist name with `GET /task/v2/tasklists/{tasklist_guid}` when scope matters.

3. Fetch comment text if available:
   - `GET /task/v2/comments?resource_id=<guid>&resource_type=task&page_size=...`
   - On larksuite.com, `/task/v2/tasks/{guid}/comments` may 404; do not treat that as task absence.
   - If a comment is only literal `[Image]`, classify it as API-limited inline image evidence and rely on native attachments or UI screenshots.

4. Download native attachments for vision analysis when screenshots are present:
   - Use `attachments[].guid`, not `file_token`.
   - `GET /task/v2/attachments/{attachment_guid}` returns JSON metadata with a signed `url`; then download that URL.
   - Ask vision to extract the visible page, device context, and highlighted problem area.

5. Cross-check current implementation before proposing code work:
   - Search current code for task IDs, feature names, and likely surfaces.
   - Check git log for related commits/PRs, e.g. `git log --grep='t104219\|pwa\|safe area' --all` and file-specific logs.
   - Map task → existing commit/test/file evidence where possible.

6. Classify each linked issue:
   - `TODO`: no matching implementation or tests found.
   - `PARTIAL`: code exists but misses an acceptance atom or evidence contradicts it.
   - `IMPLEMENTED_NEEDS_ONLINE_RETEST`: code/tests/commit exist; remaining gate is real deployed-device/UI evidence.
   - `DONE_READY_FOR_CLOSEOUT`: online UI evidence and closeout requirements already exist.

7. Report with decision information only:
   - task id + concise title
   - current Lark state/scope
   - attachment observations
   - current code/git evidence
   - classification and exact next gate

## When Lark OAuth/API access is blocked but the user provides a screenshot

If the OAuth/browser authorization path is unavailable (for example the machine is locked) and the user sends a Lark task screenshot, do not keep retrying the API loop. Use the screenshot as live Lark evidence when it contains enough acceptance atoms:

1. Extract the task id/title if visible, platform, product path, reproduction steps, actual behavior, and expected behavior from the image.
2. Preserve the API limitation explicitly: comments/attachments/tasklist metadata are unverified, but the screenshot is sufficient for initial code/githistory triage.
3. Continue with code mapping and git-history checks as usual. Search by task id when available, but do not require a task-id hit before diagnosing the surface.
4. For UI/viewport tasks, map words in the title to route families (e.g. `资产 → 转出 → 国际汇款/链上提现/快捷转账`) and inspect both current code and recently added/reverted feature commits.
5. Final closeout still requires online UI/device evidence; screenshot-only analysis is a triage/implementation input, not a Lark completion gate.

## Temporary unsupported-feature / click-behavior tasks

When a linked C-end task says a feature flow is not connected yet (for example phone/SMS/OTP verification is unavailable) and asks to change a row/button click into a top prompt:

1. Treat it as a UI interaction gate, not as a request to delete the future feature.
2. Search the current screen for the entry point, the route, and the existing flow component.
3. If the flow component/route exists, prefer non-destructive gating at the entry point: click shows the requested top Toast/Banner/Modal copy and does not navigate. Keep the route/component unless the task explicitly asks to remove it.
4. Acceptance atoms should include: no route delta for the gated entry, exact title/body copy, top prompt visibility, accessibility role/status where applicable, and unaffected sibling rows/buttons still navigate normally.
5. Add or identify focused tests that prove the entry click triggers the prompt and does not enter the unfinished flow. Do not claim final Lark closeout from local tests alone; online UI evidence/native screenshot is still required.

## Pitfalls

- Do not start implementation just because a task is incomplete in Lark. First determine whether it is stale or already fixed in current code.
- Do not close or write back to Lark from this triage step. UVISA final completion still requires the online UI retest/native screenshot gate.
- Do not equate local unit/build proof with final user-facing closeout for C-end UI tasks.
- Do not paste local screenshot paths or token-bearing API output into Lark/public reports.
- Do not delete routes, screens, buttons, or future feature flows to satisfy a temporary unsupported-feature prompt; gate the visible entry point unless removal is explicitly required.

## Example patterns from UVISA C-end issues

- iOS PWA profile install tasks may already map to `PwaInstallBanner`, `usePwaInstall`, `public/uvisa-ios-pwa.mobileconfig`, and commits such as `fix(pwa): keep iOS profile install retryable`; remaining proof is iOS Safari/desktop icon/retry behavior on the deployed URL.
- Android/iOS tab safe-area tasks may already map to `TabBar`, `App.screenScrollInsetsClass`, `index.css` safe-area/body background rules, and `safe-area-layout.test.tsx`; remaining proof is real-device online UI showing normal tab height, no top stripe, and fixed tab position during scroll.
