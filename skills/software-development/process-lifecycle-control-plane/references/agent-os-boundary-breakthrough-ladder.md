# Agent OS ordered boundary breakthrough ladder

Use this reference when advancing an agent/control-plane runtime through sequential authority rungs after broad project-level authorization. It captures the reusable procedure from the Agent OS control-plane landing: move one boundary at a time, keep neighboring gates explicitly closed, and certify each rung before continuing.

## Applicability

Use when all are true:

- The work is an agent/control-plane or lifecycle system.
- The user has authorized ordered progression / full landing.
- The next steps cross from advisory/read-only into local execution, scheduler, lifecycle write, or external dispatch.
- Each rung can be isolated with exact target, receipt, readback, tests, independent review, and multi-model certification.

Anti-conditions:

- Do not use broad authorization to infer publish/deploy/push, destructive operations, payments, credential entry, or broad fan-out.
- Do not combine multiple new side-effect classes into one unreviewable patch.
- Do not treat model agreement as execution authority; certification is evidence, not permission for a different gate.

## Recommended order

1. **Advisory/readback**
   - Default-off config.
   - Status/doctor/read-only route/report surfaces.
   - Verify no runtime mutation.

2. **Runtime route preflight**
   - Prompt requires local route/status preflight before choosing governed paths.
   - No suggested node auto-execution.

3. **Multi-model/adversarial review preflight**
   - Review-only gate before any execution/lifecycle/external expansion.
   - Independent reviewer + multi-model certification required for later rungs.

4. **Local harness executor**
   - First real executor should mutate only SSOT-local harness state/receipts.
   - Require exact authorization tuple: auth id, intent id, target ref/status, evidence refs, adapter path.
   - Harden path safety: direct-child-only files, reject dot/parent traversal, symlink rejection, descriptor-relative I/O where available, idempotent duplicate readback, rollback/reporting on receipt failure.

5. **Local scheduler heartbeat**
   - Open only no-agent, deliver=local, silent-on-success scheduler jobs.
   - Script writes only SSOT-local heartbeat receipts.
   - Verify cron readback: no external delivery, no lifecycle write-through, no worker side effects beyond the named local heartbeat.

6. **Local taskpool/Kanban lifecycle write**
   - Require exact board, task/idempotency key, intended status/action, evidence, and readback.
   - Smoke with an idempotent local task if safe: create blocked/local task, complete it, read back status and metadata proving no worker spawn and no external dispatch.

7. **Exact external dispatch**
   - Require exact allowlisted platform/target/payload, evidence, receipt, and post-send readback.
   - Smoke should prefer the current origin/home channel unless the user supplies a more specific target.
   - Receipt must record: exact_target, allowlisted, external_dispatch_executed=true, broad_fanout=false, publish/deploy/push=false, destructive=false, payment/credential=false.

8. **Publish/deploy/push or destructive operations**
   - Stop at a DecisionPacket unless the user supplies exact target, environment/remote, command, blast radius, rollback/restore path, and post-action readback.
   - These are not implied by previous external-dispatch authority.

## Per-rung closure checklist

For every rung:

- Add a default-off config key and prompt/readback guidance.
- Enable live config only for the rung being consumed.
- Add enabled/disabled/no-tools tests where applicable.
- Run focused tests and syntax checks.
- Perform the smallest real smoke for that rung.
- Record an SSOT receipt under the project ledger.
- Run independent code/runtime review; fail closed on security concerns or logic errors.
- Run multi-model certification with claim-linked evidence.
- Update project profile, remaining-gates index, progress ledger.
- Commit only scoped repo code changes; do not mix unrelated dirty files.

## Boundary stop packet

When the next rung is publish/deploy/push/destructive/credential/payment or lacks exact target, write a DecisionPacket + ContinuationPacket containing:

- objective and completed evidence;
- confirmed open/closed gates;
- pending action and requested authority fields;
- rollback/escape hatch;
- next verification commands;
- latest commit and SSOT paths.
