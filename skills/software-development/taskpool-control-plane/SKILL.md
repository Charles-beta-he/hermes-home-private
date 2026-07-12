---
name: taskpool-control-plane
description: "Use when diagnose and operate the local brain/taskpool control plane — dispatch tick, autorun, eligibility, proof/evidence governance, and fail-safe claim behavior when the pool is stalled."
---

# Taskpool Control Plane

## Dynamic runner human-escape preclaim pitfall

Detailed dynamic-runner human-escape preclaim recovery moved to `references/dynamic-runner-human-escape-preclaim.md`.

Load it when `taskpool_dynamic_runner.py` reports `human_escape_active_preclaim` or lane filters make autorun report no tasks.

Minimum in-root rule: treat safe preclaim no-op as OK, verify escape guard state, and compare configured lane with live dispatch supply before changing config.

## New / important references

- `references/proof-check-autorun-debt-classification.md` — use when `proof-check` mixes autorun event hashes with artifact/compound SHA-256 evidence: require an exact event-reference predicate, preserve the done-task candidate gate, reclassify only byte-matched artifacts through an ordered reversible hash manifest, and leave source-unmatched hashes visibly OPEN.
- `references/procedure-validation-local-rehearsal-projection.md` — use when local Agent OS procedures are stale: write rehearsal receipts under the selfcheck root (not a doubly nested rehearsal directory), rebuild projection, and prove authority-blocked/external procedures did not change.
- `references/continuation-compaction-recurrent-state-implementation.md` — use for read-only continuation manifests and explicitly approved archive-only compaction: preserve blocked/human-review packets, verify zero residual archive candidates, and distinguish newly created live packets from compaction regressions.

