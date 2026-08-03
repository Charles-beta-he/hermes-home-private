# Loop A V2 protected-runtime protocol appendix — revision 7

Status: detailed specification candidate; no implementation or system mutation authority. Revision 7 incorporates the revision-6 exact-digest review (`2a40c57b...7dcd4`, P0=0/P1=3/P2=0) in addition to earlier reviews.
Parent architecture: `/tmp/loop_a_v2_hostile_uid_isolation_redesign_v3.md`, SHA-256 `7d3432f949137c5d721f0cebe557573981eb49dcf078646eadb03f3d5cb82863`.

## 1. Scope and invariants

This appendix freezes the protocol primitives required before offline implementation may begin. UID 501 is hostile. Root, launchd, local APFS, and `_hermesloopa` service code are trusted. Availability may fail closed.

Invariants:

- Canonical authority exists only below `/var/db/hermes-loop-a`.
- Runtime and active-skill version trees are immutable `root:wheel` fresh inodes.
- Service state/evidence trees are private to `_hermesloopa`.
- No inode formerly writable or reachable for mutation by UID 501 is adopted.
- User-home artifacts are untrusted projections.
- One service lease and epoch admit one nightly writer.
- One root installer lock admits one installer/recovery writer.
- One authorization ID is durably consumed at most once.
- A consumer opens one canonical protected version through directory FDs and consumes every protected-tree object from held FDs only; its only external code dependencies are from the boot-pinned immutable macOS system generation defined in section 7.
- Any identity, durability, schema, epoch, authorization, or recovery ambiguity fences execution.

## 2. Canonical layout

All paths are on the same local APFS volume.

```text
/var/db/hermes-loop-a/                         root:wheel 0755
  FENCED                                       root:wheel 0444 (present means no service mutation/execution)
  locks/                                       root:wheel 0755
    installer.lock                             root:_hermesloopa 0640
  control/                                     root:_hermesloopa 0750
    epoch.json                                 root:_hermesloopa 0440
    smoke-pending.json                         root:_hermesloopa 0440 (present only during cutover smoke)
  runtime/                                     root:wheel 0755
    versions/                                  root:wheel 0755
      <runtime-manifest-sha256>/               root:wheel 0555
        ... exact immutable closure ...        root:wheel 0444/0555
    manifests/                                 root:wheel 0755
      <runtime-manifest-sha256>.json           root:wheel 0444
    current                                    root:wheel symlink to one versions/<digest>
  active-skills/                               root:wheel 0755
    versions/                                  root:wheel 0755
      <skill-manifest-sha256>/                 root:wheel 0555
        ... exact immutable closure ...        root:wheel 0444/0555
    manifests/                                 root:wheel 0755
      <skill-manifest-sha256>.json             root:wheel 0444
    current                                    root:wheel symlink to one versions/<digest>
  authorizations/                              root:wheel 0700
    pending/                                   root:wheel 0700
      <authorization-id>.json                  root:wheel 0400
    consumed/                                  root:wheel 0700
      <authorization-id>.json                  root:wheel 0400
    records/                                   root:wheel 0700
  policy/                                      root:wheel 0700
    rollback-floor.json                        root:wheel 0400
  installer-transactions/                      root:wheel 0700
    <transaction-uuid>/                        root:wheel 0700
      records/                                 root:wheel 0700
        <sequence>-<state>.json                root:wheel 0400
      snapshots/                               root:wheel 0700
        <role>-<digest>.json                   root:wheel 0400
      evidence/                                root:wheel 0700
        <role>-<digest>.json                   root:wheel 0400
  service/                                     _hermesloopa:_hermesloopa 0700
    lease.lock                                 _hermesloopa:_hermesloopa 0600
    windows/                                   _hermesloopa:_hermesloopa 0700
    transactions/<transaction-uuid>/           _hermesloopa:_hermesloopa 0700
      records/                                 _hermesloopa:_hermesloopa 0700
        <sequence>-<state>.json                _hermesloopa:_hermesloopa 0400
      sources/                                 _hermesloopa:_hermesloopa 0700
        source-<digest>.bin                    _hermesloopa:_hermesloopa 0400
      candidates/                              _hermesloopa:_hermesloopa 0700
        candidate-<digest>.json                _hermesloopa:_hermesloopa 0400
      receipts/                                _hermesloopa:_hermesloopa 0700
        receipt-<digest>.json                  _hermesloopa:_hermesloopa 0400
```

Every staged file is created in the same parent directory as its final name, using a transaction-bound hidden basename. No cross-parent publication is allowed.

## 3. Canonical JSON, schema, and digest rules

- JSON value serialization is RFC 8785 JCS, encoded UTF-8 with no BOM, followed by one LF; SHA-256 covers JCS bytes plus LF.
- All schemas additionally reject floats, negative integers, integers above `2^53-1`, unpaired Unicode surrogates, duplicate keys, non-NFC strings, unknown fields, and optional-field omission. Optional values are explicit null.
- Timestamps are UTC strings exactly `YYYY-MM-DDTHH:MM:SSZ`, with real calendar validation and no fractional seconds. Paths and identifiers are nonempty NFC strings with schema-specific ASCII restrictions; path fields are relative, contain no NUL, `.`/`..`, empty component, backslash, or leading slash.
- Arrays are schema-ordered. Inventory arrays are sorted by UTF-8 bytes of `relative_path`; digest-component arrays are sorted by ASCII `role`; no duplicate sort key is allowed.
- All digests are lowercase 64-character ASCII hex.
- UUIDs are lowercase canonical RFC 4122 text.
- Unknown schema versions, fields, enum values, duplicate IDs, type mismatches, range failures, or noncanonical bytes fail closed. Each hashed object validates against the exact JSON Schema digest named by the authority packet before digest comparison.

Every self-digested object has two separately validated schemas. Its digest-preimage schema requires the object's own digest field to be explicit null; its finalized schema requires a lowercase digest. The preimage is canonicalized and hashed, that digest replaces null, and the finalized object is revalidated and canonicalized. No digest field is omitted. `record_digest`, `version_digest`, `inventory_digest`, `payload_digest`, `authorization_digest`, and every other self-digest use this rule. Digests never directly or indirectly include an object that includes the original digest unless an explicit acyclic stage is defined.

## 4. Root fence and locks

### 4.1 Global root fence

`FENCED` is root-owned. The system is fenced when it exists or when its absence cannot be verified through the pre-opened canonical-root FD. Root creates it as a fresh same-parent staged file, durably publishes it, and syncs the root directory before installer/cutover work. Root removes it only after all verification, then syncs the root directory.

A service process acquires the exclusively locked service lease, then checks the fence through its canonical-root FD and immediately before every source capture, publication, journal publication, receipt, and commit. The service never acquires `installer.lock`.

`control/smoke-pending.json` is a second durable admission gate, not an authority grant. Its exact schema is: schema 1, authorization ID, installer transaction UUID, smoke transaction UUID, service epoch/instance, runtime and skill manifest/inventory digests, purpose exactly `initial-cutover-smoke`, on-demand plist digest, issued/expiry timestamps, and record digest. When present, every service invocation except the exact matching smoke exits before source capture or publication; a matching invocation must use its bound transaction UUID and closure and may create at most that one transaction. Missing, malformed, expired, mismatched, failed, already-terminal, or duplicate gate/transaction evidence blocks all service mutation. Cold boot never treats gate presence as normal admission.

