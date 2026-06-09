# Video / social-link project intake and vector DB boundary

Use when the user shares WeChat 视频号 / short-video / social-post links and asks to analyze projects, absorb them, or add follow-up work to the taskpool.

## Pattern

1. Treat the social post as a lead, not the source of truth.
   - Extract visible post text, author/date, engagement, and any OCR-visible project names.
   - For WeChat preview pages, the DOM may contain richer text than the accessibility snapshot; inspect the page text when available and use visual OCR for the covered video frame after closing QR overlays.
   - Do not rely only on the creator's hype copy.

2. Map each claimed project to a live canonical artifact.
   - Search GitHub/web for the exact project name plus distinctive phrases from the post.
   - Confirm repo owner/name, description, stars/update time, README claims, and top-level architecture files.
   - If the mapping is uncertain, label it as uncertain and avoid creating overly specific implementation tasks.

3. Write a compact evidence note before task creation.
   - Include social URL, extracted post text, mapped repo/docs URL, repo facts, and the interpretation for Hermes.
   - Store under `~/.hermes/docs/private/` or another durable evidence directory, not `/tmp`.

4. Add rich taskpool tasks, not vague “analyze X” items.
   - Include `priority`, `lane`, `architecture_target`, `priority_layer`, `dependency_order`, `multimodel_triage_result`, `capability_delta`, `anti_drift_check`, `acceptance_evidence`, `parallel_boundary`, `objective`, `accept`, `red_line`, and `evidence_ref`.
   - Use dependency order when several projects form a sequence.
   - For social-source hype, make acceptance evidence architecture/gap analysis first; promote to implementation only after a grounded review.

## Qdrant / vector database boundary

When external projects mention Qdrant, Pinecone, Chroma, Weaviate, Milvus, pgvector, embeddings, RAG, or semantic memory, explicitly classify the role:

- Suitable role: semantic retrieval over evidence, docs, session transcripts, task notes, screenshots/OCR, project artifacts, and reusable context.
- Non-role: taskpool SSOT, Kanban/lifecycle state, done/blocked/claim authority, proof gates, deterministic replay source, or canonical evidence identity.
- Required guardrail: vector results are candidate context only. Every retrieved item must link back to a source document/artifact with timestamp/version metadata; lifecycle decisions must still use the canonical ledger and proof gates.
- Comparison prompt: decide whether Qdrant is truly needed versus SQLite FTS, pgvector, or plain deterministic indexing for the specific data volume and freshness pattern.

## Pitfalls

- Do not add one task per social-link with only the post title; preserve source evidence and acceptance criteria.
- Do not mistake optional/transitive vector dependencies in a repo lockfile for the repo's actual architecture.
- Do not let Generative UI / agent UI layers become the canonical task state. Treat them as projections/adapters unless a controlled mutation API with audit/confirmation is explicitly used.
- Do not install external daemons or grant OS-level permissions (for example macOS Accessibility) during intake unless the user explicitly authorizes the side effect.

## Verification

- Evidence note exists and references both the social source and canonical repo/docs.
- Newly created tasks are discoverable in `brain_task_orchestrator.py list --json` and have rich metadata.
- Dashboard/control-center refresh succeeds.
- Any event-hook or multimodel allowlist skip is reported as a policy boundary, not hidden as success or misdiagnosed as task creation failure.
