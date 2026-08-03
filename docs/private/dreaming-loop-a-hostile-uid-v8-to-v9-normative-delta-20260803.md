# Loop A hostile-UID protocol revision 8 → revision 9 candidate normative delta

Status: candidate / HOLD. Revision 8 is rejected for execution/cutover and remains unchanged as historical evidence. This delta authorizes no system mutation, account creation, permission change, launchd change, cutover, commit, or push.

Date: 2026-08-03

## 1. Decision and threat-model correction

Revision 8 incorrectly treated a post-spawn handshake and an SCM_RIGHTS directory FD as the boundary that withheld mutation authority. A child running as the owner of writable canonical service state already has ambient pathname authority and can mutate before the handshake. Application convention cannot revoke DAC authority.

Revision 9 replaces that design with an OS-enforced broker/worker split:

- the mutation broker is the only canonical writer and runs as root under the trusted root launcher;
- the worker runs under the distinct non-root `_hermesloopa` identity;
- every canonical mutable service, installer, policy, authorization, journal, receipt, candidate, source, control, lease, and transaction directory is root-owned and grants `_hermesloopa` no owner, group, other, ACL, inherited-FD, or sandbox-exception write authority;
- the worker never receives a mutation-root FD and never performs canonical mutation;
- the broker performs only its already-admitted transaction's fixed state transition after validating worker output; the worker cannot request a path, operation, destination, authorization, transaction, or state transition.

A local unit mock of ownership is not target-host proof. Controlled disposable-root and target-host probes must execute as `_hermesloopa` and observe kernel denial for create, open-for-write, chmod, link, unlink, rename, exchange, and ancestor replacement before certification.

## 2. Canonical ownership changes

Revision-8 clauses that make `service/` or any descendant writable by `_hermesloopa` are superseded. Canonical mutable state is root-owned and root-writable only. `_hermesloopa` receives read/search access only to the exact immutable runtime tree and explicitly supplied read-only inputs needed by the worker. The broker opens canonical mutation roots through held FDs, retains all locks, performs every publication, and revalidates the complete root gate immediately before each mutation.

The scheduled LaunchDaemon is the root mutation broker. Its worker process is a distinct launchd-managed service running as `_hermesloopa`, with no Mach service or socket exposed to UID 501. launchd owns one root-configured private `AF_UNIX/SOCK_STREAM` listener below a root-only runtime directory. For one admitted transaction, the root broker connects to that listener, cross-binds launchd's reported worker PID to kernel peer PID/UID/GID, and transfers exactly one canonical length-framed, transaction-bound `SCM_RIGHTS` bundle containing only the six allowlisted read-only input roles. The worker independently verifies a root peer before accepting the bundle. No root credential, mutation FD, service-tree FD, installer FD, journal FD, lock FD, authorization FD, staged/publication FD, or open directory beneath canonical mutable state crosses the worker boundary. Darwin `AF_UNIX/SOCK_SEQPACKET` is not an available substitute on the target host.

The worker service is triggerless from public launchd surfaces. Its launch is transaction-scoped by the broker; implementation may use a separately labeled, root-configured launchd service because Darwin's public Python and C `posix_spawn` interfaces do not expose an atomic child-UID switch. A design that directly spawns the worker from a root process without independently proven credential drop is forbidden.

## 3. Worker execution and protected pathname consumption

The exact physical protected root spelling is `/private/var/db/hermes-loop-a`; `/var/db/...`, relative paths, `current` traversal, repeated slashes, dot segments, PATH lookup, and `posix_spawnp` are forbidden.

Before worker launch, the broker binds the exact physical ancestor inventory for `/`, `/private`, `/private/var`, and `/private/var/db`, including path bytes, device, inode, type, uid, gid, mode, and BSD flags. It then binds every root/runtime/versions/version/interpreter ancestor and leaf, the manifest namespace and leaf, `current` symlink inode/link bytes/parent/resolved target, inventory, and execution closure. Every actual pathname consumed by the executable or Python runtime must be a manifest entry below the direct digest version root or a named immutable Apple dependency.

Revision 9 explicitly broadens the protected-pathname exception: the vendored interpreter, frozen startup files, stdlib, application modules, and data may be pathname-read only from the direct immutable digest version root. They are not claimed to be FD-backed. UID 501 and `_hermesloopa` must be unable to mutate that namespace. Imports outside the exact manifest, user site, PYTHONPATH, plugins, hooks, `.pth`, mutable caches, bytecode writes, protected-tree `dlopen`, and non-Apple dynamic images remain forbidden.

The entrypoint is exact stdin: argv is `[spawn_path, "-I", "-S", "-B", "-"]`. The broker streams the already-held, digest-verified entrypoint bytes to child FD 0 and closes the write end. No `/dev/fd`, script pathname, `-c`, shebang, shell, dynamic bootstrap, or generated executable content is permitted.

## 4. Exact worker FD and environment contract