Root/service handoff has one lock order: first root inhibits both schedulers, then root acquires `installer.lock`, then root acquires and retains `service/lease.lock`, waiting for or terminating any existing trusted service holder. Only while holding both locks and after proving no service process may root create/change/remove the fence or smoke gate, rotate epoch, install, recover, or roll back. Root normally retains both locks until the fence and final scheduler state are durable. The sole exception is section-12 initial smoke handoff: root retains installer lock, durably publishes the exact smoke gate while holding both locks, removes/syncs the fence, then releases only the service lease so the bound smoke can acquire it. Launchd is disabled before every root wait for the service lease. An uncertain lock, scheduler, process, fence, or gate state yields outage, never mutation.

### 4.2 Installer lock

Root opens `locks/installer.lock` with `O_NOFOLLOW`, validates root owner, group `_hermesloopa`, mode `0640`, regular type, link count one, and canonical ancestor identity, then holds `flock(LOCK_EX)` for the entire installer/recovery operation. Root next opens and exclusively locks the validated service lease. Failure at either lock blocks mutation.

### 4.3 Service lease and epoch

The trusted service opens `service/lease.lock`, validates identity/owner/mode/link count, and holds `flock(LOCK_EX|LOCK_NB)` for the full run. It then opens `control/epoch.json` through held root and control directory FDs; `control/` is root-owned and not writable by the service. Epoch schema:

```json
{"epoch":1,"schema":1,"service_instance":"UUID","updated_at":"RFC3339Z"}
```

The root installer creates a fresh random `service_instance` UUID at rotation; the service adopts it from the durable epoch file and may not choose another. Rotation stages a root:_hermesloopa 0440 fresh epoch inode in root-owned `control/`, fully syncs it, then—while both root locks, durable fence, and scheduler inhibition are held—uses root-only `RENAME_SWAP` with existing `epoch.json` (or `RENAME_EXCL` for initial creation), syncs `control/`, validates both inodes/bytes, and retains the old epoch at the transaction-qualified staging name until installer terminal state. The service has read/traverse only and cannot rename, remove, or replay epoch names. Epoch increments exactly by one and becomes durable before installer commit and before the LaunchDaemon schedule is enabled. Every state-mutating service operation reopens epoch through the held control directory FD, validates canonical bytes, and requires equality to its startup epoch and instance. Stale or malformed state fails closed. FD retention does not bypass this check.

### 4.4 Initial bootstrap exclusion

Initial installation additionally locks root-owned `/var/run/hermes-loop-a.bootstrap.lock` before the canonical root exists and retains it through installer terminal state. Root first validates the fresh payload/grant from held FDs, inhibits and reads back both schedulers, and verifies the LaunchDaemon absent. It then creates `/var/db/hermes-loop-a` as root:wheel 0700 with a durable `FENCED`, root-only authorization/installer-journal skeleton, and PREPARED installer record. The authorization is durably consumed before service-account creation. Only then may root create the exact authorized account/group, create the remaining protected tree and service lease, acquire installer then service locks, and continue the same transaction. Crash recovery uses the bootstrap lock plus root-only consumed record/journal; it may complete that transaction or remain fenced, never replay the grant. Once installation commits, root finalizes canonical root metadata and the normal two-lock protocol supersedes bootstrap. Bootstrap artifacts are retained unless separately authorized for destructive removal.

## 5. Durable same-parent publication primitive

For any canonical regular file:

1. Pre-open and validate all ancestor directory FDs; never re-resolve from `/` during the transaction.
2. Create `.<final>.txn-<uuid>.tmp` in the final parent with `openat(O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW, 0600)` and process umask `077`.
3. While still holding the creation FD, root uses `fchown` when target ownership differs and every writer uses `fchmod` to the exact final mode. Validate regular type, expected owner/group/mode, no ACL, no xattr, no BSD immutable/append flag yet, link count one, and parent device.
4. Write all bytes with a complete-write loop; short/zero writes fail.
5. After byte and metadata writes, call `fsync(fd)`, then Darwin `fcntl(fd, F_FULLFSYNC=51)`; both must succeed. Re-read metadata through the same FD.
6. Rewind/read through that same read-write FD; byte-compare and recompute digest.
7. Publish with `renameatx_np(parent_fd, tmp, parent_fd, final, RENAME_EXCL)`. Pre-existing final name fails without moving either inode.
8. `fstat(fd)` and `fstatat(parent_fd, final, AT_SYMLINK_NOFOLLOW)` must match device/inode and expected metadata.
9. Call `fsync(parent_fd)`; failure blocks the next state.
10. The journal record describing publication is written only after step 9.

No cross-directory rename, fallback overwrite, unlink-before-rename, clone, hard link, or pathname quarantine exists in the regular-file publication protocol. `RENAME_SWAP` is reserved solely for root-only epoch, rollback-floor, version-pointer, and disabled/booted-out LaunchDaemon-plist primitives. Recovery deletes a temporary file only when its exact transaction inventory proves it was created by that transaction and it still matches the recorded inode/digest.

### 5.1 Transaction namespace publication

For either journal, the writer creates a same-parent `.<transaction-uuid>.tmp` directory with `mkdirat(...,0700)`, validates fresh inode/owner/mode/device, creates and syncs the complete type-specific fixed child set, publishes canonical sequence-1 `PREPARED` inside `records/`, syncs `records/` then the temp root, and finally renames the complete temp root with `RENAME_EXCL` to `<transaction-uuid>` and syncs the transactions parent. A service transaction root and each of `records`, `sources`, `candidates`, and `receipts` are `_hermesloopa:_hermesloopa 0700`; no other direct child is allowed. An installer transaction root and each of `records`, `snapshots`, and `evidence` are `root:wheel 0700`; no other direct child is allowed. Every child is a newly created directory on the parent device with a unique APFS file ID, expected owner/mode, no alias in the complete namespace inventory, and no ACL/xattr/nonzero BSD flags. The held root FD must match the final path inode. Thus no visible canonical transaction lacks its first record. A crash before final rename leaves only a transaction-qualified temp; recovery never treats it as canonical and may remove it only after validating its UUID, exact child name set, PREPARED digest/inventory, owner/mode, and every inode through held FDs. Any mismatch is retained and fences recovery.

## 6. Source capture

The UID-501 source is untrusted input. The service opens the approved pathname under validated directory FDs with `O_RDONLY|O_NOFOLLOW`, requires regular type, link count exactly one, size from 1 through 8,388,608 bytes, and records pre-read `fstat`. It streams until EOF exactly once into a same-parent protected source temp while computing bytes and digest. Every read error fails; an early EOF is accepted only as the exact captured stream and is recorded. A post-read `fstat` is recorded; metadata change marks the source `concurrently_changed=true` but cannot alter protected bytes. It applies the publication primitive to `sources/source-<digest>.bin`.

Only the protected readback bytes are parsed and supplied to generation. Candidate metadata names both source digest and source byte count. Concurrent in-place source writes may alter captured content, but candidate processing and digest always use the exact protected bytes. No candidate grants promotion authority.

## 7. Immutable version manifest and consumption

