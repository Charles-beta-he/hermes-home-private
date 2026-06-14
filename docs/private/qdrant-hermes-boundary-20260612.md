# Qdrant / Vector DB Boundary for Hermes Local Brain

Generated: 2026-06-12T10:49:47Z
Task: `2026-06-08-检查-qdrant-向量数据库在-hermes-中的正确作用边界`

## Verdict

Hermes should treat Qdrant/vector DB as an optional semantic retrieval projection for evidence, docs, task notes, session excerpts, screenshots/OCR transcripts, and reusable project context. It must not become the source of truth for taskpool lifecycle, kanban projection, proof hashes, mission ledger, permission gates, or closeout decisions.

Default recommendation now: keep the live path as deterministic local TF-IDF/SQLite retrieval and add Qdrant only behind an adapter gate when hybrid semantic retrieval is needed at larger corpus or cross-modal scale. The current local scripts already expose a default-off vector-backend pattern: `semantic_retrieval.py` resolves to `tfidf` by default, and `local_brain_turbovec_adapter.py` is gated by environment variables.

## Evidence read-back

- Existing intake artifact: `/Users/charles/.hermes/docs/private/video-project-intake-2026-06-08.md` states that Qdrant/vector DB should not replace taskpool, Kanban, or canonical ledger; suitable role is semantic retrieval over evidence, task notes, docs, screenshots/transcripts, user career artifacts, and reusable project context.
- Existing Hermes docs surface Qdrant as optional MLOps skill: `/Users/charles/.hermes/hermes-agent/website/docs/user-guide/skills/optional/mlops/mlops-qdrant.md`.
- Current live retrieval backend read-back:
  - `python3 ~/.hermes/scripts/semantic_retrieval.py backend-status` -> requested `tfidf`, active `tfidf`, prototype enabled `False`, TurboVec present `True`.
  - `python3 ~/.hermes/scripts/local_brain_turbovec_adapter.py status` -> schema `local_brain_turbovec_adapter_v1`, active `tfidf`, available `true`, rollback `unset HERMES_LOCAL_BRAIN_VECTOR_BACKEND or set HERMES_LOCAL_BRAIN_VECTOR_BACKEND=tfidf`.

## Minimal architecture

### Ingest sources

1. Canonical markdown/task notes: `~/Documents/brain/**`, especially task notes and project workpads.
2. Evidence artifacts: `~/.hermes/evidence/**`, `~/.hermes/docs/private/**`, and selected tick discussion artifacts.
3. Session excerpts: compacted conversation summaries with source session id, timestamp, and message span.
4. Structured project profiles / PRD extracts: project profile JSON and persisted PRD extracts under `~/.hermes/evidence/<project>/prd-extracts/`.
5. Optional media transcripts: OCR/audio/video transcripts only after extraction artifacts are persisted and linked.

Never ingest secrets, raw credentials, private tokens, browser cookies, auth state, or mutable runtime state as retrievable payload. Secret-like paths should be excluded or redacted before embedding.

### Chunking

- Markdown: split by frontmatter + heading hierarchy; target 400-900 tokens per chunk; preserve heading path.
- Task notes: separate frontmatter-derived summary, Objective, Acceptance Criteria, Validation, Proof Log, Final Handoff; avoid embedding huge escaped YAML fields.
- Evidence JSON: chunk by top-level record or claim; keep compact JSON pointers instead of full payload when large.
- Session excerpts: compact per decision/proof boundary, not per raw turn.
- Media transcripts: chunk by timestamp windows and include time ranges.

### Metadata schema

Recommended payload fields for any vector entry:

