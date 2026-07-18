# Neural Modular Memory

A local-only Hermes `MemoryProvider` implementing the M³G architecture defined in:

`$HERMES_HOME/docs/private/neural-modular-memory-architecture-20260719.md`

Properties:

- append-only, redacted L0 turn events;
- contract-driven multi-module projections from each event;
- source hash, scope, validity, confidence, applicability and anti-condition metadata;
- bounded FTS5 retrieval plus same-source sibling completion;
- explicit supersession/conflict edges;
- cross-session consolidation and non-destructive decay/archive;
- wraps the existing canonical `brainctl search` path;
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
