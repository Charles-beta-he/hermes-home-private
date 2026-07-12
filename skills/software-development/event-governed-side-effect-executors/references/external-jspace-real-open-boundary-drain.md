# External J-space real-open boundary drain

## Scope

Use when a user asks to move an agent/control-plane feature from projection/advisory mode toward “全部真实打开”, especially after a local evidence/workspace layer already exists.

This is a class-level pattern for consuming broad authorization into exact, reversible, evidence-backed side-effect boundaries without inventing missing live targets.

## Applicability

- A local projection/evidence/gate layer exists and has tests/readback.
- The user authorizes continuing beyond read-only/projection mode.
- Some side-effect classes have exact local targets available, while others are only named by class.
- The system has a canonical lifecycle surface such as taskpool/Kanban/mission and local scheduler/cron.

## Anti-conditions

Do not use this to infer or fabricate:

- external recipients/channels/payloads;
- deploy environments, remotes, branches, or rollback refs;
- production destructive resources;
- payment targets, credentials, OTPs, keys, cards, passwords, or seed phrases;
- broad fan-out channel sets;
- worker/subagent budgets or write authority.

If those are absent, open governance/readback coverage and stop that class at `exact_target_required`.

## Procedure

1. Run advisory route/status preflight first if the control plane has one. Treat it as routing evidence only.
2. Split broad authorization into a boundary matrix with one row per high-risk class:
   - taskpool/mission lifecycle write;
   - scheduler/cron write;
   - worker/subagent spawn;
   - external dispatch/send;
   - publish/deploy/push;
   - destructive operation;
   - payment/credential entry;
   - broad fan-out.
3. Execute only exact and reversible boundaries:
   - **Taskpool lifecycle write-through:** create or use one exact disposable task/idempotency key, transition through the normal lifecycle with accepted evidence prefixes, then read back the task file/status/proof log.
   - **Local no-agent scheduler:** create a one-shot `deliver=local`, `no_agent=true` heartbeat that writes a receipt; run/read back receipt and cron output. Keep it success-silent or local-only.
   - **Destructive canary:** create a disposable local canary under the feature artifact directory, copy to `.bak`, delete only the canary, verify absent, restore, compare sha256, and record `production_resource_touched=false`.
4. For classes without exact targets, record `governance_covered=true`, `executed=false`, and a precise `execution_status`, e.g. `blocked_missing_platform_target_payload`, `human_secret_gate_only`, or `blocked_missing_repo_remote_env_ref_rollback`.
5. Generate a durable `real_open_matrix.json` / equivalent report with:
   - coverage type;
   - governance coverage percent;
   - `unscoped_high_risk_execution=false`;
   - per-class exact target/readback/rollback requirements;
   - execution receipts or blocked reasons.
6. Update the project SSOT/progress ledger with claim-linked evidence labels:
   - `task_record:` exact task path;
   - `proof_log:` line/section containing transitions;
   - `lifecycle_readback:` status and file readback;
   - `command:` test output;
   - `artifact:` matrix/closure packet;
   - `rollback:` revert/canary restore instructions;
   - `readback:` final dashboard/closure packet.
7. Commit scoped code/docs separately from volatile runtime evidence when hooks reject evidence bundles as insufficient. If committing evidence artifacts, make sure they are intentionally part of the proof packet and include hook-recognized evidence labels.

## Verification checklist

- [ ] Unit tests cover rejection of task mismatches and invalid evidence prefixes.
- [ ] Exact taskpool task readback shows expected lifecycle transitions and final status.
- [ ] Cron heartbeat receipt says local-only and all external/deploy/destructive/payment flags are false.
- [ ] Destructive canary hash before/after restore matches and production resource touched is false.
- [ ] Dashboard/control-room readback reflects real local mutation truthfully, e.g. `taskpool_lifecycle_write_executed=true` only after real write-through.
- [ ] External dispatch, publish/deploy/push, credential/payment, worker spawn, and broad fan-out remain blocked unless exact target packets exist.
- [ ] Final language distinguishes “governance coverage 100%” from “all high-risk effects executed”.

## Pitfalls

- Broad words like “全部真实打开” open only the next exact safe boundary; they do not provide recipients, deploy refs, worker budgets, or production resources.
- Do not leave stale negative claims in closure packets after a real local boundary opens. Update `scope`, `negative_evidence`, and `excluded_claims` based on event/readback evidence.
- Auto-close hooks may advance `review -> done` after proof-gated evidence; read back the task file before assuming the explicit command performed every transition.
- A failed no-op transition after an auto-close is not proof of failure; record it as a no-op/mismatch event and rely on task file readback.
- When helper CLIs accept `--event-json` as “JSON object or path”, prefer writing long event payloads to an artifact file and passing the path. Inline JSON can be interpreted as a filesystem path first and hit OS filename-length errors before JSON parsing; the durable event artifact is also better evidence.
- If an exact local runtime-router slice is authorized, make it tiny and class-level: add a deterministic conflict/route pattern plus focused tests, then append a runtime-router event and regenerate closure so `excluded_claims` no longer says `not_integrated_with_runtime_router`.
- Treat external dispatch authorization without platform/target/payload/readback as a boundary preflight, not a send. Write a receipt with `send_executed=false`, `token_read=false`, and `blocked_missing_platform_target_payload`; do not infer the current CLI origin as a delivery channel.
- Do not store or print secrets in cron receipts, external payload summaries, or side-effect matrices.
