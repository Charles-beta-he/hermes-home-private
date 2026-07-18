# Neural Modular Memory

A local-only Hermes `MemoryProvider` implementing the M³G architecture defined in:

`$HERMES_HOME/docs/private/neural-modular-memory-architecture-20260719.md`

Properties:

- append-only, write-before-persist redacted L0 turn events, including labeled credentials and Luhn-valid 13–19 digit bare compact, space-separated, or hyphen-separated PAN values; 12/20-digit separated runs are not partially consumed as PAN prefixes;
- contract-driven multi-module projections from each event;
- source hash, scope, validity, confidence, applicability and anti-condition metadata; recall admits only an exact 64-character lowercase hexadecimal SHA-256 that equals the referenced immutable L0 event hash;
- bounded, fail-closed FTS5 retrieval plus same-source sibling completion, with one combined Brain + modular character budget;
- explicit supersession/conflict edges; correction only suppresses projections matching the explicitly replaced subject, not any shared token;
- source-counted `supported` state and cross-session consolidation; active contradiction blocks promotion;
- the provider keeps episodic/default turn projections in `session:*`, while explicit durable user preferences use a hashed profile/user `user:*` scope so independent sessions can consolidate without exposing a raw identity;
- provider recall admits only the exact current session, its exact derived durable-user scope, and `global`; Store callers must explicitly supply any additional scope;
- `procedure`/`causal`/`decision` consolidation requires direct same-event evidence in every supporting session;
- non-destructive incremental decay/archive tracked per projection (`last_decayed_at`), so repeated maintenance at the same timestamp is idempotent; recall only mutates activation telemetry (`access_count`, `last_accessed_at`, `activations`);
- in-place schema migration from known v1/v2 stores to v3, while unknown or future schema markers fail closed without being rewritten;
- wraps the existing canonical `brainctl search` path and fails closed on timeout, non-zero exit, malformed JSON or invalid provenance;
- keeps a single active provider control plane: Local Brain remains a read-only canonical-document lane, while M³G owns fast turn events/projections under the same total recall budget; exact normalized cross-lane duplicates prefer the canonical Local Brain citation, without fuzzy semantic collapsing;
- mirrors successful built-in `MEMORY.md`/`USER.md` mutations only as redacted, append-only `memory_write_receipts`; receipts are not projected or recalled, so explicit canonical memory is not duplicated in the prompt;
- writes turn events and explicit-memory receipts only for `agent_context=primary`, and follows Hermes session switches before subsequent writes;
- leaves `state.db`/`session_search`, skills, project profiles and SSOT files with their existing canonical owners instead of copying them into the graph;
- declares the external Local Brain canonical vault through `backup_paths()` so Hermes backup/import can include it alongside profile-local memory state;
- no network, no external dispatch, no tool schemas, no authority grant.

Activation:

```bash
hermes config set memory.provider neural_modular_memory
```

Rollback:

```bash
hermes config set memory.provider localbrain
```

Storage defaults to:

`$HERMES_HOME/memory/neural_modular.sqlite3`

Run focused tests:

```bash
PYTHONPATH=$HERMES_HOME/hermes-agent python3 -m unittest discover \
  -s $HERMES_HOME/plugins/neural_modular_memory/tests -v
```
