# Project profile graph and task-inventory artifacts

Scope: project onboarding/profile work where a repo has just been profiled and the user asks whether a relationship graph or task list should be generated for later use.

Applicability:
- A Hermes project profile exists or is being created under `~/.hermes/project-profiles/`.
- The project has a primary repo and optionally a reference repo.
- The desired output is durable navigation/impact-analysis support, not implementation completion.

Anti-conditions:
- Do not treat the graph as runtime proof.
- Do not turn task inventory into “done” or dispatch state.
- Do not put volatile task progress in memory; store scoped artifacts under the project workflow root and link them from the project profile.

## Artifact set

Recommended project workflow layout:

```text
~/.hermes/workflows/projects/<project>/
  progress-ledger.md
  graphs/
    <project>-code-relationship-graph.md
    <project>-code-relationship-graph.json
    README.md
  tasks/
    <release-or-board>-<section>.inventory.md
    <release-or-board>-<section>.inventory.json
    <release-or-board>-<section>.raw-lark.json   # optional, scoped evidence
```

## Code relationship graph procedure

1. Start from the project profile’s `business_domain_map`, repo paths, route/API evidence, and reference-repo boundary.
2. Emit two graph forms:
   - Mermaid Markdown for human navigation;
   - JSON nodes/edges for machine search and future impact analysis.
3. Include at least:
   - project node;
   - reference repo node when applicable;
   - layers (bootstrap/router/state/request/PWA/i18n or equivalent);
   - business domains;
   - route nodes;
   - API endpoint examples;
   - implementation file/path nodes;
   - risk nodes when useful.
4. Validate:
   - JSON parses;
   - every edge source/target exists;
   - profile links point to existing artifacts.
5. Write profile field:

```json
"code_relationship_graphs": {
  "mermaid_md": "...",
  "graph_json": "...",
  "index": "...",
  "generated_at": "...",
  "node_count": 0,
  "edge_count": 0,
  "boundary": "static code graph; advisory for navigation/impact analysis, not runtime proof"
}
```

## Task inventory procedure

1. Use a live task source or explicit snapshot; label freshness.
2. Filter ownership explicitly (for Lark: assignee open_id, not follower).
3. Normalize each task into:
   - GUID/URL;
   - original title;
   - priority;
   - domain;
   - type;
   - normalized task statement;
   - acceptance focus;
   - evidence flags (comments/images/docs).
4. Emit Markdown for reading and JSON for automation.
5. Write profile field:

```json
"task_inventories": {
  "<key>": {
    "generated_at": "...",
    "source_tasklist": "...",
    "source_section": "...",
    "task_count": 0,
    "inventory_md": "...",
    "inventory_json": "...",
    "raw_lark_snapshot": "...",
    "boundary": "整理任务内容，不代表完成；后续实施需逐条验收"
  }
}
```

## Verification checklist

- [ ] Project profile JSON parses.
- [ ] Artifact paths exist.
- [ ] Graph JSON parses and has no dangling edges.
- [ ] Task inventory JSON parses and count matches source evidence.
- [ ] If portfolio registry/profile was updated, portfolio doctor passes.
- [ ] Final report states the boundary: graph/inventory are support artifacts, not implementation/runtime proof.
