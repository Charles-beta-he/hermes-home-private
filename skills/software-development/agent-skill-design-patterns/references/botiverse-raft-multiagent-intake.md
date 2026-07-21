# Botiverse Raft — Multi-Agent Collaboration Intake

Scope: domain-level reference for human/agent collaboration planes, task claims, runtime wakes, and evidence-aware multi-agent coordination. Source-specific facts stay in this bounded intake and are not global defaults.

Applicability: use when designing a visible multi-agent workspace, converting conversations into governed tasks, coordinating eligible agents by claims, or connecting an external runtime through a wake/pull bridge.

Anti-condition: do not use this reference to claim that a specific product has a public intelligent allocator, to copy unlicensed source, to grant agents broader authority, or to replace exact-source verification with popularity claims.

Falsifier: narrow these patterns if atomic claims do not prevent duplicate work, channel eligibility causes systematic misrouting, visible collaboration artifacts add more synchronization cost than evidence value, or metadata-only wake/pull cannot meet the target latency and reliability contract.

## Source boundary

- Likely project: Botiverse Raft, product at `app.raft.build`, docs at `docs.raft.build`.
- Public docs repo: `https://github.com/botiverse/raft-docs`.
- Docs commit: `19bce24c6aed7b5dbe1ccc4a71d6cd4e42801c15`.
- External runtime repo: `https://github.com/botiverse/raft-external-agents`.
- External runtime commit: `72c31894f933b9aa9243195d038d66ee79589593`.
- Agent app scaffold repo: `https://github.com/botiverse/create-raft-app`.
- Agent app scaffold commit: `21a01daeeffed2a7136e0b30275543c039f007d1`.
- OAuth consumer sample: `https://github.com/botiverse/raft-survey-sample` at `3f4b6f6c87efdc623dc989bd268a94a42d2c6bb7`.
- No public `botiverse/raft` repository was accessible at inspection time.
- The docs, external runtime, and survey sample declare no repository license. `create-raft-app` package metadata declares MIT but the repository has no standalone license file. Treat source-specific material as reference-only unless rights are independently resolved; do not copy implementation text or code into Hermes.
- Reproducible snapshots: `runs/raft-public-reference-review-20260721/`.

Local verification:

- External runtime: typecheck passed; 32/32 tests passed; production bundle built.
- Documentation: VitePress build passed; generated agent-artifact freshness check passed.
- Agent app scaffold: 14/14 tests passed, all six templates scaffolded and built, conformance passed, package dry-run succeeded.
- OAuth consumer sample: typecheck passed; 282/282 tests passed.
- These checks validate only the public repositories, not the private collaboration server, allocator, event ingress implementation, or assignment logic.

## What the public evidence supports

The documented collaboration flow is:

```text
human/agent conversation
  -> top-level message becomes a task
  -> task metadata: channel-local number + status + one optional owner
  -> agent attempts a claim before work
  -> progress/results stay in the task thread
  -> completion advances to in_review
  -> human/team approval advances to done
```

The public docs also describe multiple agents in shared channels, channel membership as a coarse routing boundary, role-shaping through descriptions and accumulated context, large-goal decomposition into independent subtasks, one-owner claims, Member/Admin separation, separate workspaces, and selectable runtimes.

The public code demonstrates the external runtime bridge, not the central task allocator.

## Reusable patterns

### 1. Collaboration plane instead of hidden orchestration

Treat agents as visible participants in the same channels, threads, task board, and review flow as humans:

```text
conversation = intent/context
message task = commitment
thread = work log
status = lifecycle projection
owner = single responsibility holder
board = team-level current-state view
```

This makes ownership, progress, review state, and handoffs inspectable instead of hiding them behind subagent spawning.

### 2. Route through context surfaces before adding a scoring router

Use a routing hierarchy:

```text
stage 1: eligibility by workspace/channel/capability/authority
stage 2: atomic claim among eligible actors
stage 3: explicit assignment or scored arbitration only when contention requires it
```

Do not label this “intelligent assignment” unless a policy, feature extractor, scoring function, decision record, or evaluable model route is evidenced.

### 3. Task = message + minimal lifecycle metadata

Attach tracking metadata to the source message and keep detailed work in its thread. This preserves provenance and reduces synchronization surfaces.

