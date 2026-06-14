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

## Social-to-publishing pipeline boundary

When the user wants a social/video lead turned into a publishing pipeline (for example 小红书/RedNote):

- Split the chain into stages: content understanding → draft/publish package → login/session → browser form-fill → final publish → post metrics readback.
- Treat draft/package generation as low-risk and immediately automatable.
- Treat account login, cookie/session reuse, and final public posting as authority boundaries. The user must authenticate personally; default to "auto-fill then human clicks publish" unless the user explicitly authorizes full auto-publish and rollback/monitoring exists.
- Verify local platform/tool state before claiming a publishing chain is connected: list configured Hermes targets/tools, open the creator page, identify login vs editor state, and record blockers as auth/permission boundaries rather than capability absence.
- Prefer a durable publish package artifact (`note.md`, cover image, image set, tags, checklist, source evidence) before any browser automation.

## Video-content-analysis project stack pattern

For video-analysis leads that name concrete CV repos (for example Roboflow `inference`, `supervision`, `rf-detr`), classify the stack by responsibility before creating tasks:

- model layer: detection/segmentation model and license/runtime constraints;
- processing/report layer: annotation, tracking, zones, metrics, timestamps, evidence overlays;
- serving/workflow layer: local/server inference, stream/batch inputs, event APIs, external integrations.

Recommended taskpool shape: one parent architecture/gap-mapping task plus dependency-ordered child tasks for each layer. Acceptance evidence should include repo facts, license/runtime constraints, go/no-go for prototype, and a minimal smoke-test boundary. Do not install GPU drivers, download large models, start daemons, or request camera permissions during intake unless explicitly authorized.

## Digital-persona / talking-avatar video leads

When a social/video lead points to a digital-human, talking-avatar, photo+audio-to-video, or voice-driven avatar project (for example LongCat-Video-Avatar), classify it as a **future media adapter / digital persona capability**, not as an immediate runtime install.

Required intake shape:

1. Extract visible post text and OCR, but treat the social page as a lead only.
2. Map to canonical project/page/code/model artifacts and inspect README plus demo scripts for the actual input/output schema.
3. Check whether a prior generic evaluation task already exists. If yes, avoid duplicate generic tasks; add a narrower follow-up for the missing product surface (for example “Hermes digital persona `video_avatar_generate` adapter contract”).
4. Keep first task boundaries design-only unless explicitly authorized: no model weight downloads, no CUDA/FlashAttention install, no GPU daemon, no real face/voice generation, no public publish.
5. Recommended adapter contract fields: `persona_id`, `consent_ref`, `prompt`, `image_path`, `audio_path`, `mode`, `duration_policy`, `backend`, `safety.watermark`, `safety.review_required`, and provenance output paths.
6. Prefer a remote-GPU/hosted-worker boundary for heavy avatar models. Keep large model dependencies out of Hermes core and require a separate budget/permission task before any dry-run generation.

Safety red lines: explicit consent for persona image and voice/audio; provenance hashes for inputs; watermark or metadata for generated digital-human media; no third-party likeness/voice cloning without rights; generated videos default to draft/review, not public posting.

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
- If `add --json` returns `event_hook.status: ERROR` but the top-level `status: OK` and `created` path are present, treat task creation as successful and classify the hook payload separately. Common safe outcomes include `reconcile_required`, `autorun_disabled`, or an async multimodel route that moved the task into `running`.
- For security-sensitive/evolution video leads with `requires_multimodel`, verify whether the event hook started a background multimodel job with `brain_task_orchestrator.py multimodel-intervention-jobs --json`; a resulting `status: running` means the certification process owns the task, not that intake failed.
- Avoid passing a title that already starts with `Task -` to `brain_task_orchestrator.py add`; the template may add its own heading prefix and produce a visible `Task - Task - ...` title. If this happens, patch only the body heading and re-run `list --json` to verify the title projection.
- Any event-hook or multimodel allowlist skip is reported as a policy boundary, not hidden as success or misdiagnosed as task creation failure.
