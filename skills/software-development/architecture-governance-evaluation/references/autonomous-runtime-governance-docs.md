# Autonomous Runtime Governance Documentation Pattern

Scope: use when a system is evolving from scripts/tasks/cron/workers into an automation or autonomous-governance product, and the user asks for a long-term architecture/documentation update rather than another patch document.

Applicability:
- Hermes/agent/control-plane architecture reviews.
- Automation products with cron, gateway, taskpool, mission, worker, dashboard, external-dispatch, or model-certification subsystems.
- Requests such as “再次向上抽象”, “不要补丁式屎山”, “自治理”, “自动化产品要求”, “启动自检/动态自检”.

Anti-conditions:
- Do not create a one-session skill or a new parallel architecture doc for a narrow incident.
- Do not store project progress or transient runtime status here.
- Do not treat model consensus, logs, or pretty dashboards as completion evidence.
- Do not silently open external write, publish, destructive, payment, credential, or broad-fanout authority.

## Core abstraction

Use this class-level target:

```text
Autonomous Runtime Governance Architecture
= Intent Source
+ State Model
+ Capability Graph
+ Evidence Contract
+ Control/Reconciliation Loop
+ Projection Surface
+ Compensation Policy
+ Learning/Ratchet Boundary
```

Recommended runtime name:

```text
ERG Runtime: Evidence-governed Reconciliation Runtime
```

This generalizes cron startup self-check into a broader control-plane problem:

```text
Intent -> Claim -> Execution -> Evidence -> Projection -> Gate -> Compensation -> Ratchet
```

## Design principles

1. Automation is not “do it automatically”; it is “advance to a governed terminal state under evidence, authority, and risk boundaries.”
2. Every automatic action starts from an `IntentRecord`.
3. Every completion claim binds to `EvidenceNode` readback.
4. Every external side effect needs `AuthorityGrant`, `idempotency_key`, receipt, and readback.
5. CapabilityGraph says what can be done; AuthorityGraph says whether it may be done; EvidenceGraph says whether it was done.
6. Agent/worker/model outputs are proposals or advisory evidence, not lifecycle facts by themselves.
7. UI/dashboard/Control Tower are projection surfaces, not canonical fact sources.
8. Startup self-check is a readiness gate; runtime assurance is the ongoing reconciliation loop.
9. Compensation is not blind retry; it is the smallest state-machine repair.
10. All workflows must end in a named terminal state: completed, compensated, skipped, expired, dead_letter, rejected, or manual_required.

## Canonical documentation package

When existing docs are fragmented, create one canonical package instead of adding another local patch doc:

```text
docs/private/autonomous-runtime-governance/
├── 00-index.md
├── 01-vision-and-principles.md
├── 02-current-architecture-map.md
├── 03-target-architecture.md
├── 04-core-domain-model.md
├── 05-control-loop-and-reconciliation.md
├── 06-evidence-ledger-and-closure.md
├── 07-authority-and-side-effect-governance.md
├── 08-runtime-surfaces.md
├── 09-subsystem-mapping.md
├── 10-migration-roadmap.md
├── 11-adr-index.md
├── 12-verification-and-acceptance.md
└── references.md
```

Rules:
- `00-index.md` is the single entry point.
- New ADRs are registered in `11-adr-index.md`.
- New implementation phases go in `10-migration-roadmap.md`.
- New proof criteria go in `12-verification-and-acceptance.md`.
- Old architecture docs get a disposition block instead of being copied into a second truth.

## Existing-doc disposition pattern

Add a small block to old docs rather than rewriting history:

```markdown
> Architecture disposition:
> - Current role: active source | subsystem spec | historical evidence | public derivative
> - Canonical replacement/extension: docs/private/autonomous-runtime-governance/...
> - Do not extend this file with new target architecture; register new decisions in 11-adr-index.md.
```

