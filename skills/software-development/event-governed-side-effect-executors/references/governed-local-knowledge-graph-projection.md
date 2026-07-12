# Governed local knowledge-graph projection

## Applicability

Use this pattern when a canonical file-backed knowledge base must be projected into a local MCP graph or derived index for search and traversal.

Apply only when:

- the file-backed corpus remains the single source of truth;
- the derived graph can be deleted and rebuilt;
- the target is an exact local store;
- projection metadata cannot grant task, lifecycle, execution, or side-effect authority.

Do not use this pattern for bidirectional synchronization, remote graph writes, arbitrary MCP mutations, or cases where the graph is itself canonical.

## Boundary ladder

1. **Read-only projection**
   - Parse bounded metadata only.
   - Emit stable entity/relation names and source-content hashes.
   - Exclude document bodies unless the contract explicitly requires them.
   - Mark the artifact `read_only_projection_no_mcp_write`.

2. **Isolated transport compatibility**
   - Start the real MCP server against a temporary store.
   - Import a tiny fixture.
   - Read it back through the MCP tool, not only by parsing the file.
   - Verify exact entity/relation counts and preservation of an unrelated foreign record.

3. **Explicit local apply**
   - Scope: class-level local derived-graph writers whose source corpus remains canonical.
   - Applicability: one-way projection into one exact local configured store.
   - Anti-condition: not for remote stores, bidirectional sync, arbitrary write paths, or authority-bearing graph records.
   - Require an explicit apply-style switch and bind production mode to the one exact configured target; do not expose an arbitrary write path.
   - Reject symlinks in the target leaf **and every relevant parent component**. A leaf-only check is bypassable through a symlinked directory.
   - Strictly validate the complete projection before writing: exact schema/status/authority marker, owned prefixes, allowed entity types, observation shapes, relation type, and existing endpoints. A schema-valid foreign/privileged entity is still an injection and must fail closed.
   - Reconcile the complete reserved subgraph: remove stale owned entities and every relation whose `from` **or** `to` endpoint touches an owned namespace; preserve wholly unrelated foreign records.
   - Write with a same-directory temporary file, flush, `fsync`, and atomic replace.

4. **Receipt and rollback**
   - Bind before/after SHA-256, target, counts, backup path, and authority boundary.
   - If the target existed, use a collision-resistant backup name (nanosecond timestamp plus UUID), copy it, and hash-read-back the backup before replacement.
   - If the target did not exist, create an explicit absent-state rollback artifact; do not rely only on prose saying the target can be deleted.
   - Implement rollback as executable, digest-bound behavior: restore only a verified backup or delete only a newly created target, and reject target drift from the recorded after-hash.

5. **Configured-store verification**
   - Run the MCP server's connection/doctor probe.
   - Read the configured graph through the MCP protocol.
   - Run one meaningful search and verify an exact expected entity.
   - Replay the projection and require `UNCHANGED` with the same after-hash.

## Storage-format pitfall

Do not infer a server's on-disk format from its read API. For example, an MCP graph may return an object containing `entities` and `relations` while persisting newline-delimited records such as:

```json
{"type":"entity","name":"...","entityType":"...","observations":[]}
{"type":"relation","from":"...","to":"...","relationType":"..."}
```

Generate a temporary graph through the real server, inspect the resulting store, and then implement the projection writer against that verified format. A syntactically valid JSON object can otherwise be silently treated as an empty graph.

## Minimum adversarial tests

Scope: class-level verification for local SSOT-to-derived-graph writers. Applicability: before configured-store enablement or certification. Anti-condition: these checks do not authorize external writes or make the derived graph canonical.

- bounded projection and no implicit write;
- stable source hashes and no body leakage;
- wholly foreign entity/relation preservation;
- stale owned entities and relations touching either owned endpoint are removed;
- malformed projection, malformed JSON/JSONL, and invalid UTF-8 rejection;
- wrong configured target rejection;
- symlinked leaf and symlinked parent rejection;
- schema-valid privileged/foreign entity injection rejection;
- invalid observations, relation type, and missing endpoints rejection;
- first apply and byte-stable idempotent replay;
- collision-resistant backup names and backup digest equality;
- absent-target rollback artifact existence;
- real restore/delete rollback plus target-drift rejection;
- real temporary MCP readback;
- configured-store readback and meaningful exact search.

## Independent review timing

An asynchronously dispatched review is not approval. Keep `implemented`, `enabled`, `verified`, and `certified` as separate states. Do not claim certification until an independent APPROVE covers the current bytes. If a late verifier returns BLOCK after enablement, retract the completion/certification claim, preserve and read back the current store, remediate every finding, re-run the adversarial matrix, and obtain a fresh verdict.

## Authority boundary

Use a receipt marker equivalent to:

```text
local_mcp_store_write_only_no_task_authority
```

A successful projection or search result must never alter routing, `may_execute`, learning/writeback permission, lifecycle eligibility, completion certification, or external side-effect authority.
