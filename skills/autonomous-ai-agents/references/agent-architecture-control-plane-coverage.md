# Agent architecture coverage: control plane + executor fusion

Use this reference when the user asks how Hermes should cover or absorb Claude Code / Codex / OpenCode style agent architecture capabilities without replacing Hermes' governance model.

## Core framing

The durable architecture is additive, not replacement:

- Hermes remains the control plane: canonical ledger, taskpool, evidence spine, policy gates, certification, human/elevated review.
- Claude Code / Codex / OpenCode style agents act as worker adapters, executor runtimes, or subagent lanes.
- Kanban, dashboard, Lark, Telegram, worker UIs, and external agents are adapters/projections, not sources of truth.
- Parallelism is an execution strategy, not a governance strategy.

## Non-negotiable invariants

- The canonical task ledger is the single source of truth.
- Workers must not directly mark tasks `done`; at most they can advance evidence-backed results to review.
- `done` requires human or elevated policy gate approval.
- Workflow/DAG/fork-join graphs are execution projections. Forked items still need ledger identity; joins are aggregator tasks with evidence.
- Evidence must stay out of the hot path: store summary/hash/pointer in ledger; keep logs, screenshots, transcripts, traces, JSON blobs, and reports as external artifacts.
- Failure needs classification (e.g. needs_auth, unreachable, flaky, policy_blocked, implementation_error, evidence_gap), not a generic `blocked` bucket.
- Runtime dispatch, lifecycle mutation, and external adapter write-through require a separate explicit gate and rollback/readback design.

## Coverage domains to map

When producing an architecture coverage plan, explicitly cover these domains:

1. Dynamic planning / decomposition
2. Parallel subagent execution
3. Fork-join / map-reduce graph projection
4. Worker result contract
5. Multi-model certification / adversarial review
6. Evidence artifact layering
7. Workflow metadata / lane-local state
8. Error recovery / fallback / retry policy
9. Workflow composition across tools/adapters

## Recommended contract-first rollout

Prefer report-only contract validation before enabling runtime behavior:

1. Coverage report contract: map external-agent capabilities to Hermes primitives and gaps.
2. Worker result contract: require summary, artifact pointers, verification result, risk flags, next action; reject authority-smuggling fields such as `mark_done`, `external_write`, `task_status`.
3. Fork/join graph contract: validate DAG/projection shape without making it the source of truth.
4. Multi-model certification contract: represent planner/reviewer/arbiter/quorum/truth-gate decisions as evidence-backed projections.
5. Artifact pointer contract: enforce bounded summary plus `sha256:` hash and external artifact URI; reject inline content/raw blobs.
6. Workflow metadata contract: allow `workflow_state`, lane, checkpoint, deadline/resource/quota metadata while forbidding canonical lifecycle status mutation.
7. Only after these pass, open runtime in small, auditable boundaries rather than jumping straight to autonomous external execution:
   - Ledger-only start: append a durable run record with `run_status=started`; no executor invocation, no lifecycle mutation, no adapter writes, no persistent learning.
   - Governed builtin read-only executor: consume a started run, verify it from ledger, append a completed result/evidence receipt; still no external process or lifecycle authority.
   - External agent process probe: allowlisted agent binaries may run a version/preflight command such as `claude --version`, `codex --version`, or `opencode --version`; append the receipt, but send no task prompt.
   - External prompt dry-run: send a task prompt only with tools disabled and no-write/plan mode; capture stdout/stderr into an artifact and append only artifact URI/hash/summary to the ledger.
   - Read-only context packet: pass context as a `file://` artifact URI plus sha256; reject inline context, workspace file reads, write mode, tools, and lifecycle/adapter/memory/skill authority.
   - Proposal artifact intake: accept external worker output only as a validated `worker_review_proposal` artifact with `lifecycle_target=review_proposed`, failure classification, evidence refs, and evidence-backed claims. This is not fact promotion and must not mark done.
   - Multi-model certification promotion: validate reviewer quorum, truth-gate evidence, reviewer evidence, and evidence-backed claims against the recorded proposal artifact. This may at most advance to a certification-for-review state; it is still not a done fact.
   - Human/elevated done authorization projection: only after certification, accept an approval from an elevated actor, bind it to the exact certification artifact digest, require a non-expired TTL and evidence refs, and still keep fact mutation/write-through disabled. This records authorization, not the fact itself.
   - Ledger-local canonical fact mutation: consume an unexpired approved authorization, re-check certification artifact binding, require mutation evidence refs, append the local canonical lifecycle fact, and make replay idempotent by authorization id plus target status. This is the first boundary where local canonical lifecycle mutation is allowed; external adapter write-through remains disabled.
   - External adapter write intent projection: before any real adapter write, map the canonical done fact to an allowlisted adapter/target as an intent only. Require adapter allowlist, target ref/status, canonical fact digest, readiness check, readback plan, rollback plan, and evidence refs; keep `write_through_allowed=false` and reject authority-smuggling fields (`external_write`, `write_through_enabled`, lifecycle/status overrides).
   - External adapter write-through is an executor-specific slice with separate elevated authorization, idempotency, artifact capture, cancellation, readback verification, rollback/escape, and audit trail. Open one adapter at a time (for example local-file harness before taskpool note before Kanban DB) and keep the mutation narrow: exact target, expected previous state, single field/frontmatter cell, readback proof.
   - Rollback/reopen is its own digest-bound executor: consume the verified write event by exact request digest, restore only the recorded previous state after current-state check, read back, and stay idempotent. Do not treat rollback as broad reopen authority.
   - Outbound notification outbox enqueue comes after verified write/rollback, not before. It should append a pending item only, with allowlisted target/channel, payload hash/summary, evidence refs, no secret-like payload keys, and no platform API calls.
   - Delivery authorization is a separate elevated projection over a pending outbox item: exact outbox id, channel, target, payload hash, TTL, readback, and evidence refs. This still does not send.
   - Channel-specific sender dry-run precedes real send. For Telegram/Lark, validate the platform payload contract, record payload hash/summary, keep `send_executed=false`, do not read tokens, do not store raw payloads, and do not call platform APIs. Only after a dry-run boundary passes should a real sender slice be considered.
   - Scope/anti-condition: use this ordered boundary sequence only for canonical-ledger agent control planes with lifecycle facts and adapter projections. For ordinary coding-agent delegation, keep using the narrower child-agent workflow instead.

## Implementation notes

- Keep contracts `report_only` / projection-only until separately authorized.
- When crossing into runtime, use ledger-only records first; every boundary should append evidence to the ledger and explicitly state which authorities remain false.
- Preserve canonical lifecycle states separately from workflow/lane-local substates.
- Use TDD for contract/runtime additions: write RED tests for forbidden authority fields and hot-path bloat, then implement minimal validators or executor boundaries, then smoke test CLI JSON output and ledger line count. For write-through/outbox/sender work, include idempotent replay, symlink/path safety, digest drift, TTL expiry, target/channel allowlist, secret-like payload rejection, and “no send/no token read” assertions where applicable.
- For external agents, constrain by executor type and command basename; never accept arbitrary command paths as a generic “agent runner.”
- Commit changes in scoped slices and document which capabilities are still intentionally disabled.

## Useful phrasing

One-line summary: Hermes should be the long-term trustworthy control plane and evidence ledger; external agent CLIs should be high-throughput execution brains connected through constrained worker contracts and certification gates.
