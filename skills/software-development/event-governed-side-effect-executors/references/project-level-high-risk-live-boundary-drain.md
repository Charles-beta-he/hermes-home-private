# Project-level high-risk live-boundary drain

## Scope

Use when a user grants broad project-level authorization to continue an internal agent/control-plane project into higher side-effect classes: real subagent/LLM process, taskpool lifecycle mutation, mission stage reports/dispatch-events, cron scheduling, exact private-repo push, exact external dispatch, deploy/publish, and destructive operations.

## Applicability

- The user has already authorized the project as a whole.
- The implementation has prior local receipts/proposals/evidence to consume.
- Some boundaries now have exact targets and rollback/readback, while others are only named by class.

## Anti-conditions

Do not infer arbitrary targets from broad class authorization. These still need exact executable targets:

- External dispatch: platform, recipient/channel, payload, fanout set, and readback.
- Deploy/publish: platform/project/environment/ref, health check, rollback target.
- Destructive operation on non-temp resources: exact resource, backup/restore path, pre/post readback.
- Credential/payment entry: never type secrets; stop at human gate.

## Procedure

1. Run local routing/status preflight if the project has an Agent OS or control-plane route surface.
2. Split the broad authorization into exact smallest executable boundaries.
3. Execute boundaries that are exact and reversible:
   - Spawn a real subagent/LLM process as a bounded smoke. Give it no external/write/destructive authority unless separately needed.
   - Mutate taskpool lifecycle only for an exact task/idempotency key, with transition readback.
   - Append mission stage-report and dispatch event only to an exact mission id, then read recent events/status.
   - Schedule a no-agent local cron heartbeat with `deliver=local`; run it once if needed and read the local receipt.
   - Push only when repo/remote/branch are exact and safe for the user's repo policy; read back `git ls-remote`.
   - For destructive coverage without an exact production target, use a temp-file delete/restore smoke with backup and sha256 readback, and label it as smoke only.
4. Stop, do not improvise, for class-only external dispatch/deploy/destructive requests. Return an intervention packet naming the missing exact target fields.
5. Keep receipts concise and evidence-bound: command output IDs, event IDs, job IDs, branch/ref, file path, sha256, and readback state.

## Pitfalls

- Broad words like “全部授权” open the next exact boundary; they do not supply a recipient, deploy environment, or production resource.
- A subagent process can prove real model execution without inheriting authority to write or send.
- `cronjob.create` requires scripts under `~/.hermes/scripts/` to be referenced by relative filename, not absolute path.
- Taskpool event hooks may claim or route a task under another actor; do not force transitions broadly. If force is used for a self-created exact receipt task, say so and record the reason.
- Mission stage-report success does not imply the mission is unblocked; read `mission status` because unrelated open decisions may remain.