```yaml
source_message_id: required
channel_id: required
sequence_number: channel-local
status: todo|in_progress|in_review|done|closed
owner_id: nullable
thread_id: required
```

### 4. Atomic claim is the duplicate-work primitive

One-owner semantics matter more than elaborate team metaphors:

```text
claim(task, actor)
  succeeds only if owner is empty and task is claimable
  records actor + timestamp + claim version
  returns authoritative post-state
```

A loser must stop or choose another task. Add lease/stale-claim reconciliation for crash recovery; the public docs do not prove that the source product implements leases.

### 5. Separate decomposition from execution authority

Let an agent propose subtasks, then review the split before execution:

```text
goal -> proposed DAG -> dependency/overlap review -> approved runnable frontier -> claims
```

This avoids parallelizing overlapping or incorrectly scoped work merely because agents are available.

### 6. Make review a lifecycle state

Keep `in_review` distinct from `done`. Bind the transition to fresh evidence for the exact task slice; do not infer approval from an agent saying “finished.”

### 7. Identity and authority are orthogonal to capability

An agent may prepare a privileged action without executing it:

```text
can_reason_about(action) != can_execute(action)
capability != authority
proposal artifact != side-effect receipt
```

### 8. Content-free wake, agent-owned pull

Transport only wake metadata. Keep message bodies and cursor state out of the injection adapter; the awakened agent pulls authoritative content through an authenticated tool:

```text
bridge -> authenticated metadata-only wake -> visible runtime notice
agent -> authenticated pull -> message body + cursor semantics
```

Success means the notice entered, or is durably queued to enter, visible model context—not merely that an endpoint accepted bytes.

### 9. Reliability follows signal semantics

Use distinct contracts:

- Behavioral wake: at-least-once-until-consumed, with dedup and reconciliation.
- Observational telemetry: at-most-once, bounded, loss-tolerant, with explicit drop counts.

Do not give telemetry the same reliability budget as control signals, and never let reporting block agent work.

### 10. Runtime adapters expose provenance and supervision

Useful adapter controls include:

- per-session token on loopback;
- explicit profile provenance and fail-closed conflicts;
- spawn and attach modes;
- child-process state projection;
- exponential restart backoff and stable-run reset;
- bounded telemetry queue with visible loss;
- closed-schema validation and capped content;
- shutdown cleanup and bounded kill escalation.

These controls do not prove central routing quality.

## Claim discipline at the inspected snapshot

- Human/agent collaboration product: supported by public docs and bridge code.
- Agents divide work: supported as a documented subtask, context, and claim workflow.
- Task routing: supported only as coarse channel/context eligibility plus claim coordination.
- Intelligent assignment: not supported by public source evidence; no public allocator/scoring/model-routing implementation was found.
- Latest version 1.4: unsupported. Public package versions were docs `0.1.0`, repository root `0.1.0`, and channel plugin `0.3.1`; no public release/tag established `1.4`.
- 230k+ attention and viral in 17 hours: unverified social metrics, not architecture evidence.

## Deepened public evidence: agent-facing app boundary

Scope: source-specific evidence stays in this bounded intake; derived contracts below are class-level only. Applicability: agent-facing app manifests, third-party fact ingress, service actions, and local CLI credential boundaries. Anti-condition: do not infer private server internals, runtime authority, or license rights from these public scaffolds.

A second public repository, `botiverse/create-raft-app`, exposes a maintained scaffold and conformance model for Raft-native applications:

- commit: `21a01daeeffed2a7136e0b30275543c039f007d1`;
- package version: `0.2.0`;
- package metadata declares MIT, but the repository has no standalone `LICENSE` file;
- 14/14 Node tests passed, including scaffold-and-build checks for all six templates;
- its conformance suite passed;
- a public OAuth consumer sample at `botiverse/raft-survey-sample` commit `3f4b6f6c87efdc623dc989bd268a94a42d2c6bb7` passed typecheck and 282/282 tests, but declares no license.

These sources do not reveal the private multi-agent allocator. They do add evidence for capability projection, external facts, identity boundaries, and agent-specific credential isolation.

### 11. Manifest is capability metadata, never authority

An agent-facing manifest may declare:

```yaml
execution_mode: http_api | local_cli
actions: product-semantic operations
context_check: current service/account context
credential_boundary: per-agent state rules
positive_capabilities: what the adapter supports
negative_capabilities: what it explicitly cannot do
```

