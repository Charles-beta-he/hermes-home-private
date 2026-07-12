# Bounded Loop Engineering and Multi-Controller Convergence

## Applicability

Use this reference when deciding whether a taskpool is truly automated, when event hooks and cron/controllers disagree, or when adding feedback/learning loops to task execution.

Anti-conditions:

- Do not use “loop engineering” as authority to claim, dispatch, close, publish, deploy, or mutate policy.
- Do not convert every deterministic task into an autonomous agent loop.
- Do not promote one task’s reflection directly into global memory, skills, or policy.

## Core distinction

A taskpool can have automated transitions without having a complete engineering loop.

Classify three layers separately:

1. **Lifecycle loop (deterministic):** intake → validate → eligible → claim → running → evidence → review → done, with blocked/retry/reconcile/expired/cancelled branches.
2. **Execution loop (bounded agentic):** observe → plan → act → readback → evaluate → adapt.
3. **Compounding loop (selective learning):** review → root cause → extract reusable pattern → test → promote → measure.

The safe default is deterministic lifecycle control, agentic execution only when the path is uncertain, and evidence-gated promotion of reusable assets.

## Automation truth-check

Do not answer “is it automated?” from the creation hook or one scheduler alone. Establish a timeline from all active control paths.

1. Enumerate every ingress/controller:
   - task creation/status event hooks;
   - short-interval dynamic runner;
   - periodic agent-team/controller jobs;
   - retry/reconcile/watchdog paths;
   - manual dispatch surfaces.
2. Read the task’s actual lifecycle history and timestamps.
3. Compare each controller’s route/eligibility decision for the same task.
4. Read the spawned worker job and handoff/envelope, not only task status.
5. Run exact-task eligibility after the transition; broad scheduler selection is not authority.
6. Classify the result:
   - **consistent:** all paths share the same policy decision;
   - **policy divergence:** one path defers/denies while another claims;
   - **contract bypass:** claim/run occurred with incomplete handoff, envelope, authority, acceptance, or evidence contract;
   - **healthy fail-closed:** task remains pending/blocked and no side effect occurs.

A task that automatically moves `pending → claimed → running → blocked` proves automation, but not loop quality or completion.

## Cross-controller invariant

All event, cron, retry, reconcile, and manual-dispatch paths must call the same eligibility/policy SSOT before claim. Controller-specific routing may rank candidates, but must not redefine authority.

Before `claim` or `running`, require:

- exact task identity and current version/digest;
- complete handoff or mission envelope;
- acceptance criteria and evaluator/readback contract;
- required/max authority and allowed write surfaces;
- dependency and concurrency boundaries;
- iteration/time/cost/retry budgets;
- stop conditions and rollback/escape path.

Missing required fields must keep the task pending or move it to a structured blocked state. Do not enter running merely to discover that the execution contract is empty.

## Bounded execution-loop contract

An agent loop is appropriate only when:

- the path cannot be fully predetermined;
- environment feedback is available after each material action;
- evaluation criteria are clear enough to measure progress;
- actions are reversible or permission-gated;
- iteration adds measurable value.

Required controls:

- maximum iterations, elapsed time, tokens/cost, and retries;
- idempotency keys, leases, and duplicate-event suppression;
- real environment readback rather than model completion claims;
- independent/deterministic evaluators where possible;
- no-progress detection and repeated-failure circuit breaker;
- structured blocker and stop reason;
- human checkpoints for credentials, payment, production, external dispatch, destructive actions, and other irreversible boundaries.

## Compound-loop promotion gate

The compounding step should create a candidate asset, not silently mutate global behavior.

Promotion sequence:

`shadow report → human/independent review → deterministic test → scoped promotion → measurement → rollback if degraded`

Good promotion targets: tests, verifier rules, templates, class-level skill references, reusable scripts, and capability-graph edges.

Keep project facts in project profiles/SSOT and keep task/session progress out of durable memory.

## Failure modes

- **Multi-controller policy drift:** event route defers but periodic controller claims.
- **Empty-handoff execution:** worker starts with no usable handoff/envelope and immediately blocks.
- **Retry storm:** failure is treated as another attempt without changed evidence or backoff.
- **Self-evaluation correlation:** the same model generates and approves its output without external truth.
- **Goodhart drift:** the loop optimizes a proxy metric while violating the real objective.
- **Controller competition:** multiple schedulers race to claim or repeatedly requeue the same task.
- **Unbounded compounding:** one-off reflections pollute global policy/memory.

## Closeout state and certification are orthogonal

Never collapse lifecycle state, completion scope, and certification into one boolean.

Track at least these dimensions separately:

- lifecycle state: `blocked | review | done`;
- completion boundary: for example `document_only` versus implementation/runtime delivery;
- certification state: `not_certified | degraded | certified`;
- ratification artifact/status;
- authority granted for follow-on implementation or side effects.

An advisory task may legitimately reach `done` because its document/evidence-deposition boundary passed while still carrying `certification_status=not_certified` and a pending ratification marker. Report that as “document-only advisory closeout,” not as certified truth, implementation acceptance, or expanded authority.

