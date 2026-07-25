# Exact-allowlist disk reclamation and receipt certification

## Scope

Use this procedure for destructive removal of explicitly selected build, test, cache, staging, or historical run artifacts when disk pressure blocks a verified workflow.

Applicability:

- the human is choosing among concrete deletion options;
- every target can be named and identity-checked before deletion;
- the operation is limited to artifact reclamation rather than live database maintenance.

Anti-conditions:

- do not use this as authority for SQLite `DELETE`, FTS rebuild, `VACUUM`, WAL checkpoint, scheduler/Cron activation, credential changes, or broad TTL cleanup;
- do not translate a parent directory, glob, category label, or old summary into an allowlist;
- do not treat model consensus or an old receipt as current deletion authority;
- do not claim current free space from a historical receipt—run a fresh filesystem readback.

## Authority resolution

1. Present a current DecisionPacket containing exact paths, total allocated bytes, expected consequence, irreversibility/rollback, and preserve set.
2. Bind symbolic replies such as `A`, `B`, or `option 1` to that exact packet. If compaction or delivery loss removed the mapping, authorization is unresolved.
3. Hash the final allowlist and record the human authority statement. Authorization applies only to those entries and does not expand to adjacent cleanup classes.
4. Immediately before mutation, re-read the allowlist and fail closed on count, path, type, identity, size, root, or preserve-set drift.

## Pre-delete identity contract

For each target record, where available:

```yaml
path:
dev:
ino:
mode:
mtime_ns:
logical_size:
allocated_bytes:
is_symlink:
```

Rules:

- reject symlink targets unless the exact symlink object—not its referent—was explicitly authorized;
- reject missing, replaced, or type-changed entries rather than silently shrinking or expanding the operation;
- use allocated bytes for disk-impact estimates and logical bytes for artifact identity/reporting;
- record protected/preserved artifact identities and hashes before deletion.

## Execution chain

1. Recompute fresh free space and sequential peak requirement.
2. Validate exact allowlist hash and every target identity.
3. Delete only the listed objects; never substitute a parent-directory delete or broad glob.
4. `fsync` every affected parent directory after directory-entry mutation.
5. Scan every allowlisted path with a non-following existence check and record residuals.
6. Re-read the preserve set and require identity/hash parity.
7. Re-run filesystem capacity readback and any component-level disk model needed by the blocked workflow.
8. Publish the receipt only after all claimed readbacks complete.

## Receipt contract

A machine-readable receipt should include at least:

```yaml
schema:
status: completed_verified | failed | partial
executed_at:
authority:
allowlist_path:
allowlist_sha256:
declared_root:
deleted_count:
deleted:
  - pre_delete_identity
estimated_allocated_bytes:
free_bytes_before:
free_bytes_after:
free_bytes_delta:
parent_directories_fsynced:
preserve_before:
preserve_after:
residual_targets:
```

`completed_verified` requires all of the following:

- deleted count equals the authorized allowlist count;
- residual target count is zero;
- preserve identities/hashes match before and after;
- affected parent directories were fsynced;
- receipt was written and read back;
- receipt digest was recomputed from installed bytes.

A positive free-space delta is useful evidence but is not the sole success predicate: APFS, sparse files, concurrent writes, snapshots, and delayed reclamation may cause estimated allocated bytes and observed free-space delta to differ.

## Independent certification

The verifier must independently:

1. read the receipt from its durable path and recompute its digest;
2. parse and check all success predicates;
3. re-scan every target for fresh absence;
4. re-read the preserve set;
5. run a fresh filesystem-capacity check, reported separately from historical receipt values;
6. link each material claim to concrete evidence IDs or artifact paths.

A reviewer line such as `APPROVE`, `32/32_PASS`, or `HASH_MATCH=YES` is advisory until the underlying review artifact is durably readable and claim-linked. If evidence coverage is zero or high-severity claims remain `needs_link_review`, completion certification must fail closed even when model votes agree.

## Absorption and durability check

When converting a successful cleanup into reusable Hermes experience, distinguish four layers:

1. **Event evidence:** allowlist, receipt, hashes, and fresh target readback.
2. **Class-level rule:** entity-stripped authority, identity, deletion, fsync, residual, preserve, and receipt procedure in this reference.
3. **Durable publication:** the reference and root pointer are committed or otherwise published in the canonical skill library; an uncommitted working-tree edit is only a draft.
4. **Runtime enforcement:** `scripts/validate-disk-reclamation-receipt.py` checks the immutable receipt/allowlist contract and can optionally perform fresh target, preserve-set, and filesystem-capacity readback. It is strictly read-only and fail-closed.

Run it with an independently known receipt digest:

```bash
python3 scripts/validate-disk-reclamation-receipt.py \
  /absolute/path/to/receipt.json \
  --expected-sha256 <known-receipt-sha256> \
  --fresh
```

A `pass` validates the historical receipt predicates plus the requested fresh readbacks. It does not grant authority for another deletion, SQLite maintenance, scheduler activation, or any other side effect.

Do not save one-off target counts, released GiB values, local paths, commit IDs, or current capacity as global memory. Keep those in event evidence; keep the transferable procedure here.

## Verification checklist

- [ ] Latest DecisionPacket resolves symbolic authority to exact paths and bytes.
- [ ] Allowlist digest and pre-delete identities match immediately before mutation.
- [ ] No authority expansion to database, scheduler, credential, or adjacent cleanup classes.
- [ ] Only exact targets were removed.
- [ ] Parent directories were fsynced.
- [ ] Fresh residual count is zero.
- [ ] Preserve identity/hash parity holds.
- [ ] Receipt predicates and digest are independently read back.
- [ ] Current capacity is reported from a fresh readback, not the receipt.
- [ ] Verifier claims are linked to durable evidence.
- [ ] Skill/reference publication state is distinguished from a working-tree draft.