- `references/continuation-closure-after-interruption.md` — use when a continuous closeout loop is interrupted by tool-budget/context limits or async verification: resume from fresh canonical readback, keep advancing independent safe slices, classify every residual gap, preserve missing-input truth boundaries, and require a latest-byte verifier vote before closure.
- `references/validator-false-green-hash-drift-authorized-continuation.md` — use when Local Brain validation suddenly goes green after scope/parser changes, when taskpool hash verification mirrors canonical indexing, or when user authorization releases blocked historical tasks: detect malformed-frontmatter invisibility before L3 scope, reuse canonical block/secret-filter logic, refresh verifier snapshots, read lifecycle state after concurrent resolver actions, and keep missing-source acceptance OPEN.
- `references/concept-bound-recall-preflight-mcp-projection.md` — use when local-brain `concepts`/tags should drive deterministic recall or an existing verifier, or when evaluating a generic Memory MCP bridge: normalize into authority-neutral `concept_refs` before envelope hashing, persist hash-bound excerpt-free receipts, make verifier triggers PASS/FAIL/SKIP and policy-invariant, and validate metadata-only MCP projections in a disposable store before opening any persistent dual-store write path.
- `references/automatic-semantic-knowledge-recall-integrity.md` — use when validated task intake automatically retrieves local knowledge: derive bounded queries only from the structured semantic envelope, bridge explicit local-brain `concepts` tags into validated authority-neutral `concept_refs` before hashing/recall, persist excerpt-free hash-bound receipts, reject internally consistent forgeries through current-source verification, account for top-k instability with a wider bounded verification window, and certify via isolated real-backend lifecycle probes plus exact-byte independent review.
- `references/structured-semantic-intent-and-idle-readiness.md` — use when knowledge/solution/workflow processing must be driven by a versioned semantic intent envelope and declarative capability graph rather than keywords; includes authority/writeback separation, complete producer call-site inventory, validated-parent child inheritance, reversible frontmatter persistence, save/reload decision tests, metamorphic negative tests, safe fail-closed behavior, idle-neutral readiness, and qualification-claim boundaries.
- `references/read-only-scoped-certification-amendment.md` — use for narrow independent final verification of a hash-bound local taskpool certification packet: enforce an exact-version byte freeze, run cwd-sensitive manifests from the declared root, verify parser totality (malformed serialization plus wrong container/entry types) without permissive fallback, execute stable-inode `flock` crash-release coverage with zero-residual-child readback, bind saved suite summaries by hash, and land the final verdict as a separate receipt without inflating scoped local claims into historical, external, clean-release, global, or real multi-model certification.
- `references/architecture-and-test-matrix-inventory.md` — use for read-only full-system taskpool audits: separate each durable state model/SSOT, inventory lifecycle ownership and controller loops, trace adapters/mirrors for direct-write bypasses, map tests from assertions rather than filenames, run under the project-declared runtime, and classify concrete failures separately from untested high-risk gaps.
- `references/bounded-loop-and-multicontroller-convergence.md` — use when deciding whether taskpool automation is genuinely closed-loop, when event hooks/cron/controllers disagree, or when adding bounded Agent/compound loops; includes cross-controller eligibility SSOT, pre-run contract completeness, stop/evaluator gates, failure modes, and core literature.
- `references/automated-claim-bypass-and-handoff-invariant-audit.md` — use for independent P0/controller-convergence reviews: enumerate every automated low-level claim caller, compare the complete mutation-time gate (including execution-flow/selfcheck/write guard), trace required handoff fields through legacy batch producers, preserve structured denial JSON even on non-zero subprocess exits, and detect partial-claim release failures, claim/retry churn, or false background-spawn success after a new consumer invariant.
- `references/social-signal-advisory-drain-runbook.md` — use when continuing/progressing a backlog of public social/media advisory taskpool cards: preserve source boundaries, write decision-matrix artifacts, attach sha256 proof to lifecycle transitions, and keep runtime/certification gates closed.
- `references/compound-agent-loop-taskpool-mapping.md` — scoped reference for mapping compound/self-improving agent loop contracts into taskpool cards; applicability: governed intake/recertification only; anti-condition: does not authorize runtime/worker/scheduler/external writes.
- `references/workspace-projection-taskpool-bridge-boundary.md` — use when connecting WorkspaceProjection/EvidenceDAG/ReflectionReadback/CompletionClaimPacket outputs to taskpool review/done gates, event projection, or read-only dashboards; includes exact-source/write-surface preflight, dashboard-history pitfall, no-hidden-state/no-model-only-proof boundaries, and the four-field exact target/payload/rollback/readback gate for any write-through.
- `references/batch-intake-and-recertification-repair.md` — batch intake + degraded recertification repair.
- `references/multimodel-routing-vs-thinking-drain.md` — split taskpool multi-model routing-plan intervention from task-content thinking/ratification; includes stage-to-tier guidance and drain-loop checks.
- `references/advisory-only-pass-review-gate.md` — avoid evidence-only advisory tasks ping-ponging back to pending after `PASS_ADVISORY_ONLY`; keep review/done authority separated.
- `references/quota-observability-fail-closed-child-closeout.md` — close quota-observability narrowing children with honest fail-closed evidence when quota confidence is unobservable/low-confidence; exact claim refusal beats standalone eligibility for dispatch authority.
- `references/exact-temporary-allowlist-and-advisory-closeout.md` — when dry-run selects a bounded child but exact handoff returns `allowlist_miss`, use a temporary exact task allowlist entry, remove it after the run, and remember PASS_ADVISORY_ONLY closeout needs recognized implementation evidence such as `pytest`/test/build, not selfcheck alone.
- `references/blocked-worker-produced-proof-closeout.md` — when a worker reports `blocked` but the child note/scratch artifact contains the requested narrowed brief or proof, stabilize the artifact, write readback, move through `blocked -> retry -> claimed -> running -> review`, auto-close, then sync the parent without running parent-worker churn.
- `references/parent-certification-churn-and-missing-axis-drain.md` — when a parent remains selected/retry after children seem done, avoid repeated parent worker churn: inspect taxonomy axes, stale child evidence, parent aggregation, and work-first blockers; backfill missing-axis children or stale proofs before ratification.
- `references/authorized-local-child-drain-after-blocked-parent.md` — when the user authorizes continued local-only progress despite blocked/not-certified parents, iterate full-pool split/sync, close newly generated children with deterministic local brief/readback/test evidence, wait out event-hook multimodel races, and keep parent certification separate.
- `references/false-selected-parent-and-live-certification-drain.md` — when broad dispatch selects a parent but exact eligibility/certification gates deny execution, avoid parent-worker churn: respect live certification ownership, split new taxonomy axes into children, then verify no live jobs/allowlist residue.
- `references/browser-readback-precommit-evidence.md` — when a scoped taskpool/project closeout commit is blocked because local-brain pre-commit does not recognize real browser screenshot/console readback, preserve the gate and repair the evidence-shape classifier under TDD instead of bypassing the hook.
- `references/normal-automation-advance-chain.md` — class-level chain for continuing blocked/retry taskpool work without punting: snapshot, deterministic maintenance, human-escape recovery, live-owner reconciliation, child-parent sync, exact eligibility, multimodel routing/thinking, certification loop breakers, scoped tests/commits, and final readback.
- `references/targeted-evidence-packet-after-t3-pause.md` — Applicability: blocked parent tasks whose child convergence is clean but the configured certification/economy gate is paused after repeated ratification failure. Anti-condition: do not use as completion authority, do not fabricate missing artifacts, and do not rerun a paused multimodel loop without a fresh exact authorization/readback path.
- `references/quota-observability-profile-local-continuation.md` — Profile-local quota-observability continuation: when historical quota artifacts are stale/missing or no-header model routes appear non-certifying, recreate fresh continuation packets, use `confidence-gate --gate`, run profile-local smokes/probes, and preserve the boundary between route availability and exact quota.
- `references/intelligent-agent-layer-event-route.md` — use when taskpool events must route into the intelligent agents layer: keep taskpool as SSOT/proof gate, put expansion decisions in smart routing, wake agents only through a governed worker bridge, and verify route availability separately from actual spawned work.

