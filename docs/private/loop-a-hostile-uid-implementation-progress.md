# Loop A hostile-UID protected-runtime implementation progress

**Goal:** Implement the revision-9 root-broker/distinct-UID-worker isolation candidate locally without system mutation, commit, or push.
**Status:** implementation candidate / HOLD pending production activation boundary, authorized hostile-UID integration, and current-digest independent closure.
**Normative delta:** `dreaming-loop-a-hostile-uid-v8-to-v9-normative-delta-20260803.md`

## Authority boundary

Authorized: reversible writes and tests in this worktree.
Closed: root/system/account/launchd/cron/active-skill mutation, cutover, commit, and push.

## Objective model

- Only a root broker may mutate canonical transaction, journal, source, candidate, receipt, and pointer state.
- The `_hermesloopa` worker must be a distinct non-root launchd/native-boundary process with no pathname, ACL/group, or inherited-FD mutation route into canonical roots.
- Worker output is untrusted data. The broker validates a bounded canonical frame and maps it only to a fixed durable transaction/publication operation.
- No completion or certification claim is permitted before current-digest dual review and authorized system-level denial/readback evidence.

## Implemented local slices

- Existing canonical JSON, exact schemas, authorization, state graphs, publication, journals, transaction namespaces, and root mutation gates.
- Broker-result validation binds nonce, worker PID, transaction UUID, source digest, candidate digest/size, runtime manifest digest, and runtime inventory digest.
- Bounded pipe result transport: one canonical metadata frame, exact candidate bytes, EOF, one end-to-end deadline, and fixed size limits.
- Fixed broker coordinator with repeated gate/transaction binding checks and no worker-selected pathname, operation, destination, authorization, or state transition.
- Journal/publication adapter from exact `CANDIDATE_STAGED` to a fixed `candidates/candidate/{candidate.json,payload.bin}` tree and durable `CANDIDATE_WRITTEN` readback.
- Publication failure records durable `RECOVERY_REQUIRED`; candidate-publication success followed by journal-append failure is read back and either accepted as exact durable success or durably fenced as `RECOVERY_REQUIRED`.
- Darwin handshake requires exactly one canonical request followed by `SHUT_WR`/EOF before an attestation-only acknowledgement; failure kills and reaps the child.
- Exact worker FD contract now maps ten roles to child FDs 0..9: entrypoint, result, diagnostics, challenge, attestation-control, retained executable, version root, manifest, inventory, and canonical source. Every FD >=10 is explicitly closed in the local `posix_spawn` prototype.
- Exact FD role/direction/type/CLOEXEC checks reject duplicates, writable protected inputs, and mutation-root inode identities.
- macOS peer credentials are read through a validated ctypes adapter using `LOCAL_PEERPID`, `LOCAL_PEEREPID`, and `LOCAL_PEERCRED`; exact PID/UID/GID and root-broker admission are enforced.
- Real macOS tests cover `posix_spawn` source input on FD 9 and AF_UNIX listener observation of the connecting child PID/UID/GID.
- Mutation-adequacy regressions cover every handshake binding field independently, parent-directory fsync, post-publication full-journal readback, invalid-result zero publication, and partial-commit recovery.

## Latest verified local evidence

- Full protected suite after the current implementation changes: `305 passed in 99.91s`.
- `compileall`: exit 0.
- Schema artifact regenerated and checked: `101450 bytes`.
- Freeze manifest regenerated and checked after all candidate-byte changes: manifest SHA-256 `2df5012f9c358ea76f22622a292a7282ece7388084b7333ac7801a47801e8172`, candidate aggregate `a86ee5a4c56a5465464e9867bd91fd51e076c1b8a9a2c3bd57ae7d099f79d9e7`; two independent reviews are in flight against that exact identity.

## Superseded-review reconciliation

The independent review bound to the older v8 digest `7297e4e0...afa7b` returned BLOCK. Its mutation-FD handshake findings are superseded because v9 transfers no mutation FD and now requires one request plus half-close. Its actionable lifecycle, handshake-field-totality, parent-fsync, and durable-journal-readback findings were reproduced against the current source and addressed with executable tests. Its root-owned nested-inventory race is not an `_hermesloopa` capability path under v9, but still requires broker-lock and authorized root-layout evidence before production certification. The old digest verdict cannot certify or reject the later candidate without fresh re-review.

## Remaining blockers

- No complete production launchd/native worker activation protocol yet proves the broker and worker are distinct UIDs before Python executes.
- The peer-credential adapter is not yet wired into a real launchd socket admission/readback path.
- Native or launchd close-on-exec-default behavior is not proven; `/dev/fd` enumeration is prototype evidence only.
- The root-only v9 service layout and broker lease have not been created or denied against the hostile `_hermesloopa` principal on a disposable root.
- No authorized ACL/group/xattr/BSD-flag denial matrix, inherited-FD scan, cold-start, crash/replay, or launchd PID/UID/GID readback has run.
- Current freeze digest still requires two independent reviews with P0/P1 findings reconciled against exact readable bytes.
- Cutover, smoke, commit, and push remain closed.

## Decision

Remain `HOLD`. Do not perform system cutover, launchd/cron/account mutation, commit, or push.