A version directory contains directories and regular files only; symlinks, sockets, devices, FIFOs, hard links, ACLs, xattrs, and nonzero BSD flags are forbidden. Every directory is a fresh inode finalized `root:wheel 0555`. Every regular file is a fresh inode finalized `root:wheel 0444` or `0555`, link count one. `current` is the only allowed symlink and exists outside version directories.

The canonical version manifest is stored outside the version tree at `<kind>/manifests/<version_digest>.json`; it is never a tree inventory entry. It has exactly: `schema` integer 1; `kind` enum `runtime|active-skills`; `version_digest` digest or null under the preimage rule; `created_at` timestamp; `policy_generation` positive integer; `release_lineage` UUID; `release_sequence` positive integer; `entries` array; `inventory_digest` digest; and `execution_closure` object or null. Each entry has exactly: `relative_path` safe path string; `type` enum `directory|file`; `mode` integer; `uid` integer; `gid` integer; `size` integer or null; `sha256` digest or null; `executable` boolean. Entries are path-sorted and include every descendant of the version root.

The separate inventory object has exactly `schema` integer 1, `kind` enum `runtime|active-skills`, `release_lineage` UUID, `release_sequence` positive integer, `entries` the byte-identical canonical entries array from its manifest, and `inventory_digest`. Its preimage schema requires `inventory_digest:null`; its finalized schema requires the lowercase SHA-256 of the JCS preimage. Kind, lineage, sequence, entries, and computed digest must exactly equal the manifest fields before either object is usable. The schema bundle names distinct `inventory-preimage-v1` and `inventory-final-v1` schemas. The finalized manifest digest names both manifest file and version directory; manifest bytes are published first, then the complete version directory, and both must agree.

For runtime, the protected version vendors the interpreter executable, complete stdlib, modules, data, and every non-Apple library; the interpreter statically links every required non-Apple native module, and protected-tree `dlopen`/pathname extension loading is forbidden. `execution_closure` names their protected inventory roles and a path-sorted `external_dependencies` array limited to the kernel-selected sealed system volume, boot cryptexes, dyld, and Apple shared-cache images. Each external entry has absolute system path/image identity, kind, mode, uid/gid, byte count/hash where independently readable, platform build, mounted root snapshot UUID/seal identity, cryptex generation, dyld shared-cache UUID, and Apple code-signing designated requirement. Active-skills uses explicit null.

The root-owned launcher opens the selected protected version, manifest, vendored interpreter, script, modules, and data through held FDs; verifies all bytes/metadata; and executes the held interpreter FD with `fexecve`, passing only inherited read-only FDs for protected inputs. Pathname execution or import of protected/non-system code is forbidden. Before execution and in a pre-mutation child handshake, launcher and child independently require the same mounted read-only sealed-system snapshot, boot/cryptex generation, OS build, SIP/seal state, dyld cache UUID, Apple signatures, and loaded-image inventory. Those generations cannot be replaced in a running boot; any mismatch, unsealed/writable system source, non-Apple external image, OS update, or inability to prove the immutable generation fails closed until a newly reviewed manifest is authorized. No external stdlib, plugin, user site, CLT file, package, or mutable data dependency is allowed.

Tree construction for one explicit kind creates `<kind>/versions/.tree-<transaction-uuid>.tmp` with `mkdirat(...,0700)` in that kind's `versions` parent. Every descendant is newly created beneath held directory FDs; regular files use the publication durability order, and each directory is synced after its complete child set. Finalization validates complete inventory, applies final file metadata, then directory metadata bottom-up, syncs every directory bottom-up, and revalidates. Before either final publication, durable installer state `RUNTIME_TREE_STAGED` or `SKILL_TREE_STAGED`, matching that kind, binds both transaction-qualified temp names, devices/inodes, target final names, manifest/inventory digests, and complete metadata. Root then publishes that kind's manifest and complete temp directory to their absent digest names using same-parent `RENAME_EXCL`, validates both through held FDs, and syncs both parents before the matching `RUNTIME_TREE_BUILT` or `SKILL_TREE_BUILT`. A crash leaving exactly one side is attributable through the matching staged record and may be completed from the exact held staged peer or rolled back after exact inode/digest recheck; an unbound or mismatched orphan fences recovery. No partially built tree has a digest name and no consumer may use either side until both agree. Initial installation performs the runtime pair and then the active-skills pair as two separately inventoried, journaled operations; no state or evidence object may combine their temporary or final inodes.

Tree verification walks from a held version-directory FD with `fstatat(..., AT_SYMLINK_NOFOLLOW)` and `openat(O_NOFOLLOW)`, compares the complete sorted name set, metadata, and same-FD bytes to the manifest, and rejects extras. UID 501 and `_hermesloopa` must fail all mutation probes.

Canonical Python execution uses only the vendored held-FD interpreter and `-I -B`; `PYTHONNOUSERSITE=1`; an empty/sanitized environment; and FD-backed protected import hooks. Shebang resolution, pathname fallback, user site-packages, UID-501 paths, plugins, hooks, shell evaluation, dynamic generated code, and model-produced executable content are forbidden. The child emits its exact protected-FD and immutable-system loaded-image inventory to the launcher before either permits mutation.

## 8. Service transaction journal

Each transaction has immutable one-record-per-file journal entries under `records/`:

`00000001-PREPARED.json`, `00000002-SOURCE_CAPTURED.json`, etc. Each is published by the same-parent primitive. Record fields:

```text
schema, transaction_uuid, sequence, purpose, schedule_digest, scheduled_occurrence,
scheduled_window_id, service_epoch, service_instance,
prior_record_digest, state, recorded_at, runtime_manifest_digest,
skill_manifest_digest, source_digest, candidate_digest, receipt_digest,
inventory[], evidence{}, record_digest
```

Inventory entries bind role, relative canonical path, device, inode, mode, uid, gid, link count, byte count, and SHA-256. Optional values are explicit nulls, never omitted.

The service-record schema types are exact: `schema` integer 1; `transaction_uuid` UUID; `sequence` positive integer; `purpose` enum `nightly|initial-cutover-smoke`; `schedule_digest` digest and `scheduled_occurrence` exact UTC minute string `YYYY-MM-DDTHH:MM:00Z` for nightly, both explicit null for initial smoke; `scheduled_window_id` digest for nightly and explicit null for initial smoke; `service_epoch` positive integer; `service_instance` UUID; `prior_record_digest` null only for sequence 1 otherwise digest; `state` one listed enum; `recorded_at` timestamp; every manifest/source/candidate/receipt digest a digest or null according to state; `inventory` a path-sorted array of exact inventory objects; `evidence` an object validated by the state-specific schema; `record_digest` digest. An inventory object has exactly `role` ASCII token, `relative_path` safe path, `device`/`inode`/`mode`/`uid`/`gid`/`link_count`/`byte_count` nonnegative integer, and `sha256` digest. Purpose, schedule digest, scheduled occurrence, window ID, and transaction UUID are present from PREPARED and immutable across the complete chain. For every nightly record, validation recomputes the window ID from schedule digest and occurrence and recomputes the UUIDv5 before accepting that record or its transaction root. The authority packet names one schema-bundle digest containing the service-record, state-evidence, candidate, receipt, manifest, inventory-preimage/final, initial-target-bundle-preimage/final, authorization payload/final, consumed-record, installer-record, rollback-floor, epoch, scheduler-snapshot, scheduler-admission-preimage/final, smoke-gate, and AuthorityGrant schemas.