## Review/done lifecycle proof pitfall

Detailed review/done lifecycle proof rules moved to `references/review-done-lifecycle-proof-pitfall.md`.

Load it when closing implementation tasks, especially `review -> done`, advisory-only multimodel outputs, or rejected evidence prefixes.

Minimum in-root rule: do not force-close for dashboard cleanliness; add deterministic implementation evidence and structured refs.

## Task creation retry / duplicate cleanup

Detailed task-creation retry/duplicate cleanup moved to `references/task-creation-retry-duplicate-cleanup.md`.

Load it after `add` hook errors, timeouts, or duplicate task files.

Minimum in-root rule: inspect created path and search existing tasks before retrying; archive duplicates only after confirming a canonical task.

## Task creation CLI guardrails

Detailed `brain_task_orchestrator.py add` / retry / duplicate-control / capability-absorption guardrails were moved to `references/task-creation-cli-guardrails.md`.

Load it when creating or repairing taskpool task files, especially after hook errors, timeout ambiguity, duplicate creation, add-repo-capability-absorption, or evidence-prefix rejection.

Minimum in-root rule: before retrying a failed-looking task creation, search/read existing task files for the intended title; evidence refs must use accepted prefixes such as `command:`, `artifact:`, `proof:`, `url:`, or `file:`.

Pitfall: work-lane project tasks can fail closed at creation time when the project profile has no `source_weighting_policy`. For a receipt-only/local-write boundary that must not dispatch workers, use an advisory lane with explicit project/status/evidence and read the created task back; do not force a work-lane task through by weakening profile gates. If the task must be dispatchable work, add the scoped source-weighting policy to the project profile first, then retry creation after searching for duplicates.

## Overview

Diagnose and operate the local brain/taskpool control plane — dispatch tick, autorun, eligibility, proof/evidence governance, and fail-safe claim behavior when the pool is stalled. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

The extended taskpool trigger/routing map was moved to `references/when-to-use-routing.md`.

Load it when deciding whether a request belongs to taskpool-control-plane versus a narrower workflow, especially for blocked/retry/review/done/proof/multimodel/dispatch ambiguity.

Minimum in-root triggers: stalled pool, dispatch/autorun/eligibility, proof/evidence lifecycle, stale claims, taskpool closeout, blocked/retry/review drain, and taskpool multimodel/advisory gates.

Don't use for:
- ordinary project implementation when taskpool lifecycle/proof/dispatch is not involved;
- external dispatch, destructive cleanup, credential entry, publish/deploy/push, or broad fan-out without the exact authority gate named by the taskpool/control-plane policy;
- force-closing work just because deterministic local proof exists while a governed certification gate is still advisory or blocked.

## Infrastructure-Blocked Evolution Task Archiving

