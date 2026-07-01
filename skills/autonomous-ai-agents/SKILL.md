---
name: autonomous-ai-agents
description: Use when you need the Autonomous Ai Agents workflow umbrella. See references/
  for detailed guides.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - autonomous
    - ai
    - agents
    - agent
    - umbrella
    - routing
    related_skills:
    - claude-code
    - codex
    - hermes-agent
    - hermes-pipeline
    - opencode
---

# Autonomous Ai Agents

## Overview

This umbrella skill is the routing surface for autonomous ai agents. Use it to choose the most specific child skill, reference, or workflow instead of treating the category name as a one-size-fits-all procedure.

## When to Use

- You need help somewhere inside autonomous ai agents and want the quickest route to the right child skill.
- You are not yet sure which autonomous ai agents sub-workflow best matches the request.
- You want a compact map of the autonomous ai agents skill family before loading a more specific procedure.
- Don't use for: a request that already clearly matches one specific autonomous ai agents child skill; load that child skill directly.

## Routing Guide

- `claude-code` — you need to delegate coding tasks to Claude Code (Anthropic's CLI agent).
- `codex` — you need to delegate coding tasks to OpenAI Codex CLI agent.
- `hermes-agent` — you need guidance on using and extending Hermes Agent — CLI usage, setup, configuration, spawning additional agents, gateway platforms, skills, voice, tools, profiles, and a concis....
- `hermes-pipeline` — you need to build automated task pipelines using hermes chat -q as execution engine.
- `opencode` — you need to delegate coding tasks to OpenCode CLI agent for feature implementation, refactoring, PR review, and long-running autonomous sessions.

## Class-Level Architecture Patterns

- For "agent architecture coverage" requests, especially Hermes + Claude Code/Codex/OpenCode comparisons, load `references/agent-architecture-control-plane-coverage.md` before proposing implementation. Preserve the split: Hermes is the canonical control plane / ledger / evidence / policy layer; external agents are worker adapters or executor runtimes. Do not collapse execution parallelism into governance authority.

## Selection Rules

- Prefer the narrowest child skill that matches the user request, platform, and desired artifact.
- Stay at the umbrella level only for routing, taxonomy, or category-wide orientation.
- If the request spans multiple subskills, use this umbrella to map the lane first, then hand off to the specific workflow that will do the real work.

## Absorbed Workflow Packages (3 consolidated in curator umbrella pass)

These former narrow child skills are now treated as subsections/reference packages under this class-level umbrella. Load the package only when the task needs that provider/tool's detailed commands, templates, or scripts; support package directories preserve any former references/templates/scripts/assets under the demoted package; otherwise use the umbrella routing rules above.

- `claude-code` → `references/packages/claude-code/README.md`: Use when you need to delegate coding tasks to Claude Code (Anthropic's CLI agent).
- `codex` → `references/packages/codex/README.md`: Use when you need to delegate coding tasks to OpenAI Codex CLI agent.
- `opencode` → `references/packages/opencode/README.md`: Use when you need to delegate coding tasks to OpenCode CLI agent for feature implementation, refactoring, PR review, and long-running autonomous sessions.


## Common Pitfalls

1. Using the autonomous ai agents umbrella as the full procedure even though a more specific child skill already fits.
2. Reading the routing map but never loading the referenced child skill or support material that contains the actual execution steps.
3. Choosing a child skill without checking that its platform, tools, and expected artifacts match the current task.
4. Jumping from architecture coverage directly to external-agent task execution or external adapter writes. First open audited boundaries in order: contract projection → ledger-only runtime start → governed builtin read-only executor → external-agent version/preflight probe → no-tool/no-write prompt dry-run → read-only context artifact packet → proposal artifact intake → multi-model certification gate → elevated done authorization projection → ledger-local canonical fact mutation → external adapter write intent projection → adapter write authorization → executor-specific adapter write with readback → rollback/escape → notification outbox enqueue → delivery authorization → channel-specific dry-run → only then consider real sender/tool gates.
5. Treating local canonical fact mutation as permission to write external systems. A local `done` fact is necessary but insufficient; external adapters still need intent projection, elevated write-through authorization, exact adapter/target binding, readback verification, and rollback/escape design. Notifications also need their own outbox and delivery gates; do not collapse adapter write success into Lark/Telegram send authority.
6. Putting evidence or message payloads into the hot ledger path. For outbox/sender boundaries, store only hashes, summaries, IDs, and artifact pointers; reject secret-like keys and keep raw platform payloads out of canonical records.

## Claude Code Goal + Ultracode Control Loop Reference

Applicability: for class-level analysis of autonomous coding-agent control loops, especially Claude Code `/goal`, Ultracode/dynamic workflows, and similar “continue until verifiable condition holds” workflows.

- See `references/claude-code-goal-control-loop.md` for the durable pattern: `/goal` is not a JavaScript feature; it is a session-scoped completion-condition loop whose evaluator can only judge evidence surfaced in the transcript.
- Ultracode adds a reusable orchestration lesson: combine higher reasoning with script-held dynamic workflows, producer/verifier subagents, progress/cost visibility, and saved commands for repeatable work.
- For JS/TS/frontend work, frame goals around verifiable project commands and evidence (`test`, `lint`, `typecheck`, `build`, e2e, visual regression) plus anti-regression constraints.

Anti-conditions: do not apply this as a project-specific rule, do not claim `/goal` itself verifies correctness without surfaced command/output evidence, do not treat npm distribution details as proof that the agent core is JavaScript-based, and do not treat Ultracode-style orchestration as permission to bypass authority gates.

## Claude Code PostToolUse Hook Reference

Applicability: for class-level analysis of post-tool evidence hooks, especially Claude Code `PostToolUse`, `PostToolUseFailure`, and `PostToolBatch` patterns.

- See `references/claude-code-posttooluse-hook.md` for the durable pattern: `PostToolUse` is post-execution observation and feedback, not prevention. Tool effects have already happened.
- Transferable Hermes lesson: use post-tool events to capture evidence, derive risk/latency/context, steer the next step, and feed verification ledgers while keeping permission prevention in pre-tool gates.
- For parallel tools, prefer batch/turn-level aggregation before claiming “all checks passed.”
- When implementing the pattern in a real runtime, use `references/posttooluse-runtime-landing.md`: preserve internal-vs-wire event names, keep non-post payload extras backward-compatible, prevent failure hooks from masking error results, cover agent-owned tool paths, and verify with temporary-home CLI smoke plus focused tests/re-review.

Anti-conditions: do not treat output replacement/redaction as a privacy boundary for already-recorded telemetry, do not store raw tool payloads in hot ledgers, and do not claim a runtime hook exists without implementation/readback/tests.

## Verification Checklist

- [ ] The request was mapped to the best-fitting child skill or explicitly kept at umbrella level for routing only.
- [ ] The selected child skill descriptions, references, and prerequisites were checked before substantive execution.
- [ ] Any claimed handoff, output, or route decision was read back against the specific child workflow before completion.
