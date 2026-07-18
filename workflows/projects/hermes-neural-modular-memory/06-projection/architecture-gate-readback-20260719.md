# M³G Architecture Gate Readback — 2026-07-19

- canonical_design_doc: `/Users/charles/.hermes/docs/private/neural-modular-memory-architecture-20260719.md`
- implementation: `/Users/charles/.hermes/plugins/neural_modular_memory/`
- active_profile: `default`
- active_config_readback: `memory.provider=neural_modular_memory`
- authority_boundary: local-only, authority-neutral, reference-only; no tool schemas; no external dispatch

## Deterministic gate readback

- Hermes venv unit tests: `Ran 11 tests ... OK`
- `py_compile`: exit 0 for `store.py`, `provider.py`, `__init__.py`
- provider discovery: `neural_modular_memory`, available `True`
- SQLite: `PRAGMA integrity_check=ok`
- immutable-event triggers: `events_no_delete`, `events_no_update`
- live prefetch: 1616 chars; authority boundary present; `source_event` and `sha256` provenance present
- Local Brain compatibility: canonical `brainctl search` block remains present

## Negative evidence

- Scope isolation and bounded sibling completion: covered by focused tests.
- Unrelated constraint is not contradicted by a theme correction: covered by focused test.
- Replayed turn does not duplicate events/projections: covered by focused test.
- Secret/token/Authorization/private-key patterns do not persist raw values: covered by focused test.
- Weak projection archives without deleting L0: covered by focused test.
- Storage failure returns empty recall rather than blocking the session: covered by focused test.

## Exact target and rollback

- Exact commit scope: canonical design document, this gate readback, and `plugins/neural_modular_memory/` source/tests/docs only.
- Runtime rollback: `hermes config set memory.provider localbrain`.
- Code rollback: revert the exact scoped local commit; do not reset the mixed Hermes-home worktree.
- Database remains local at `/Users/charles/.hermes/memory/neural_modular.sqlite3` for audit.

## Certification boundary

This readback supports `locally_implemented_and_verified` only. It does not establish biological equivalence, cross-device durability, long-horizon retrieval quality, external publication, or global certification. Independent verifier vote remains a separate closure input.
