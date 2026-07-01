# Multi-implementation truth-source drift

Applicability: use when a project appears to have multiple implementation lines or packaging targets (for example PWA plus RN/native, prototype repo plus profile workspace, old bootstrap slice plus newer product repo) and the user suspects “多事实源” / split truth.

Anti-conditions:
- Do not promote a project-specific repo/path/status into the class-level skill body.
- Do not treat tests in one implementation line as proof that another line is current.
- Do not call a fixture, sample dataset, or demo seed a canonical fact source unless runtime code proves it is gated to demo/dev mode.
- Do not rewrite project code from this audit unless the user explicitly asks to implement consolidation.

## Audit procedure

1. Enumerate fact surfaces separately:
   - project profile and progress ledger;
   - product/PRD/ADR docs;
   - each implementation repo/package/workspace;
   - runtime data sources, caches, fixtures, and sample data;
   - taskpool/closure evidence.
2. Classify each surface as one of:
   - canonical governance source;
   - current implementation source;
   - projection/cache source;
   - fallback source;
   - fixture/demo seed;
   - historical/bootstrap evidence;
   - stale or orphaned line.
3. Compare implementation package names, paths, and consumers. Divergent package namespaces or duplicate core/gateway packages are drift signals, not automatically errors.
4. Inspect runtime imports for fixture bleed-through. A sample file becomes a production risk when the production assistant path imports it without an explicit demo/dev gate.
5. Verify each active line with its own narrow tests/builds before reporting status, and keep the statuses separated.
6. Recommend a single source-of-truth chain and explicit demotions, for example:
   canonical profile/Brain → exporter/cache → Gateway projection → mobile local projection → drafts/handoff queue only.
7. Write project-specific consolidation facts into the project profile or ledger, not the class-level skill. If implementation work is needed, create a task candidate/proposal rather than encoding it as a skill.

## Reporting format

- “What exists”: list each implementation line with path/package/test evidence.
- “Where truth lives”: name the canonical governance source and projection/cache sources.
- “Drift risks”: duplicate package namespaces, stale ledgers, runtime fixture imports, untracked native packaging, taskpool status mismatch.
- “Safe consolidation”: which source becomes primary, which lines become historical/bootstrap, and what code gates prevent fixture/demo data from becoming production evidence.