When an evolution lane task's analysis is complete but multimodel certification is blocked by infrastructure (missing API keys, quota expired, provider unavailable), the task can be archived with evidence of completion. `--force` does NOT bypass `multimodel_certification_required_before_done` gate; use `--to archived` instead. See `references/infrastructure-blocked-evolution-task-archiving.md`.

## Operational Watchdog Cron Scripts

Detailed watchdog cron triage moved to `references/operational-watchdog-cron-scripts.md`.

Load it for taskpool health watchdogs, no-agent cron scripts, Telegram/selfcheck alert noise, or subprocess timeout patterns.

Minimum in-root rule: cron/watchdog changes are local and fail-closed unless exact external delivery/credential boundaries are authorized.

## Cron Scheduler Recovery — Model Provider 429 Blocking

Detailed cron/provider 429 recovery steps were moved to `references/cron-provider-429-recovery.md`.

Load it when scheduled jobs fail due provider/model/network quota degradation and a local no-agent wrapper or health-gate decision is needed.

Minimum in-root rule: classify current cron errors read-only first; do not batch mutate cron, validate secrets, or send messages without exact authorization and readback.

## Event-Driven Auto-Execution (Preferred)

When implementing task pool auto-execution, use **event-driven architecture** over polling/timed triggers. User preference (2026-05-31): "为什么是定时？而不是自动化根据待执行直接触发？" - Why is it timed instead of automatic trigger based on pending tasks?

See `references/event-driven-auto-execution.md` for the event architecture patterns, and `references/bounded-loop-and-multicontroller-convergence.md` when event hooks coexist with cron, retry, reconcile, agent-team, or manual dispatch controllers.

Key principles:
- Events should trigger immediate eligibility evaluation when task state changes, not wait for the next polling cycle.
- An event is a wake signal, not claim/execute authority.
- Every controller must use the same exact-task eligibility/policy SSOT before claim.
- Handoff/envelope/authority/acceptance/evidence/stop contracts must be complete before entering `running`.
- To verify automation, reconstruct the lifecycle timeline and read worker jobs; do not infer the result from the creation hook alone.

## Core principle

The fail-safe objective is: taskpool must not idle-spin when there is a dispatchable priority task.

Treat these as separate concerns:
1. Can a concrete task be safely claimed right now?
2. Is the control plane globally healthy/governed?

Global governance warnings should be surfaced, but they should not automatically block bounded claim-and-handoff for an otherwise dispatchable P1 task.

## Fast triage flow

The detailed fast triage flow was moved to `references/fast-triage-flow.md`.

Load it when the pool appears stuck and you need ordered checks for hooks, cron, policy, eligibility, dispatch, and lifecycle evidence.

Minimum in-root rule: inspect live state before declaring stuck; avoid retry loops that create duplicates or steal active claims.

## Manual autorun handoff -> worker start

Detailed handoff-to-worker recovery was added in `references/manual-autorun-handoff-worker-start.md`.

Load it when `autorun-runner` or `brain_task_dispatch_tick.py --autorun-step` creates a handoff / claim but no actual worker is progressing. Minimum in-root rule: a handoff is not execution proof; explicitly start `agent_team_controller.py consume-claimed --background` only for the exact claimed task/handoff, then verify worker job id, pid/alive, task status transition, and proof/selfcheck readback. Do not steal legitimate live claims or force-close review gates.

## Reconcile-required after write readback pitfall

If `eligibility-check` or `dispatch-dry-run` still reports `reconcile_required` after `reconcile --write`, do not loop the same command or assume the pool is broken. Run `next --reconcile --json` so due retries can be promoted through the same selection path, then verify with `next --no-reconcile --json` and `HERMES_LOCAL_BRAIN_AUTORUN=1 ... eligibility-check --json`. A successful recovery is `eligible=true`, empty `reasons`, and a concrete `task_id`; `selfcheck` may still carry non-blocking handoff archival warnings.

## Manual anti-idle rule

If all of the following are true:
- active tasks exist,
- no task is currently `claimed` or `running`,
- at least one P1 task is dispatchable,
- no hard safety blocker is present,

then manually push one highest-priority P1 task to `claimed`.

