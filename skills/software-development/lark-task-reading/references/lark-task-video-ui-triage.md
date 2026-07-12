# Lark Task Video UI Triage

Use when a Lark/Feishu task links a concrete Task URL/GUID and the acceptance depends on a short screen recording attachment (UI jump, flicker, keyboard, scroll, gesture, modal, loading, or routing behavior).

## Applicability

- A specific Lark Task GUID or `applink.larksuite.com/client/todo/detail?guid=...` is in scope.
- The task has a native video attachment (`.mp4`, `.mov`) or screenshot sequence.
- The user asks to analyze/triage the task before or instead of implementation.

Anti-conditions:
- Do not mutate task status/comments from this workflow unless the user explicitly asks for writeback/closeout.
- Do not treat local code paths or private evidence paths as shareable project facts; summarize them or land them in the project profile/SSOT if needed.
- Do not close a UI task from text analysis alone; video triage identifies reproduction and likely landing points, not final acceptance.

## Procedure

1. Direct-fetch the task by GUID (`GET /task/v2/tasks/{guid}`) rather than paginating all tasks.
2. Read the live task fields: `summary`, `status`, `members`, `tasklists`, `attachments`, `completed_at`, and `url`.
3. If `tasklists[].tasklist_guid` is present, enrich the human-readable tasklist name via `/task/v2/tasklists` so scope is clear.
4. Read comments with `/task/v2/comments?resource_id={guid}&resource_type=task&page_size=...`; if comments are empty or `/tasks/{guid}/comments` 404s on larksuite.com, record that explicitly instead of treating it as a blocker.
5. For each native video attachment:
   - call `GET /task/v2/attachments/{attachment_guid}` using the attachment `guid`, not `file_token`;
   - parse the JSON metadata and download from `data.attachment.url`;
   - save under a request-specific evidence directory.
6. Extract objective video facts with `ffprobe`: duration, dimensions, framerate, size.
7. Extract frames at a low rate first (usually `ffmpeg -vf fps=1,scale=360:-1`) and make a contact sheet. Increase fps only if the defect is too fast to see.
8. Analyze the contact sheet/video for:
   - exact user path before the defect;
   - surface where the defect happens;
   - trigger action (focus, typing, delete, keyboard open/close, route return, sheet open, async loading);
   - visible invariant that should remain stable;
   - whether the issue is frontend layout/state, backend/API, data contract, or product ambiguity.
9. Map to likely code landing points only after the video facts are stated. If current local code lacks the exact visible field/component from the video, report branch/version drift instead of forcing a patch target.
10. Provide an analysis packet: live task metadata, video evidence summary, reproduction path, likely root-cause class, code search/landing hints, and acceptance checklist.

## Keyboard/layout-specific triage notes

For mobile soft-keyboard jump/flicker tasks:

- Separate browser/WebView automatic `scrollIntoView` from app-level viewport/keyboard helpers. Many jumps are caused by both adjusting scroll in the same focus cycle.
- Ordinary amount/remark/address inputs should usually keep header/footer/CTA in the page's intended shell and scroll only the middle content region enough to reveal the focused field.
- Re-rendering on each input/delete can retrigger scroll correction; tests should prove text changes do not repeatedly move the outer window/body/document scroller.
- Character counters, placeholders, and empty/non-empty input states must keep the input/card height stable.
- Acceptance evidence should include focus, several typed characters, deletion back to empty, and no visible jump of the relevant cards/CTA/input.

## Report template

```text
Task metadata
- GUID / task_id / status / tasklist / assignee
- Summary
- Attachments and comments readback

Video facts
- Duration / dimensions / frame sample rate
- User path
- Trigger
- Visible defect

Root-cause class
- Frontend layout/state vs backend/API/product ambiguity
- Likely surfaces/components/helpers
- Branch/version drift, if observed

Acceptance checklist
- Exact interaction to replay
- Stable elements/invariant
- Negative cases (delete, empty value, keyboard dismiss, route return)
```
