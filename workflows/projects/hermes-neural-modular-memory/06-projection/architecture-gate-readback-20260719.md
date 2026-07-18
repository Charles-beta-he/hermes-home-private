# M³G Architecture Gate Readback — 2026-07-19

- canonical_design_doc: `/Users/charles/.hermes/docs/private/neural-modular-memory-architecture-20260719.md`
- implementation: `/Users/charles/.hermes/plugins/neural_modular_memory/`
- active_profile: `default`
- active_config_readback: `memory.provider=neural_modular_memory`
- authority_boundary: local-only, authority-neutral, reference-only; no tool schemas; no external dispatch

## Deterministic gate readback

- Hermes venv full suite: `Ran 26 tests ... OK`
- System Python full suite: `Ran 26 tests ... OK`
- Repeat gate: 100 complete iterations × 26 tests = 2600 tests; 0 failures, 0 errors; process exit 0
- `py_compile`: exit 0 for `store.py`, `provider.py`, `__init__.py`, and the test module
- `hermes config check`: configuration valid; active readback is `memory.provider=neural_modular_memory`
- provider discovery: discovered `True`, available `True`, loaded `True`
- live prefetch after same-session sync: 598 chars; authority boundary `True`; provenance `True`; within budget `True`; `get_tool_schemas=[]`
- SQLite: `PRAGMA integrity_check=ok`; 4 events, 10 projections, 16 edges, 12 activations
- immutable-event triggers: `events_no_delete`, `events_no_update`
- implementation hashes before scoped commit:
  - `store.py`: `37dead328a9fcc02581deaf59d9ad7bfcdf2eafe7a8efd0df9ac4d1ac97c7b6f`
  - `provider.py`: `f4d30c73c193769963f5ea626d0be81b3096fbba32c7d03e46579b2868c431f3`
  - `test_memory_runtime.py`: `4078e5294ca02ad8e1443292bb06576fec8893a1038fadb1e3f2aab45cab2627`

## Independent verifier remediation map

The first independent verifier returned `FAIL` against an earlier drifting hash. Every concrete blocker and requested negative-test class was handled in the current slice:

- consolidation now rejects active `contradicts` edges;
- recall activation no longer promotes a single source to `supported`; two source events are required;
- `procedure`/`causal`/`decision` require direct same-event evidence in every supporting session before consolidation;
- same-scope unrelated correction regression remains covered;
- recall telemetry exception is explicit in the SSOT;
- primary and sibling recall share reference-only, expiry, scope, status, and provenance gates;
- Brain + modular recall share one total character budget;
- repeated `turn_key` with changed content raises `ValueError` instead of silently reusing an event;
- scope isolation covers session/task/project/user/domain plus global;
- brainctl timeout, non-zero exit, malformed JSON/hash/path/line fail closed;
- AWS key, cookie/session, card identifier, token, Authorization, and private-key patterns are redacted;
- automated test asserts `get_tool_schemas()==[]` and the authority-neutral prompt boundary.
- bare 13–19 digit payment-card/PAN text is redacted before L0 and projection persistence;
- provider-ingested explicit durable preferences derive a non-PII `user:*` scope, consolidate across two real provider sessions, and remain recallable from a third session while episodic projections remain session-scoped;
- correction suppression requires sufficient overlap with the explicitly replaced subject, preventing shared-token cross-topic suppression;
- FTS lookup errors and empty candidate sets return no modular recall instead of falling back to a scope-wide scan.

A fresh independent verifier vote against the next exact committed hash remains required before any wording stronger than `locally_implemented_and_verified`. Earlier votes against prior hashes remain historical evidence only.

## Exact target and rollback

- Exact commit scope: canonical design document, this gate readback, and `plugins/neural_modular_memory/` source/tests/docs only.
- Runtime rollback: `hermes config set memory.provider localbrain`.
- Code rollback: revert the exact scoped local commit; do not reset the mixed Hermes-home worktree.
- Database remains local at `/Users/charles/.hermes/memory/neural_modular.sqlite3` for audit.

## Certification boundary

This readback supports `locally_implemented_and_verified` only. It does not establish biological equivalence, production-grade certification, cross-device durability, long-horizon retrieval quality, external publication, or global certification.