Before the final closeout statement—especially after an asynchronous verifier or controller has run—perform a fresh exact-task SSOT readback. Do not preserve an earlier `blocked` snapshot in a verifier packet after another controller has advanced the task. A broad/default list may omit completed tasks; if the exact ID is absent, inspect the exact task record or use an include-done/read-by-ID surface instead of concluding the task is missing or unchanged.

Keep certification scopes explicit and independent:

1. focused tests passing;
2. full relevant regression passing;
3. independent review vote;
4. scoped controller-convergence certification;
5. full taskpool/system certification;
6. task-level completion and task-level ratification.

The parent/orchestrator should issue any certification only after combining objective execution/readback evidence with the independent vote and naming the boundary. A reviewer’s PASS is evidence, not permission to silently broaden certification beyond the reviewed paths.

## Verification checklist

- [ ] All active controllers and their schedules/triggers were enumerated.
- [ ] A fresh lifecycle timeline proves what actually moved the task.
- [ ] Route, exact eligibility, claim authority, and worker job agree.
- [ ] Handoff/envelope completeness is enforced before running.
- [ ] The evaluator uses real readback and named acceptance evidence.
- [ ] Iteration, cost, retry, no-progress, and stop limits are explicit.
- [ ] Worker self-report cannot directly grant done authority.
- [ ] High-risk side effects remain behind exact human/authority gates.
- [ ] Compound promotion is tested, scoped, reversible, and not based on one session.

## Core literature map

Use these as conceptual foundations rather than as automatic implementation authority:

- Norbert Wiener, *Cybernetics* (1948): feedback and control.
- W. Ross Ashby, *An Introduction to Cybernetics* (1956): requisite variety.
- Chris Argyris & Donald Schön, *Organizational Learning* (1978): single- and double-loop learning.
- Ramadge & Wonham, “Supervisory Control of a Class of Discrete Event Processes” (1987), DOI `10.1137/0325013`: disable unsafe controllable events while preserving allowed behavior.
- Kephart & Chess, “The Vision of Autonomic Computing” (2003), DOI `10.1109/MC.2003.1160055`: autonomic/MAPE-K lineage.
- van der Aalst et al., “Workflow Patterns” (2003), DOI `10.1023/A:1022883727209`: branching, synchronization, cancellation, and workflow structure.
- Brun et al., “Engineering Self-Adaptive Systems through Feedback Loops” (2009), DOI `10.1007/978-3-642-02161-9_3`.
- Humble & Farley, *Continuous Delivery* (2010); Beyer et al., *Site Reliability Engineering* (2016): small batches, observability, risk, rollback, and postmortems.
- Yao et al., ReAct (`arXiv:2210.03629`); Shinn et al., Reflexion (`arXiv:2303.11366`); Madaan et al., Self-Refine (`arXiv:2303.17651`): feedback-driven agent iteration, with external-ground-truth caveats.
- Anthropic, “Building Effective Agents” (2024): prefer simple composable workflows; use evaluator-optimizer only with clear criteria; require ground truth, checkpoints, and stopping conditions.
- Every, “Compound Engineering”: `Plan → Work → Review → Compound → Repeat`; useful industry method, not a formal academic standard.

## P0 code convergence pattern

When an automated controller can claim tasks, do not let it invoke a low-level `claim` mutation after filtering only on `dispatchable`.

Use one of these safe patterns:

1. Single task: invoke the canonical `auto-claim-and-handoff --task <id>` bridge and require `status=OK`, `claimed=true`, and a non-empty handoff.
2. Batch selection: project **every selected task** through the exact-task eligibility SSOT with selfcheck enabled, then apply the same execution-flow dry-run/dispatch decision as the single-task bridge before the first claim mutation. Return structured `eligibility_decisions` for accepted and denied tasks.
3. Batch mutation/executor: invoke canonical `auto-claim-and-handoff` independently for every exact task. Do not switch back to low-level `claim` after a manifest has been approved. A manifest, `dispatchable=true`, resource headroom, or operator batch approval is not a substitute for exact eligibility, execution-flow, write-guard, and handoff gates.

At every worker boundary (`claim-cycle`, queued `execute-cycle`, event-driven `consume-claimed`, and cron/tick batch executor), reject an empty handoff before `claimed → running`. Propagate the canonical handoff, run id, and proof metadata to the consumer. Release through the normal retry/blocked lifecycle with a structured reason such as `missing_handoff_contract`; never fabricate a handoff or continue merely because an envelope or batch lease exists.

Keep these TDD counterexamples:

- controller invokes low-level `claim` rather than canonical eligibility + handoff;
- parallel selection contains one allowlisted and one unallowlisted task;
- an allowlisted parallel task is blocked by selfcheck or execution-flow but is still claimed;
- a cron/tick batch executor treats `dispatchable=true` or manifest approval as claim authority;
- a canonical batch denial still triggers a worker;
- claimed item with an empty handoff attempts envelope creation or `running` transition;
- a denied task changes state despite a fail-closed eligibility decision.

Verification must cover event-hook routing, dynamic/cron dispatch, the parallel batch bridge, and the periodic controller. A green controller unit test alone does not prove cross-controller policy convergence.