The complete child FD map is fixed and schema-bound:

- 0: read-only entrypoint pipe;
- 1: worker result/output pipe, write end only;
- 2: bounded diagnostic pipe, write end only;
- 3: challenge pipe, read end only;
- 4: private broker-control socket endpoint;
- 5: retained interpreter FD, read-only;
- 6: retained version-root FD, read-only/search only;
- 7: finalized manifest FD, read-only;
- 8: finalized inventory FD, read-only;
- 9: canonical transaction source FD, read-only.

Every source FD is distinct and duplicated collision-safely. Child descriptors 0 through 9 replace any prior descriptors. Every descriptor numbered 10 or above is closed by explicit file actions, and all newly opened parent descriptors are non-inheritable. The fixed entrypoint consumes transaction source bytes only from FD 9; pathname reopen or per-transaction script embedding is not an allowed substitute. Production certification additionally requires a native or launchd boundary proving close-on-exec-default semantics; Python `/dev/fd` enumeration alone is local prototype evidence, not production closure.

Read roles must have `O_RDONLY`; no worker FD may identify any canonical mutation root. Output/control roles are pipes or the one private socket, never regular files or canonical directories. The environment is exactly `LANG=C`, `LC_ALL=C`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONHASHSEED=0`, `PYTHONNOUSERSITE=1`, and `PYTHONUTF8=1`; no ambient entry is inherited.

## 5. Handshake and broker semantics

The nonce/PID/identity handshake is retained as freshness and transcript binding, not as the source of filesystem isolation. On success, the already non-root worker launcher sends exactly one canonical request frame and then half-closes its write direction; the broker requires EOF before returning a canonical `attestation-only` acknowledgment with no SCM_RIGHTS payload. The root broker treats this transcript only as an input to its later result validation; it never grants a filesystem capability. Missing, duplicate, malformed, replayed, late, missing-or-premature half-close, PID-mismatched, identity-mismatched, extra-record, or post-close data terminates the interpreter child and leaves the broker transaction nonmutating or durably aborted according to the existing journal state.

Before sending any transaction secret or accepting any worker output, the root broker must authenticate the connected AF_UNIX peer against the exact launchd-reported worker PID, effective PID, non-root UID, and GID using Darwin kernel peer-credential readback. UID-only admission is insufficient because another process under the same worker UID could race or impersonate the trusted launchd instance. Python APIs that omit `SOL_LOCAL`/`LOCAL_PEERPID` do not waive this requirement; a verified native or ABI-bound adapter is required.

The worker emits exactly one bounded canonical result bound to the nonce, PID, source digest, runtime manifest/inventory, and transaction UUID. The broker rejects any path or operation field. The broker independently validates result schema, digest, source binding, candidate bytes, size, and transaction state, revalidates the root gate and immutable runtime namespace, and only then performs the one fixed publication transition. No capability can be duplicated, forwarded, or replayed because no mutation capability is transferred.

Child self-report does not prove the loaded executable image. The security boundary instead combines an immutable root-owned execution namespace, exact physical-path/adjacent readback, distinct no-write worker identity, fixed FD/environment contract, broker-side result validation, and broker revalidation before every mutation. Root namespace mutation remains in the trusted computing base and outside the UID-501/worker-compromise guarantee.

## 6. Required RED replacement

The stale revision-8 `before fexecve` row is removed. Revision-9 acceptance requires executable negatives for:

1. worker direct mutation of every canonical sink before and after handshake;
2. writable group/other/ACL access on any mutation ancestor;
3. leaked mutation-root or writable protected-input FD;
4. extra inheritable FD and FD-number collision;
5. relative, `/var` alias, `current`, PATH, `posix_spawnp`, dot-segment, repeated-slash, alternate `argv[0]`, and wrong direct-digest path;
6. physical ancestor, current symlink inode, resolved target, manifest directory/leaf, interpreter ancestor/leaf, and execution-closure drift;
7. entrypoint pathname substitution and protected import namespace replacement;
8. startup under `-I -S -B -` with exact environment and no user site, `.pth`, plugin, bytecode, or external module consumption;
9. handshake replay, PID mismatch, half-close, extra record, duplicate completion, and proof that no FD is attached to the acknowledgment;
10. worker-supplied path/operation/destination/authorization fields and malformed or oversized output;
11. broker result validation failure with zero canonical residue;
12. target-host `_hermesloopa` denial probes against a disposable root and the final canonical metadata readback.

## 7. Acceptance and authority boundary

Revision 9 remains candidate/HOLD until:

- implementation and schema artifacts match this delta;
- every required local negative that does not need system privilege is GREEN;
- controlled target-host identity/permission/launchd probes are authorized and GREEN;
- two independent reviewers bind the same final candidate digest and report P0=0/P1=0;
- exact cutover authority is granted separately.

No prior green revision-8 suite or stale review can certify revision 9.