Rationale: the scheduler’s fail-safe job is to prevent taskpool empty-spin. `blocked` siblings or historical `done`-task evidence debt should not freeze the entire pool.

## Control-plane diagnosis checklist

Use this order:
1. Verify the live CLI surface (`brain_task_orchestrator.py --help`) so you invoke the right taskpool commands.
2. `dashboard` / `list` / status distribution
3. `eligibility-check`
4. `autorun-runner`
5. `proof-check`
6. `evidence-spine`
7. `selfcheck`
8. taskpool dynamic-runner JSONL logs and cron outputs
9. dispatch tick source/tests if behavior still looks wrong

## Taskpool Intake, Framing, and Parallel Execution Umbrella

Detailed taskpool intake/framing/parallel-execution umbrella mapping moved to `references/taskpool-intake-framing-parallel-umbrella.md`.

Load it when adding tasks, applying project-profile source weighting, or operating parallel agent-team lanes.

Minimum in-root rule: taskpool items need governed lane, priority, dependency/parallel boundary, proof expectation, and profile evidence when applicable.

## Generated convergence child source-policy gate

Detailed auto-subtask source-policy repair moved to `references/generated-convergence-child-source-policy.md`.

Load it when `auto-split-non-convergence` or another generator creates work/project children, or when a generated child is pending/retry but `eligibility-check` reports `task_not_dispatchable`. Minimum in-root rule: generated `lane=work` + `project` children must carry `source_weighting_policy_ref`; repair only non-terminal children that need dispatch, then verify `eligibility-check` before exact claim/handoff.

## Task Adapter Framework (pluggable source pattern)

Detailed TaskAdapter framework notes moved to `references/task-adapter-framework-pointer.md`.

Load it when ingesting from Lark/brain/GitHub/direct sources or extending adapter write-through.

Minimum in-root rule: keep source adapters, registry, pipeline, and executor mutation boundaries explicit and permission-gated.

## Observability and Depth Classification

Detailed observability/depth-classification notes moved to `references/observability-depth-classification.md`.

Load it when backlog triage or dispatch routing depends on progress visibility or iceberg/task-depth classification.

Minimum in-root rule: lifecycle state alone is insufficient; expose progress, depth, and profile-aligned routing evidence.

## Adding external repo / doc analysis tasks to the pool

The detailed external repo/doc/social-source intake recipe was moved to `references/external-repo-doc-analysis-intake.md`.

Load it when turning an external repository, document, article, or public-media lead into a governed taskpool candidate. Keep source claims, target surface, evidence refs, red lines, non-goals, and acceptance gates explicit.

Minimum in-root rule: adding a task is tracking, not delivery; if the user says `全盘推进`, continue the next safe bounded implementation/evidence slice immediately.

## SSOT: One Task Pool Only

When building any distributed worker, executor, or edge node, do NOT create a competing task pool. The canonical task pool is `brain_task_orchestrator.py` + `kanban.db`. Workers are execution-only layers that fetch tasks from the brain and report results back. See `references/ssot-violation-edge-worker-task-pool.md` for the anti-pattern, correct architecture, detection checklist, recovery steps, and the concrete three-layer implementation pattern (UnifiedTaskPool adapter → EdgeWorkerExecutor → UnifiedAPI).

## Edge Worker Test Coverage

When improving test coverage for hermes-edge-worker, use `references/edge-worker-test-coverage-improvement.md`: it covers the systematic pattern for baseline assessment, component test creation, syntax verification, assertion adjustment, and coverage targets.

## Implementation guidance for dispatch tick fixes

Detailed dispatch tick fix guidance moved to `references/dispatch-tick-fix-guidance.md`.

Load it when patching `max_agents`, dynamic-N, parallel boundaries, iceberg dispatch integration, brain overlay contracts, or tick logging behavior.

For independently failing baseline tests during a scoped controller/certification slice, load `references/dispatch-tick-baseline-independence-and-test-seam-drift.md`: trace before/reconcile/projection/after state, audit the exact monkeypatch wrapper seam, prove causal separation from the current diff, and distinguish scoped certification from a full dispatch-tick/full-suite claim.

Minimum in-root rule: separate warnings from errors and preserve fail-closed behavior only for true safety blockers; never weaken reconciliation or liveness gates to satisfy a stale synthetic fixture.

