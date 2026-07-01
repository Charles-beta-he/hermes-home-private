# Lark Fusion Map: Arc Dispatch + GitHub Dispatch

Extracted from `/Users/charles/.hermes/skills/software-development/lark-task-reading/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Fusion map: arc-dispatch + github-dispatch

Keep these strengths together when changing either project.

### Shared baseline

- Reusable `lark_task_reader.py` module with:
  - `prioritize_tasks(tasks, preferred_scopes=None, scope_mode=None)`
  - `scope_match(task, preferred_scopes=None)`
  - `configured_scope_mode()` and `configured_preferred_scopes()`
  - alias expansion for scope names such as `UVISA-2.0新版开发`, `uvisa-app-2.0`, `UVISA-2.0`, `新版开发`
- Search across unstable Lark payload shapes: `summary`, `title`, `description`, `custom_fields`, tasklist/container/breadcrumb metadata, plus the whole JSON payload as safety net.
- Annotate every collected task with:
  - `_lark_task_scope`
  - `_lark_task_scope_match`
- Preserve fallback semantics: `prefer` returns scoped tasks if any exist; otherwise it returns all incomplete tasks.

### arc-dispatch strengths to keep

- Direct route at collection time for unambiguous tasks, including multi-project fan-out.
- Route payloads include `project_id`, `project_path` via envelope project, and `reference_path` for read-only reference projects.
- Fetch comment text and linked Lark docs before execution so the confirmer/executor sees context, links, screenshots, and product notes.
- Dry-run CLI shows exactly what would be enqueued before mutating the local DB.
- Simple unittest lane for the Lark reader and dry-run collector behavior.

### github-dispatch strengths to keep

- Rich comment parsing marks non-text evidence:
  - images as `[图片:<image_key_prefix>]`
  - files as `[附件:<name>]`
  - linked docs as doc/wiki references for later fetch
- Extract `comment_image_keys` / file tokens so a later image-download or vision lane can fetch binary evidence instead of losing it in text-only collection.
- Fetch comments and linked docs concurrently for new tasks with a bounded worker pool; one task's enrichment failure must not stop the whole collection tick.
- Separate collection from routing when ambiguity is high: collect unrouted envelopes first, then route with `project_profile` and `file_tree` evidence.
- Record stage timing/outcome in workflow DB so slow Lark reads are observable instead of invisible.
- Router can enrich payloads with `project_profile` and a bounded `file_tree` before executor planning.
