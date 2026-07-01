# High-risk boundary coverage with disposable canary

## Scope

Use when a user asks to advance an agent/control-plane project to "100% coverage" across high-risk side-effect classes such as scheduler/cron mutation, taskpool or mission lifecycle writes, gateway/external sends, worker spawn/leases, compensation execution, publish/deploy/push, destructive operations, payment/credential entry, or broad fan-out.

## Core lesson

Treat broad class-level authorization as permission to land and read back a **governance coverage matrix**, not as permission to invent real targets. A truthful "100%" claim must say what is covered:

- 100% governance/readback coverage for every named class;
- exact-target, receipt, rollback, and readback requirements for each class;
- no unscoped real side effects;
- explicit execution status per class.

Do not call class-only requests "fully executed" unless each class has an exact target/payload/rollback/readback and the execution actually happened.

## Safe implementation pattern

1. Run local status/route preflight if available; route must remain advisory unless a later exact executor boundary is authorized.
2. Define a fixed boundary catalog with one record per high-risk class. Each record should include:
   - `id`, `label`;
   - `governance_covered=true`;
   - `exact_target_required=true`;
   - `receipt_required=true`;
   - `rollback_required=true`;
   - `readback_required=true`;
   - `executed` and `execution_status`;
   - `minimum_authority` text for the next executable packet.
3. Add tests before implementation:
   - all requested classes are present;
   - coverage percent is 100 only when all classes are represented;
   - unscoped high-risk execution is false;
   - payment/credential entry is `human_secret_gate_only` and `agent_may_type_secret=false`;
   - exact-target classes remain not executed unless an exact target is provided.
4. If destructive coverage is requested without a production target, use only a disposable local canary:
   - create a canary under the project runtime/temp area;
   - copy to `.bak`;
   - delete only the canary;
   - verify absent;
   - restore from backup;
   - compare before/restored sha256;
   - record `production_resource_touched=false`.
5. Generate a report artifact and record it in the project SSOT/profile/ledger.
6. Run focused/full tests, py_compile, and read back the report before claiming coverage.

## Boundary status defaults

Recommended defaults when exact targets are absent:

- scheduler/cron mutation: `exact_target_required`, executed=false.
- taskpool/mission lifecycle write: `exact_target_required`, executed=false.
- gateway outbox mutation/external send: `exact_target_required`, executed=false.
- worker spawn/lease: `exact_target_required`, executed=false.
- compensation execution: `exact_target_required`, executed=false.
- publish/deploy/push: `exact_target_required`, executed=false.
- destructive action outside exact files: `exact_target_required`, executed=false; optional canary smoke may set `canary_delete_restore_verified`, executed=true for the canary only.
- payment/credential entry: `human_secret_gate_only`, executed=false, `agent_may_type_secret=false`.
- broad fan-out: `exact_target_required`, executed=false.

## Pitfalls

- Do not let "coverage percent 100" imply real scheduler/external/payment/deploy execution. Label it as governance coverage unless real exact actions ran.
- Do not infer recipients, deploy environments, production resources, worker nodes, cron jobs, or fan-out channel sets from broad authorization.
- Do not type passwords, API keys, cards, OTPs, seed phrases, or other secrets even if payment/credential entry is listed as authorized.
- A destructive canary smoke proves the destructive boundary mechanics only for the disposable canary; it is not proof of safe deletion of any real resource.
- Preserve unrelated dirty files and commit only the scoped coverage implementation/report.
