# Step 1.2b: Deepen the Search (Breadth-First, Then Depth)

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/research/research-paper-writing/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Step 1.2b: Deepen the Search (Breadth-First, Then Depth)

A flat search (one round of queries) typically misses important related work. Use an iterative **breadth-then-depth** pattern inspired by deep research pipelines:

```
Iterative Literature Search:

Round 1 (Breadth): 4-6 parallel queries covering different angles
  - "[method] + [domain]"
  - "[problem name] state-of-the-art 2024 2025"
  - "[baseline method] comparison"
  - "[alternative approach] vs [your approach]"
  → Collect papers, extract key concepts and terminology

Round 2 (Depth): Generate follow-up queries from Round 1 learnings
  - New terminology discovered in Round 1 papers
  - Papers cited by the most relevant Round 1 results
  - Contradictory findings that need investigation
  → Collect papers, identify remaining gaps

Round 3 (Targeted): Fill specific gaps
  - Missing baselines identified in Rounds 1-2
  - Concurrent work (last 6 months, same problem)
  - Key negative results or failed approaches
  → Stop when new queries return mostly papers you've already seen
```

**When to stop**: If a round returns >80% papers already in your collection, the search is saturated. Typically 2-3 rounds suffice. For survey papers, expect 4-5 rounds.

**For agent-based workflows**: Delegate each round's queries in parallel via `delegate_task`. Collect results, deduplicate, then generate the next round's queries from the combined learnings.
