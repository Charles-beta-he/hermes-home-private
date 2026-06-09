# Local-brain LLM Wiki intake pattern

Use when a user approves storing research/video/repo insights in the local brain, especially Karpathy-style LLM Wiki / Obsidian / second-brain ideas.

## Core framing

Treat the local-brain wiki as an **evidence-backed compiled knowledge layer**, not as a new authority source.

Layering:

```text
raw evidence / source notes
  -> compiled wiki markdown
  -> recall index: FTS / Qdrant
  -> answer with citations
  -> optional promotion gate: skill / memory / taskpool / ADR
```

## Recommended landing zones

- `02-证据与原文/evidence/`: original evidence notes for videos, webpages, repos, OCR/transcripts, metadata, source links.
- `03-知识库/`: compiled concept/project/comparison/index pages.
- `04-知识原子/`: reusable but not-yet-promoted experience atoms.
- `05-实践与项目/tasks/`: governed execution tasks.
- `06-治理与评审/`: boundaries, ADRs, review notes, proof gates.

If the user only says “认可” after a proposed local-brain/wiki/taskpool plan, interpret it as approval to perform the next concrete safe step that was just proposed, while preserving red lines and avoiding broad migration.

## Minimum write pattern

1. Create or update an evidence note with:
   - source URL and resolved URL if available;
   - title/author/date/visible metrics;
   - extracted claims;
   - candidate upstream repos/docs;
   - uncertainty labels.
2. Create or update a compiled concept/project note with:
   - evidence refs back to raw notes;
   - local-brain layer placement;
   - promotion rules;
   - anti-drift rules;
   - lint checks.
3. If user approved taskpool intake, create a governed task only after duplicate search and triage. The task should reference both evidence and concept notes.

## Boundaries

- Wiki/Obsidian/local brain notes are knowledge projections, not taskpool/ledger authority.
- Qdrant/vector DB is recall only; it must回链 source/wiki files and must not become fact authority.
- Do not automatically promote wiki content into memory, skill, taskpool, or ADR.
- Do not install Obsidian plugins, migrate vault structure, or run third-party automation unless explicitly authorized.
- Do not save bulky task findings to memory; memory is for stable preferences/facts only.

## Lint checks for compiled wiki notes

- orphan pages;
- dead links;
- duplicate concepts;
- stale claims;
- source-less claims;
- conclusions without verified/inferred/speculative status where it matters;
- wiki conclusions without evidence backlinks;
- content that should be promoted to skill/task/ADR but remains ungoverned prose.

## Output habit

Report exact files written and the boundary classification. Keep the answer short unless the user asked for a design document.