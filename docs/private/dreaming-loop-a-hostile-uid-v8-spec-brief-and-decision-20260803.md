# Loop A revision-8 candidate — Spec Brief and Decision Record

Status: candidate / HOLD. This document authorizes no system mutation, cutover, commit, or push.
Date: 2026-08-03
Worktree: `/Users/charles/.hermes/worktrees/dreaming-loop-20260801`

## Spec Brief

### Goal

Make the protected Loop A runtime executable on the declared Darwin target while preserving the hostile-UID isolation property as closely as the platform permits: verify the complete protected executable and input closure through held FDs; allow exactly one root-owned canonical interpreter pathname to be executed with `posix_spawn`; perform immediately adjacent pathname-to-held-FD identity and byte readback; and keep all mutation authority closed until an independently validated child handshake completes.

### Non-goals

- No claim that pathname `posix_spawn` is kernel-atomic with prior FD verification.
- No protection against a malicious or concurrently mutating root, kernel, launchd, APFS implementation, or trusted launcher.
- No pathname import of protected scripts, stdlib, modules, skills, configuration, or data.
- No `/dev/fd`, shebang, shell, mutable trampoline, copied temporary executable, user-home executable, or best-effort fallback.
- No system installation, root/account/permission mutation, launchd/cron mutation, cutover, commit, or push in this implementation slice.
- No production or cutover acceptance from unit tests alone.

### Source facts and boundaries

- Frozen revision 7 requires `fexecve` of a retained interpreter FD and prohibits pathname execution.
- On the declared macOS 26.5.2 / Darwin 25.5.0 / SDK 26.5 target, Python exposes no `os.fexecve`; `libSystem` exposes no `fexecve`; SDK headers expose neither `fexecve` nor `execveat`; a strict native compile probe fails; and `/dev/fd/<held-fd>` execution fails with `EACCES`.
- Darwin provides pathname `execve`/`posix_spawn` only. Therefore revision 7 is preserved and revision 8 is a versioned architecture successor, not an in-place weakening.
- The hostile principals are UID 501 and `_hermesloopa`. Root, launchd, kernel, APFS, and reviewed launcher/service code remain in the trusted computing base.
- The user explicitly selected and authorized local reversible drafting and implementation of the revision-8 path: held-FD verification + root-owned hostile-UID-unwritable canonical path + adjacent identity readback + pathname `posix_spawn`.

### Invariants and business rules

1. Every protected executable observation is derived from held FDs: device/inode, type, owner/group/mode, link count, ACL, xattrs, BSD flags, byte count, and SHA-256.
2. Every canonical execution ancestor and the executable leaf is root-owned, non-symlink, non-aliased, metadata-exact, and non-writable/non-renamable by UID 501 and `_hermesloopa`.
3. The exact interpreter relative path is resolved beneath a retained parent/version FD. Absolute or traversing relative input, empty components, `.`, `..`, NUL, and alternate path spellings reject.
4. Immediately before spawn, a fresh `O_RDONLY|O_NOFOLLOW` open of that exact relative leaf must match the retained executable FD in identity, metadata, bytes, and digest.
5. Root/version/current/manifest/inventory/execution-closure identities must remain unchanged through the adjacent pre-spawn readback.
6. Exact argv is `[canonical_interpreter_path, "-I", "-B", fd_backed_entrypoint]`; the adapter may not insert a shell, shebang, fallback executable, or mutable path.
7. Environment is built from a fixed allowlist rather than inherited. `PYTHONNOUSERSITE=1` is fixed; `PATH`, `PYTHONPATH`, `PYTHONHOME`, user-site, loader-injection, plugin/hook, and unapproved locale variables are absent.
8. Protected scripts, stdlib, modules, skills, configuration, and data are supplied through inherited read-only FDs and FD-backed loaders only.
9. Spawn creates no mutation authority. The child receives a one-time launcher nonce and must report exact child PID, executable identity/digest, protected-FD inventory, current/manifest/inventory identities, and immutable-system/loaded-image inventory.
10. Missing, duplicate, malformed, stale, mismatched, wrong-PID, or wrong-nonce handshake evidence terminates the child and leaves mutation closed.
11. A one-use mutation-capability acknowledgement is emitted only after exact handshake equality. No service or installer mutation sink may be reachable before that acknowledgement.
12. Pathname spawn retains a residual root race. Hostile-UID safety depends on the proven authority boundary, not on repeated `stat` calls pretending to provide FD-bound execution.

### Negative acceptance cases

