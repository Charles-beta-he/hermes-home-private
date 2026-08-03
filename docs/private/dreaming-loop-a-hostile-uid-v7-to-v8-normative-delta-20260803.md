# Loop A hostile-UID protocol revision 7 → revision 8 candidate normative delta

Status: candidate / HOLD. Revision 7 remains frozen and unchanged.

## Unchanged normative surface

Every revision-7 rule remains normative except where the exact clauses below are replaced. This delta grants no system mutation, cutover, commit, or push authority.

## D-1 — Scope invariant

Revision-7 invariant “consumes every protected-tree object from held FDs only” is replaced by:

- Every protected-tree identity and byte digest is derived from held FDs.
- Protected scripts, stdlib, modules, skills, configuration, and data are consumed only through inherited read-only FDs and FD-backed loaders.
- Exactly one canonical vendored-interpreter pathname may be consumed by Darwin `posix_spawn`, subject to D-2 through D-7.

## D-2 — Platform capability finding

- On the declared target, `fexecve` and `execveat` are unavailable at the Python binding, `libSystem` symbol, and SDK-header levels; strict native compilation fails.
- `/dev/fd/<held-fd>` execution is behaviorally unsupported and is forbidden as a substitute.
- The revision-8 exception is a platform-specific architecture decision, not an optional optimization.

## D-3 — Canonical execution namespace

Before spawn, the launcher must hold and verify the canonical root, runtime kind, `versions`, selected version, executable ancestors, executable leaf, external manifest, inventory, `current` target, and execution closure.

Every execution-path ancestor and leaf must be:

- on the expected canonical device and mount identity;
- root-owned with the frozen group and exact mode;
- a directory or one-link regular file as declared;
- non-symlinked and non-aliased;
- free of extended ACLs, xattrs, and nonzero BSD flags;
- unmodifiable and unrenamable by UID 501 and `_hermesloopa`.

Failure or inability to prove any property rejects before process creation.

## D-4 — Immediately adjacent pathname-to-FD readback

After exact argv/environment construction and with no callback or mutable operation between validation and spawn, the launcher must:

1. Resolve the exact manifest-relative interpreter path beneath the retained canonical parent/version FD.
2. Open the leaf with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`.
3. Compare device, inode, type, owner, group, mode, link count, ACL, xattrs, and BSD flags with the retained verified executable FD.
4. Re-read all bytes and require exact byte-count and SHA-256 equality with the retained FD and manifest.
5. Re-read canonical root/version/current/manifest/inventory/execution-closure identities and require equality with the retained observations.
6. Call pathname `posix_spawn` as the next operation.

Any mismatch rejects. No retry through a different pathname or executable is allowed.

## D-5 — Exact process contract

The only allowed argv is:

```text
[canonical_interpreter_path, "-I", "-B", fd_backed_entrypoint]
```

The environment is built from a protocol-fixed allowlist, includes `PYTHONNOUSERSITE=1`, and does not inherit `PATH`, `PYTHONPATH`, `PYTHONHOME`, user-site, loader-injection, plugin/hook, mutable-path, or unapproved locale variables.

Inherited protected-input FDs are read-only, explicitly inventoried, and mapped to fixed child descriptors. Unlisted descriptors are closed.

Forbidden process mechanisms include `/dev/fd` execution, shebang resolution, shell evaluation, mutable trampolines, copied temporary executables, user-home executables, and pathname import of protected or non-system code.

## D-6 — Pre-mutation child handshake

Spawn success creates no mutation authority. The launcher issues a one-time nonce and withholds a one-use mutation capability until the child reports one canonical handshake bound to:

- launcher nonce and child PID;
- interpreter device/inode/type/owner/group/mode/link count/byte count/SHA-256;
- exact protected-FD inventory;
- canonical root/version/current/manifest/inventory identities;
- immutable mounted-system, boot/cryptex, OS build, SIP/seal, dyld-cache, Apple-signature, and loaded-image inventory.

The launcher independently validates exact equality and only then acknowledges the one-use capability. Missing, duplicate, malformed, stale, late, wrong-PID, wrong-nonce, or mismatched handshake evidence terminates the child and leaves mutation closed. Every mutation sink must require the acknowledged capability; ordering cannot rely on child convention alone.

## D-7 — Residual race and trust boundary

Pathname `posix_spawn` is not kernel-atomic with prior FD verification. Revision 8 therefore guarantees hostile-UID isolation only under the proved condition that UID 501 and `_hermesloopa` cannot modify or rename any execution ancestor or leaf. Root, launchd, the kernel, APFS, and reviewed launcher/service code remain trusted. Concurrent malicious root mutation is outside the hostile-UID guarantee, although visible drift must still fail adjacent readback.

## Required successor negative matrix

1. hostile-writable or service-writable ancestor;
2. symlinked/replaced ancestor or leaf;
3. hard-linked executable;
4. pathname identity differs from retained FD;
5. byte, digest, metadata, mount, or current/version/manifest/inventory drift;
6. unsafe relative path or alternate spelling;
7. argv shell/shebang/fallback substitution;
8. forbidden inherited environment;
9. pathname-backed protected import or entrypoint;
10. missing/malformed/duplicate/stale/wrong-PID/wrong-nonce/mismatched handshake;
11. mutation attempt before capability acknowledgement;
12. successful hostile-principal mutation or rename probe;
13. `/dev/fd` or copied-temp fallback present or reachable.

## Acceptance boundary

Local unit and harness tests may establish only the adapter contract. Revision-8 acceptance additionally requires controlled target-host integration, crash/race testing, exact candidate digests, mutation-sensitive tests, and independent current-digest P0=0/P1=0 review. Cutover remains a separate exact-authority action.
