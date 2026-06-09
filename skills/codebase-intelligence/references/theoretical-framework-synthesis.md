# Theoretical Framework Synthesis from Codebase

When the user asks to "find theoretical foundations", "abstract principles", "formal model", or "academic references" for a codebase or system, use this multi-model dispatch pattern.

## Dispatch Pattern (3 parallel subagents)

```
delegate_task(tasks=[
  {  # Task A: Deep code → theory mapping
    goal: "Analyze [system] source code and map design patterns to CS/math theory",
    toolsets: ["terminal", "file"],
    context: "
      Read [key source files].
      For each architectural pattern found:
        1. Name the theoretical concept (scheduling theory, concurrency control, FSM, queueing theory, distributed systems, proof-carrying code, event sourcing, safety-critical systems)
        2. Map to specific implementation (cite file + function)
        3. Identify gap (what theory predicts vs what code does)
        4. Suggest improvement
        5. List 3-5 academic references per principle
      Output JSON: {principles: [{name, theory, hermes_implementation, gap, improvement, related_works}]}
    "
  },
  {  # Task B: Literature search
    goal: "Search for recent (2024-2026) academic papers and blog posts on [relevant domains]",
    toolsets: ["web"],
    context: "
      Search arxiv, ACM, IEEE, Anthropic/OpenAI/Google blogs.
      For each work: title, author, year, venue, key_insight, relevance_to_[system], url.
      Focus on: [domain-specific search terms]
      Output JSON: {works: [{title, author, year, venue, key_insight, relevance, url}]}
    "
  },
  {  # Task C: Formal synthesis
    goal: "Synthesize a unified theoretical model of [system]",
    toolsets: ["terminal"],
    context: "
      Create formal model: M = (S, S₀, T, Σ, δ, Ω, Π, G)
      Define: states, transitions, priority functions, policy oracles, guard predicates.
      Verify properties: safety, liveness, fairness, bounded execution, mutual exclusion.
      Identify novelty vs existing theory.
      Propose improvements grounded in theory.
      Output JSON: {core_abstraction, formal_model, properties, novelty, improvements}
    "
  }
])
```

## Synthesis Step (after all 3 complete)

1. Read output JSON files from each subagent
2. Cross-reference: which theoretical principles from Task A are supported by literature in Task B?
3. Validate formal model from Task C against concrete findings in Task A
4. Produce unified report with:
   - Core abstraction (one sentence)
   - N abstractable principles (table format)
   - Formal model definition
   - Property verification table (✅/❌)
   - Innovation points
   - Curated reference list (classic + modern)

## Key Theory Domains to Cover

| Domain | Classic Papers | Modern Extensions |
|--------|---------------|-------------------|
| Scheduling | Liu & Layland 1973, EDF, MLFQ | Gittins index, contextual bandits |
| Concurrency | 2PL (Eswaran 1976), optimistic (Kung 1981) | CRDTs, CALM theorem |
| State Machines | Harel 1987 Statecharts | TLA+, Alloy |
| Queueing | Kendall 1953, Little 1961 | Heavy-traffic limits |
| Distributed | Lamport 1978, Gray & Cheriton 1989 leases | Raft, Paxos |
| Proof Systems | Necula 1997 PCC | Verifiable computation, zk proofs |
| Event Sourcing | Fowler 2005, CQRS | EventStore, Axon |
| Safety | Leveson 2011 STAMP | Runtime verification |
| AI Agents | — | Magentic-One, LangGraph, AutoGen, Swarm |

## Pitfalls

1. **Don't just list papers** — each reference must map to a specific implementation detail
2. **Don't skip the gap analysis** — theory vs practice difference is the insight
3. **Formal model must be concrete** — not hand-wavy "it's like X", but actual state/transition definitions
4. **Property verification needs proof sketches** — not just "holds" or "doesn't hold"
5. **Output files should be JSON** — machine-readable for downstream use (dashboards, docs)
6. **Task B (literature) may fail** — web search is unreliable; have Task C fill gaps from training knowledge
