---
type: reference
status: active
created: 2026-05-06T07:41:43Z
updated: 2026-05-06T07:41:43Z
source_url: https://openai.com/index/open-source-codex-orchestration-symphony/
github: https://github.com/openai/symphony
tags:
  - 大模型开发
  - AI应用开发
  - harness-engineering
  - agent-orchestration
  - codex
---

# OpenAI Symphony - Codex Orchestration

## Screenshot OCR source

symphony github地址：https://github.com/openai/symphony
原文链接：https://openai.com/index/open-source-codex-orchestration-symphony/ #大模型开发 #AI应用开发 #harness_

The final tag was truncated in the screenshot; likely `#harness_engineering` or similar.

## What Symphony is

Symphony is an issue-driven coding-agent orchestrator. It turns a project-management board, especially Linear, into a control plane for autonomous Codex implementation runs.

Instead of humans supervising many interactive Codex sessions, humans manage work items. Symphony continuously maps eligible issues to isolated agent workspaces, starts agents, restarts stalled/crashed runs, and requires proof of work for review.

## Key article claims

- OpenAI teams first redesigned repositories for agent work via harness engineering: tests, guardrails, automation, and agent-friendly repo structure.
- The next bottleneck was human attention and context switching, not just agent capability.
- Engineers could manage only a few interactive sessions before coordination overhead dominated.
- Symphony reframes the unit of work from “session” or “PR” to “task/issue/deliverable.”
- OpenAI reports up to 500% increase in landed PRs for some teams.

## GitHub snapshot observed 2026-05-06

- Repo: `openai/symphony`
- Language: Elixir
- License: Apache-2.0
- Description: “Symphony turns project work into isolated, autonomous implementation runs, allowing teams to manage work instead of supervising coding agents.”
- Reference implementation: `elixir/`
- Language-agnostic spec: `SPEC.md`

## Architecture primitives worth absorbing

1. Issue tracker as control plane.
2. Per-issue isolated workspace.
3. In-repo workflow contract (`WORKFLOW.md`).
4. State-machine lifecycle for tasks.
5. Agent runner separated from orchestrator.
6. Proof-of-work as a required completion artifact.
7. Observability logs/status surfaces for many concurrent runs.
8. Recovery behavior for crash/stall/retry.
9. Human review at work-result level instead of session micromanagement.

## How Hermes should absorb this

Do not replace Hermes runtime with Symphony. Absorb the governance primitives:

| Symphony primitive | Hermes-native evolution |
|---|---|
| Linear board | Obsidian `05-实践与项目/tasks/`, Lark/Linear adapters later |
| Per-issue workspace | git worktree / task workdir linked from task note |
| `WORKFLOW.md` | Hermes skill + project workflow contract |
| Agent subprocess | Hermes subagent, Codex CLI, Claude Code, or cron job |
| Proof of work | test/build output, git commit, evidence bundle, L6 review note |
| Status surface | `brainctl status`, WAL, cron health, Obsidian dashboard/MOC |
| Restart/retry | Hermes cron/process supervision and task state transitions |

## Local brain implication

Symphony’s main lesson for the local brain is that task state must be explicit, bounded, and reviewable. Durable memory should not become a dumping ground for WIP status.

Therefore:

- Task state belongs in expiring task notes, not Hermes injected memory.
- Evidence and proof links are first-class.
- Model review artifacts are review evidence, not truth evidence.
- Project workflow contracts should be versioned like code.
- The human should view work through Obsidian and status notes, while Hermes executes through brainctl/cron/subagents.

## Links

- Article: https://openai.com/index/open-source-codex-orchestration-symphony/
- Repo: https://github.com/openai/symphony
- Spec: https://github.com/openai/symphony/blob/main/SPEC.md
- Elixir reference: https://github.com/openai/symphony/tree/main/elixir
- Related: https://openai.com/index/harness-engineering/
