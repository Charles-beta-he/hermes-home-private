# High-risk exact execution smoke pattern

Use when the user has explicitly authorized high-risk boundaries (external dispatch, deploy/publish/push, destructive operation) and has also accepted or supplied exact targets. This pattern is for bounded smoke execution, not broad production rollout.

## Applicability

- The user has authorized the high-risk class and supplied exact targets, or explicitly accepted a previously proposed target packet.
- The goal is to prove the boundary with receipts/readback, not to invent new product behavior.
- Operations are scoped to one target each: one message target, one deploy/build target, one destructive target with backup/restore.

## Anti-conditions

- Do not infer an arbitrary contact/channel from “continue”; list available targets and require/consume an exact target packet.
- Do not broaden a Docker image build into `compose up` or production deploy unless the target packet explicitly says so.
- Do not perform destructive work without exact target, backup path, restore command, and verification command.
- Do not convert transient setup/network errors into durable negative claims about tools.

## Execution checklist

1. Preflight routing/policy if the task touches Agent OS, scheduler, taskpool, gateway, publish/deploy, or destructive operations.
2. Restate the target packet internally: target, payload/action, readback, rollback/restore, and blast radius.
3. External dispatch:
   - send to the exact target and record platform receipt/message id;
   - if the primary target times out, do not retry-loop; only use a fallback target that was already in the accepted packet, then record the fallback explicitly.
4. Deploy/publish smoke:
   - keep the selected deploy shape exact (for example Docker image build only vs compose up);
   - when Docker metadata fetch times out, first pull the declared base images individually, then rerun the build;
   - for long builds, run in a tracked background process and wait/poll to completion;
   - read back with `docker image inspect` or the platform’s equivalent receipt.
5. Destructive smoke:
   - backup first;
   - execute the exact destructive action;
   - verify the destructive effect;
   - restore from backup unless the target packet explicitly wants permanent deletion;
   - verify hash/status after restore.
6. Record a durable ledger/stage report with only receipts and boundaries, not a task narrative.

## Verification evidence to report

- External dispatch: target, platform receipt/message id, and any fallback used.
- Deploy/publish: artifact id/digest/tag, inspect/readback output, and whether runtime was started.
- Destructive: target, backup, delete/modify verification, restore verification, and checksum/readback.
- Repo changes: scoped commit/push readback only if the target packet included publish/push.
