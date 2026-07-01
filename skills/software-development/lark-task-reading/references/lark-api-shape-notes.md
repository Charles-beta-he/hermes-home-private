# Lark API Shape Notes

Extracted from `/Users/charles/.hermes/skills/software-development/lark-task-reading/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Lark API shape notes

Lark/Feishu API shapes vary by tenant, version, and permission set. Code should be tolerant in reads, strict in payload contract.

- Task list: `/task/v2/tasks?page_size=...&completed=false` with pagination.
- Single task fetch: `GET /task/v2/tasks/{guid}` returns `data.task` directly. Use when paginated fetch times out or the task is not in the incomplete list. See `references/lark-direct-task-fetch-by-guid.md`.
- Task update: `PATCH /task/v2/tasks/{guid}` with `{"task": {...}, "update_fields": [...]}`. The `task` wrapper is required — omitting it returns 400. See `references/lark-task-api-v2-update-and-closeout.md`.
- Comments API: `POST /task/v2/tasks/{task_id}/comments` returns 404 on larksuite.com (international). Use `description` field for evidence instead.
- `larksuite/cli` official dry-runs are useful for checking current endpoint/parameter shape without hitting the network: `task +get-my-tasks --as user --complete=false --page-all --dry-run`, `task tasklists list --as user --dry-run`, and `task tasklists tasks --as user --dry-run`. Treat this as an oracle/fallback aid, not a replacement for project-specific payload normalization.
- Tasklist scope enrichment: `/task/v2/tasks` may return only `tasklists[].tasklist_guid` without the human-readable list name. For hard scope reads like `UVISA-2.0新版开发`, fetch `/task/v2/tasklists`, build `tasklist_guid -> name/url`, enrich each task with `tasklist_names`, and only then run `prioritize_tasks(..., scope_mode="only")`. See `references/tasklist-scope-enrichment.md`.
- Comment endpoints may differ:
  - `/task/v2/tasks/{task_guid}/comments?page_size=...`
  - `/task/v2/comments?resource_id={task_guid}&resource_type=task&page_size=...`
- Comment `content` can be JSON rich text, plain string, list, dict, or malformed. Parse defensively.
- Inline images pasted into Task comments may be downgraded by the official Task API to literal `"[Image]"` with no `image_key` / `file_token`. Verified on larksuite.com with user token and scopes including `task:comment:read`, `task:attachment:read`, `task:task:read`: `/task/v2/comments`, `/task/v2/comments/{comment_id}`, `user_id_type` variants, and `include_attachments=true` still returned only `[Image]`; `/task/v2/attachments?resource_id=<task_guid>&resource_type=task` returned native task attachments, not inline comment images. Treat this as an official API limitation/evidence gap, not a parser miss.
- Task-native attachments are different from inline comment images. `/task/v2/attachments` can return `file_token`, `name`, `size`, and a short-lived signed `url` for files explicitly attached to the task, including screenshot files added as native attachments or evidence backfills. Prefer the signed `url` for download when present: the Drive-style `file_token` may return `99991679 Unauthorized` unless the current user token has broader Drive/media download scopes, even though the Task attachment list itself is readable. Fall back to `/drive/v1/medias/{file_token}/download` only when no URL is present. Do not assume native attachments cover screenshots pasted inside comments.
- To upload a native screenshot/file attachment to a Lark task on `open.larksuite.com`, use `POST /task/v2/attachments/upload` with multipart fields `resource_type=task`, `resource_id=<task_guid>`, and file field `file`; then verify with `GET /task/v2/attachments?resource_type=task&resource_id=<task_guid>`. The old/guessed `/task/v2/attachments/upload_all` path returns 404 and must not be treated as a successful native attachment upload.
- Tenant/bot token is not a replacement for user token on personal/assigned tasks: in the same probe, tenant token returned 403 for task/comment/attachment reads even though tenant scopes listed task read permissions. Keep user OAuth as the primary live-task read path.
- Linked-doc URLs may be `docx` or `wiki`; wiki nodes may need a `wiki -> docx` conversion before fetching doc content.
- Support both `larksuite.com` and `feishu.cn` domains when extracting links.
