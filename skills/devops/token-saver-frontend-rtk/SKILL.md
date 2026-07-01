---
name: token-saver-frontend-rtk
category: devops
description: "Use when layer 1-2 token optimization for React/Vue frontend: CASI + RTK state machine + index-first file reading + backend-verified assertions. 40-60% token reduction vs unoptimized. Use when working in uvisa-app-2.0 or similar React/Vue projects."
triggers:
  - "frontend token optimization"
  - "React token saving"
  - "uvisa-app token reduction"
  - "frontend RTK workflow"
  - "前端省token"
tags: [token-optimization, frontend, react, rtk, casi]
---

# Token Saver Frontend RTK (Layer 1-2)

## Overview

Layer 1-2 token optimization for React/Vue frontend: CASI + RTK state machine + index-first file reading + backend-verified assertions. 40-60% token reduction vs unoptimized. Use when working in uvisa-app-2.0 or similar React/Vue projects. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

Frontend-specific token optimization derived from analysis of 5 real uvisa-app-2.0 sessions.

**Full analysis & rules**: `references/rtk_layer12_fewshot.md` (symlinked to token-saver-rtk)

## Quick Reference

### Layer 1: CASI Tri-State Gate

Before ANY tool call:
```
NOVEL   → gather evidence first (search, grep, read)
KNOWN   → act directly (patch, write)
STALE   → verify changed lines before acting
```

**Frontend-specific index-first**: read exports/types/references, not implementation.
- Component: `grep 'export function ComponentName' -A 20` (get props + first JSX)
- Service: `grep 'export const.*Service' -A 5` then `grep 'serviceName:' -A 3`
- Type: `grep 'export interface.*Props' -A 15`
- Store: `grep 'export.*Store' -A 10`

### Layer 2: RTK State Machine

| Step | Tool calls | Action |
|------|-----------|--------|
| Intent Parse | 0 | Decompose user request into DSL verbs |
| Scope Locate | 1 | grep/interface search → file + line |
| Evidence | 2-3 | Targeted reads (index-first) |
| Implement | 1-2 | patch/write |
| Verify | 1 | `tsc --noEmit` (≥2 files) or `vitest run` (behavior) |
| Claim | 0 | Scope-locked assertion |

### Key Rules

1. **tsc > browser verify** (for code changes). Browser only for visual/UI state.
2. **Patch > Write** for <3 changes. Read 5 lines around target for context.
3. **No raw reads of large files** — grep index first, then offset/limit read.
4. **Fail-fast**: if 2 consecutive tool calls produce no useful output, STOP and reassess.
5. **Prefer 1 file read + 1 patch** over multiple reads + full rewrite.

### Backend Verification (Lark t107438 lesson)

Don't trust frontend data flow for hidden business logic. Examples:
- Aggregate calculations (totals, fee splits) → verify in backend service
- Status transitions → verify state machine
- Permission checks → verify auth middleware

Evidence: session `9b1a3181-4f1f-43bc-a2a1-416825953666` — wasted 5+ tool calls on frontend dead-ends before checking backend.

## When to Use

- Working in `uvisa-app-2.0` (React 19 + TypeScript + Zustand)
- Any React/Vue frontend project with TypeScript
- When token cost per task matters (daily development workflow)


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