Nightly admission uses the authorization-bound scheduler object stored at fixed protected runtime role `config/nightly-schedule.json`, with exact fields `{schema:1, daily_utc_hhmm, admission_seconds, schedule_digest}` and the section-3 preimage/final digest rule. `daily_utc_hhmm` is one zero-padded UTC minute and `admission_seconds` is 1..3600 without crossing the next UTC day. The service reads trusted system UTC only after the lease, chooses the greatest scheduled UTC occurrence not after now, and admits only while `occurrence <= now < occurrence + admission_seconds`. `scheduled_window_id` is SHA-256 over the exact ASCII bytes `nightly-v1\0<schedule_digest>\0<occurrence-YYYY-MM-DDTHH:MM:00Z>`. The nightly transaction UUID is UUIDv5 with protocol-fixed namespace `62cc109f-5d56-5a4d-b6e9-1357d0d25dcf` and name equal to the 64-character ASCII `scheduled_window_id`; neither epoch nor rotating `service_instance` participates in this derivation. Transaction-root RENAME_EXCL is the durable unique window claim. PREPARED and every successor record carry the exact schedule digest and occurrence. If the deterministic root already exists, every record in its complete validated chain must carry the identical scheduled-window ID, transaction UUID, purpose, schedule digest, and UTC occurrence, and the service must recompute both derived identifiers before reconciliation; collision, missing/null/inconsistent values, malformed content, or any other transaction claiming that occurrence fences without creating a second root. A duplicate, retry, epoch rotation, service-instance rotation, clock rollback, DST change, adjacent-boundary race, or cold boot can therefore only reconcile that same transaction UUID and can never create a second transaction for the occurrence. Outside the window it exits nonmutating. `service/windows/` must remain empty in revision 7 and is reserved; transaction roots are the sole claims.

Allowed transitions only:

```text
START -> PREPARED
PREPARED -> SOURCE_CAPTURED | ABORTED | RECOVERY_REQUIRED
SOURCE_CAPTURED -> SMOKE_STARTED | ABORTED | RECOVERY_REQUIRED
SMOKE_STARTED -> CANDIDATE_STAGED | ABORTED | RECOVERY_REQUIRED
CANDIDATE_STAGED -> CANDIDATE_WRITTEN | ABORTED | RECOVERY_REQUIRED
CANDIDATE_WRITTEN -> RECEIPT_WRITTEN | RECOVERY_REQUIRED
RECEIPT_WRITTEN -> VERIFIED | ABORTED | RECOVERY_REQUIRED
VERIFIED -> COMMITTED | RECOVERY_REQUIRED
RECOVERY_REQUIRED -> ROLLED_BACK
```

`COMMITTED`, `ABORTED`, and `ROLLED_BACK` are terminal. `RECOVERY_REQUIRED` blocks new service transactions until explicit recovery.

## 9. Service reconciliation table

- No record directory: no transaction; no cleanup by pathname.
- Valid `PREPARED`, no source: append `ABORTED`. If exactly one protected `source-<digest>.bin` exists, UID/mode/link-count and same-FD bytes match its basename digest, and no other mutation exists, append deterministic `SOURCE_CAPTURED`; otherwise `RECOVERY_REQUIRED`. This is the sole recovery rule for the crash gap between source publication and its journal checkpoint.
- Valid `SOURCE_CAPTURED`, exact recorded source only: retain source as evidence and append `ABORTED`, or continue to `SMOKE_STARTED` only for the same live invocation.
- Valid `SMOKE_STARTED`, exact recorded source exists and no candidate mutation: retain source as evidence; append `ABORTED`.
- Valid `CANDIDATE_STAGED`, exact temp still matches: remove only by held parent FD and exact inode recheck, sync parent, append `ABORTED`; otherwise `RECOVERY_REQUIRED`.
- Valid `CANDIDATE_WRITTEN`, exact candidate present: if no receipt exists, publish and parent-sync the one deterministic FAIL receipt bound to the candidate; then append `RECEIPT_WRITTEN` with that receipt digest and append `ABORTED`. If exactly that receipt already exists after a crash but no RECEIPT_WRITTEN record does, same-FD validate its bytes, inode, ownership, mode, link count, candidate binding, and sole cardinality, append the deterministic `RECEIPT_WRITTEN`, then append `ABORTED`. A second, non-FAIL, mismatched, malformed, or unbound receipt yields `RECOVERY_REQUIRED`; recovery never publishes another receipt when the exact one exists.
- Valid `RECEIPT_WRITTEN`, exact objects/cardinality converge: PASS appends `VERIFIED`; deterministic FAIL appends `ABORTED`; mismatch -> `RECOVERY_REQUIRED`.
- Valid `VERIFIED`, all exact objects/cardinality/runtime/source/epoch converge: append `COMMITTED`; mismatch -> `RECOVERY_REQUIRED`.
- Terminal record plus extra canonical name, missing inventory object, digest mismatch, sequence gap, duplicate sequence, chain mismatch, unknown temp, or malformed record: fail closed; do not unlink; require human recovery.

For either purpose, `COMMITTED` requires exactly the chain PREPARED → SOURCE_CAPTURED → SMOKE_STARTED → CANDIDATE_STAGED → CANDIDATE_WRITTEN → RECEIPT_WRITTEN → VERIFIED → COMMITTED and exactly one inventory-bound source, candidate, and PASS receipt. A chain containing RECOVERY_REQUIRED cannot commit. A deterministic FAIL receipt transitions from RECEIPT_WRITTEN to ABORTED and can never verify or commit. Zero/duplicate/extra objects, another chain, or another result is invalid. `nightly` requires its deterministic window ID/UUID, no smoke gate, exact normal scheduler/epoch, and no other transaction claim for that occurrence. `initial-cutover-smoke` additionally requires its UUID and closure equal the consumed installer authorization and durable smoke gate, and it must be the sole transaction while that gate exists. Purpose substitution or any extra transaction fails acceptance and leaves the gate/fence in force.

## 10. Root installer journal and rollback floor

Installer records use the immutable one-record-per-file and digest-chain rules under `installer-transactions/<uuid>/records/`. Exact fields are: schema 1, transaction UUID, positive sequence, prior digest, state, timestamp, authorization ID/payload/finalized digests, AuthorityGrant digest, policy generation/lineage/sequence, prior/proposed floor digests, expected-current/target manifest and inventory digests, initial-target-bundle digest, architecture/protocol/schema/authority-packet/installer/runtime/RED digests, scheduler-before digest/action, smoke UUID/gate/on-demand/final plist digests, kind-qualified tree inventory, kind-qualified pointer inventory, operation evidence, and record digest. Operation-inapplicable values are explicit null. A record for a kind-qualified tree or pointer state carries evidence for exactly that kind and must repeat the immutable initial-target-bundle digest when the operation is `install-initial`.

