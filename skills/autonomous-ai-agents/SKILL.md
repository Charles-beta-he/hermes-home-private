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

These former narrow child skills are now treated as subsections/reference packages under this class-level umbrella. Load the package only when the task needs that provider/tool's detailed commands, templates, or scripts; otherwise use the umbrella routing rules above.

- `claude-code` → `references/absorbed/claude-code/SKILL.md`: Use when you need to delegate coding tasks to Claude Code (Anthropic's CLI agent).
- `codex` → `references/absorbed/codex/SKILL.md`: Use when you need to delegate coding tasks to OpenAI Codex CLI agent.
- `opencode` → `references/absorbed/opencode/SKILL.md`: Use when you need to delegate coding tasks to OpenCode CLI agent for feature implementation, refactoring, PR review, and long-running autonomous sessions.


## Common Pitfalls

1. Using the autonomous ai agents umbrella as the full procedure even though a more specific child skill already fits.
2. Reading the routing map but never loading the referenced child skill or support material that contains the actual execution steps.
3. Choosing a child skill without checking that its platform, tools, and expected artifacts match the current task.
4. Jumping from architecture coverage directly to external-agent task execution or external adapter writes. First open audited boundaries in order: contract projection → ledger-only runtime start → governed builtin read-only executor → external-agent version/preflight probe → no-tool/no-write prompt dry-run → read-only context artifact packet → proposal artifact intake → multi-model certification gate → elevated done authorization projection → ledger-local canonical fact mutation → external adapter write intent projection → adapter write authorization → executor-specific adapter write with readback → rollback/escape → notification outbox enqueue → delivery authorization → channel-specific dry-run → only then consider real sender/tool gates.
5. Treating local canonical fact mutation as permission to write external systems. A local `done` fact is necessary but insufficient; external adapters still need intent projection, elevated write-through authorization, exact adapter/target binding, readback verification, and rollback/escape design. Notifications also need their own outbox and delivery gates; do not collapse adapter write success into Lark/Telegram send authority.
6. Putting evidence or message payloads into the hot ledger path. For outbox/sender boundaries, store only hashes, summaries, IDs, and artifact pointers; reject secret-like keys and keep raw platform payloads out of canonical records.

## Verification Checklist

- [ ] The request was mapped to the best-fitting child skill or explicitly kept at umbrella level for routing only.
- [ ] The selected child skill descriptions, references, and prerequisites were checked before substantive execution.
- [ ] Any claimed handoff, output, or route decision was read back against the specific child workflow before completion.

