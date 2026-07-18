# Neural Modular Memory

A local-only Hermes `MemoryProvider` implementing the M³G architecture defined in:

`$HERMES_HOME/docs/private/neural-modular-memory-architecture-20260719.md`

Properties:

- append-only, redacted L0 turn events;
- contract-driven multi-module projections from each event;
- source hash, scope, validity, confidence, applicability and anti-condition metadata; recall admits only an exact 64-character lowercase hexadecimal SHA-256 that equals the referenced immutable L0 event hash;
- bounded, fail-closed FTS5 retrieval plus same-source sibling completion, with one combined Brain + modular character budget;
- explicit supersession/conflict edges; correction only suppresses projections matching the explicitly replaced subject, not any shared token;
- source-counted `supported` state and cross-session consolidation; active contradiction blocks promotion;
- the provider keeps episodic/default turn projections in `session:*`, while explicit durable user preferences use a hashed profile/user `user:*` scope so independent sessions can consolidate without exposing a raw identity;
- provider recall admits only the exact current session, its exact derived durable-user scope, and `global`; Store callers must explicitly supply any additional scope;
- `procedure`/`causal`/`decision` consolidation requires direct same-event evidence in every supporting session;
- non-destructive decay/archive; recall only mutates activation telemetry (`access_count`, `last_accessed_at`, `activations`);
- wraps the existing canonical `brainctl search` path and fails closed on timeout, non-zero exit, malformed JSON or invalid provenance;
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