The initial-target bundle is a separately finalized self-digested object with exactly `schema` integer 1, `runtime`, `active_skills`, and `bundle_digest`. Each of `runtime` and `active_skills` is an exact tuple with fields `kind`, `release_lineage`, `release_sequence`, `manifest_digest`, and `inventory_digest`; `kind` is respectively `runtime` and `active-skills`, both lineages equal the authorization lineage, and each tuple exactly matches its finalized manifest and inventory. Its preimage requires `bundle_digest:null`; its final schema requires the computed digest. No third tuple, omission, reorder, or duplicate kind is admitted. For initial installation the bundle and bundle digest are non-null and the single-target fields are null; for every other operation the bundle fields are null. The initial proposed floor must contain both and only these two forward tuples before any smoke admission.

Allowed installer transitions:

```text
START -> PREPARED
PREPARED -> AUTH_CONSUMED | ABORTED
AUTH_CONSUMED -> RUNTIME_TREE_STAGED | SKILL_TREE_STAGED | RUNTIME_POINTER_STAGED | SKILL_POINTER_STAGED | FLOOR_STAGED | RECOVERY_REQUIRED
RUNTIME_TREE_STAGED -> RUNTIME_TREE_BUILT | RECOVERY_REQUIRED
RUNTIME_TREE_BUILT -> SKILL_TREE_STAGED | RUNTIME_POINTER_STAGED | RECOVERY_REQUIRED
SKILL_TREE_STAGED -> SKILL_TREE_BUILT | RECOVERY_REQUIRED
SKILL_TREE_BUILT -> RUNTIME_POINTER_STAGED | SKILL_POINTER_STAGED | RECOVERY_REQUIRED
RUNTIME_POINTER_STAGED -> RUNTIME_POINTER_SWITCHED | RECOVERY_REQUIRED
RUNTIME_POINTER_SWITCHED -> SKILL_POINTER_STAGED | VERIFIED | RECOVERY_REQUIRED
SKILL_POINTER_STAGED -> SKILL_POINTER_SWITCHED | RECOVERY_REQUIRED
SKILL_POINTER_SWITCHED -> FLOOR_STAGED | VERIFIED | RECOVERY_REQUIRED
FLOOR_STAGED -> FLOOR_SWITCHED | RECOVERY_REQUIRED
FLOOR_SWITCHED -> SMOKE_GATE_PUBLISHED | VERIFIED | RECOVERY_REQUIRED
SMOKE_GATE_PUBLISHED -> SMOKE_ACCEPTED | RECOVERY_REQUIRED
SMOKE_ACCEPTED -> VERIFIED | RECOVERY_REQUIRED
VERIFIED -> COMMITTED | RECOVERY_REQUIRED
RECOVERY_REQUIRED -> ROLLED_BACK
```

`COMMITTED`, `ABORTED`, and `ROLLED_BACK` are terminal. Operation paths are exact: `install-initial` takes RUNTIME_TREE_STAGED → RUNTIME_TREE_BUILT → SKILL_TREE_STAGED → SKILL_TREE_BUILT → RUNTIME_POINTER_STAGED → RUNTIME_POINTER_SWITCHED → SKILL_POINTER_STAGED → SKILL_POINTER_SWITCHED → FLOOR_STAGED → FLOOR_SWITCHED → SMOKE_GATE_PUBLISHED → SMOKE_ACCEPTED → VERIFIED → COMMITTED. `promote-runtime` takes the runtime tree/pointer path then direct VERIFIED; `promote-skill` takes the skill tree/pointer path then direct VERIFIED. `rollback-protected` takes only the runtime or skill pointer path selected by its destination and then direct VERIFIED; `update-floor` starts at FLOOR_STAGED and then direct VERIFIED. Branches listed in the graph but inconsistent with the immutable operation/destination are invalid. Every unlisted edge is invalid. No chain containing `RECOVERY_REQUIRED` may reach VERIFIED or COMMITTED; its only terminal transition is exact protected `ROLLED_BACK`. Authorization consumption is a durable filesystem effect completed before `AUTH_CONSUMED`; a crash between effect and record is reconciled from the exact consumed record, which names the installer transaction UUID and authorization digest. Before consumption, abort is allowed. After consumption, only same-transaction completion, exact protected rollback, or fenced `RECOVERY_REQUIRED` is allowed.

Reconciliation validates the entire root-owned transaction directory, authorization ledger, both complete initial version trees when applicable, pointer names/targets, scheduler snapshot, fence, smoke gate, epoch, plists, and policy floor. Unknown files, mixed target inventory, missing digest-chain records, pointer ambiguity, consumed-record mismatch, or target below floor yields fenced human recovery without unlink. A kind-qualified `*_POINTER_STAGED` removes only that exact transaction-qualified staged pointer after inode/target recheck. A kind-qualified `*_POINTER_SWITCHED` either verifies the exact target and continues along the operation's exact path or swaps back to the exact recorded prior protected pointer while both locks and fence remain held; any mismatch remains fenced. For initial installation, recovery treats the two trees and two pointers as four ordered, separately bound effects: it may complete forward in the specified runtime-tree, skill-tree, runtime-pointer, skill-pointer order, or reverse only exact published effects in reverse order after inode/digest recheck. It may never accept a mixed two-kind terminal closure, publish the floor, or admit smoke while either tuple/tree/pointer is absent, stale, extra, or unswitched. Every one-present/one-absent and one-switched/one-unswitched combination remains fenced until exact completion or rollback is durably journaled. `SMOKE_GATE_PUBLISHED` permits only the section-12 gated smoke handoff; recovery disables/boots out its on-demand plist before reacquiring the service lease and fencing. A valid exact committed smoke advances to SMOKE_ACCEPTED; absent, failed, duplicate, wrong-purpose, or mismatched evidence remains gated/fenced RECOVERY_REQUIRED. `SMOKE_ACCEPTED` may install the final plist and clear the gate only while fenced with both locks.

`policy/rollback-floor.json` has exactly: schema 1; positive `policy_generation`; immutable `release_lineage` UUID; nonnegative `minimum_release_sequence`; canonically sorted `permitted_versions` entries; `updated_at`; `prior_floor_digest`; `authorization_id`; and `record_digest`. Each permitted entry has exactly kind `runtime|active-skills`, positive release sequence, manifest digest, inventory digest, and disposition `forward|rollback`. Entries are ordered by the complete tuple `(kind ASCII bytes ascending, release_sequence numeric ascending, manifest_digest ASCII bytes ascending, inventory_digest ASCII bytes ascending, disposition ASCII bytes ascending)`; exact duplicate tuples and duplicate `(kind, release_sequence)` keys are rejected. Initial installation sets generation 1, one lineage, minimum sequence 1, and the exact initial manifests. Updates require exact-current CAS, a consumed root authorization, generation increment by one, the same lineage, and a minimum sequence greater than or equal to the prior minimum; no existing sequence may be rebound to another digest. A target or rollback is allowed only when its manifest's lineage matches, its release sequence is at least the minimum, and the exact kind/sequence/manifest/inventory tuple occurs in `permitted_versions`. Digest comparison is used only inside this canonical tuple order and equality/CAS; digest magnitude never expresses release precedence. Floor loss, corruption, lineage divergence, sequence rebinding, noncanonical order, duplicate key/tuple, or absent tuple fences execution.

