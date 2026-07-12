# Concept-bound local-brain recall, deterministic preflight, and MCP projection

## Applicability

Use when task intake carries local-brain `concepts`/tags and the control plane must turn them into reproducible knowledge recall or deterministic governance checks.

Anti-conditions:

- Do not interpret note tags, MCP tool availability, or knowledge hits as route/execute/lifecycle/writeback authority.
- Do not populate a persistent MCP graph until its source-of-truth, invalidation, deletion propagation, rebuild, and rollback contracts are explicit.
- Do not copy note body/excerpts into receipts or metadata-only graph projections.

## Canonical concept bridge

1. Normalize explicit task `concepts` into an optional validated `concept_refs` list before computing the semantic-envelope hash.
2. Validate each reference as a bounded lowercase slug and deduplicate while preserving order.
3. Build deterministic recall queries from `concept_refs` before broader outcome/capability terms.
4. Persist only source path, heading, score, and SHA-256; exclude excerpts.
5. Recompute current-source hits at executable lifecycle boundaries and fail closed on query, source, or hash drift.
6. Keep the semantic policy decision invariant before and after adding recall/preflight receipts.

Prefer one authority-neutral `concept_refs` channel for concept IDs, controlled tags, and aliases instead of parallel schemas that can drift. `source_refs` belong to evidence verification, while status/permission/write-surface fields remain control-plane inputs rather than query expansion.

## Concept-triggered deterministic preflight

When a concept identifies an existing deterministic verifier (for example theory-impact propagation), bind the trigger explicitly:

- matching concepts produce a bounded read-only preflight receipt;
- unmatched tasks produce `SKIP`;
- required verifier `FAIL` or `ERROR` blocks canonical intake in strict mode;
- receipt authority is explicitly `read_only_preflight_no_authority`;
- persist trigger IDs, coverage summary, failed-check names, and structured error types—never raw stderr or new policy bits.

Test PASS, FAIL, ERROR, SKIP, trigger ordering, and semantic-policy invariance. Run the real verifier once after unit GREEN and read back its coverage.

## MCP memory projection ladder

Treat a generic memory MCP as a transport/storage option, not as the local-brain SSOT.

Safe adoption order:

1. `doctor`/tool discovery: prove the configured MCP is reachable and inventory read/write/delete tools.
2. Read configured storage state: distinguish configured/reachable from persisted/populated/routed.
3. Build a metadata-only projection in memory or `/tmp`:
   - `brain_note` entities contain relative path, source SHA-256, and bounded status;
   - `brain_concept` entities contain the concept ID;
   - `brain_note --has_concept--> brain_concept` relations;
   - no body, excerpt, prompt, authority, or secret fields.
4. Run a disposable real-server smoke with an isolated memory file: create entities, create relations, read graph, verify counts/types, then delete the fixture directory.
5. Keep the configured persistent graph unchanged until incremental upsert, stale-hash invalidation, note deletion propagation, idempotency, rebuild, and rollback are implemented and tested.

A generic memory MCP that is configured and exposes tools but has no backing file/entities is **reachable but unused**, not a functioning local-brain integration.

## Verification checklist

- Semantic contract rejects malformed/oversized concept refs.
- Query plan is deterministic and bounded.
- Recall receipt excludes note excerpts and is hash-bound.
- Preflight PASS/FAIL/SKIP behavior is tested.
- Preflight cannot add or mutate semantic policy bits.
- Real deterministic verifier returns expected coverage.
- MCP projection contains metadata only and has bounded counts.
- Disposable MCP smoke proves entity and relation schema compatibility.
- Production/configured MCP store remains untouched unless separately authorized.
- Dirty shared worktrees use exact-file/hunk review; do not commit unrelated controller changes merely to package the slice.
