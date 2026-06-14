# Hermes local-brain RAG / evidence retrieval evaluation — Douyin mHe lead

Date: 2026-06-14
Task: `2026-06-14-douyin-mhe-生产级raghermes本地证据检索与数据库治理评估`
Source intake: `/Users/charles/.hermes/docs/private/2026-06-14-douyin-mhe-production-rag-intake.md`
Benchmark fixture: `/Users/charles/.hermes/hermes-agent/evals/cases/local-brain-rag-retrieval-benchmark-v0.json`
Validation command: `python3 /Users/charles/.hermes/hermes-agent/scripts/validate_local_brain_rag_eval.py /Users/charles/.hermes/hermes-agent/evals/cases/local-brain-rag-retrieval-benchmark-v0.json --probe-state-db /Users/charles/.hermes/state.db`

## 1. Source evidence and repo mapping

- Social source is a Douyin note by `mHe`, resolved at intake to `https://www.douyin.com/note/7648655441894886691`, title `我用这套方法做了一个生产级 RAG 系统。最近我基于 LLM - 抖音`, published `2026-06-07 22:09:53`.
- Visible claim summary: production RAG is built around evaluation-first, simple baseline first, structure-preserving chunks, vector+BM25 complementarity, RRF fusion, rerank ROI, conservative context injection, and experiment logging.
- Canonical related artifact search maps the “LLM WiKi” phrase to `nashsu/llm_wiki` (`https://github.com/nashsu/llm_wiki`), TypeScript/Tauri desktop app with raw-source → wiki → schema style persistent knowledge base, optional LanceDB semantic search, MCP/API surfaces, and Obsidian-compatible wiki files.
- Boundary: the Douyin note did not directly prove that `mHe` authored or used `nashsu/llm_wiki`. Treat the repo as a related/canonical artifact for pattern extraction, not as authorship proof.

## 2. Hermes retrieval/database landing zones

Current Hermes surfaces found in code inspection:

| Surface | Evidence | Current capability | Gap against production-RAG checklist |
|---|---|---|---|
| Session state DB | `hermes_state.py` declares SQLite state store, WAL fallback, FTS5 message search, trigram CJK search, BM25 rank ordering. | Good deterministic session retrieval baseline; zero LLM cost; read-only recall via `session_search`. | No labeled eval suite for query quality; no RRF/vector/rerank comparator; no experiment ledger for retrieval changes. |
| Session search tool | `tools/session_search_tool.py` has DISCOVERY/SCROLL/BROWSE shapes, anchored windows, bookends, hidden tool-source filtering. | Strong UX for conversation recall and read-back evidence. | Ranking is FTS/BM25-centric; no structure-aware parent/child section model outside sessions. |
| Existing tests | `tests/tools/test_session_search.py` covers schema, FTS hits, sorting, scroll, role filters, cross-profile links. | Good functional regression coverage. | It does not measure MRR/Recall@k/context precision or retrieval failure taxonomy. |
| Evaluation fixtures | `evals/cases/research-evidence-summary.json` exists, but no local-brain RAG retrieval benchmark existed before this tranche. | Fixture convention exists. | Need local-brain retrieval fixture and validator. This tranche adds v0 benchmark fixture + validator. |

Recommended landing order:

1. **Benchmark first**: keep SQLite FTS/session_search as baseline; add labeled query fixture + validator before changing retrieval.
2. **Structure index second**: add read-only section metadata over docs/task notes (`source_uri`, `heading_path`, `breadcrumb`, `parent_section_id`, `raw_source_ref`) without daemon or vector DB.
3. **Hybrid retrieval third**: compare SQLite FTS/BM25 vs deterministic lexical section index; only then consider vector/RRF/rerank as optional candidate context.
4. **Authority boundary always**: retrieval results can suggest context only; taskpool markdown, kanban DB, proof logs, and deterministic command artifacts remain SSOT/proof authority.

## 3. Gap matrix: mHe seven principles → Hermes actions