Floor publication is a root-only journaled primitive reserved alongside epoch/pointer/plist swaps. Before mutation, `FLOOR_STAGED` binds the complete proposed floor bytes/digest, transaction-qualified same-parent staged name/device/inode, prior floor bytes/digest/device/inode or explicit absent, policy-directory device/inode, and expected CAS. Initial installation has one literal order: create, fully sync, and revalidate the staged floor inode; append and parent-sync `FLOOR_STAGED`; publish to absent `rollback-floor.json` with `RENAME_EXCL`; sync `policy/`; validate the final held FD, name, inode, and bytes; then append `FLOOR_SWITCHED`. The final floor name may not be created before the durable matching `FLOOR_STAGED` record. `update-floor` likewise fully syncs the staged inode and durably appends `FLOOR_STAGED` before using RENAME_SWAP with the staged file, syncing `policy/`, validating both resulting names/inodes/bytes, retaining the prior floor at the transaction-qualified name, and then appending `FLOOR_SWITCHED`. It rotates/verifies epoch before VERIFIED/COMMITTED; prior-floor retirement is only after terminal state and exact recheck. Recovery deterministically completes or reverses only the bound create/swap under both locks/fence; a final floor without an earlier matching durable `FLOOR_STAGED`, or any unknown/mismatched state, remains fenced and is never adopted or unlinked automatically. Initial smoke admission is impossible until the initial floor is final, parent-synced, held-FD verified, and journaled FLOOR_SWITCHED.

## 11. Exact authorization envelope

Authorization construction is acyclic and has three stages.

1. `authorization_payload` contains exactly:

```text
schema, authorization_id, operation, approval_identity, issued_at, expires_at,
nonce, transaction_uuid, smoke_transaction_uuid, service_epoch,
policy_generation, release_lineage, release_sequence, exact_destination,
prior_floor_digest, proposed_floor, proposed_floor_digest,
expected_current_manifest_digest, expected_current_inventory_digest,
protected_source_digest, candidate_digest, target_manifest_digest,
target_inventory_digest, initial_target_bundle, initial_target_bundle_digest,
architecture_digest, protocol_appendix_digest,
authority_packet_digest, schema_bundle_digest, installer_manifest_digest,
runtime_manifest_digest, red_evidence_digest, scheduler_before_digest,
scheduler_action, payload_digest
```

`payload_digest` is computed by the section-3 preimage/final rule and the payload contains neither grant nor finalized-authorization digest. Field types follow section 3: schema is integer 1; IDs, nonce, and transactions are ASCII token or UUID per schema; operation is `install-initial|promote-runtime|promote-skill|rollback-protected|update-floor`; `exact_destination` is exactly one of `protected-bundle|runtime|active-skills|rollback-floor`, never a free path; lineage is UUID; policy generation and epoch are positive. `release_sequence` is positive for single-kind promote/rollback and explicit null for install-initial/update-floor because the initial bundle carries two independently bound positive sequences. Operation/destination pairs are exact: install-initial→protected-bundle, promote-runtime→runtime, promote-skill→active-skills, rollback-protected→runtime or active-skills, update-floor→rollback-floor. `smoke_transaction_uuid` is non-null only for install-initial. Source/candidate are non-null only for promote operations and explicit null for install-initial, rollback-protected, and update-floor. For `install-initial`, the complete finalized initial-target bundle and its digest are non-null, expected-current and single target manifest/inventory fields are explicit null, and both canonical current names must be proven absent. For promote/rollback, destination selects exactly one kind, expected-current fields encode that kind's CAS, the single target manifest/inventory fields are non-null, and initial-target-bundle fields are null. For update-floor, expected-current and both target forms are null. Prior floor is null only when no floor exists. For `install-initial|update-floor`, `proposed_floor` is the complete finalized section-10 object and `proposed_floor_digest` is its computed digest; for every other operation both are explicit null. During initial installation, both floor tuples must equal the initial-target bundle exactly. Thus the grant binds prior-floor CAS, proposed minimum sequence, and the complete permitted tuple set. `scheduler_action` has exactly `{old_job_id, expected_enabled, target_enabled, launchd_label, launchd_target_state, on_demand_plist_digest, final_plist_digest}` with operation-specific explicit nulls.

2. A fresh direct user AuthorityGrant delivered through the current authenticated Hermes origin session grants that exact `payload_digest`, never a future finalized authorization digest. The authenticated wire form is exactly one LF-terminated ASCII line with single spaces and this fixed key order: `HERMES-AUTH-V1 authorization_id=<token> payload_sha256=<64hex> operation=<enum> destination=<enum> issued_at=<timestamp> expires_at=<timestamp> nonce=<token>\n`. Values use the same restricted schema lexemes and cannot contain whitespace or `=`. Any prefix/suffix, CR, extra/missing/reordered key, alternate encoding, or noncanonical value is rejected.

The parsed AuthorityGrant JSON preimage has exactly `schema:1`, `authorization_id`, `payload_sha256`, `operation`, `destination`, `issued_at`, `expires_at`, `nonce`, `wire_sha256`, and `authority_grant_digest:null`; `wire_sha256` hashes the exact wire bytes. Its digest is computed by section 3, inserted, and finalized. Mapping is literal: wire `HERMES-AUTH-V1` fixes JSON schema 1; each of the seven `key=value` lexemes becomes the same-named JSON string; grant `authorization_id`, `operation`, `issued_at`, `expires_at`, and `nonce` equal the same payload fields; grant `payload_sha256` equals `authorization_payload.payload_digest`; grant `destination` equals `authorization_payload.exact_destination`. No coercion or renamed intermediate field exists. The finalized JSON bytes—not the wire text—are nested in finalized authorization. The trusted root operator supplies the exact wire bytes directly; no local transcript, database, or file may create or widen a grant.

3. The finalized authorization contains exactly `schema`, the complete finalized `authorization_payload`, `payload_digest`, the complete finalized `authority_grant`, `authority_grant_digest`, and `authorization_digest`. The payload and grant digest fields must equal their nested finalized objects; `authorization_digest` uses the section-3 preimage/final rule. Thus payload → grant → finalized authorization is one-way and contains no digest cycle.

A UID-501 file has no authority until held-FD payload bytes match the externally granted payload digest and the finalized payload, grant record, and authorization are copied into fresh protected inodes. All component digests form one payload; substitution or omission fails. Expiry, policy lineage/floor, scheduler binding, expected-current CAS, target inventory, and smoke UUID are checked immediately before consumption.

The consumed-record schema has exactly: schema 1, authorization ID, payload digest, finalized authorization digest, AuthorityGrant digest, installer transaction UUID, smoke transaction UUID, operation, destination enum, policy generation/lineage/sequence, prior/proposed floor digests, consumed timestamp, expected-current digests, target manifest/inventory digests, initial-target-bundle digest, scheduler action digest, and record digest. Operation-specific nullability is identical to the payload. It is exclusively published under the authorization ID and can never be removed or reused by normal recovery.

## 12. One-time root installer transaction

Common ordering for an existing protected installation:

