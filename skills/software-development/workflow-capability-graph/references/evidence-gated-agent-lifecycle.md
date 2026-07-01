# Evidence-Gated Agent Lifecycle

Scope: use when turning a domain agent (travel, product, offline evidence, workflow executor, etc.) into a lifecycle-governed capability graph rather than a one-off prompt or static plan.

Applicability:
- User asks for project/system-level agent rollout, agent-generation pipelines, dynamic gates, multi-model certification, or coverage of existing agents.
- A vertical agent needs state, evidence, gates, runtime projection, UX cards, observability, ratchet, and retirement boundaries.

Anti-conditions:
- Do not claim true certification from documents, single-agent discussion, or local tests alone.
- Do not treat broad/project/system authorization as permission for external send, publish/deploy/push, destructive actions, payments, credential entry, or broad fan-out without exact target, rollback, and readback.
- Do not save project facts or live runtime facts into global memory.

## Lifecycle stages

1. Intent intake
2. Scenario modeling
3. State model
4. Capability graph
5. Evidence contract
6. Gate template
7. Agent role decomposition
8. Pipeline compilation
9. Simulation / fixture
10. Multi-model certification
11. Runtime projection
12. UX surface
13. Observability
14. Reflection / ratchet
15. Retirement / boundary control

Formula:

```text
Agent = State Model + Capability Graph + Evidence Contract + Gate System + Certification + Runtime UX + Observation + Ratchet + Retirement
```

## Gate taxonomy

- Static gates: hard anchors and global rules, e.g. no night mountain driving, flight/return constraints, memory-write boundary.
- Dynamic gate templates: define required evidence and outcomes but do not pre-decide values.
- DynamicGateManifest: a TTL-bound runtime decision produced from fresh evidence and certification votes.

Dynamic gate states:

```text
draft -> advisory -> certified
      -> blocked / rejected / expired / overridden
```

A `pass` decision is only `certified` when the required independent review coverage exists (for example safety + evidence + arbiter). Otherwise it remains `advisory`. Any blocked vote fails closed.

## Evidence contract

Every claim that can affect a gate needs:

- source type and source ref
- freshness / TTL
- confidence and verification status
- supported claim IDs
- sensitivity and redaction boundary

Dynamic facts (weather, traffic, tickets, parking, live runtime state, user location) need TTL and must expire. Static order/user-confirmed anchors can live in the project SSOT.

## Agent role panel

Use roles as wrappers around capability nodes, not labels:

| Role | Checks |
|---|---|
| Planner | scenario and state coherence |
| Evidence reviewer | source linkage, freshness, missing claims |
| Safety/policy reviewer | hard constraints, authority, side effects |
| Experience/UX reviewer | actionability and user cost |
| Arbiter | final pass/warn/fail/blocked manifest |
| Ratchet | memory/skill/project-SSOT/no-write classification |

## Runtime projection

A lifecycle agent should project decisions into runtime artifacts, for example:

- Handoff lifecycle summary: requested action class, state band, evidence IDs, certification status, authority boundary.
- Live card: current confirmation, next action, latest time/safety gate, fallback, do-not-do.
- Ledger/readback: trace ID, evidence IDs, votes, decision, TTL, user override, outcome.

## Writeback classifier

- Stable user preference/persona -> memory.
- Project facts, live status, booking details, paths -> project SSOT/profile.
- Reusable procedure -> skill/reference.
- Cross-project default behavior change -> ratchet proposal unless directly authorized and validated.
- Temporary state -> no durable write.

If the user corrects an over-broad memory write, undo/replace it and express the lesson as a gate or project rule, not as another broader memory.

## Verification checklist

- [ ] Lifecycle stages are represented or explicitly blocked.
- [ ] Existing agents have coverage rows and blockers; no false global certification.
- [ ] Gates define pass/warn/fail/blocked.
- [ ] Dynamic gates have TTL/freshness and evidence IDs.
- [ ] Certification votes are recorded separately from execution authority.
- [ ] External side effects remain closed unless exact target, rollback, and readback are present.
- [ ] Runtime artifacts/tests prove at least the claimed local slice.
