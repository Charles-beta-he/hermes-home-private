# PWA Offline Context Assistant Pattern

Use when a mobile/PWA assistant must remain useful offline without becoming an ungrounded local LLM. This pattern is for evidence-constrained, user-transparent-but-not-user-burdensome offline answers based on previously synced online context.

## Applicability

Use when:
- The target surface is iOS/Android PWA or mobile web.
- Users should ask normal chat questions, not manually search history.
- Offline accuracy matters more than open-ended local generation.
- The online agent/server remains the authority for tools, current facts, and high-risk actions.

Anti-conditions:
- Do not use this as a full offline Agent design.
- Do not let the PWA execute tools, send messages, mutate files, or call external APIs offline.
- Do not treat local model output as a fact source. Local WASM/WebWorker/LLM may rank, compress, or draft only from evidence.

## Product model

Online:
1. Server/agent answers normally.
2. Server produces offline-ready `ContextCard` / `EvidenceSpan` / `TaskSnapshot` records.
3. PWA syncs compact records, not raw full history by default.

Offline:
1. User asks a normal question.
2. PWA silently classifies intent.
3. WebWorker retrieves relevant ContextCards/EvidenceSpans from IndexedDB.
4. Evidence gate decides: answer, cautious answer, draft-only, or refusal/handoff.
5. UI gives a natural answer; sources are collapsed by default but expandable.
6. Anything uncertain goes into a pending handoff queue for online reconciliation.

Network restored:
1. PWA uploads handoff packet containing query, local decision, evidence hits, and confidence.
2. Online agent returns `confirmed | expanded | corrected | rejected` reconciliation.
3. If corrected/rejected, show the user; do not silently overwrite the offline answer.

## Recommended local stack

MVP:
- PWA App Shell + manifest + service worker for static shell only.
- IndexedDB for business data.
- WebWorker for tokenization/search/scoring to avoid blocking input/scroll.
- Deterministic BM25/n-gram/entity/recency retrieval.
- Evidence-gated template/natural response.
- Local model adapter contract can be implemented before selecting a real model: it must be citation-gated against retrieved evidence hit ids and must fall back cleanly to deterministic wording.

Defer until measured benefit or an explicit packaging/runtime decision:
- WASM SQLite/FTS5.
- local embeddings/rerankers.
- local model summarization.
- WebGPU acceleration.
- native Capacitor/iOS shell.

## Core data contracts

`ContextCard` fields should include:
- id, chatId, title, shortSummary/longSummary
- decisions, constraints, openQuestions
- keywords, entities, topics
- timeRange, authorityLevel, sensitivityLevel, expiresAt
- sourceRefs, sourceHash, cardVersion, indexHints

`EvidenceSpan` fields should include:
- id, cardId, messageId, speaker, text, timestamp
- sourceHash, scoreHint, sensitivityLevel

`OfflineAnswer` fields should include:
- userQuery, answerText, answerState
- evidenceHits, evidenceScore, refusalReason
- createdAt, syncStatus
- modelMode (`deterministic` or `local_model_grounded`) and optional localModelId when a local model adapter is accepted

If adding a local model adapter, make it a wording/rerank adapter, not a fact source. The adapter should receive `{ query, hits }` and return `{ text, citedHitIds }`. Accept its text only when every citedHitId belongs to the current retrieved hit set; otherwise discard the model output and fall back to deterministic answer/refusal. This lets PWA/iOS reserve WebGPU/WASM/native runtimes without hardcoding a model before the runtime/package decision.

`HandoffPacket` fields should include:
- userQuery, offlineAnswerId, localEvidenceHits
- localDecision, refusalReason, userFollowups
- reconciliationStatus when returned by server

## Evidence gate defaults

Intent classes:
- `history_decision` / `summary_or_plan`: eligible for local evidence answer.
- `realtime_fact`: refuse offline and queue handoff.
- `external_action`: save draft only; require online confirmation/execution.
- `high_risk`: refuse offline and queue for online safety checks.

Thresholds:
- score >= 0.75: answer from evidence.
- 0.45 <= score < 0.75: cautious answer plus online reconciliation.
- score < 0.45: refuse and queue handoff.

Important pitfall: if refusing because of realtime/high-risk/action intent, do not display unrelated retrieved sources just because lexical retrieval found cards. Sources should be shown only for answer/cautious-answer decisions.

## Sync and gateway boundary

For future distributed/mobile use, prefer an independent Pocket/Mobile Gateway boundary over embedding mobile sync directly into the agent core:

PWA/mobile client -> Pocket Gateway -> Agent/Brain/session/task sources

Gateway owns:
- device registration, revoke/wipe state, sync cursors
- no-store HTTP API contract
- ContextCard/EvidenceSpan/TaskSnapshot projection
- handoff queue and reconciliation status
- local-first DB such as SQLite, later Postgres/queue if distributed

Agent/Brain owns:
- generating authoritative ContextCards
- current facts, tools, actions, and safety decisions
- handoff deep processing and reconciliation

MVP endpoints:
- `GET /v1/sync/bootstrap`
- `GET /v1/sync/changes?since=...&types=context,evidence,index,task`
- `POST /v1/sync/deviceState`
- `POST /v1/pwa/offline-handoff`
- `GET /v1/pwa/offline-handoff/:id/result`
- optional local pairing endpoints: `POST /v1/devices/pairing-codes`, `POST /v1/devices/register`, `POST /v1/devices/:id/revoke`

## Security defaults

- Service worker caches static shell only; never cache `/api/` or `/v1/` sync/chat/tool responses.
- Sensitive APIs return `Cache-Control: no-store`.
- Access tokens stay in memory; refresh should be HttpOnly Secure SameSite cookie when available.
- Never store third-party tool tokens, long-lived bearer tokens, secrets, or executable tool grants in PWA storage.
- Store offline records encrypted with WebCrypto AES-GCM when feasible; treat PWA encryption as risk reduction, not native Keychain equivalence.
- Revoke must cause bootstrap to return `requiredClientAction: wipe`.

## Verification checklist

- App shell opens offline and installed-mode layout handles safe area.
- User can ask normally; no manual history-search UX required.
- WebWorker capability probe succeeds; UI remains responsive.
- Evidence answer shows collapsed sources; refusal/action/realtime answers do not show misleading sources.
- Local model adapter tests cover both paths: accepted output cites only retrieved evidence hit ids; bad citations/non-retrieved ids are discarded and deterministic output is used.
- Realtime and external-action requests refuse/draft offline and enqueue handoff.
- Handoff payload excludes unrelated evidence on refusal.
- Gateway returns no-store headers and validates device id.
- Pairing code is one-time use; revoke returns wipe on next bootstrap.
- Tests cover answer/refusal/action, remote sync mapping, sync client no-store, encrypted record roundtrip, gateway contracts, SQLite persistence, and pairing/revoke behavior.
