---
name: architecture-theory-audit
description: "Use when analyzing a software architecture's theoretical foundations — mapping current dependencies, identifying gaps, finding relevant core theories/works, and proposing prioritized improvements. Triggers: 'architecture theory', 'theoretical foundation', 'theory gap analysis', 'what theory does this depend on', 'find core works for this design'."
triggers:
  - architecture theory analysis
  - theoretical foundation audit
  - theory gap identification
  - design principle review
  - academic grounding for architecture
---

# Architecture Theory Audit

## Overview

Use when analyzing a software architecture's theoretical foundations — mapping current dependencies, identifying gaps, finding relevant core theories/works, and proposing prioritized improvements. Triggers: 'architecture theory', 'theoretical foundation', 'theory gap analysis', 'what theory does this depend on', 'find core works for this design'. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

Systematic methodology for mapping a software architecture's theoretical foundations, identifying gaps where theory is missing, and proposing prioritized improvements grounded in core academic works.

## When to Use

- Reviewing an architecture design for theoretical completeness
- Identifying which academic foundations are already implicitly depended on
- Finding missing theories that should ground existing components
- Proposing improvements ranked by theoretical rigor and practical impact

## Methodology

### Step 1: Enumerate Architectural Components

List every distinct architectural component/pattern in the system. For each:
- What it does (function)
- How it's implemented (mechanism)
- What pattern it follows (if explicit)

### Step 2: Map Current Theoretical Dependencies

For each component, identify which theoretical foundations it implicitly or explicitly uses:

| Question | Maps To |
|----------|---------|
| Scheduling/priority logic? | Real-time scheduling theory (Liu & Layland 1973) |
| Concurrency/locking? | Concurrency control (2PL, optimistic) |
| State transitions? | State machines (Harel 1987 Statecharts) |
| Queue/buffering? | Queueing theory (Kendall notation, Little's Law) |
| Distributed coordination? | Distributed systems (leases, consensus, Paxos) |
| Evidence/verification? | Formal verification (PCC, Hoare logic) |
| Event logging? | Event sourcing (Fowler 2005) |
| Safety/fail-safe? | Safety-critical systems (Leveson 2011) |
| Plugin/extension? | Design patterns (Gamma 1994, Strategy) |
| Workflow/orchestration? | Process algebra (CSP, Petri nets) |

### Step 3: Identify Gaps

For each component, check:
1. **No theory**: Component works but has no theoretical grounding → find the right theory
2. **Weak theory**: Component uses a simplified version of a theory → find the full treatment
3. **Wrong theory**: Component applies theory outside its domain → find the correct domain theory
4. **Missing component**: Theory exists but isn't applied → propose the component

### Step 4: Find Core Works

For each gap, identify the seminal works:
- **Seminal paper**: The original paper that established the theory
- **Definitive textbook**: The standard reference for practitioners
- **Modern survey**: Recent survey that connects theory to practice
- **Practical guide**: How to actually implement the theory

### Step 5: Prioritize Improvements

Rank gaps by:
- **P1 (Immediate)**: Theory directly improves current decision-making (e.g., confidence scoring)
- **P2 (Short-term)**: Theory enables formal verification of existing behavior
- **P3 (Long-term)**: Theory opens new capabilities not yet implemented

### Step 6: Produce Output

Structure as:
```json
{
  "current_foundations": [...],
  "missing_foundations": [...],
  "improvement_proposals": [...],
  "priority_summary": {...}
}
```

## Theory Domain Quick Reference

| Domain | Key Theories | Core Works |
|--------|-------------|------------|
| Scheduling | RMF, MLFQ, Gittins Index | Liu 1973, Gittins 1974 |
| Concurrency | 2PL, OCC, Serializability | Eswaran 1976, Kung 1981 |
| State Machines | FSM, Statecharts, TLA+ | Harel 1987, Lamport 2002 |
| Queueing | M/M/1, M/D/c, Little's Law | Kendall 1953, Little 1961 |
| Distributed | Paxos, Raft, BFT, Leases | Lamport 1978/1982/2001, Gray 1989 |
| Formal Methods | PCC, Hoare Logic, CSP | Necula 1997, Hoare 1969/1978 |
| Event Systems | Event Sourcing, CQRS, Pub/Sub | Fowler 2005, Young 2005 |
| Safety | STAMP, STPA, Capability-based | Leveson 2011, Saltzer 1975 |
| Decision Theory | Bayesian, Prospect Theory, Optimal Stopping | Bayes 1763, Kahneman 1979, Wald 1950 |
| Workflow | Workflow Patterns, BPMN, Petri Nets | van der Aalst 2003, Petri 1962 |
| Information Theory | Entropy, Channel Capacity | Shannon 1948 |
| Evidence | Dempster-Shafer, Belief Functions | Shafer 1976 |
| Multi-Agent | BFT, Social Choice, Mechanism Design | Arrow 1950, Castro 1999 |
| Learning | Multi-Armed Bandits, Active Learning | Robbins 1952, Settles 2012 |
| NLP/Understanding | Statistical NLP, Entropy-based | Manning 1999, Jurafsky 2009 |

## Example Gap Analyses

See `references/hermes-task-system-gap-analysis.md` for task pipeline theory gaps (2026-05-29).
See `references/hermes-selfheal-gap-analysis.md` for self-healing architecture theory gaps (2026-05-30).
See `references/theory-domain-quick-reference.md` for curated academic reference by domain.

## Pitfalls

- **Don't over-formalize**: Not every component needs a formal model. Practical heuristics are fine when the cost of formalization exceeds the benefit.
- **Don't cargo-cult theory**: Citing a paper doesn't make the implementation correct. The theory must actually constrain the design.
- **Consider the audience**: If the architecture is for a small team, heavy formal methods may be impractical. Match rigor to context.
- **Gap ≠ bug**: A missing theoretical foundation doesn't mean the current implementation is wrong. It means it's unverified.
- **Theory selection**: Multiple theories may apply to one component. Choose the one that provides the most actionable constraints.
- **Research methodology**: For large-scale theory mapping (6+ components), spawn parallel research subagents via `delegate_task` — each covers one domain (e.g., "self-healing patterns", "backpressure patterns", "evidence governance"). Synthesize findings into a unified gap analysis. Don't try to research everything sequentially in one agent.
- **Don't cite patterns you can't implement**: Academic patterns must map to concrete code changes with file paths and function names. A citation without an implementation plan is decoration, not architecture.

## Output Quality Bar

A good theory audit:
1. Maps every significant component to at least one theoretical foundation
2. Identifies at least one gap per component that isn't trivially filled
3. Proposes improvements that are concrete enough to implement
4. Prioritizes by practical impact, not theoretical elegance
5. References seminal works, not just textbooks or blog posts

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
