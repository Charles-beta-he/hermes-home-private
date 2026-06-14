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

## Pitfalls

- Do not start implementation just because a task is incomplete in Lark. First determine whether it is stale or already fixed in current code.
- Do not close or write back to Lark from this triage step. UVISA final completion still requires the online UI retest/native screenshot gate.
- Do not equate local unit/build proof with final user-facing closeout for C-end UI tasks.
- Do not paste local screenshot paths or token-bearing API output into Lark/public reports.

## Example patterns from UVISA C-end issues

- iOS PWA profile install tasks may already map to `PwaInstallBanner`, `usePwaInstall`, `public/uvisa-ios-pwa.mobileconfig`, and commits such as `fix(pwa): keep iOS profile install retryable`; remaining proof is iOS Safari/desktop icon/retry behavior on the deployed URL.
- Android/iOS tab safe-area tasks may already map to `TabBar`, `App.screenScrollInsetsClass`, `index.css` safe-area/body background rules, and `safe-area-layout.test.tsx`; remaining proof is real-device online UI showing normal tab height, no top stripe, and fixed tab position during scroll.