Keep these relations explicit:

```text
manifest validity != installation
installation != grant
role/app type != authority
conversation role != authority
capability discovery != runtime readiness
```

The inspected conformance code rejects `appType` and `conversationRole` when they are used as authority sources. Reusable authority sources remain registration, grant, scope, review, and runtime permission.

### 12. Negative capabilities are executable review inputs

A capability contract should not only say what it can do. It should explicitly block adjacent surfaces such as:

- reading or sending collaboration messages;
- using host-user credentials;
- exposing tokens or raw identity profiles;
- creating custom privileged action cards;
- accepting third-party action requests;
- executing shell fragments from a remote manifest.

Validate positive and negative capabilities together. A template that gains a new capability without revisiting its negative set should fail review.

### 13. External events are facts, not commands

Model third-party agent ingress as a typed fact envelope:

```yaml
source_type: third_party_app
app_identity: required
target_agent: exactly one
resource: exact server + agent-inbound audience
kind: event | notification
summary: bounded
payload: structured, bounded, inert data
payload_hash: required
external_event_id: stable retry key
ttl: bounded
```

Required flow:

```text
declared non-default scope
  -> one-agent access request
  -> resource-bound short-lived token
  -> bounded event validation
  -> idempotency check
  -> neutralize mention/ref/control-shaped text
  -> async queue
  -> provenance-preserving delivery
```

The payload remains untrusted data even after authentication. It may inform an agent that a meeting started; it does not authorize joining the meeting. Reserve command or action-request kinds rather than letting callers encode them inside free text.

### 14. Scope, target, resource, idempotency, and TTL form one ingress contract

Any one control is insufficient:

- Scope limits event kind.
- Target binds one agent.
- Resource binds the selected server and ingress audience.
- Idempotency prevents duplicate delivery under retry.
- TTL prevents stale facts from becoming current triggers.
- Payload hash supports evidence and readback.
- Provenance keeps the app distinct from human, agent, and system actors.

Treat `202 queued` as accepted asynchronous work, not delivered or consumed work. A deduplicated retry should return the original event identity rather than enqueue again.

### 15. Use product-semantic actions, not route mirrors

Expose `summarize-note`, not every internal notes endpoint. Product-semantic actions make install review, authority review, audit logs, and future compatibility understandable.

At invocation time:

```text
discovered action
  -> installed/granted action
  -> validate parameters
  -> re-check service-local authorization
  -> execute product operation
  -> structured result/error + receipt
```

The service remains responsible for its own authorization. Agent login proves identity and selected server context; it does not replace app policy.

### 16. Per-agent credential state is useful but not a full sandbox

For local CLI adapters, isolate:

```text
HOME
XDG_CONFIG_HOME
XDG_DATA_HOME
credential file path
```

per agent, and invoke a bare command with argv rather than a shell fragment. Preserve stdout/stderr and child exit status.

This prevents accidental reuse of the host user's global login, but it does not prove filesystem, network, process, or secret-exfiltration isolation. State that boundary explicitly.

### 17. Separate identity, session, workspace, and process lifecycle

A persistent Agent identity should survive ordinary process and session resets:

| Operation | Process | Runtime session/context | Workspace/memory | Identity/membership |
|---|---|---|---|---|
| restart | replaced/resumed | preserved | preserved | preserved |
| session reset | restarted/fresh | cleared | preserved | preserved |
| full reset | restarted/fresh | cleared | cleared | preserved |
| stop | stopped | retained by policy | preserved | preserved |
| delete | removed | removed | cleaned | removed; historical messages remain |

Do not use one overloaded `reset` operation. Bind destructive reset/delete transitions to human authority and present their exact preservation scope before execution.

### 18. Evidence ladder for external-agent claims

Use these levels:

```text
L0 third-party promotion
L1 product documentation
L2 public adapter/scaffold code
L3 pinned local tests/build
L4 authenticated product runtime readback
L5 core implementation + concurrency/failure tests
```

A claim may not inherit the highest level available elsewhere in the system. For example, an L3 runtime-adapter test does not upgrade private task claiming or intelligent allocation beyond L1.

### 19. Bind the complete principal tuple before app authorization

A token that is valid at the issuer is not yet an app-authorized principal. Preserve and validate:

```text
issuer/provider
+ client_id or audience
+ server_id/resource
+ stable sub
+ strict principal type
+ granted scopes
```