## False-positive `done` tasks

Detailed false-positive done audit moved to `references/false-positive-done-tasks.md`.

Load it when a done task did not produce the promised behavior.

Minimum in-root rule: inspect task body and live feature path; control-plane proof is not feature-specific implementation evidence.

## Historical proof/evidence debt cleanup

When `proof-check --json` fails but the failures are historical closeout debt rather than live execution risk, clean the debt instead of normalizing permanent failure.

## Stale-claimed task recovery before declaring the pool blocked

Detailed stale-claimed task recovery was moved to `references/stale-claimed-recovery.md`.

Load it when tasks are `claimed`/`running` but no live worker/process/evidence exists.

Minimum in-root rule: prove stale ownership and preserve another worker's legitimate active claim; release/requeue only with structured evidence.

## Blocked parents can already have finished convergence subtasks

Detailed blocked-parent/finished-child reconciliation was moved to `references/blocked-parent-finished-children.md`.

Load it when children/subtasks appear done but the parent remains blocked/retry/review or certification does not converge.

Minimum in-root rule: finished children are evidence, not automatic parent closeout; run parent reconciliation/proof gates before status promotion.

## References

The long root reference index was moved to `references/root-reference-index.md`.

Load it when looking for older specialized runbooks not named in the current root skill.

Minimum in-root rule: prefer the narrowest named reference for the active symptom, then use the index if the symptom is not covered above.

## Common Pitfalls

1. Treating a taskpool status label as proof of feature delivery. Always read the task body and live target evidence.
2. Retrying add/transition commands after a timeout without first checking whether the previous command partially succeeded.
3. Upgrading advisory-only multimodel outputs or local py_compile/proof-check health into certified done authority.
4. Sending advisory-only `PASS_ADVISORY_ONLY` evidence tasks back to `pending` after deterministic worker proof exists; this re-dispatches the same task and creates blocked/retry ping-pong. Keep them in `review` without granting done authority; see `references/advisory-only-pass-review-gate.md`.
5. Review-gap repair children and bounded CLI/control-plane implementations are not automatically UI closeouts. If `PASS_ADVISORY_ONLY` or historical body/non-goal words like “修复/验证/browser/api/UI” force screenshot/API proof, inspect the closeout surface classifier before changing evidence. Explicit non-empty `harness_surfaces` should bound the required output proof (`local-cli` ≠ UI; `backend` requires API/readback but not UI). Repair the classifier under RED→GREEN tests; never add fake screenshot/API markers. Legacy active tasks may separately need a truthful validated semantic-intent envelope. See `references/closeout-surface-obligation-classifier.md`.
6. Cleaning dashboards by force-closing or archiving instead of fixing evidence shape, lifecycle ownership, or stale-claim state.
6. Re-dispatching the same blocked parent worker after children are done and certification still fails. First inspect `parent_aggregation`, missing taxonomy axes, stale child-status proofs, and the ratification surface; see `references/parent-certification-churn-and-missing-axis-drain.md`.
7. Treating broad scheduler selection as execution authority for a parent. Always run exact task eligibility and live worker/certification readback before adding allowlist or claiming; see `references/false-selected-parent-and-live-certification-drain.md`.

## Verification Checklist

- [ ] Live taskpool state was read back from the canonical brain/taskpool surface, not inferred from memory.
- [ ] Lifecycle transitions used structured evidence prefixes and the allowed status chain.
- [ ] Any stale-claim, blocked, review, retry, or done claim was backed by a fresh command/artifact/proof readback.
- [ ] External dispatch, destructive cleanup, credential entry, publish/deploy/push, broad fan-out, and real adapter writes remained closed unless exact authority existed.
- [ ] Historical proof warning reductions were justified by namespace false-positive removal or exact source-byte matches; unmatched hashes stayed visibly OPEN.
- [ ] Multi-record task mutation manifests were verified as ordered hash chains, with current bytes matching the final record only.
- [ ] Continuation closure compared buckets/packet IDs rather than raw active count, because the current session can create new live packets.
- [ ] Local procedure rehearsal receipts landed under the registry-scanned root; external/authority-blocked procedure states were proved unchanged.
- [ ] The relevant narrow reference under `references/` was loaded when the root pointer indicated it was needed.