Suggested dispositions:
- Agent OS SSOT: active source for vision/target model.
- Capability control plane: active subsystem/domain-model source.
- Control Tower long-term plan: active source for projection/operator surface.
- Workflow Kernel migration ADRs: active source for kernel migration and strangler rollout.
- Long boundary-opening ledgers: historical evidence, not future architecture entrypoint.
- Public developer architecture docs: public-safe derivative only.

## Domain model checklist

Unify subsystem-specific terms into these objects:

- `IntentRecord`: source, objective, expected effect, risk class, side-effect expectation, TTL, idempotency key.
- `CapabilityNode`: responsibility, inputs/outputs, side effects, gates, evidence requirements, cannot-prove list.
- `AgentWrapper`: wraps capability nodes; has policy/authority; does not own facts by role name.
- `AuthorityGrant`: exact target, actor, scope, TTL, rollback/readback, allowed side-effect class.
- `ExecutionLease` / `RunRecord`: executor, status, attempts, artifact refs, heartbeat.
- `EvidenceNode`: command/file/API/message/test/screenshot/model/human/ledger evidence with freshness and verification status.
- `GateDecision`: pass/warn/fail/blocked/expired/manual_required with evidence refs.
- `ProjectionRecord`: dashboard/taskpool/mission/gateway/doc projection plus readback status.
- `CompensationRecord`: mark_only/resend/retry/rollback/dead_letter/manual with idempotency and max attempts.
- `ClosureRecord`: terminal state, evidence refs, residual risks, next boundary.
- `RatchetRecord`: memory/skill/project-SSOT/test/no-write classification.

## Reconciliation loop

Map every subsystem through MAPE-K / reconciliation:

```text
Monitor: collect observed state
Analyze: classify divergence
Plan: choose next safe action
Execute: run only authorized action
Knowledge: ledger, evidence, tests, skill/SSOT ratchet
```

Subsystem examples:
- Cron: schedule slot -> IntentRecord; output/artifact/delivery receipt -> Evidence; mark-only/resend/requeue/missed -> Compensation.
- Gateway: inbound message -> Intent; outbound message_id/outbox -> Projection/Evidence.
- Taskpool/Kanban: task candidate -> Intent; proof logs/tests -> Evidence; lifecycle mutation -> AuthorityGate.
- Mission: objective/tick budget -> Intent; stage reports/handoffs -> Evidence/Gates.
- Workers/agent teams: worker output -> proposal artifact; certification/human gate required before lifecycle fact mutation.
- Control Tower/dashboard: projection/cockpit only; canonical facts remain in ledgers.

## Theory map tied to constraints

Use references only when they affect design:

- Cybernetics / Ashby / Stafford Beer -> require sensor/controller/actuator/feedback/boundary modeling.
- Autonomic Computing / MAPE-K -> every autonomous capability must declare Monitor/Analyze/Plan/Execute/Knowledge.
- Runtime Verification -> define safety/liveness properties as monitors, e.g. one external receipt per idempotency key.
- Sagas / compensating transactions -> external failures use compensation tables, not blind retry.
- Transaction processing / WAL -> durable records around crash windows.
- SRE -> separate startup/readiness/liveness/business-completion evidence.
- Leveson STAMP/STPA -> safety is a control-structure problem; authority gates are safety controls.
- Kubernetes reconciliation -> desired/observed divergence is a first-class work object.

## Verification checklist

- [ ] There is a single canonical index for the long-term architecture.
- [ ] Existing architecture docs have disposition roles.
- [ ] Each subsystem maps to Intent/Evidence/Gate/Closure.
- [ ] External side effects have authority, idempotency, receipt, and readback requirements.
- [ ] Model output remains advisory unless tied to observed proof.
- [ ] Projection surfaces are not treated as canonical ledgers.
- [ ] Migration roadmap is staged, reversible, and evidence-gated.
- [ ] Acceptance distinguishes doc-level, projection-level, runtime-level, compensation-level, and production-level proof.
