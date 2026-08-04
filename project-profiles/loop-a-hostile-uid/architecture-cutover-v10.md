# Loop A Darwin Hostile-UID Cutover Architecture (v10)

Status: local reversible candidate; production host mutation requires root password and exact apply of the deployment plan.

## Goal
Ship a fail-closed Darwin activation path for Loop A:
- distinct non-root worker UID/GID `_hermesloopa` / 309
- root-owned production tree under `/private/var/db/hermes-loop-a`
- digest-bound vendored CPython runtime archive
- LaunchDaemon worker + root broker with exact FD/attestation contracts
- human-executable apply/verify/rollback plan with receipts

## Non-goals
- No silent sudo password entry
- No force-push
- No host mutation inside unit tests
- No claim of production smoke until launchctl/readback succeeds

## Design surfaces
- `scripts/loop_a_protected/darwin_runtime_bundle.py` — immutable runtime packaging
- `scripts/loop_a_protected/darwin_installer.py` — pure planner/composer
- `scripts/loop_a_protected/darwin_account.py` — exact dscl account contract
- `scripts/loop_a_protected/darwin_native_spawn.py` + `native/loop_a_darwin_spawn.c`
- `scripts/loop_a_protected/darwin_root_broker_service.py` / `darwin_worker_service.py`
- `scripts/build_loop_a_darwin_*_artifact.py` — local artifact writers

## Gate readback
- Full protected suite: 417 passed
- Focused Darwin slice: 108 passed
- Freeze digests: `docs/private/evidence/loop-a-hostile-uid-v10/cutover-freeze-20260804.json`
- Host preimage: account/plists/root absent; UID/GID 309 unused
- Deploy blocked until interactive root auth is available

## Rollback
- Fresh-install rollback boots out services, removes plists/account/group, rmdirs production root in reverse order
- Source rollback: `git revert` of this commit on branch `claude/dreaming-loop-20260801`
