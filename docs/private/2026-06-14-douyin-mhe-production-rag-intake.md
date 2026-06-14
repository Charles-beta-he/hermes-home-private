# Social/RAG intake evidence — Douyin mHe production RAG principles

Date: 2026-06-14

## Social source

- User source text: `3.58 复制打开抖音，看看【mHe的图文作品】我用这套方法做了一个生产级 RAG 系统。最近我基... https://v.douyin.com/bCkF7B6LI7g/ :0pm Z@Z.ZZ icN:/ 08/16`
- Resolved URL: https://www.douyin.com/note/7648655441894886691
- Page title: `我用这套方法做了一个生产级 RAG 系统。最近我基于 LLM - 抖音`
- Author: `mHe`
- Published at: `2026-06-07 22:09:53`
- Visible metrics at intake: likes `1239`, comments `111`, visible counts `1555` and `187`; author profile shows fans `406`, total likes `6239`.
- Hashtags: `#RAG #AI编程 #知识库 #LLM`

Visible post text summarized:

> Author built a “production-grade RAG retrieval service” based on an `LLM WiKi` knowledge base, without LangChain or LlamaIndex, hand-writing a hybrid retrieval RAG system. Seven principles: (1) evaluation first, 30 labeled eval cases beats a week of parameter tuning; (2) start simple with vector retrieval before BM25/RRF/rerank; (3) preserve structural information such as heading hierarchy, breadcrumbs, parent-child relations; (4) vector + BM25 complement each other and RRF fusion beats single-channel retrieval; (5) rerank is high ROI, Cross-Encoder can improve MRR 10–15%; (6) less is more, more candidates/context/injection often adds noise; (7) record every experiment because failed experiments are valuable. Final claim: RAG quality usually fails from weak engineering design, not weak models; chapter-tree data model, dual-channel fusion, conservative context injection, evaluation-driven development are differentiators.

Interpretation: treat the Douyin post as a RAG engineering lead and principle checklist, not as proof of a specific system implementation. Claims such as “production-grade” and “MRR +10–15%” need source-backed validation before adoption.

## Canonical mapping / related artifact search

The post mentions `LLM WiKi`. GitHub search for `LLM WiKi RAG` maps strongly to:

- Repo: https://github.com/nashsu/llm_wiki
- Full name: `nashsu/llm_wiki`
- Description: `LLM Wiki is a cross-platform desktop application that turns your documents into an organized, interlinked knowledge base — automatically. Instead of traditional RAG (retrieve-and-answer from scratch every time), the LLM incrementally builds and maintains a persistent wiki from your sources。`
- Stars/forks at intake: `11361 / 1388`
- Default branch: `main`
- Language: TypeScript
- License: GitHub API reports `Other / NOASSERTION`
- Updated at: `2026-06-13T19:32:31Z`

Important: the Douyin post does not directly provide a repo link, and search did not prove that `mHe` used `nashsu/llm_wiki`. Treat this mapping as a canonical related artifact for “LLM Wiki pattern,” not as authorship proof.

`nashsu/llm_wiki` structure inspected:

- Top-level: `README.md`, `README_CN.md`, `README_JA.md`, `README_KO.md`, `llm-wiki.md`, `package.json`, `src/`, `src-tauri/`, `mcp-server/`, `extension/`, `assets/`, `plans/`, `scripts/`, Vite/Tauri configs.
- `src/`: `App.tsx`, `commands/`, `components/`, `stores/`, `types/`, etc.
- `package.json`: Vite + React 19 + Tauri 2 + TypeScript + Zustand + graphology + sigma + Milkdown; scripts include `typecheck`, `build`, `test`, `mcp:build`, `mcp:test`, `tauri`.

README signals from `nashsu/llm_wiki`:

- Cross-platform desktop app that incrementally builds and maintains a persistent wiki from documents, instead of re-deriving answers on every query.
- Based on Karpathy’s LLM Wiki pattern.
- Features include two-step chain-of-thought ingest, multimodal image ingestion, optional MinerU PDF parsing, 4-signal knowledge graph, Louvain community detection, graph insights, optional LanceDB vector semantic search, persistent ingest queue, folder import, source folder auto-watch, Deep Research, async review, Chrome Web Clipper, local HTTP API + MCP server + AI Agent Skill.
- Core preserved pattern: Raw Sources (immutable) → Wiki (LLM-generated) → Schema; operations Ingest/Query/Lint; `index.md`, `log.md`, wikilinks, YAML frontmatter, Obsidian compatibility, human curates / LLM maintains.

## Hermes interpretation

This is relevant to Hermes local-brain / evidence retrieval, but with strict boundaries:

- RAG/vector retrieval can provide candidate context over evidence/docs/session/task notes, but must not become taskpool SSOT, lifecycle authority, proof gate, or deterministic replay source.
- Production RAG principles can become a Hermes evaluation-driven retrieval pipeline pattern: small labeled eval set, baseline vector retrieval, BM25, RRF fusion, rerank, structural chunking, conservative context injection, experiment ledger.
- LLM Wiki pattern can inform persistent evidence-wiki or documentation spine design, but raw sources and canonical ledgers remain authoritative.
- If used for Hermes, first task should be source-review + benchmark/eval design, not immediate vector DB installation.

## Recommended taskpool objective

Create a P2 evolution task for Hermes local-brain retrieval/RAG/database governance:

1. Preserve social evidence and inspect canonical LLM Wiki/RAG artifacts.
2. Define a production-RAG benchmark for Hermes evidence retrieval: 30 labeled queries, MRR/Recall@k/context precision, failure taxonomy.
3. Compare SQLite FTS / current session_search / deterministic indexes / vector DB / BM25+RRF+rerank under Hermes privacy and proof constraints.
4. Design data model: document hierarchy, breadcrumbs, parent-child sections, source provenance, immutable raw source refs, experiment ledger.
5. Define red lines: vector DB is candidate context only; no lifecycle authority, no proof gate replacement, no private upload, no unapproved daemon install.

## Red lines

- Do not install/run LLM Wiki, vector DB, LanceDB, MinerU, Tauri app, browser extension, or MCP server during intake.
- Do not grant file-system indexing over private brain/project directories without explicit scoped permission.
- Do not upload Hermes brain/tasks/session/private docs to cloud parsers or hosted embedding APIs during intake.
- Do not use social-post claims as benchmark results.
- Do not make vector similarity retrieval a canonical taskpool or proof authority.
