---
name: lark-task-reading
description: "Read Lark Task Center tasks for dispatch pipelines, fusing arc-dispatch and github-dispatch patterns: scoped task prioritization, comment/doc/image enrichment, routing, dry-run safety, and loop verification. Use when adding, debugging, or operating Lark task collection."
license: MIT
tags: [lark, feishu, task-center, dispatch, automation, workflow]
related_skills: [hermes-workflow-orchestrator, arc-dispatch-executor, multi-model-thinking, loop]
skill_tier: molecule
---

# Lark Task Reading

Use this skill when working on Lark/Feishu Task Center collection for `arc-dispatch`, `github-dispatch`, or any Hermes pipeline that does:

```
Lark Task Center -> collector -> envelope -> router -> confirmer/executor -> reporter
```

The goal is not to copy one project's code into another. The goal is to preserve the best reusable patterns from both projects in the Hermes skill tree so future Lark-task work starts from the same proven playbook.

## Default behavior

- Prefer tasks visibly under `UVISA-2.0新版开发`.
- If no UVISA-2.0 scoped tasks are visible in the fetched incomplete-task list, fall back to all incomplete tasks.
- Use `LARK_TASK_SCOPE_MODE=only` only when you want a hard filter.
- Use `LARK_TASK_SCOPE_MODE=off` to disable scope preference.
- Override scopes with comma-separated `LARK_TASK_PREFERRED_SCOPES`, e.g. `UVISA-2.0新版开发,OtherProject`.
- Preserve read-only collection during dry runs: no Lark comments, no status writes, no task mutation.

## Operational boundary: skill knowledge vs project runtime

A Hermes skill is a playbook, not an executable adapter. Loading this skill must not by itself imply that `arc-dispatch` or `github-dispatch` source files should be opened, imported, symlinked, or executed.

For user-facing requests such as "读取 Lark 任务", "看一下 UVISA-2.0 新版开发分类下关于我的任务", or "列出我的任务":

1. Treat the source of truth as the Lark/Feishu Task API or an explicitly configured Hermes-native helper.
2. Do **not** scan old Desktop/archive duplicates looking for `run.sh`, `collector.py`, `orchestrator.py`, `router.py`, or `lark_task_reader.py`.
3. Do **not** execute a project pipeline from a copied or archived path, especially paths under desktop cleanup folders.
4. Only inspect or run `arc-dispatch` / `github-dispatch` code when the user explicitly asks to debug, migrate, compare, or operate that dispatch project.

The project files are reference implementations for pattern extraction. Normal task reading should be read-only and should not depend on whichever historical project copy happens to be discoverable first.

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

## Implementation pattern

1. **Token**
   - Use a reusable token helper (`lark_auth.get_token()` where available) instead of one-off login probes.
   - Tokens are secrets/runtime state. Never commit them and never paste them into skills, docs, issues, or memories.

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

5. **Dedup**
   - Dedup by `lark_task_guid` across all local envelope statuses, not just pending/running.
   - For fan-out, dedup sibling envelopes by `(lark_task_guid, project_id)`.

6. **Context enrichment**
   - Fetch comments for new tasks only.
   - Extract plain text, URLs, doc/wiki links, images, files, and creator names.
   - Fetch linked docs with a strict `max_docs` cap and `max_chars` cap.
   - Preserve both normalized text (`comments`, `docs_content`/`linked_docs`) and machine-actionable handles (`comment_image_keys`, `lark_url`).

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

## Lark API shape notes

Lark/Feishu API shapes vary by tenant, version, and permission set. Code should be tolerant in reads, strict in payload contract.

- Task list: `/task/v2/tasks?page_size=...&completed=false` with pagination.
- Tasklist scope enrichment: `/task/v2/tasks` may return only `tasklists[].tasklist_guid` without the human-readable list name. For hard scope reads like `UVISA-2.0新版开发`, fetch `/task/v2/tasklists`, build `tasklist_guid -> name/url`, enrich each task with `tasklist_names`, and only then run `prioritize_tasks(..., scope_mode="only")`. See `references/tasklist-scope-enrichment.md`.
- Comment endpoints may differ:
  - `/task/v2/tasks/{task_guid}/comments?page_size=...`
  - `/task/v2/comments?resource_id={task_guid}&resource_type=task&page_size=...`
- Comment `content` can be JSON rich text, plain string, list, dict, or malformed. Parse defensively.
- Linked-doc URLs may be `docx` or `wiki`; wiki nodes may need a `wiki -> docx` conversion before fetching doc content.
- Support both `larksuite.com` and `feishu.cn` domains when extracting links.

## UVISA routing

Add UVISA mappings before legacy/default projects:

- `uvisa_backend` -> `/Users/charles/Desktop/folder/work/uvisa-backend`
- `uvisa_app_2_0` -> `/Users/charles/Desktop/folder/work/uvisa-app-2.0`

Backend-specific keywords must appear before generic UVISA frontend keywords so `UVISA-2.0后端` routes to backend instead of frontend.

Recommended ordering:

1. Explicit backend lane: `UVISA-2.0后端`, `后端`, `API`, `接口`, `uvisa-backend`.
2. Explicit frontend lane: `uvisa-app-2.0`, `H5`, `移动端`, `用户端`, screen names.
3. Cross-project/fan-out lanes.
4. Default lane last.

## Loop implementation

When the user asks to "loop" Lark reading or to fuse patterns into the skill tree, use this loop:

1. **Inspect** both reference projects:
   - `lark_task_reader.py`
   - collector/comment/doc enrichment code
   - router project mapping and staged/fan-out routing
   - tests around scope filtering, comment extraction, doc links, and dry-run behavior