```json
{
  "source_uri": "file:///absolute/path.md#heading-or-json-pointer",
  "source_type": "task_note|evidence|doc|session_excerpt|prd_extract|media_transcript",
  "source_hash": "sha256:<content-chunk-or-source-hash>",
  "canonical_owner": "brain_markdown|taskpool_orchestrator|session_db|project_profile|evidence_artifact",
  "task_id": "optional task id",
  "project": "optional project",
  "architecture_target": "optional target",
  "created_at": "source timestamp if known",
  "indexed_at": "index timestamp",
  "permission_tier": "read|budget-handoff|...",
  "redaction_status": "none|redacted|excluded",
  "truth_rank": "candidate_context_only"
}
```

Collections/namespaces:

- `hermes_docs`: stable docs/skills/reference material.
- `hermes_evidence`: evidence artifacts and persisted PRD extracts.
- `hermes_tasks`: task notes and task-local SSOT snapshots.
- `hermes_sessions`: compacted session excerpts only.

Keep collection names projection-specific; do not create `taskpool_state` or `mission_state` collections as authorities.

### Retrieval gate

Retrieval results enter prompts only as candidate context after a deterministic gate:

1. Query classifier chooses allowed collections by task/project/permission tier.
2. Metadata filters enforce project, architecture_target, source_type, permission_tier, and redaction_status.
3. Result must include a resolvable `source_uri` and `source_hash`.
4. Before using a claim as evidence, re-read the canonical source file/session/artifact and verify the hash or current content.
5. If the source cannot be read, downgrade to context hint; never use it as proof.
6. Lifecycle transitions still require orchestrator `transition ... --evidence` with structured evidence and closeout gates.

### Truth-source回链

- Task lifecycle truth: `brain_task_orchestrator.py` task markdown + kanban projection, not vector DB.
- Project semantics truth: project profile / PRD / task-local SSOT, not vector DB.
- Evidence truth: file artifacts and command output logs, not embedding text.
- Session truth: session DB / transcript, not vector chunk.
- Vector result truth status: candidate recall only until canonical source read-back succeeds.

## Qdrant vs alternatives

| Option | Best role | Pros | Limits / risk | Hermes recommendation |
|---|---|---|---|---|
| SQLite FTS / current TF-IDF | Default local brain recall and deterministic replay | local, simple, transparent, cheap, easy rollback | weaker semantic recall | keep as default and fallback |
| TurboVec/FAISS-like local adapter | Fast local vector prototype | local, no external service, already gated by `HERMES_LOCAL_BRAIN_VECTOR_BACKEND` pattern | prototype maturity, index management | use for local benchmarking before Qdrant service |
| Qdrant | Production-like filtered vector/hybrid retrieval over larger corpus | payload filters, scalable ANN, service API, collection/schema controls | extra daemon/service, index drift, operational cost, must not become SSOT | optional projection adapter only, default-off |
| pgvector | If Hermes already has Postgres for another reason | transactional with relational metadata | heavier DB dependency for local Hermes | not recommended unless Postgres already exists |
| Chroma | notebook/dev RAG | easy local API | weaker production governance/ops boundary | okay for experiments, not main Hermes projection |
| Pure FTS | proof/evidence exact lookup | deterministic and auditable | no semantic expansion | always retain for proof/read-back |

## Update triggers

- On task/evidence/doc write: enqueue an index refresh event with path + source hash; do not block the write.
- On deletion/archive: tombstone vector entries by `source_uri` and keep audit entry; do not silently delete proof history.
- On PRD/project-profile update: re-index affected project namespace and invalidate old retrieval cache.
- On session compaction: index only compacted excerpts with explicit source spans.
- Nightly maintenance can rebuild projections from canonical sources; rebuild must not mutate task status.

## Closeout gaps / next implementation slice

This tranche is architecture/evidence only. A future implementation task may add a `semantic_vector_adapter` interface with read-only Qdrant/TurboVec backends, but should remain default-off and test that:

1. vector hits are rejected as lifecycle authority without canonical read-back;
2. source URI/hash read-back is required before proof use;
3. default backend remains TF-IDF unless an explicit env/config gate is set;
4. redacted/excluded files are not embedded.
