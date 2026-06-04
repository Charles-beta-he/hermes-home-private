# ReferenceReview: GitHub Trending agent/browser automation → Hermes taskpool

- Date: 2026-06-04
- Task: `2026-06-04-评估今日-trending-中-agent-browser-automation-项目对-hermes-taskpool-的可迁移模式`
- Source evidence bundle: GitHub Trending official row rank 4, repo `NousResearch/hermes-agent`, description `The agent that grows with you`
- Source URL: https://github.com/NousResearch/hermes-agent
- Local checkout: `/Users/charles/.hermes/hermes-agent`
- Local commit reviewed: `84f7a37aeba7959f762277f9d451f6f93830db81`
- Local branch reviewed: `feat/mcp-semantic-probes-real-client`
- GitHub API verification: repository reachable, default branch `main`, license MIT, pushed `2026-06-04T10:32:27Z`

## Claims and evidence

### Claim 1 — The Trending artifact is not a separate external browser-automation project

Evidence:
- GitHub API returned `full_name=NousResearch/hermes-agent`, `description=The agent that grows with you`, `license=MIT License`, `default_branch=main`.
- The task evidence bundle only includes `https://github.com/NousResearch/hermes-agent`; no second browser automation repository was present in the task payload.

Decision:
- Treat this as a self-reference review of Hermes' own automation surface, not as adoption of a new third-party project.
- Do not add a new dependency or cargo-cult a Trending claim.

### Claim 2 — Hermes already has first-class browser automation primitives

Evidence:
- `tools/browser_tool.py:3-12` identifies the Browser Tool module and states it supports Browser Use, Browserbase, and local Chromium with identical agent-facing behavior.
- `tools/browser_tool.py:14-25` lists local/cloud modes, per-task session isolation, accessibility-tree snapshots, ref-selector interactions, task-aware extraction, and cleanup.

Decision:
- No new browser automation engine is justified from this evidence alone.
- The transferable pattern is evidence-gated browser runs: browser capabilities should be evaluated by concrete harness traces/snapshots, not by repository popularity.

### Claim 3 — Hermes already exposes unattended automation and parallel workstreams

Evidence:
- `README.md:23` describes the built-in cron scheduler with delivery to any platform.
- `README.md:24` describes isolated subagents for parallel workstreams and Python scripts that call tools via RPC.
- `cron/jobs.py:1-5` stores cron jobs under `~/.hermes/cron/jobs.json` and outputs under `~/.hermes/cron/output/{job_id}/{timestamp}.md`.

Decision:
- No high-blast-radius runtime implementation is needed for this task.
- The immediate useful migration is governance: ensure taskpool work tasks that reference external/trending sources carry a concrete source weighting policy before dispatch.

## Implemented delta

Low-risk control-plane metadata hardening landed during this review:

1. Added `source_weighting_policy` to `/Users/charles/.hermes/project-profiles/hermes.json`.
2. Added these dispatch references to the task frontmatter:
   - `project_profile_ref: /Users/charles/.hermes/project-profiles/hermes.json`
   - `source_weighting_policy_ref: /Users/charles/.hermes/project-profiles/hermes.json#source_weighting_policy`
3. Regenerated taskpool dashboard/derived views.

## Validation performed

- `python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write --json` → PASS / dashboard regenerated.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json` → target task became `dispatchable: true`.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json` → target task nominated as next task.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json` → `dispatchable: true`.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --json` → `selected_count: 1`.
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json` → PASS; existing edge-node warnings and historical evidence debt remain unrelated.

## Adoption decision

Adopt:
- Source-weighting dispatch gate for Hermes work-lane tasks.
- Evidence-first reference review artifact before turning Trending repos into implementation tasks.
- Browser automation evaluation should require concrete file/line evidence and runnable smoke traces.

Do not adopt now:
- No new browser engine or taskpool runtime dependency.
- No direct code change to `tools/browser_tool.py`, cron scheduler, or worker dispatch from this single Trending row.

## Residual risk / human-intervention boundary

- This review is sufficient to close the current P3 work/reference task.
- Larger changes would require human/product approval or a new task: e.g. changing browser harness runtime, enabling autorun globally, or adopting an external browser automation library.