1. Validate payload, exact wire-derived AuthorityGrant, finalized authorization, scheduler snapshot, policy floor, and every digest-bound component from held FDs without mutation.
2. Inhibit both schedulers exactly as authorized: disable/bootout LaunchDaemon and pause old Hermes job; read back both states and matching processes.
3. Acquire installer lock, then acquire the service lease with `flock(LOCK_EX)`; prove no service process; publish/sync durable fence and retain both exclusive locks.
4. Create the root installer transaction namespace with durable `PREPARED`, then atomically consume authorization and publish `AUTH_CONSUMED`.
5. Operation-specific mutation is exact. `install-initial` validates its complete initial-target bundle, then separately builds, stages, publishes, and journals the runtime pair followed by the active-skills pair using their kind-qualified TREE states; it then separately stages, publishes, and journals runtime current followed by active-skills current using their kind-qualified POINTER states. `promote-runtime|promote-skill` perform only their selected kind's tree and pointer states. `rollback-protected` skips tree states and stages only the selected kind's exact already-protected permitted pointer. `update-floor` skips every tree/pointer state and stages the exact proposed floor under section 10.
6. A non-initial pointer operation exchanges qualified next and current using root-only RENAME_SWAP, syncs the kind parent, validates both inodes/targets, and appends the matching kind's POINTER_SWITCHED state. Initial installation instead publishes each absent current with RENAME_EXCL in runtime-then-active-skills order, syncs and validates each kind parent before its matching POINTER_SWITCHED record, and records explicit absent prior pointers. `update-floor` publishes and journals FLOOR_SWITCHED under section 10.

A non-initial operation then verifies its operation-specific result—pointer and full manifest/inventory/closure for promote/rollback, or complete floor CAS/swap for update-floor—plus authorization consumption, scheduler inhibition, and negative permissions; runs protected read-only selfcheck where a pointer exists; rotates epoch durably; publishes VERIFIED then COMMITTED; sets only the authorized final scheduler state while retaining the lease; removes/syncs fence; and releases service lease then installer lock.

Initial installation follows section 4.4 until the service lease exists, acquires installer then exclusive service locks and proves step-3 conditions, and joins step 5 with its already durable PREPARED/consumption. Only after both kind-qualified POINTER_SWITCHED records converge may it create and fully sync the staged initial proposed floor, append and sync FLOOR_STAGED, publish it via RENAME_EXCL, sync and held-FD validate it, and append FLOOR_SWITCHED in the literal section-10 order. Only then may it perform this crash-durable smoke protocol before COMMITTED:

1. Revalidate the final held-FD initial floor and its target tuples. Install and read back the authorization-bound on-demand plist, which has no calendar/start/network/path/watch/Mach-service trigger and cannot run except explicit kickstart. Run protected read-only selfcheck and rotate epoch while fenced.
2. Publish/sync the exact root-owned smoke gate and append `SMOKE_GATE_PUBLISHED`. Bootstrap/enable only the on-demand label and prove no PID. The old job remains paused and no final schedule exists.
3. While holding both locks, remove/sync FENCED; retain installer lock and release only service lease. Kickstart the exact label once. The matching service acquires the lease, completes or aborts its one gate-bound transaction, and exits; every duplicate/nonmatching invocation is nonmutating.
4. Disable/bootout the on-demand label and read back no PID; then, while still holding installer lock, reacquire service lease and publish/sync FENCED. If root crashed anywhere after gate publication, recovery starts with this same scheduler-inhibition → installer-lock → service-lease → fence sequence; the durable gate and triggerless plist prevent normal admission meanwhile.
5. Require the exact eight-state committed smoke chain, one source/candidate/PASS receipt, no extra transaction, exact floor/epoch/manifests, and immutable gate/authorization bindings; append `SMOKE_ACCEPTED`. Any failure/uncertainty retains gate and fence and enters RECOVERY_REQUIRED.
6. While fenced and holding both locks, bootout the on-demand plist, install/read back the authorization-bound final scheduled plist, rotate epoch durably, remove/sync the smoke gate, and prove normal cold-boot admission. Only then append VERIFIED and COMMITTED, enable/bootstrap the final schedule, remove/sync fence, and release service lease, installer lock, then bootstrap lock.

If any crash occurs after authorization consumption, recovery may complete only that transaction or restore an exact prior protected version allowed by the floor. It may not reuse the authorization. If neither exact state is provable, execution remains gated/fenced.
## 13. Scheduler ownership and cutover

The only canonical scheduled writer is LaunchDaemon `system/com.nous.hermes.loop-a` at `/Library/LaunchDaemons/com.nous.hermes.loop-a.plist`. Its plist is root:wheel 0644, digest-bound, has exact `ProgramArguments`, `UserName=_hermesloopa`, protected working directory, sanitized environment, and no shell. A plist is initially published to an absent final name with RENAME_EXCL. Replacement is allowed only while both schedulers are inhibited, the label is disabled/booted out with no PID, both root locks and FENCED are held, and the exact old/new plist inodes and digests are journal-bound; root swaps the final name with a transaction-qualified same-parent staged plist using RENAME_SWAP, syncs `/Library/LaunchDaemons`, validates both names/inodes/bytes, and retains the old plist until installer terminal recovery. UID 501, including Hermes cron job `600370f80d83`, can never open the service lease or mutate canonical state; re-enabling that old job can create only untrusted user-home output and is an operational failure, not a second canonical writer.

A scheduler snapshot has exactly: schema 1, timestamp, old job ID, old persisted enabled boolean, old schedule string, old script path/digest, Hermes jobs-state digest, launchd label, installed plist digest or null, authorized on-demand/final plist digests, launchctl disabled boolean, launchctl loaded boolean/PID or null, service-lease device/inode/holder evidence, matching-process inventory, and record digest. The authorization binds its digest and exact target action.

Forward cutover is exactly the section-12 initial smoke-gate branch. No scheduled plist is installed or enabled, and installer COMMITTED is impossible, until root has reacquired scheduler exclusion and both locks, fenced, accepted the exact successful smoke, removed the gate, and installed the final plist. No alternative ordering is valid.

Rollback ordering is exact:

1. Validate a fresh `rollback-protected` payload/grant, target floor tuple, and scheduler snapshot without mutation.
2. Inhibit both schedulers: disable/bootout the LaunchDaemon and pause the old Hermes job; read back both persisted states and matching processes.
3. Acquire installer lock then acquire the service lease with `flock(LOCK_EX)`, prove no service process, publish/sync the fence, and retain both exclusive locks.
4. Reconcile or block installer/service transactions; consume the rollback authorization in a new installer transaction.
5. Restore the exact prior protected pointer only when its lineage/sequence/manifest/inventory tuple is explicitly permitted by the rollback floor; otherwise remain fenced.
6. Verify hashes, pointer, execution closure, policy, processes, scheduler snapshot, and negative permissions; rotate and verify epoch durably; only afterward publish rollback terminal commit.
7. Set only the authorization-bound final scheduler state while retaining the service lease: either enable the protected LaunchDaemon or restore the old job to its exact prior enabled state with LaunchDaemon disabled/unloaded. Remove/sync the fence only after complete readback, then release service lease and installer lock.

Canonical data, account, and protected trees are retained unless a separate destructive-removal grant names exact objects.

Cold boot is fail-closed: the LaunchDaemon service must acquire the protected lease, require absent fence, validate epoch, policy floor, current pointer, full manifest, plist digest, process identity, and smoke-gate state before mutation. Gate absent admits only exact normal nightly scheduling; gate present admits only its one bound initial smoke and never a normal run. A missing/partial/failed/duplicate/unaccepted gate transaction or scheduler/transaction inconsistency writes nothing and exits nonzero; root recovery remains required. No boot path grants UID 501 canonical authority.