- Any execution ancestor or leaf is group/world writable, hostile-owned, service-owned, symlinked, hard-linked, ACL-bearing, xattr-bearing, flagged, wrong-mode, wrong-device, or identity-substituted.
- The held executable is changed after initial verification.
- The canonical pathname is replaced between initial verification and adjacent readback.
- The executable digest or byte count differs from the manifest.
- `current`, selected version, manifest, inventory, or execution closure changes before spawn.
- argv is not exact or names `/dev/fd`, a shell, shebang entrypoint, copied temp executable, or noncanonical interpreter.
- inherited environment contains any forbidden Python/import/loader/plugin/path variable.
- protected import or entrypoint is pathname-backed rather than FD-backed.
- mutation is attempted before handshake acknowledgement.
- handshake is missing, malformed, duplicated, stale, wrong-nonce, wrong-PID, or differs in any protected/system identity.
- UID 501 or `_hermesloopa` mutation/rename probes succeed on any ancestor or leaf.
- the platform cannot prove an ancestor or leaf's ACL/xattr/flag/identity state.

### Evidence required

- Candidate protocol and normative-delta exact SHA-256.
- RED evidence for every negative acceptance cluster before launcher production code.
- Focused GREEN evidence for the exact adapter and handshake.
- Mutation RED against disposable copies for deleted adjacent-readback, metadata, digest, argv/environment, and handshake gates.
- Exact `posix_spawn` argv/environment readback through a real local child harness.
- Hostile-principal namespace mutation probes in a controlled disposable root; unit mode/owner simulations are not production authority evidence.
- Full protected suite, compileall, generated schema `--check`, and no-cache/no-bytecode invocation provenance.
- Disposable-root crash/race integration.
- Independent current-digest security review with P0=0/P1=0 before any acceptance promotion.
- Separate exact authority and post-action readback before system cutover.

## Objective model and chosen path

Success criteria are the invariants and evidence above. Constraints are Darwin's missing FD-exec primitive and the closed system/cutover authority boundary. Viable paths were: retain revision 7 and remain permanently blocked; locate a real native FD-exec primitive; or create a versioned successor whose safety depends on root-owned namespace authority and adjacent readback. Native language, symbol, header, compile, and behavioral probes falsified the second path on the target. The user selected the third. Consequence: revision 8 can protect against UID 501 and `_hermesloopa`, but cannot truthfully claim kernel-atomic execution of the verified FD and includes root in the TCB.

## Decision Record DR-8-001

Decision: create revision 8 as a successor to frozen revision 7. Replace only the impossible held-FD execution mechanism with the exact protected-pathname `posix_spawn` exception defined above. Preserve revision 7 unchanged.

Authority opened: local reversible docs, RED tests, minimal implementation, and local verification inside the named worktree.

Authority closed: root/system/account/permission changes, canonical `/var/db/hermes-loop-a` writes, launchd/cron mutation, cutover, commit, and push.

Rollback: delete or revert only the uncommitted revision-8 candidate files and launcher/test changes in the worktree. No system rollback is required because this slice must not mutate the host runtime.

Decision state: authorized candidate implementation; HOLD for acceptance and all external/system effects.

## Converge state

| Claim | Required evidence | Current state |
|---|---|---|
| Revision-7 primitive is unavailable on target | binding/symbol/header/compile/behavior probes | evidenced in implementation progress; carried as the revision-8 decision boundary, not reclassified as FD-exec support |
| Revision-8 rules are explicit | candidate protocol + normative delta + this packet + exact freeze manifest | drafted and digest-frozen as a candidate; independent current-digest review pending |
| Launcher rejects hostile pathname states | RED then focused GREEN | local adjacent-readback replacement/byte-mutation and canonical-path negative tests pass in the 228-test protected suite; hostile-principal system integration remains closed |
| Spawn argv/environment are exact | real local child harness readback | real Darwin `posix_spawn` child harness verifies stdin script, fixed FD map, duplex nonce channel, stdout/stderr, exact argv/environment; production protected root is not installed |
| Mutation remains closed before handshake | negative integration tests | handshake mismatch/timeout/one-use tests prove no capability FD is sent locally; production service-sink integration remains pending and requires system authority |
| No forbidden fallback exists | source scan + negative tests | explicit `/dev/fd`, shell, env and noncanonical executable rejection tests pass; independent current-digest review pending |
| Current protected suite remains green | fresh full-suite output after final mutation | `228 passed in 79.16s`; compileall exit 0; schema artifact and freeze manifest checks verified |
| Cutover safe | controlled integration + exact authority + readback | closed/not authorized; no cutover-safety certification claimed |