| Principle | Hermes interpretation | Immediate artifact in this tranche | Next dependency |
|---|---|---|---|
| Eval first | Do not tune retrievers without labeled queries. | `local-brain-rag-retrieval-benchmark-v0.json` with 30 cases and metrics metadata. | Add runner that can score a candidate retriever output file. |
| Start simple | Keep current SQLite FTS/session_search as baseline. | Validator probes state DB FTS/trigram tables. | Baseline scorer for `session_search`/state DB. |
| Preserve structure | Store heading tree/breadcrumb/provenance in section records. | Data model below. | Read-only doc/task section extractor. |
| Vector + BM25 complement | Do not replace lexical retrieval; compare channels. | Metric plan includes channel attribution and fusion candidates. | Optional vector/RRF experiment only after baseline. |
| Rerank ROI | Rerank is optional T2 experiment, not first slice. | Rerank marked as gated comparator, not installed. | Cross-encoder/local reranker evaluation task if baseline fails. |
| Less is more | Measure context precision and injected-token budget. | Fixture requires `max_context_items` and `context_precision_at_k`. | Prompt-builder budget gate. |
| Experiment ledger | Every run records config, artifact path, and result hash. | Data model includes `retrieval_experiment` ledger. | Append-only local results store. |

## 4. Evaluation set and metrics

The v0 fixture defines 30 labeled query slots across five domains:

- session recall and cross-session continuity;
- taskpool lifecycle/proof evidence;
- Hermes code/docs architecture lookup;
- social/repo intake provenance;
- governance red-line / authority boundary lookup.

Metrics:

- `MRR@10`: first relevant hit rank for each query.
- `Recall@5` and `Recall@10`: whether expected source classes appear.
- `ContextPrecision@5`: fraction of top-k snippets that are actually useful for answering.
- `AuthorityViolationRate`: fraction of answers that treat candidate retrieval as lifecycle/proof authority.
- `ProvenanceCompleteness`: whether every returned item carries source URI/path, line/message/section id, and timestamp when available.

Acceptance threshold for a future baseline runner should be conservative: produce a report first; do not fail closed until the benchmark and scorer are ratified.

## 5. Proposed data model

```text
raw_source
  id, kind(session|task|doc|repo_review|social_evidence), uri, content_hash, captured_at, authority_rank

document_section
  id, raw_source_id, path_or_session_id, heading_path[], breadcrumb, parent_section_id,
  ordinal, text_hash, token_count, line_start, line_end, message_id, timestamp

retrieval_candidate
  experiment_id, query_id, retriever_name, candidate_rank, section_id, score,
  channel(fts|trigram|bm25|vector|rrf|rerank), snippet, provenance_json

retrieval_experiment
  id, created_at, code_ref, config_hash, fixture_path, output_path,
  metrics_json, notes, side_effects=false
```

Authority rules:

- `raw_source.authority_rank` documents provenance strength; it does not grant lifecycle authority.
- `retrieval_candidate` rows are ephemeral experiment outputs and must not be copied into task frontmatter as proof unless backed by original source read-back.
- Vector embeddings, if later approved, must store only local-derived embeddings and must be rebuildable from raw source hashes.

## 6. Vector DB / rerank boundary

Allowed later experiments, after explicit authorization and a baseline scorer:

- local-only lexical/FTS/BM25 scorer;
- local embedding index over a tiny fixture subset;
- RRF fusion over lexical + vector candidate IDs;
- rerank over already-local snippets.

Forbidden in this task:

- installing/running LanceDB, LLM Wiki, Tauri app, MCP server, MinerU, or any daemon;
- uploading private brain/session/task data to hosted embedding or rerank APIs;
- using vector similarity as taskpool SSOT, proof gate, or done evidence;
- broad file-system indexing without a scoped permission gate.

## 7. Dependency order / follow-up tasks

1. **Current tranche done**: source-review + benchmark fixture + validator + state DB FTS probe.
2. Add a read-only scorer that accepts retriever output JSON and computes MRR/Recall/context precision without touching live DBs.
3. Add a baseline adapter for current `SessionDB.search_messages` / `session_search` against an isolated synthetic fixture.
4. Add structure extractor for markdown/task notes with heading/breadcrumb/provenance, still read-only.
5. Only if baseline gaps are proven, propose optional hybrid/vector/RRF/rerank experiment behind explicit local-data and no-daemon gates.

## 8. Closeout classification

This is an evaluation/source-review task, not an implementation of a production RAG service. It is eligible for `review` after the benchmark fixture and validator pass. It is not eligible for `done` until a reviewer accepts that the evaluation artifact satisfies the advisory objective or a later certified closeout path ratifies it.
