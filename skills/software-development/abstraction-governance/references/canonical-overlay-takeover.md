# Canonical Overlay Takeover Pattern

Scope: class-level abstraction/memory/documentation governance for cases where a new canonical structure must take over interpretation and future write targets from an older local brain, project ledger, architecture corpus, or evidence store.

Applicability:
- The user asks to reorganize, absorb, or let a new memory/architecture structure “接管” an older local brain or scattered documentation.
- Existing artifacts include historical receipts, certification records, authority decisions, project profiles, ledgers, or JSON evidence that must remain auditable.
- The desired outcome is canonical interpretation and future write routing, not physical deletion or blind migration.

Anti-conditions:
- Do not use this to authorize runtime behavior, external side effects, destructive cleanup, credential entry, push/deploy/publish, or lifecycle mutation.
- Do not physically overwrite old ledgers, receipts, project profiles, or evidence stores without a separate dependency/readback/rollback gate.
- Do not promote project-scoped facts into global memory; keep them in project profiles or scoped references.

## Pattern

Use an overlay / canonical-index / strangler strategy:

1. Establish a canonical packet or index as the new interpretation layer.
2. Absorb older sources into an explicit source map: source path, current role, pattern absorbed, canonical landing.
3. Add disposition banners to old Markdown/source documents:
   - current role: source / historical evidence / active subsystem spec;
   - canonical entrypoint;
   - canonical landing;
   - instruction not to extend the old file with new target architecture.
4. Treat JSON ledgers, receipts, gate indexes, certifications, and project profiles as governed source artifacts; record them in a manifest instead of editing them into prose.
5. Add a read-only doctor that verifies:
   - required canonical files exist;
   - index references every required document;
   - old source files have disposition banners;
   - JSON/profile sources still exist;
   - project profile points to the canonical entrypoint;
   - findings are empty or clearly classified.
6. Write the scoped project profile and progress ledger with the takeover status and evidence, if applicable.
7. Make a scoped commit only for the takeover artifacts and disposition banners; do not mix unrelated dirty files.
8. State the boundary explicitly: interpretation/write-target takeover complete; runtime/schema migration remains a separate authority gate.

## Completion criteria

A takeover is complete only when:
- canonical entrypoint exists and names anti-sprawl rules;
- source absorption map exists;
- disposition manifest exists;
- old Markdown sources have read-back banners;
- read-only doctor passes;
- scoped project profile/ledger points to the canonical packet when a project profile exists;
- old historical evidence remains preserved;
- the final report names what is not opened by the takeover.

## Common pitfalls

- Calling a clean new structure “complete” while old files remain plausible future edit targets.
- Physically moving/deleting evidence before proving no active consumer depends on the old path.
- Treating documentation consensus as runtime authority.
- Collapsing project profiles and historical receipts into global memory.
- Committing unrelated local receipt/log churn with the canonicalization commit.
