# PWA Offline Context Gateway Pattern

Scope: class-level mobile/PWA delivery pattern for an online assistant companion that needs limited offline usefulness on mobile browsers. This is not tied to one repository, product name, provider, or deployment.

Applicability:

- Mobile/PWA companion for an online assistant or agent.
- Offline UX should be user-transparent: the user asks normally; the app silently searches synced context.
- Accuracy matters more than open-ended offline generation.
- Future architecture may become distributed or multi-device.

Anti-conditions:

- Do not use this as a justification for offline tool execution.
- Do not store high-privilege API keys, tool tokens, or long-lived bearer tokens in the PWA.
- Do not make WebGPU/WASM local LLM the MVP dependency unless the explicit product goal is local generation and the device matrix is proven.
- Do not put mobile sync/device/auth concerns directly into an assistant/agent core loop when a separate edge/gateway boundary is viable.

## Product model

Define the PWA as:

> online assistant lightweight client + offline evidence-constrained context assistant + network-restored handoff/reconciliation layer.

Offline mode is not “full agent offline.” It should only answer from locally synced evidence such as ContextCard, EvidenceSpan, TaskSnapshot, pinned decisions, and recent summaries.

User experience:

1. User asks in normal chat; no manual “search history” interaction.
2. App detects offline/weak network.
3. Local worker retrieves and ranks synced ContextCards/EvidenceSpans.
4. Evidence gate decides: answer, cautious answer, refuse, or draft-only.
5. Sources are hidden by default but expandable.
6. Low-confidence, refused, realtime, or action requests become handoff packets.
7. When online, the server-side assistant reconciles: confirmed / expanded / corrected / rejected.

## MVP stack

Prefer this order:

1. PWA shell + Service Worker for app shell only.
2. IndexedDB for structured offline data.
3. WebWorker for tokenization, search, ranking, evidence scoring, and response policy so the UI thread stays responsive.
4. Deterministic retrieval first: Chinese n-gram/BM25-style search + recency/authority/source weighting.
5. WASM/FTS/embedding/reranker only after real evaluation proves benefit.
6. Local LLM only as a constrained rerank/compress/draft enhancer; never as the fact source.

## Data contracts

Core local records:

- `ContextCard`: title, summary, decisions, constraints, open questions, keywords, entities, topics, time range, authority level, sensitivity level, source refs, source hash, card version.
- `EvidenceSpan`: card id, message id, speaker, text, timestamp, source hash, sensitivity, score hint.
- `OfflineAnswer`: query, answer state, evidence hits, evidence score, refusal reason, sync status.
- `HandoffPacket`: query, offline answer id, local evidence, local decision, refusal reason, followups, reconciliation status.

State model:

- `online_deep_answer`: online assistant answer; can include tools/current facts.
- `offline_evidence_answer`: local cached evidence answer.
- `offline_refusal`: evidence insufficient, realtime, high-risk, or unavailable.
- `offline_draft`: external action request saved as draft only.
- `pending_handoff`: queued for online processing.
- `reconciled`: online assistant checked and marked confirmed/expanded/corrected/rejected.

## Evidence gate rules

- Realtime facts, current prices/news/weather/versions, system state, and tool-dependent questions: refuse offline and queue handoff.
- External actions such as send/delete/commit/deploy/pay: draft-only offline; never auto-execute on reconnect without confirmation.
- High-risk or sensitive topics: refuse or require online safety checks.
- Strong evidence: answer naturally and attach hidden sources.
- Partial evidence: cautious answer with boundary language and auto-handoff.
- Weak/no evidence: refuse; do not show unrelated retrieved snippets as “sources.”

Common thresholds:

- `score >= 0.75`: answer.
- `0.45 <= score < 0.75`: cautious answer + handoff.
- `< 0.45`: refuse + handoff.

## Gateway boundary for future distributed service

For long-term/distributed architectures, prefer an independent sync gateway rather than embedding mobile sync/device/auth into the agent core.

Gateway responsibilities:

- `/v1/sync/bootstrap`
- `/v1/sync/changes?since=...&types=context,evidence,index,task`
- `/v1/sync/deviceState`
- `/v1/pwa/offline-handoff`
- `/v1/pwa/offline-handoff/:id/result`
- device registration/revocation, sync policy, tombstones, TTL, remote wipe, local data encryption key wrapping.

Agent/core responsibilities:

- reasoning, tools, memory/session/task source data, high-risk execution, audit, ContextCard generation, handoff reconciliation.

Recommended rollout:

1. Start as modular monolith/local gateway with in-memory or SQLite state.
2. Keep API contracts versioned and no-store.
3. Add pairing-code device registration and wrapped local data encryption key.
4. Add an adapter to the real assistant source of truth.
5. Only later split Postgres/queue/object storage/workers if needed.

## Unique fact source and canonical projection

Scope: use this for any mobile/PWA offline assistant companion that introduces a sync gateway and cached `ContextCard`/`EvidenceSpan` projection. Anti-condition: do not apply to ordinary static PWAs, generic offline-first CRUD apps, or apps where the mobile client is explicitly intended to be the fact author.

Treat the online assistant/brain/session store as the only fact source. The gateway may synchronize and cache a projection, but must not become the authority that invents ContextCards.

Recommended source chain:

1. Agent/brain/session store owns raw conversation, memory, task, and tool-result facts.
2. A read-only canonical exporter projects those facts into `ContextCard` / `EvidenceSpan` JSON.
3. The gateway calls the exporter or reads a fresh canonical projection cache.
4. The PWA syncs the gateway projection into IndexedDB and answers only from local evidence.

Projection cache pattern:

- Keep an agent-side cache table such as `contextcard_changes(revision, type, object_json, updated_at)`.
- Fresh cache rows take precedence over rule-based projection from the session DB.
- Stale/missing cache rows fall back to deterministic read-only projection.
- The cache is not a second truth source; refresh authority stays with the agent/brain.
- Next-level quality improvements should add an agent/brain cache writer or session-end hook, not move ContextCard generation into the gateway or PWA.

Exporter hygiene:

- Open source databases read-only.
- Default to user-facing session sources; exclude background cron/internal task sources unless explicitly requested.
- Filter system prompt boilerplate, skill bodies, planner/smoke payloads, and budget/iteration relay text before syncing to mobile.
- Keep app-shell caching separate from `/v1/` sync responses; sync/handoff responses stay `Cache-Control: no-store`.

## Security defaults

- PWA is low-trust.
- `access_token` in memory only; prefer HttpOnly Secure SameSite refresh cookie when web auth exists.
- Never store tool credentials/API keys/refresh tokens in IndexedDB/localStorage/Cache Storage.
- Service Worker should cache app shell/static assets only; do not cache `/api/` or `/v1/` sensitive responses.
- Sensitive API responses should use `Cache-Control: no-store`.
- Encrypt local structured data with WebCrypto AES-GCM; formal MVP should wrap the local data encryption key via gateway/device registration.
- High-sensitivity ContextCards default to not synced; pinned/explicit user choices can override only through policy.

## Verification checklist

- PWA opens and is installable; standalone safe-area/input bar works on iOS.
- Offline app shell loads.
- WebWorker/IndexedDB capability probe works.
- Offline historical decision question returns a natural answer with hidden expandable sources.
- Realtime question refuses and queues handoff without unrelated citations.
- Action request becomes draft-only.
- Gateway bootstrap/changes/handoff/result pass curl or contract tests.
- `Cache-Control: no-store` is present on sync/handoff responses.
- Tests cover answer/refusal/draft/handoff and remote change mapping.
