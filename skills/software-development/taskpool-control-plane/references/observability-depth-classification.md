# Taskpool Observability and Depth Classification

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Observability and Depth Classification

This skill is also the umbrella for taskpool visibility and task-depth analysis:

- Former `hermes-observability` → dashboards, step-level task progress, heartbeats, task timelines, health score trends, and alert panels. Load `references/hermes-observability.md` when implementing or debugging progress emitters, dashboard data aggregation, or “why is running invisible?” UX.
- Former `task-depth-analysis` → iceberg tiering / task complexity classification, project-profile domain maps, low-confidence multimodel review, and frontend-vs-backend implementation effort. Load `references/task-depth-analysis.md` when backlog triage or dispatch routing depends on task depth.

Class rule: taskpool operation is not only lifecycle transitions. A healthy control plane must expose progress, classify work depth, and keep task metadata/routing evidence aligned with project profiles.