Keep mutable display fields separate:

```text
preferred_username
name
server slug
avatar
```

Do not use mutable handles or slugs as database identity or audit actor keys. Reject missing resource IDs and unknown principal types rather than defaulting them to a broader category.

Required gate sequence:

```text
token verification
  -> client/audience match
  -> resource/server match
  -> stable subject present
  -> principal type enum match
  -> required scopes present
  -> app-local authorization
```

### 20. Scaffold conformance needs semantic negative cases

Tests that confirm `userinfo` appears in generated code, that a template builds, or that arbitrary non-empty Bearer strings are no longer accepted do not prove token binding. Add negative cases for:

- a valid token minted for another client/audience;
- a token bound to another server/resource;
- missing `sub` or `server_id`;
- unknown or missing principal type;
- missing or excessive scopes;
- mutable handle/server-slug changes after account creation;
- callback codes not bound to the locally initiated login flow;
- stale/revoked token behavior and session-cookie cleanup.

Passing scaffold tests while these cases are absent is a coverage gap, not proof of an exploitable production vulnerability. Keep exploit claims blocked until authenticated cross-client and cross-resource runtime tests exist.

### 21. Validate protocol discovery as a typed document

A discovery probe must check all of:

```text
expected endpoint
+ 2xx status
+ JSON content type
+ schema/issuer fields
+ endpoint origin policy
```

An SPA fallback can return `200 text/html` for an unknown `/.well-known` path. Never treat status alone as successful OAuth, OpenID, manifest, or agent-protocol discovery.

Public deployed bundles are a separate evidence channel. They can reveal deployed asset hashes, compatibility aliases, and candidate protocol strings, but minified strings are not canonical semantics and do not prove authenticated server behavior.

### 22. Govern brand and wire-protocol migrations separately

A product rename must not silently rename protocol identifiers. Track:

```text
canonical product name
canonical current wire IDs
legacy aliases
compatibility owner
usage telemetry
removal gate and date
```

Keep aliases at parsing/adaptation boundaries and emit canonical names in new outputs. Residual legacy strings in bundles or robots metadata prove migration residue, not necessarily incorrect runtime behavior.

Historical documentation corrections should become regression tests when they change semantics, especially:

```text
mention != delivery
delivery != wake
restart != session reset
identity != runtime session
```

## State and failure model

| Surface | Success means | Does not mean | Required recovery/readback |
|---|---|---|---|
| Wake endpoint | notice injected or durably queued into visible context | message consumed | retry/dedup + runtime state |
| Message pull | authoritative content fetched | task accepted | cursor/read state |
| Task claim | authoritative owner is caller | lease is crash-safe | claim version + stale reconciliation |
| Agent result | result posted and task moved to review | accepted/done | exact review evidence |
| Inbound event | queued or deduped under one event ID | delivered, consumed, or authorized action | event ID/hash/expiry/status |
| Manifest | syntax and contract valid | installed, granted, reachable, or safe | install/grant/runtime probes |
| App action | service operation returned structured result | product acceptance | service receipt + domain readback |
| Activity telemetry | observation accepted into bounded queue | complete behavioral history | dropped count and queue health |
| Reset | declared state layers changed | every state/cache was removed | post-state of process/session/workspace/identity |

## Hermes delta map

Already strong in Hermes:

- taskpool lifecycle, claim/lease/reconciliation;
- AuthorityGrant and exact-target side-effect gates;
- evidence/readback and `review != done`;
- gateway supervision and bounded telemetry;
- capability graphs with `cannot_do`.

Incremental patterns from this source set:

1. First-class message-to-task provenance projection.
2. Channel/context eligibility as a pre-router before scored assignment.
3. Human-reviewed decomposition frontier before fan-out.
4. Formal evidence levels that prevent adapter tests from upgrading private-core claims.
5. Agent app manifests with positive and negative capability conformance.
6. Third-party fact ingress that is structurally unable to become command authority.
7. Resource-bound one-agent tokens combined with idempotency, TTL, payload hash, and inert rendering.
8. Product-semantic action names plus service-local authorization recheck.
9. Per-agent HOME/XDG credential isolation explicitly labeled weaker than a sandbox.
10. Reset contracts that state which of process, session, workspace, identity, and membership change.
11. Canonical principal binding across issuer, client/audience, resource, stable subject, strict type, and scopes.
12. Separation of mutable presentation fields from database and audit identity.
13. Semantic negative-case conformance for cross-client/resource tokens and callback binding.
14. Typed discovery validation that rejects SPA fallback HTML and wrong endpoint placement.
15. Explicit legacy wire-alias governance during product renames.

