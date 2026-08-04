# Loop A hostile-UID protocol revision 9 → revision 10 normative delta

Date: 2026-08-03
Status: implementation candidate; production cutover remains HOLD until the revision-10 candidate is frozen, independently certified, exactly authorized, deployed, and read back.
Parent: revision-9 candidate and its frozen revision-8 base.

## 1. Scope

Every revision-9 rule remains normative except where this delta explicitly replaces it. This delta resolves contradictions found while composing the first real macOS launchd activation path. It grants no standing mutation authority and does not certify any implementation.

## 2. Activation topology retained

The transport remains:

```text
root scheduled broker
  -> connects to launchd-owned private AF_UNIX/SOCK_STREAM endpoint
  -> launchd starts the distinct-UID _hermesloopa outer worker
  -> broker binds launchctl PID to kernel peer PID/UID/GID
  -> worker binds the kernel peer to the exact root broker PID/UID/GID
  -> broker sends one exact six-role SCM_RIGHTS bundle
  -> worker launches one isolated inner child
```

A coordinator-created socketpair, broker-owned listener, direct root spawn with credential drop, or same-UID fallback is forbidden.

## 3. Sole immutable-descendant directory exception

Revision 9's categorical prohibition on transferring any directory beneath a canonical mutation root is replaced.

Exactly one directory role may cross the broker/worker boundary: `version-root`. Its held identity must equal the broker-approved runtime-version identity and its canonical path must be exactly:

```text
/private/var/db/hermes-loop-a/runtime/versions/<runtime-manifest-digest>
```

The ancestry walk may encounter exactly the approved `runtime` mutation-root identity. Encountering any other canonical mutation-root identity rejects the bundle. The version root itself must not equal any mutation-root identity. It and every descendant in its manifest inventory are root:wheel, directories `0555`, regular files `0444` or `0555`, link-count constrained, and free of symlinks, ACLs, xattrs, and nonzero flags. No second directory descriptor or writable version descriptor is permitted.

The exception is read authority over one already-frozen version, never mutation authority over `runtime`.

## 4. Duplex attestation control descriptor

Inner FD 4, role `attestation-control`, has direction `control`. It must be one connected AF_UNIX stream endpoint opened read/write. A read-only or write-only description, wrong socket type, or additional control endpoint rejects the launch.

The other inner FD directions remain unchanged.

## 5. Outer bootstrap versus inner entrypoint

The exact-stdin entrypoint rule applies to the inner computational child. Its argv remains exactly:

```text
[canonical_interpreter_path, "-I", "-S", "-B", "-"]
```

and its entrypoint bytes arrive only on inner FD 0.

The outer launchd worker is a separate, non-computational activation shim. Launchd may start the same immutable interpreter with `-I -S -B -` and `StandardInPath` bound to one manifest-inventoried root-owned bootstrap file. That bootstrap may only replace the environment with the fixed allowlist, derive the direct-digest version root from `sys.executable`, add that version's immutable `libexec` to `sys.path`, import the worker service, and run one bounded session. It may not inspect user paths, select a candidate, mutate canonical state, or use PATH, PYTHONPATH, PYTHONHOME, a shell, shebang, `/dev/fd`, or mutable fallback.

## 6. Candidate context binding

The outer FD-bundle record advances to schema 2 and adds exactly one business-context field, `skill_name`, using the canonical single-component grammar:

```text
[A-Za-z0-9][A-Za-z0-9._-]{0,80}
```

The broker binds this value from the admitted transaction before activation. The worker cannot select or modify it. `transaction_uuid` remains the candidate `run_id`; the stable digest of protected source FD bytes remains `source_sha256`.

The inner child receives only the protected source and runtime inputs and emits bounded UTF-8 candidate content, not an authority envelope. After successful attestation and zero exit, the outer worker constructs the canonical `hermes.dreaming.candidate.v2` envelope from exactly:

- `run_id = bundle.transaction_uuid`;
- `skill_name = bundle.skill_name`;
- `source_sha256 = SHA-256(protected source FD bytes)`;
- `candidate_bytes = exact inner stdout bytes`.

The root broker independently validates the envelope against its admitted transaction binding. Worker output cannot select a pathname, destination, operation, authorization, transaction, or state transition.

Encoding `skill_name` inside the untrusted source bytes is forbidden because it would conflate source content with broker-authoritative transaction context.

## 7. Native spawn closure

Production inner-child creation must use a compiled Darwin adapter with `POSIX_SPAWN_CLOEXEC_DEFAULT` and exact `dup2` file actions mapping ten distinct source descriptors to child FDs 0 through 9. PATH lookup, `posix_spawnp`, `/dev/fd` enumeration, pre-spawn enumeration of ambient descriptors, shell execution, and close actions derived from a racy process-wide FD snapshot are forbidden.

The child must prove exactly FDs 0 through 9 at startup and no open descriptor at or above 10.

## 8. Account binding

Revision 10 deployment authorization must bind or reference a frozen account contract containing the exact non-root UID, GID, account name `_hermesloopa`, group name `_hermesloopa`, home `/var/empty`, shell `/usr/bin/false`, hidden/login-disabled state, primary group, and empty supplementary-group set. A UID/GID selected only at apply time is not exactly authorized.

## 9. Hostile mutation evidence boundary

Active mutation probes are required only on disposable exact-layout replicas and disposable launchd integration roots. Production canonical inodes receive non-mutating metadata, ACL, ownership, path, descriptor, process, and denial readback. No positive write probe is run against a live canonical sink.

## 10. Acceptance

Revision 10 cannot cut over until all of the following are fresh and current-digest bound:

1. consolidated schema and freeze identities;
2. native-spawn exact-FD evidence;
3. actual launchd PID/UID/GID cross-binding in both directions;
4. real distinct-UID hostile denial evidence on disposable roots;
5. complete broker transaction, cold-start, crash/replay, cleanup, smoke, and rollback evidence;
6. two independent reviews with P0=0 and P1=0;
7. one exact deployment tuple and a human-executed root authority gate where required.