2. **Extract reusable patterns** into this skill or a linked reference. Do not copy secrets or transient task data.
3. **Patch the project code only if needed**; otherwise keep the improvement in the skill tree.
4. **Verify**:
   - skill frontmatter parses and description length is below Hermes limits
   - `python3 ~/.hermes/scripts/skill-steward.py --graph-check --json`
   - project tests/compile for any project code touched
5. **Commit scoped files only**. In a dirty `~/.hermes` repo, run:
   ```bash
   git diff --cached --stat
   git restore --staged .
   git add scripts/lark_task_reader.py scripts/test_lark_task_reader.py \
     skills/software-development/lark-task-reading/SKILL.md \
     skills/software-development/lark-task-reading/references/tasklist-scope-enrichment.md
   git status --short -- scripts/lark_task_reader.py scripts/test_lark_task_reader.py skills/software-development/lark-task-reading
   git commit -m "feat: add Hermes-native Lark task reader"
   ```
6. **Continue** if verification finds missing coverage or graph violations; stop only when the skill tree audit passes and the scoped commit is clean.

## Multi-model routing

Use multi-model thinking by risk level, not by habit:

- T0: deterministic checks for small doc wording changes.
- T1: one reviewer when adding a new collector pattern or changing routing semantics.
- T2: 3-model advisory when fusing patterns across `arc-dispatch` and `github-dispatch`.
- T3: 4-model ratification only for write-back automation, autonomous execution, or state-machine changes that can mutate external systems.

If the multi-model artifact says `not_certified`, treat it as advisory provenance. Do not claim ratification; resolve the issue ledger with deterministic evidence and rerun only if certification is required for the decision.

## Verification

For `github-dispatch`:

```bash
cd /tmp/github-dispatch
.venv/bin/python -m pytest tests/test_collector.py tests/test_pipeline.py -q
.venv/bin/python -m compileall -q collector.py lark_task_reader.py router.py orchestrator.py
```

For `arc-dispatch`:

```bash
cd /tmp/arc-dispatch
python3 -m unittest tests.test_lark_task_reader -v
python3 tests/test_basic.py
python3 -m compileall -q collector.py lark_task_reader.py router.py tests/test_lark_task_reader.py
```

For skill-tree-only changes:

```bash
python3 - <<'PY'
from pathlib import Path
import re, yaml
p = Path.home()/'.hermes/skills/software-development/lark-task-reading/SKILL.md'
s = p.read_text()
assert s.startswith('---')
m = re.search(r'\n---\s*\n', s[3:])
assert m
fm = yaml.safe_load(s[3:m.start()+3])
assert fm['name'] == 'lark-task-reading'
assert len(fm['description']) <= 1024
assert len(s) <= 100000
print('skill frontmatter ok')
PY
python3 ~/.hermes/scripts/skill-steward.py --graph-check --json
```

After Python compile checks, delete generated `__pycache__/*.pyc` if the repo tracks/deletes pyc files, so commits do not include bytecode churn.

## Project-pipeline commands

Use these only after intentionally choosing a live dispatch project as the runtime target, and run them from that project's canonical git root. They are **not** the default way to answer a normal "read my Lark tasks" request.

```bash
# First prove the runtime target is the intended project, not an archive/duplicate copy
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status --short

# Default: prefer UVISA-2.0新版开发, fall back to all incomplete tasks
./run.sh --mode collect-only --dry-run

# Hard filter to UVISA-2.0新版开发
LARK_TASK_SCOPE_MODE=only ./run.sh --mode collect-only --dry-run

# Custom preferred scope list
LARK_TASK_PREFERRED_SCOPES=UVISA-2.0新版开发 ./run.sh --mode collect-only --dry-run

# Disable scope preference for a broad audit
LARK_TASK_SCOPE_MODE=off ./run.sh --mode collect-only --dry-run
```

## Pitfalls

- Lark Task API metadata shapes vary; match across summary, description, custom fields, tasklists, containers, breadcrumbs, and the full JSON payload.
- If `/task/v2/tasks` includes only `tasklists[].tasklist_guid`, scope matching by list name will fail until you enrich from `/task/v2/tasklists`; do this before `only` mode and before claiming the desired project list was read.
- Do not certify `UVISA-2.0新版开发` hard-scope correctness from title/body keywords. Require enriched `tasklist_names` evidence.
- Lark task `description` can be empty while comments hold the actionable details; `issue_body` should merge description + comments + docs, not description alone.
- Do not infer task completion from title; keep `_should_dispatch` checks for `completed_at` and `状态` field.
- Do not commit temporary login probes, Lark tokens, generated bytecode, downloaded attachments, or screenshots with sensitive task data.
- `github-dispatch` may be a non-git folder in this environment; verify with `git status` before promising a commit.
- Do not collapse image/file placeholders into plain text only. Preserve machine-actionable keys for later binary fetch/vision work.
- Do not let one failing comment/doc fetch abort the whole collector tick; isolate per-task enrichment failures and record enough trace to debug.
- Do not turn safe collection into automatic task execution. Collection, routing, execution, validation, and reporting are separate gates.

## Verification checklist

- [ ] Scoped tasks are preferred by default and fallback remains intact.
- [ ] `only` and `off` modes work.
- [ ] Payload includes scope metadata.
- [ ] Comments, URLs, doc/wiki links, image/file placeholders, and image keys are preserved when present.
- [ ] Dedup checks all local statuses; fan-out dedups siblings.
- [ ] Dry-run performs no external writes.
- [ ] Backend routes are checked before generic frontend routes.
- [ ] Relevant tests and compile checks pass.
- [ ] Skill graph strict check passes after skill edits.