## 14. RED acceptance matrix

Mandatory test families:

- UID 501 and service UID negative writes to root/runtime/active-skills/auth ledgers.
- Pre-existing hostile FDs to every old inode.
- Source mutation/truncation during every read boundary.
- Symlink/hard-link/`..`/ACL/group/inherited-FD traversal attacks.
- Same-parent final-name collision and no-unlink/no-swap behavior.
- Kill/fault injection at every write, fsync, F_FULLFSYNC, rename, directory fsync, journal, fence, epoch, authorization, scheduler, install, recovery, rollback boundary.
- Concurrent/stale service epochs and retained FDs.
- Two installers racing one authorization; one durable consumption maximum.
- Authority-envelope component substitution/omission/replay/expiry/target change.
- Multi-object install mixed-version prevention while fenced.
- Projection forgery and fallback rejection.
- Exact wrapper/dependency execution as service UID and candidate/receipt cardinality.
- Restore from backup with hostile archive FDs; fresh protected destination inodes only.
- Target-host crash/power-loss matrix with expected path aliases, inode inventory, journal state, and permitted residue defined per crash point.
- Root installer versus launchd/service lease races, including scheduler start between every check and mutation.
- Differential RFC 8785/JCS vectors for Unicode, escaping, integers, timestamps, duplicate keys, unknown fields, type errors, and array ordering.
- Metadata fault injection around `fchown`, `fchmod`, ACL/xattr/BSD-flag checks, file sync, full sync, and parent sync.
- Fresh directory and transaction-qualified current-link crash states before/after parent sync, swap/exclusive publish, journal, and residue reconciliation.
- Every installer transition and crash boundary around PREPARED, consumption, tree build, pointer stage/switch, epoch, scheduler, verification, and commit.
- Every allowed and forbidden service/installer transition, including mandatory CANDIDATE_WRITTEN → RECEIPT_WRITTEN → ABORTED with deterministic FAIL-receipt evidence and rejection of direct CANDIDATE_WRITTEN → ABORTED.
- Grant-channel and authorization substitution, malformed IDs, collision, replay, expiry, scheduler/target/inventory/policy-floor substitution, and post-consumption replay.
- Rollback below floor, floor loss/corruption, and concurrent floor CAS.
- Cold boot/power loss at every scheduler cutover step proving UID 501 and old cron never obtain canonical write authority.
- Exact FD-consumption tests for scripts, imported modules, interpreter/stdlib identity, renamed version trees, and rejection of user-site/plugin/shebang/dynamic code.
- Fixed authorization-payload → AuthorityGrant → finalized-authorization vectors proving acyclic construction, nested digest equality, and substitution rejection.
- Service-UID epoch unlink/rename/stash/replay attempts against root-owned `control/`, including retained old epoch FDs.
- Preimage/finalized-schema vectors proving explicit-null acceptance only in preimages and omission/non-null rejection.
- Manifest relocation/self-inclusion/orphan-pair recovery and extra/missing inventory tests.
- Interpreter, stdlib, loader, dylib, code-signing, and OS-update drift against `execution_closure`.
- Crash injection before/after transaction-root publication, PREPARED parent sync, source publication, and SOURCE_CAPTURED publication.
- Rollback tests for incomparable digests, divergent lineages, sequence rebinding, stale generations, below-floor and absent permitted tuples.
- Duplicate, absent, normal-purpose-substituted, wrong-UUID, malformed, and extra-window smoke transactions.
- Power loss at every boundary from smoke-gate publication through fence removal, lease handoff, kickstart, service terminal record, root reacquisition, SMOKE_ACCEPTED, gate removal, final-plist publication, epoch durability, COMMITTED, scheduler enablement, and fence removal.
- Cold boot with missing/partial/failed/duplicate/wrong-UUID/unaccepted smoke evidence, plus natural scheduler and concurrent kickstart attempts during the gated window.
- Protected interpreter/import replacement before `fexecve`; sealed snapshot/cryptex/dyld generation and loaded-image mismatch before child handshake and mutation.
- `update-floor` substitutions of prior digest, proposed digest, minimum, lineage, or any permitted tuple after grant issuance.
- AuthorityGrant wire/JSON normalization, CRLF, encoding, whitespace, reordered/duplicate fields, bad wire hash, preimage, finalized digest, and nested-object differential vectors.
- Per-purpose zero/duplicate/extra source, candidate, receipt, PASS/FAIL, window, and transaction-chain cases.
- Installer transaction roots with every missing, extra, misowned, mis-moded, aliased, or partially published fixed child.
- Rollback crashes immediately before/after epoch durability and terminal commit.
- Floor initial-create/update crashes before/after stage record, file sync/full-sync, RENAME_EXCL/swap, parent sync, FLOOR_SWITCHED, epoch rotation, commit, reversal, and prior-inode retirement; initial smoke with absent/partial/stale/unjournaled floor.
- Golden/adversarial inventory preimage/final objects covering kind/lineage/sequence mismatch, missing/reordered/extra entries, directory metadata, digest null rules, and manifest differential.
- Sequential duplicate nightly starts, retry after every crash point, cold-boot replay, UTC wall-clock rollback, DST/local-zone change, adjacent-window boundary races, and deterministic UUID collision/mismatch.
- Every service RECOVERY_REQUIRED chain proving commit is rejected and only exact ROLLED_BACK is terminal.
- Exact AuthorityGrant key mapping vectors for all seven wire values, especially payload_sha256→payload_digest and destination→exact_destination.
- The same UTC nightly occurrence before and after epoch/service-instance rotation, proving both starts derive the same protocol-namespace UUID and a second root is rejected before creation; existing-root window/purpose/schedule/occurrence mismatch fences.
- Initial-target-bundle preimage/final vectors and operation-nullability vectors; runtime/active-skills tuple substitution, omission, duplication, extra kind, lineage drift, independent sequence drift, and floor mismatch all reject.
- Initial-install fault injection before and after each kind-qualified TREE and POINTER state/publication, including every one-present/one-absent and one-switched/one-unswitched combination; smoke and floor publication remain impossible until both exact pointers converge.
- Every installer predecessor that can enter RECOVERY_REQUIRED proving direct VERIFIED and COMMITTED are schema/state-machine rejected and only exact ROLLED_BACK is terminal.
- Initial and update floor probes proving no transaction-attributable final `rollback-floor.json` may exist without an earlier durable FLOOR_STAGED record binding its exact inode and bytes.
- Every installer, recovery, rollback, cutover, and smoke-reacquisition path proving `service/lease.lock` uses `flock(LOCK_EX)` and never a shared lock.
- Existing deterministic nightly roots with missing, null, altered, or state-inconsistent schedule digest/occurrence, plus independently recomputed window ID and UUIDv5 checks before any reconciliation.
- Power loss after deterministic FAIL-receipt publication and after RECEIPT_WRITTEN publication, proving one receipt only and convergence through RECEIPT_WRITTEN to ABORTED.
- Rollback-floor canonical-order vectors with reversed entries, equal-prefix tuples, duplicate complete tuples, duplicate kind/sequence keys, and an independent comparator/digest implementation.

All P0/P1 findings must be zero on the exact protocol, schema bundle, implementation, installer, test, and authority-packet digests before system mutation.
