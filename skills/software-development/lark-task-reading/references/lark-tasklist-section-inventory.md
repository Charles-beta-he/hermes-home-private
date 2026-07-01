# Lark tasklist section inventory pattern

Scope: read-only整理任务清单 from an already-open Lark/Feishu Task board when the user points to a tasklist title plus a visible UI group/section such as `h5端任务`.

Applicability:
- The user wants “先整理任务内容 / 任务清单”, not task execution or Lark writeback.
- A tasklist name is known (for example `V1.2.0版本更新计划`) and the UI visibly shows a section/group count.
- Normal scoped task reads return tasklist membership but not reliable section names.

Anti-conditions:
- Do not use this as proof that tasks are complete.
- Do not mutate Lark status/comments/attachments.
- Do not infer ownership from follower membership; assigned-only still requires current user `open_id` and `members[].role == assignee`.
- Do not claim screenshot/image requirements are absent when comments contain `[Image]`; mark image evidence as pending download/UI capture.

## Procedure

1. Verify current Lark user identity through `/authen/v1/user_info` and record only non-secret fields: display name and `open_id`.
2. Read the target tasklist with the normal safe flow first:
   - `lark_task_flow.py --preferred-scope '<tasklist name>' --scope-mode only --summary`
   - Then JSON mode to capture task payloads.
3. Filter owner tasks by exact assignee open_id:
   - include task only if any `members[]` has `role == "assignee"` and `id == current_open_id`.
   - follower/member-only is not ownership.
4. If the UI section name is not available in payload (`section_names` empty), use the raw `tasklists[].section_guid` and visible board order/count as a section boundary:
   - Inspect the expanded UI group title/count from the board screenshot or browser/computer-use capture.
   - Use the direct tasklist endpoint `/task/v2/tasklists/{tasklist_guid}/tasks?completed=false&page_size=...` to get the board-ordered list.
   - Identify the contiguous range that matches the visible section start title and count.
   - Cross-check the same GUIDs against the normal `/task/v2/tasks` payload to retain comments, tasklist names, members, and descriptions.
5. Land two artifacts:
   - a human-readable Markdown inventory grouped by priority/domain/type;
   - a machine-readable JSON inventory preserving GUIDs, titles, owner ids, Lark URL, comments/image-placeholder flags, normalized task, and acceptance focus.
6. Write only scoped project artifacts/profile references when useful:
   - project profile pointer to the inventory;
   - raw Lark snapshot under project workflow/evidence if needed.
7. Verify:
   - task count equals the visible section count;
   - all inventory tasks are assigned to the current user;
   - JSON parses;
   - project profile parses / portfolio doctor passes if profile was updated.

## Reporting format

Report:
- tasklist + section name;
- owner filter evidence (`current user`, `open_id` matched, no token values);
- task count;
- output artifact paths;
- P0/P1/P2 or other classification counts;
- boundary: “整理任务内容，不代表完成；后续实施需逐条验收”.

## Pitfalls

- `/task/v2/sections` may fail or return no usable names even when `section_guid` exists. Capture the fallback pattern, not a durable claim that the endpoint is broken.
- `/task/v2/tasklists/{guid}/tasks` may return more tasks than the current filtered list and lacks full task details; use it for board order/section boundary only, then enrich from detail/list payloads.
- A tasklist-wide direct read can surface tasks outside the user-owned subset. Always re-apply assignee filtering.
- Do not replace a user-visible board category such as `h5端任务` with broad keyword analysis over all incomplete tasks. If the user says the category should have a specific count (for example “这个分类下我应该只有15个”), treat that as a section-boundary correction: page through the tasklist endpoint, identify the visible contiguous block/order, then intersect that block with exact `members[].role == "assignee"` for the current robot login user. Report both counts separately: category total vs robot-owned subset.
- For UAEC/H5-style boards, “H5-related” and “inside the H5 category” are different scopes. The former may include global/三端/frontend-adjacent tasks across the whole board; the latter is the visible Lark category/section only. Prefer the category/section scope when the user points to a board classification.
- Board section names/counts are UI evidence; if the user later changes grouping/filtering, re-read the board rather than reusing stale ranges.
