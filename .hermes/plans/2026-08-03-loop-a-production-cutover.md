# Loop A production cutover — Spec Gate and execution plan

Date: 2026-08-03
State: implementation authorized; production mutation remains digest-bound
Branch: `claude/dreaming-loop-20260801`
Baseline commit: `76ec8f634cf02a1dd0030949946779a86906210b`

## Spec Brief

### Goal

Turn the certified revision-9 hostile-UID broker/worker component candidate into an explicitly versioned revision-10 deployable macOS LaunchDaemon successor, then certify, commit, non-force push, deploy, smoke-test, and retain an exact rollback path.

### Authority received

The user authorized continuous Loop advancement plus push and deploy in the current conversation. This opens local implementation, testing, certification, commit, and non-force push to the existing branch. System deployment must still consume the final revision-9 exact authorization tuple because the protocol itself requires a digest-bound one-time grant; credential/password entry remains a human gate.

### Non-goals

- No weakening from distinct-UID launchd activation to same-UID or direct root spawn.
- No mutation FD, canonical writable pathname, shell, shebang, `/dev/fd`, `PATH`, `posix_spawnp`, user-site, plugin, or mutable-runtime fallback.
- No claim that launchd configuration/unit tests equal target-host end-to-end proof.
- No password, secret, or credential entry by the agent.
- No force push or deployment to any host other than this macOS host.

### Source facts and boundaries

- macOS 26.5.2, arm64; Xcode clang is available.
- Non-interactive sudo is unavailable.
- `_hermesloopa`, `/private/var/db/hermes-loop-a`, and the worker LaunchDaemon are absent at intake.
- Revision 9 selects a launchd-owned private AF_UNIX/SOCK_STREAM listener. The root broker connects, launchd activates a distinct-UID worker, the broker binds launchctl PID to kernel peer PID/UID/GID, and transfers six read-only SCM_RIGHTS roles.
- Independent review and a disposable Darwin kernel probe confirmed this topology is feasible, including connect-before-accept peer-PID binding.
- Production composition exposed revision-9 contradictions: the version-root descendant rule, FD 4 direction, outer-bootstrap semantics, and missing candidate skill-context binding. These are resolved only through the explicit revision-10 delta; revision 9 is not silently reinterpreted.
- The committed candidate contains enforcement components but no production installer, broker CLI, worker entrypoint, runtime-bundle builder, or system integration harness.

### Business rules and invariants

1. Root is the sole canonical mutation authority.
2. `_hermesloopa` has no write/create/link/unlink/rename/chmod authority on canonical state or immutable runtime.
3. The launchd worker authenticates a root peer; the broker authenticates the exact launchd-reported PID plus UID/GID.
4. Only the six revision-9 read-only descriptor roles cross the outer boundary.
5. Worker output is bounded untrusted data; it cannot select operation, path, destination, authorization, transaction, or state transition.
6. The vendored runtime and entrypoint are content-addressed, root:wheel, non-writable, manifest-bound, and read back before launch.
7. Account, layout, plist, bootstrap, smoke, and rollback are idempotent or fail closed with receipts.
8. Deployment preserves the prior active version and plist until smoke succeeds; rollback restores that exact predecessor or removes an initial install.
9. Any candidate-byte edit invalidates prior tests/reviews and requires a successor freeze.

### Negative cases

- Missing/wrong worker account UID/GID; worker unexpectedly root.
- Socket path, plist, runtime, or any ancestor writable by worker/UID 501/group/other or through ACL.
- Wrong/extra/missing/aliased/writable SCM_RIGHTS role.
- launchctl PID absent, duplicated, stale, or different from kernel peer PID.
- Worker inherits FD >=10 or a mutation-root identity.
- Runtime/manifest/inventory/entrypoint digest or pathname identity drift.
- Cold-start timeout, crash before result, malformed/oversized result, replay, duplicate completion.
- Smoke failure leaves final scheduler enabled or destroys the predecessor.
- Rollback target identity differs or rollback is not idempotent.

