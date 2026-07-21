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
- No public `botiverse/raft` repository was accessible at inspection time.
- Neither inspected public repo declares a repository license. Treat the material as reference-only; do not copy implementation text or code into Hermes.
- Reproducible snapshots: `runs/raft-public-reference-review-20260721/`.

Local verification:

- External runtime: typecheck passed; 32/32 tests passed; production bundle built.
- Documentation: VitePress build passed; generated agent-artifact freshness check passed.
- These checks validate only the two public repositories, not the private collaboration server or its assignment logic.

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

## Hermes adaptation

1. Project messages into tasks without losing source provenance.
2. Use eligibility filters and atomic claims before complex routing algorithms.
3. Require an approved task DAG before broad parallel execution.
4. Keep `in_review` separate from `done` and bind approval to exact evidence.
5. Separate agent capability, identity, and authority.
6. Use metadata-only wakes and authoritative pull for external runtime integrations.
7. Match reliability guarantees to signal semantics.
8. Surface supervision state, restarts, drops, and provenance as first-class evidence.

## Verification checklist for derived systems

- [ ] Every task points to its source message/thread.
- [ ] Claim is atomic and duplicate-safe under concurrency.
- [ ] Stale owners/claims have a lease or reconciliation path.
- [ ] Routing claims identify eligibility inputs and, if scored, expose decision evidence.
- [ ] Proposed decomposition is checked for overlap and dependencies before fan-out.
- [ ] `in_review -> done` requires fresh approval/readback.
- [ ] Capability and authority are modeled separately.
- [ ] Wake transport carries no untrusted content bodies.
- [ ] Wake success proves visible-context injection or durable queueing.
- [ ] Control signals and telemetry use explicit, different delivery semantics.
- [ ] Runtime child state, restart count, queue loss, and profile provenance are observable.