## Hermes adaptation

1. Project messages into tasks without losing source provenance.
2. Use eligibility filters and atomic claims before complex routing algorithms.
3. Require an approved task DAG before broad parallel execution.
4. Keep `in_review` separate from `done` and bind approval to exact evidence.
5. Separate agent capability, identity, and authority.
6. Use metadata-only wakes and authoritative pull for external runtime integrations.
7. Match reliability guarantees to signal semantics.
8. Surface supervision state, restarts, drops, and provenance as first-class evidence.
9. Treat app/skill manifests as discovery metadata; require separate install, grant, scope, review, and runtime-permission gates.
10. Validate `negativeCapabilities` together with positive capabilities.
11. Define third-party ingress as typed facts whose authenticated payload remains inert, untrusted data.
12. Bind ingress jointly to scope, exact agent/server resource, idempotency, TTL, hash, provenance, and neutralized rendering.
13. Separate event accepted, queued, deduped, delivered, consumed, and acted states.
14. Prefer product-semantic actions and re-check authorization in the owning service.
15. Use per-agent HOME/XDG credential state while describing it honestly as weaker than an OS sandbox.
16. Model process, runtime session, workspace/memory, identity, and membership as separate state layers.
17. Give restart, session reset, full reset, stop, and delete distinct contracts and readbacks.
18. Attach claim-level evidence locally; do not let L3 evidence on one adapter upgrade an L1 private-core claim.
19. Bind authenticated principals to issuer, expected client/audience, server resource, stable subject, strict type, and scopes before app-local authorization.
20. Keep mutable handles, names, slugs, and avatars out of canonical account and audit keys.
21. Make conformance fail on cross-client/resource tokens, missing identity fields, unknown types, scope mismatch, and unbound login callbacks.
22. Require typed discovery documents; reject 200 HTML fallbacks and minified-bundle hints as canonical protocol evidence.
23. Keep legacy aliases at compatibility boundaries with telemetry and an explicit removal gate.

## Verification checklist for derived systems

- [ ] Every task points to its source message/thread.
- [ ] Claim is atomic and duplicate-safe under concurrency.
- [ ] Stale owners/claims have a lease or reconciliation path.
- [ ] Routing claims identify eligibility inputs and, if scored, expose decision evidence.
- [ ] Proposed decomposition is checked for overlap and dependencies before fan-out.
- [ ] `in_review -> done` requires fresh approval/readback.
- [ ] Capability and authority are modeled separately.
- [ ] Manifest conformance checks positive and negative capabilities and grants no authority by itself.
- [ ] Third-party event scope is non-default, exact-targeted, resource-bound, bounded, idempotent, expiring, hashed, and provenance-preserving.
- [ ] Event payload is rendered as inert data and cannot encode action authority.
- [ ] Accepted, queued, deduped, delivered, consumed, and acted are distinct states.
- [ ] Product-semantic actions re-check service-local authorization and produce a readback receipt.
- [ ] Local CLI uses per-agent credential state and does not claim filesystem/network sandboxing without proof.
- [ ] Reset/readback explicitly covers process, session, workspace/memory, identity, and membership.
- [ ] Wake transport carries no untrusted content bodies.
- [ ] Wake success proves visible-context injection or durable queueing.
- [ ] Control signals and telemetry use explicit, different delivery semantics.
- [ ] Runtime child state, restart count, queue loss, and profile provenance are observable.
- [ ] Authenticated principals bind issuer, expected client/audience, server resource, stable subject, strict type, and required scopes.
- [ ] Mutable handles, names, slugs, and avatars are not canonical account or audit identity.
- [ ] Conformance includes cross-client/resource tokens, missing identity fields, unknown principal types, scope mismatch, and callback-binding negatives.
- [ ] Protocol discovery validates endpoint, status, JSON content type, schema/issuer, and origin policy; SPA fallbacks fail.
- [ ] Legacy wire aliases are isolated, observable, and have an explicit removal gate.
- [ ] Every architecture claim names its own L0–L5 evidence level and `cannot_prove` boundary.
