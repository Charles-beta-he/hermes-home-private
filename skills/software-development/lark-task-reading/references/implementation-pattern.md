# Lark Task Reading Implementation Pattern

Extracted from `/Users/charles/.hermes/skills/software-development/lark-task-reading/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Implementation pattern

1. **Token / user authorization**
   - Prefer the unified read-only entrypoint for normal Lark task work: `python3 ~/.hermes/scripts/lark_task_flow.py --scope-mode only --summary` or `--url '<applink-with-guid>' --summary`. It runs the single-flight guard first, preserves auto-click authorization, then calls the reader with `auto_auth=False` so there is no second hidden OAuth/login path. See `references/lark-oauth-single-flight-guard.md`.
   - Run an auth preflight before any Task API call. Distinguish `CURRENT_READY`, `CURRENT_BLOCKED_NO_TOKEN`, `CLI_UNBOUND`, `HERMES_APP_CREDENTIALS_MISSING`, and `PREVIOUS_SNAPSHOT_AVAILABLE`; do not misreport a stale snapshot as a fresh live read.
   - Use a reusable token helper (`lark_auth.get_token()` where available) instead of one-off login probes.
   - If the Hermes-native reader fails with `NO_TOKEN` but older snapshots exist, classify the reader logic separately from the current auth state: the logic may be sound while live collection is blocked.
   - `larksuite/cli` can be used as an official auth/dry-run/API-shape oracle. In Hermes context it may require `lark-cli config bind`; because its help explicitly says AI agents must ask first, do not run bind without user confirmation of intent and identity preset. For personal/assigned tasks, `user-default` is required; `bot-only` cannot access user resources.
   - If a Lark/Feishu user authorization flow is triggered by the bot/MCP and opens a browser window, operate the browser directly: inspect the page, click the authorize/allow/continue button, then return to the task reader and retry the API call.
   - `lark-cli auth login --no-wait --json` device flow may only open a fresh Lark login page, not an authorization approval page. If the browser is not already logged in and no credentials/session are available, stop and classify `CURRENT_BLOCKED_NO_TOKEN` / `CLI_NO_USER_SESSION`; do not continue clicking around, do not ask the user to run the polling command, and do not claim a live task read. Use stale snapshots only as explicitly labeled triage evidence.
   - Tokens are secrets/runtime state. Never commit them and never paste them into skills, docs, issues, or memories.
   - When auth is blocked by duplicate `Authorization URL` notifications, `EADDRINUSE ::1:3010`, stale background `lark-mcp login` output, or auto-authorization not triggering, prefer the single-flight OAuth guard pattern in `references/lark-oauth-single-flight-guard.md` instead of launching another raw login. First run status-only (`lark_oauth_guard.py --json --no-open`); if it reports a valid token, do not refresh. If refresh is required, do not combine `--auto-authorize` with `--no-open`: auto-click needs the OAuth URL opened in the macOS browser. Use `lark_task_reader.py` default auto-auth path or `lark_oauth_guard.py --json --cleanup-stale --auto-authorize`.
   - See `references/larksuite-cli-auth-and-dryrun.md` for the larksuite/cli bind, auth, and dry-run oracle pattern.

2. **Fetch incomplete tasks**
   - Use paginated Task Center reads, e.g. `completed=false` with `page_token` until `has_more` is false.
   - Fail loudly on non-zero API code for the task list itself; this is a collector-blocking error.

3. **Scope priority before dispatch filtering**
   - Call `lark_task_reader.prioritize_tasks(fetch_tasks(token), ...)` immediately after fetching tasks and before `_should_dispatch`.
   - Reason: the scoped lane should decide which task pool to look at before status/dedup trimming.

4. **Dispatch filter**
   - Include only tasks that are incomplete and do not already carry the Lark `状态` custom field used by the pipeline.
   - Do not infer completion from title text.
   - Keep `_should_dispatch` small and deterministic.

5. **Dedup / taskpool insertion**
   - Dedup by `lark_task_guid` across all local envelope/taskpool statuses, not just pending/running.
   - For fan-out, dedup sibling envelopes by `(lark_task_guid, project_id)`.
   - For local-brain taskpool insertion, also dedup by normalized title because older notes may predate `lark_task_guid` frontmatter. On a title match, enrich the existing note with `lark_task_guid`, `lark_suite_entity_num`, `lark_task_url`, scope, assignee open_id/name, and a fresh comments snapshot instead of creating a new task.
   - After insertion/enrichment, run the taskpool selfcheck/evidence-spine and verify every live GUID from the accepted payload is present in the taskpool before reporting success. Refresh derived dashboards (`brain_task_orchestrator.py dashboard --write`) so subsequent task-pool progress checks reflect the new workload.

6. **Context enrichment**
   - Fetch comments for new tasks only.
   - Extract plain text, URLs, doc/wiki links, images, files, and creator names.
   - Fetch linked docs with a strict `max_docs` cap and `max_chars` cap.
   - Preserve both normalized text (`comments`, `docs_content`/`linked_docs`) and machine-actionable handles (`comment_image_keys`, `lark_url`).
   - When screenshot-only acceptance is likely, run the reader with `--download-images` so `comment_images[]` contains local cache paths for downstream vision analysis. Downloads are read-only, bounded, local-only evidence; failed image downloads must be recorded per image and must not abort task collection.
   - If the Task comments API returns only literal `[Image]` placeholders, run the dedicated rich-comment evidence probe before falling back to manual UI screenshots:
     ```bash
     python3 ~/.hermes/scripts/lark_rich_comment_image_downloader.py \
       --task-guid <lark_task_guid> \
       --out-dir ~/.hermes/evidence/lark-rich-comment-images/<task_guid> \
       --debug --json
     ```
     This script tries comment list/detail rich payloads, full-payload `image_key` / `file_token` extraction, image/media download endpoints, and task-native attachments. If it still reports `unavailable_placeholders`, classify the missing screenshot as a Lark API evidence gap and use UI screenshot automation; do not treat the image requirement as absent.

7. **Routing**
   - If the title/scope makes a project unambiguous, route immediately like `arc-dispatch`.
   - If routing is ambiguous or the pipeline uses GitHub-style staged processing, create `__unrouted__` envelopes first, then route in a separate stage with `project_profile` and bounded `file_tree` evidence.
   - Backend-specific keywords must come before generic frontend keywords.

8. **Payload contract**
   - Minimum fields:
     - `lark_task_guid`
     - `summary` / `issue_title`
     - `description` / `issue_body`
     - `comments`
     - `linked_docs` or `docs_content`
     - `custom_fields` when available
     - `members` when available
     - `lark_url`
     - `lark_task_scope`
     - `lark_task_scope_match`
     - `collected_at`
   - Optional but recommended:
     - `tasklists`
     - `tasklist_names`
     - `tasklist_scope_enrichment_warning` when `/task/v2/tasklists` is unavailable
     - `comment_image_keys`
     - `comment_image_placeholders`: count of literal `[Image]` / `[图片]` placeholders when Lark Task APIs strip image metadata and expose no `image_key` / `file_token`.
     - `comment_images` (optional, only when `--download-images` is enabled): list of `{image_key, source, status, local_path, content_type, size_bytes, endpoint, error}`. `status=downloaded|cached` means `local_path` is local evidence for vision analysis and must not be pasted into public Lark closeout comments. `status=unavailable` means the task/comment definitely contains image evidence, but the current Lark read payload only returned `[Image]` without a downloadable key; preserve it as a blocker/evidence gap instead of treating the task as text-only.
     - `project_id`
     - `project_path`
     - `reference_path`
     - `project_profile`
     - `file_tree`
     - `labels`

9. **Reporter boundary**
   - Collector reads and creates local envelopes.
   - Reporter writes back to Lark/GitHub.
   - Do not let collection dry-run write comments/status. This boundary prevents accidental external side effects.
