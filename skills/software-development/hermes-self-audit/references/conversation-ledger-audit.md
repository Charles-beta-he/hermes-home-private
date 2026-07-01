# Conversation ledger audit: compaction ordering, secret propagation, and async notifications

Use this reference when auditing Hermes chat/session records after a user reports that a desktop/chat session did the wrong thing, ignored the latest request, exposed a secret, or mishandled a background-process notification.

## Landing-zone classifier

- Reusable procedure/debug path -> this reference under `hermes-self-audit`.
- Concrete code fix -> create a taskpool candidate or implement in Hermes source after a scoped SSOT/evidence packet.
- Project path, API key, exact session IDs -> do not store in SKILL.md; keep only redacted examples in this reference.
- Stable preference about reporting style -> user memory/profile, not this reference.
- Session progress/results -> no durable write.

## Symptoms

- The user gives a new request, but the assistant continues an older task from a compaction handoff.
- `session_search` or ContextCard generation returns secrets that were present in user messages or tool outputs.
- A background process watch notification arrives after a summary, and the assistant answers from stale process state instead of rechecking.

## Audit procedure

1. Identify the target ledger(s): current profile `state.db`, `sessions.db`, ContextCard DBs, and any profile-specific DBs explicitly in scope.
2. Search for the triggering text or redacted secret fingerprint across:
   - `messages.content`
   - serialized `tool_calls` / provider message item columns
   - FTS/trigram tables
   - ContextCard `object_json` / staging DBs
3. For each hit, reconstruct ordering by `id`, `session_id`, `role`, and timestamp. Look specifically for:
   - true user request preceding a `[CONTEXT COMPACTION — REFERENCE ONLY]` block;
   - compaction block recorded as `role=user` after the true request;
   - assistant turns after the compaction block acting on stale summary content.
4. Classify sensitive propagation:
   - original user/tool message only;
   - indexed in FTS/trigram tables;
   - copied into ContextCard title/keywords/constraints/summary;
   - reintroduced by session search or prompt-building.
5. For background process notifications, never rely on an earlier `process list`. Recheck live process state and probe the bound local port before reporting no residue.
6. Report with redacted values and separate:
   - evidence-backed finding;
   - blast radius;
   - current live state;
   - recommended fix lane (secret rotation, ledger cleanup, compaction ordering patch, redaction gate, process notification handling).

## Pitfalls

- Do not quote full API keys or tokens in the audit report, skill, memory, task title, or ContextCard.
- Do not treat a Context Compaction block as the active request. It is evidence/reference only; the latest non-compaction user message is the active request.
- Do not conclude a local server is closed from a stale process list when a watch notification just arrived. Re-read live process state and probe the port.
- Do not store exact session IDs as global rules. They can appear in a scoped evidence packet or cleanup task, not in reusable SKILL.md guidance.
- Do not encode temporary setup failures as durable negative tool claims.

## Fix lanes to propose

- **Secret rotation:** if a key appears in session DB/FTS/ContextCard, recommend revocation/rotation before cleanup.
- **Ledger cleanup:** backup DBs, replace exact secret with a placeholder, rebuild FTS/trigram indexes, then rescan.
- **Compaction ordering:** ensure compaction summaries cannot be appended after the active user request as the newest `role=user` turn; fail closed if a compaction block says "message below" but no real user message follows.
- **Redaction gates:** sanitize at raw message ingest, tool-result storage, FTS indexing, ContextCard source-card generation, richer-card prompts, and session-search output.
- **Async notification handling:** watch-pattern notifications should trigger fresh `process poll/list` and port probing before final status claims.

## Verification checklist

- [ ] Search spans raw messages, serialized tool/provider fields, FTS/trigram tables, and ContextCard DBs.
- [ ] Ordering was checked around the actual latest user message, not just session previews.
- [ ] Sensitive strings are redacted in every user-facing report.
- [ ] Live process/port state is rechecked after background notifications.
- [ ] Proposed durable writes are classified: skill/reference vs taskpool candidate vs memory vs no-write.
