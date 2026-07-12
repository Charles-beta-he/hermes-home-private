# Global certification closure under authority and evidence boundaries

## Applicability

Use for Agent OS/control-plane requests such as “loop until everything is globally certified” where the live status aggregates inventory, procedure E2E, operational health, and an independent certification receipt.

Anti-conditions:
- Do not use this to redefine required procedures as optional merely to turn status green.
- Do not treat a local rehearsal, static selfcheck, model consensus, or a broad “continue everything” instruction as external E2E authority.
- Do not bulk reset/stash/commit unrelated worktree changes to clear an operational finding.

## Closure model

Treat global certification as a conjunction of independently evidenced axes:

1. **Inventory** — every enabled system is mapped or explicitly exempted and each required attestation is fresh.
2. **Procedure E2E** — every required procedure has a fresh receipt satisfying its evidence kinds, acceptance atoms, negative assertions, cleanup readback, and success-count threshold.
3. **Operational health** — active runtime findings are zero; a procedure PASS does not erase dirty-worktree, provider-runtime, auth, delivery, or dependency findings.
4. **Independent certification** — the verifier receipt binds the exact final projection/hash after the previous three axes pass.

Report axis states separately. A scoped Local Brain/taskpool PASS must not be projected into whole-Agent-OS certification.

## Ordered drain loop

1. Run the authoritative status and route preflight; persist the initial JSON.
2. Enumerate every `not_certified` reason by axis and classify it:
   - `safe-local-read`
   - `safe-local-reversible-write`
   - `needs-exact-target-payload`
   - `needs-human-secret-or-browser-auth`
   - `needs-external-readback`
   - `needs-scope-ownership` (for unrelated worktree state)
   - `missing-source-evidence`
3. Drain all safe local classes first, refreshing the authoritative projection after each batch.
4. For a stale inventory attestation, rerun the exact static discovery commands, update only the attestation basis/time, and verify `unattested_system_ids=[]`. This closes inventory only; it does not prove provider runtime or quorum.
5. For proof-hash debt, classify namespaces before migration. A strict autorun event proof (`proof:sha256:<64hex>`) is not interchangeable with artifact hashes. Reclassify only after byte-level SHA-256 and task-binding verification; unresolved source hashes remain visible warnings.
6. For continuation/archive debt, archive only explicitly disposable or audit-confirmed candidates. Verify `delete_performed=false` when preservation is required and byte-read back all human-review packets.
7. For external procedures, produce an exact AuthorityRequest containing procedure, platform/account, target/thread, exact payload or read scope, success count, receipt/readback requirements, rollback/escape hatch, and negative assertions. Do not turn this request into a grant yourself.
8. If the active interface has no externally readable origin (for example, a local CLI), `delivery.origin.send` cannot be certified from that context. Move to a gateway-origin conversation or obtain an exact platform/chat/thread; do not substitute another delivery procedure.
9. For OAuth, stop at the browser/human credential gate. The agent may verify status, lock/listener cleanup, and redacted token validity after the human completes authorization, but must not type credentials.
10. For dirty worktrees, inventory exact repos/counts/path classes. Preserve unrelated changes. Clean status requires an ownership decision or a policy-supported scoped exclusion—not an inferred bulk commit/reset.
11. Re-run all projections only after gated E2E effects have real receipts. Then obtain an independent verifier PASS bound to the latest bytes/projection.

## Authority precision checklist

A general objective such as “continue until globally certified” authorizes continued local safe work, but does not by itself name:

- an external platform/chat/thread;
- message payload(s) and acceptable irreversibility;
- tenant/account/task read scope;
- real model-call tier, prompt, and cost boundary;
- credential/OAuth completion;
- ownership of hundreds of unrelated Git changes.

Ask for the smallest exact bundle. If no response arrives, fail closed and preserve the prepared request packet.

## Evidence accounting pitfalls

- Keep reference count, unique hash count, task count, file count, and manifest record count separate.
- A full filesystem scan with zero matches strengthens the source-loss boundary; it does not license a replacement hash.
- A static model-router selfcheck can refresh inventory but runtime remains `not_verified` until actual calls and evidence refs exist.
- `e2e_passed` procedures can coexist with degraded operational health.
- A verifier PASS must state its scope. “PASS (debt-drain scope)” is not global certification.
- An asynchronous verifier dispatched before later edits is stale; re-dispatch or bind the vote to the final projection/hash.

## Verification checklist

- [ ] Initial and final authoritative status artifacts exist.
- [ ] Every certification axis has explicit fresh evidence.
- [ ] No validator/required-procedure weakening was used to manufacture green status.
- [ ] External receipts bind exact target and payload/read scope.
- [ ] OAuth/credentials were completed by a human.
- [ ] Dirty-worktree handling preserves unrelated work and has ownership evidence.
- [ ] Historical/source-missing debt remains visible.
- [ ] Independent verifier binds the exact final bytes/projection.
- [ ] Final claim says `global certified` only when the authoritative status itself reports eligible/certified healthy.