### Evidence required

- RED then GREEN focused tests for every new production surface.
- Full protected suite with non-zero test inventory; compile/static checks.
- Disposable-root metadata and denial matrix; real `_hermesloopa` denial matrix after provisioning.
- launchctl plist parse/bootstrap/kickstart/print PID readback.
- Kernel peer PID/UID/GID readback on the actual activated connection.
- Inner-child FD inventory and exact environment readback.
- Cold-start, success, failure, crash/replay, cleanup, and rollback probes.
- Frozen candidate digest and two independent current-digest P0=0/P1=0 reviews.
- Staged-tree identity, commit/tree readback, non-force remote readback.
- Final exact deploy tuple, one-time authorization receipt, deployment receipt, live smoke receipt, and rollback receipt/readiness proof.

## Objective model and chosen path

Success means an actual launchd-activated `_hermesloopa` worker participates in one broker-owned transaction on this host, with identity/FD/denial/runtime evidence and an executable rollback. The principal constraints are the protocol's exact digest-bound authorization and the unavailable non-interactive sudo path.

Viable paths:

1. launchd-owned Unix listener plus SCM_RIGHTS over the accepted connection — chosen; this is revision 9.
2. coordinator-created socketpair transferred into launchd — rejected; no proven public launchd descriptor-import primitive and not required by revision 9.
3. root direct spawn with credential drop — rejected by revision 9.
4. same-UID prototype — component test only, forbidden for cutover.

## Dependency-ordered implementation slices

1. P1 production contracts: exact paths, labels, account identity, runtime layout, plist, commands, receipts, rollback model.
2. P2 runtime builder: deterministic content-addressed runtime closure, manifest/inventory, immutable metadata plan, byte-readback verification.
3. P3 worker service entrypoint: launch_activate_socket, exact identity/environment/FD preflight, one bounded session, deterministic exit.
4. P4 broker activation client: root preflight, connect-trigger activation, bounded launchctl PID acquisition, peer cross-binding, six-FD send, result validation.
5. P5 installer: plan/apply/verify/rollback commands; account/layout/plist/bootstrap operations through exact argv without shell; write-ahead receipts.
6. P6 disposable integration harness: fake root plus subprocess identity simulations; fault-injection and denial matrix.
7. P7 target-host integration: provision account/root/runtime/plist; real launchd/peer/FD/denial/cold-start/crash/smoke/rollback evidence.
8. P8 converge: freeze, dual current-digest review, commit, non-force push, exact deploy authorization, deploy, smoke, final readback.

## Risk and stop gates

- Local edits/tests: reversible, proceed continuously.
- Commit/non-force push to the named branch: explicitly authorized, proceed after current-tree certification.
- Root account/filesystem/LaunchDaemon mutation: production-sensitive; execute only against the final exact target/digest/rollback tuple. Because sudo requires interactive credentials, stop at a human-executed exact command if non-interactive authority remains unavailable.
- Any request for password/credential entry: stop; never type it.

## Converge matrix

| Claim | Code/test evidence | Runtime evidence | State |
|---|---|---|---|
| Deployable exact bundle | pending | pending | OPEN |
| Distinct-UID launchd activation | pending | pending | OPEN |
| Peer PID/UID/GID cross-binding | existing component tests; production wiring pending | pending | OPEN |
| Six read-only roles/no mutation FD | existing unit tests; production wiring pending | pending | OPEN |
| Hostile UID denial | local mocks only | pending | OPEN |
| Cold-start/crash/replay cleanup | partial unit tests | pending | OPEN |
| Rollback | protocol docs only | pending | OPEN |
| Current-digest certification | v9 predecessor commit certified; production successor pending | n/a | OPEN |
| Commit and remote parity | predecessor only | successor pending | OPEN |
| Production smoke | none | pending | OPEN |
