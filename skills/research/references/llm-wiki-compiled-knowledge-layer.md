# LLM Wiki as a compiled knowledge layer

Use this reference when evaluating Karpathy-style LLM Wiki / Claude Obsidian / Obsidian second-brain projects, or when the user asks how to turn videos, repos, articles, transcripts, screenshots, or project evidence into durable Hermes knowledge.

## Core distinction

LLM Wiki is not ordinary RAG.

- RAG: retrieve raw chunks at question time and synthesize a temporary answer.
- LLM Wiki: incrementally compile raw sources into a persistent, interlinked markdown knowledge base that is updated as new evidence arrives.

Durable framing:

```text
raw evidence / source docs
  -> LLM-maintained markdown wiki
  -> optional recall index (FTS/vector DB)
  -> cited answers, task candidates, skill/ADR promotion candidates
```

Do not invert the authority chain. Raw sources remain canonical evidence. The wiki is a compiled projection. Vector DB / Qdrant is recall only.

## Recommended Hermes landing zones

LLM Wiki mechanisms are useful for:

- long-video/course evidence products: transcript, OCR, chapter notes, deduped source index, Q&A entry points;
- project/repo intake: source note, project page, concept pages, comparison pages;
- research digests: evidence-backed concept maps rather than one-off summaries;
- taskpool context: background knowledge with citations, not lifecycle authority;
- skill distillation staging: repeated procedures can be promoted from wiki pages into skills after review;
- career/domain research: company, role, JD, market, and technology pages with source links.

Suggested local structure:

```text
~/.hermes/docs/wiki/
  sources/
  concepts/
  projects/
  comparisons/
  indexes/
```

Each synthesized claim should preserve:

- source URL/path and capture time;
- confidence: verified / inferred / speculative;
- evidence pointer: transcript timestamp, README line, screenshot/OCR note, or raw file path;
- promotion status: background only / task candidate / skill candidate / ADR candidate.

## Promotion gates

Never auto-promote wiki content into stronger authority surfaces.

- wiki knowledge -> readable background / cited answer;
- stable reusable workflow -> skill patch/create;
- stable user preference -> memory, compact declarative form;
- concrete executable work -> taskpool item with priority/dependency/triage metadata;
- architecture decision -> ADR;
- task status / done / blocked / claimed -> taskpool ledger/API only.

## Pitfalls

- Treating Obsidian/wiki as taskpool SSOT.
- Treating vector search similarity as evidence.
- Letting LLM-generated synthesis overwrite raw sources.
- Generating large markdown piles without linting for duplicates, orphan pages, stale claims, and uncited claims.
- Turning one video summary into memory/skill without proving class-level reuse.

## Useful acceptance checks

A good LLM Wiki evaluation should answer:

1. What are the raw sources and immutable evidence surfaces?
2. What markdown artifacts are generated and how are links maintained?
3. Are contradictions/stale claims explicitly tracked?
4. Is there a lint/health-check path for orphan pages, dead links, duplicate concepts, stale claims, and uncited synthesis?
5. What is the recall layer, and does every recall hit link back to a markdown/source artifact?
6. Which outputs are eligible for promotion into taskpool, skills, memory, or ADRs, and what gate controls that promotion?
