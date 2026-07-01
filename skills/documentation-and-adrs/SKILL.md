---
name: documentation-and-adrs
description: Use when recording significant technical decisions, rationale, and consequences as Architecture Decision Records (ADRs).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - documentation
    - adr
    - architecture
    - decision-records
    related_skills:
    - framework-audit
    - writing-plans
    - private-fork-evolution-governance
---

# documentation-and-adrs

## Overview


Code tells WHAT. ADRs tell WHY. Every non-obvious technical decision deserves a record.

## When to Use

- Recording significant technical decisions, rationale, and consequences as Architecture Decision Records (ADRs)


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## ADR Template
```markdown
# ADR-{NNN}: {Title}

Date: YYYY-MM-DD
Status: proposed | accepted | deprecated | superseded by ADR-XXX

## Context
What is the problem we're solving? What constraints exist?

## Decision
What did we choose and why?

## Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|-------------|
| A | ... | ... | ... |
| B | ... | ... | ... |

## Consequences
What becomes easier? What becomes harder? What new risks exist?
```

## When to Write an ADR
- Choosing between frameworks/libraries (tRPC vs REST vs GraphQL)
- Major architectural pattern (monorepo structure, event sourcing)
- Data model decisions (normalized vs denormalized)
- Deprecation of a core system
- Security or compliance requirement that shapes architecture

## When NOT to Write an ADR
- Trivial choices (naming, formatting)
- Decisions that are immediately reversible with no migration cost
- Things already covered by project CLAUDE.md or AGENTS.md

## ADR Lifecycle
1. **proposed**: Written, under review
2. **accepted**: Approved and in effect
3. **deprecated**: No longer followed (link to replacement)
4. **superseded**: Replaced by newer ADR

Store in: `docs/adr/` or `.hermes/notes/adr/`

## Multi-model or certification boundary in ADRs

When an architecture decision uses a multi-model review, record the certification status explicitly:
- `full_certified` only when quorum, truth/evidence gates, and discussion/ratification all pass;
- `degraded_review` when useful model outputs exist but planner quorum, provider auth, timeout, or discussion certification failed;
- include which recommendations were accepted, which amendments changed the plan, and which claims remain non-certified.

Do not phrase degraded multi-model output as full certification. Use it as design input plus local evidence, and make the next implementation slice evidence-gated.

## Verification Checklist
- [ ] ADR number is sequential (check existing ADRs)
- [ ] Context clearly describes the problem
- [ ] At least 2 alternatives evaluated
- [ ] Consequences section not empty
- [ ] Status is "proposed" (not "accepted" before review)

## Common Pitfalls

0. **Certification laundering.** If an ADR is informed by degraded multi-model review, provider timeouts, or below-quorum fanout, record that status explicitly. Do not phrase it as full certification; separate local evidence, model recommendations, and unresolved certification limits.

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
4. When an ADR is informed by a degraded multi-model review, record the certification boundary explicitly. Distinguish full certification from partial/degraded advice, and avoid using degraded review alone to authorize high-blast-radius core changes.
