# Batch public-media + screenshot intake

Applicability: Use when the user provides multiple social/public-media links plus a transcript/recording-share page or local screenshot and asks to analyze/add to the governed taskpool. This is a class-level intake pattern for mixed evidence quality, not a record of one source.

Anti-conditions: Do not claim full video playback, private transcript access, or hidden app content. Do not treat social captions, star counts, cost claims, or "official" wording as verified facts. Do not install/import external repos, use credentials, deploy, or mutate runtime during intake.

## Procedure

1. Resolve each public link to the most authoritative public preview available.
   - For WeChat Channels, use the existing `wechat-channels-public-preview-api.md` pattern and record only public preview fields.
   - For record/share pages that expose only generic page metadata, preserve the app/login/transcript boundary and use any user-provided screenshot as a separate evidence source.
2. Normalize evidence into a single scoped artifact note before task creation:
   - original URL / local file path;
   - access boundary (`public_preview`, `app_gate`, `screenshot_only`, `verified_artifact`, `blocked`);
   - visible author/title/date/counts/caption;
   - source claims vs direct verification;
   - prior task/project coverage and dedupe judgment;
   - recommended action (`adopt`, `recertify`, `reject`, `child-task`, `blocked`).
3. Verify named external artifacts directly before adoption:
   - GitHub API / README / docs / paper / package registry as applicable;
   - record direct verification separately from the social caption;
   - if search/API rate limits or no authoritative source is found, mark as blocker rather than guessing.
4. Search existing brain/taskpool records for source names and aliases before writing a task.
   - Existing coverage should become a bounded `recertification / net-new delta` objective, not another generic analysis card.
5. Choose taskpool granularity from the user's wording and source relationship.
   - Default for thematically related sources: create a single batch intake/recertification task.
   - If the user explicitly says “分别” / “separately”, keep one shared evidence directory and batch analysis note for efficiency, but create separate advisory cards per source or clearly source-separated cards, plus a `created_tasks.json`/readback index.
   - Acceptance must require a decision matrix and child-task creation only for verified, actionable, net-new deltas.
   - Include anti-drift/red-line language against runtime mutation, credentials, external dispatch, and social-claim laundering.
6. Read back the created task Markdown. If frontmatter/body acceptance collapsed or omitted repeated criteria, patch both projections immediately.
7. Run a taskpool selfcheck/readback appropriate to the mutation and report hook errors separately from the fact that the card exists.

## Recommended evidence note shape

```text
# <date> <theme> batch intake

Source boundary: ...

## User-provided sources

1. <URL/path>
   - Access boundary:
   - Visible/public fields:
   - Caption/screenshot claims:
   - Direct verification:
   - Prior coverage / dedupe:
   - Intake judgment:

## Batch judgment

- New/high-signal candidates:
- Overlap / recertification candidates:
- Unverified claims / blockers:

## Recommended taskpool boundary

Create one governed task that verifies authoritative artifacts, dedupes prior coverage, outputs an adopt/recertify/reject/child-task matrix, and prohibits runtime side effects during intake.
```

## Pitfalls

- A Qianwen/record share HTML page may expose only generic metadata while the useful content is in a user-provided screenshot. Record this as `screenshot_only` evidence rather than treating the share as transcript access.
- Mixed social batches often contain both new leads and already-covered themes. Do not let the new-source momentum create duplicate generic tasks.
- Public preview API success is not video playback proof; it is metadata/caption evidence only.
- `brain_task_orchestrator.py add` can return top-level OK with event-hook errors; read back the task and patch evidence/acceptance before reporting success.
