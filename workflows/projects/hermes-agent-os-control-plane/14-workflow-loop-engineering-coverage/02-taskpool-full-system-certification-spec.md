# Taskpool Full-System Local Certification — Canonical Spec

Date: 2026-07-10
Project: hermes-agent-os-control-plane
Mode: certification
Risk: critical control-plane review; implementation limited to local reversible code/tests/docs. No external dispatch, delivery, OAuth, credentials, deploy, publish, push, destructive cleanup, or production write.

## Objective model

### Goal

Certify the complete **local Hermes taskpool subsystem** as a coherent bounded lifecycle system, not merely its claim bridge. Certification must bind architecture inventory, deterministic lifecycle gates, proof/ratification semantics, controller convergence, worker handoff, retry/reconcile recovery, isolated E2E behavior, store/projection consistency, full relevant tests, runtime readback, and independent verifier evidence.

### Certification boundary

Included:

- local task intake and task-file parsing;
- lifecycle states and transition validation;
- eligibility, selfcheck, permission, execution-flow and write guards;
- event hook, dynamic runner/cron, dispatch tick, hourly controller and manual/canonical bridge classification;
- claim lease, handoff, worker-consumer, retry/reconcile and orphan recovery;
- evidence/proof gates, advisory/document-only completion semantics, multimodel/ratification fail-closed behavior;
- parent-child evidence aggregation and false-positive done detection;
- local Markdown/task-vault state and taskpool projections;
- isolated local canary/fault injection in temporary vaults only;
- taskpool-related production scripts and tests;
- current runtime read-only health and scheduler/claim readback.

Excluded from successful local certification but required to remain explicitly fail-closed:

- external delivery, Telegram/Lark Task API writes, OAuth recovery, credentials, production adapters;
- deployment, publish, push, payments, destructive cleanup and broad fan-out;
- unrelated Agent OS procedures and unrelated product/project task correctness.

External authority-blocked procedures are not taskpool certification failures if they are represented as blocked-by-authority, cannot be mistaken for healthy, and no taskpool completion depends on fabricated external evidence.

### Current evidence

- Scoped controller-convergence P0 is independently certified: 209 relevant tests passed twice; no automated low-level claim bypass found.
- Fresh final local taskpool manifest: `570 passed in 133.33s`; this includes controller, lifecycle, proof, recovery, bridge and dynamic-runner suites discovered under `scripts/`.
- Fresh Native Kanban manifest: `604 passed, 1 skipped in 36.67s` across DB, core, dashboard, tools, worker-runs and gateway watcher suites.
- Fresh isolated full-lifecycle canary: `1 passed, 117 deselected in 1.52s`, covering intake -> eligibility -> canonical claim/handoff -> running -> review -> strict ratification -> done -> selfcheck/proof readback in a temporary vault with file-backed dashboard and ledger readback artifacts.
- Fresh live `selfcheck --json`: PASS, 818 tasks, zero invalid boundary tasks, zero dispatchable tasks; four semantic profile warnings remain WARN-only.
- Fresh live `proof-check --include-active --json`: PASS, 723 checked, zero failures and 92 terminal historical proof-format warnings.
- Fresh active-claim readback: zero active and zero orphan claims. Escape guard is not triggered and reports zero current timeouts.
- Historical closeout audit remains explicitly outside the certification truth claim for old task outcomes: 722 done, 571 heuristic suspicious (`100 implementation_done_missing_real_chain_validation`, `471 unchecked_acceptance_needs_review`). These records are historical debt, not silently certified by this system implementation packet.
- Worktree is materially dirty and mixed-lineage; certification must bind to exact file hashes and cannot claim a clean release commit unless isolated reproduction is proven.

## Non-goals

- Do not weaken proof, ratification, lifecycle, reconciliation, or handoff gates to make tests green.
- Do not rewrite/force-close/archive historical tasks solely for dashboard cleanliness.
- Do not mutate live task state for canary purposes.
- Do not equate unit tests, model votes, process spawn, task `done`, or proof hash presence with complete certification.
- Do not expand autorun/allowlists or open external actions.

## Invariants

1. Every automated mutation path uses the canonical exact-task authority inside the mutation boundary.
2. `claimed -> running` requires a non-empty verified handoff; partial claim failure releases deterministically.
3. Lifecycle transitions are deterministic, evidence-gated, and history-valid.
4. `done` is interpreted with lane/completion boundary; document-only advisory done never implies certified truth or implementation authority.
5. Required certification/ratification failure cannot produce certified/done where that gate applies.
6. Reconcile never steals a live owner and does recover orphaned/expired claims.
7. Duplicate events and retries are idempotent and budget bounded.
8. Proof/evidence status is consistent across standalone and aggregate readback surfaces, or differences are explicitly scoped and machine-visible.
9. Temporary certification harnesses cannot touch the live task vault, scheduler, workers, gateway, or external services.
10. Independent review cannot certify claims unsupported by command/artifact evidence.

## Acceptance criteria

- AC1 Architecture inventory: all local taskpool production entrypoints, stores, adapters/projections, controllers and lifecycle authorities are enumerated and classified; no unknown automated mutation caller remains.
- AC2 Lifecycle: every valid state/transition and every invalid/negative transition is covered, including `certified`, advisory document-only closeout, review/done proof gates and lifecycle-history validation.
- AC3 Claim/execution: canonical eligibility+selfcheck+execution-flow+write-guard+claim+handoff behavior and denial/partial-success cleanup pass across all automated controllers.
- AC4 Recovery: deterministic tests cover duplicate event, lease expiry, orphan worker/claim, worker rejection/crash, retry budget/no-progress, partial claim and idempotent reconciliation.
- AC5 Proof/ratification: structured/unstructured evidence, hash validity, negative markers, degraded quorum, missing ratification, advisory-only evidence and false-positive done cases fail or classify exactly as specified.
- AC6 Parent/store/projection: parent-child evidence aggregation, Markdown parsing/write-readback, canonical task identity and relevant local projections are consistent under isolated tests.
- AC7 E2E canary: an isolated temporary-vault lifecycle executes intake -> eligible -> claim/handoff -> running -> evidence -> review -> done with real local code paths and readback; parallel negative canaries prove denial and recovery. No live task is changed.
- AC8 Full relevant verification: complete discovered taskpool test matrix, py_compile/static checks, scoped diff check and runtime read-only commands pass with no unexplained failure.
- AC9 Runtime health: live selfcheck, proof/evidence, claim/worker registry and scheduler status are read back. Historical debt is either repaired with exact evidence or formally classified without contradiction; no active orphan/stale claim remains.
- AC10 Independent certification: at least one fresh independent read-only verifier audits the final hashes and evidence matrix and returns PASS with no unresolved High/Critical finding.

## Negative cases required

- allowlist/permission/selfcheck/execution-flow/write-guard denial;
- claim success plus missing handoff or handoff write failure;
- consumer rejection after background spawn;
- duplicate creation/event/retry;
- expired claim and live-owner claim distinction;
- worker crash/no receipt and stale owner reconciliation;
- invalid transition and invalid lifecycle history;
- malformed/unstructured evidence and missing/invalid proof hash;
- `PASS_ADVISORY_ONLY`, degraded quorum or ratification-pending incorrectly granting certified authority;
- advisory document-only done incorrectly projected as implementation/certification;
- parent done despite incomplete child/evidence aggregation;
- task-vault/store inconsistency;
- aggregate evidence spine masking standalone proof failure.

## Candidate paths and decision

A. Certify from the existing 209-test scoped bundle. Rejected: omits lifecycle/proof/recovery/store/E2E surfaces.

B. Mutate a real task through the live scheduler. Rejected: unnecessary state risk, concurrent controllers and ambiguous evidence ownership.

C. Selected: inventory first; add/fix deterministic tests in existing harnesses; run isolated temporary-vault E2E and fault injection; reconcile read-only live health; then run complete relevant suite and independent final review. Historical/live mutations require a separately justified exact reversible step and are never performed merely to obtain PASS.

## Architecture inventory

| Surface | Canonical role | Mutation authority / safety boundary | Verification |
|---|---|---|---|
| `brain_task_orchestrator.py` | Markdown task SSOT, lifecycle, eligibility, exact claim, handoff, proof and ratification | deterministic transition table; exact-task claim; write guard; non-empty handoff | included in 570-test manifest; isolated E2E |
| `agent_team_controller.py` | hourly/manual controller | calls canonical `auto-claim-and-handoff --task`; structured denial; release on missing handoff | scoped P0 209/209 plus final manifest |
| `brain_task_dispatch_tick.py` | batch/event selection | candidate selection only; each mutation calls canonical bridge | scoped P0 and final manifest |
| `brain_task_idle_runner.py`, `brain_task_autorun_step.py` | idle/manual autorun wrappers | eligibility/selfcheck/execution-flow before mutation | final manifest |
| `taskpool_dynamic_runner.py`, `taskpool_dynamic_runner_cron.py` | outer event-driven runner and cron adapter | bounded cycle; human-escape precheck; advisory no-op on no change; cross-process `flock` | 12 dynamic-runner tests; final manifest |
| taskpool event hook / envelope bus | mutation trigger and receipts | duplicate/budget/escape guards; structured terminal receipts | final manifest and prior 45-test fault audit |
| `task_pool_guardian.py` and silent wrapper | lease/orphan reconciliation | does not steal live owner; bounded repair | final manifest |
| `taskpool_active_claim_guard.py`, `taskpool_escape_guard.py` | report-only live safety readback | mutation requires separate explicit flags | live zero-active/orphan and no escape trigger |
| `taskpool_drain_until_empty.py` | bounded drain utility | defaults DENIED; explicit `--execute`; positive max cycle | 3 tests plus default exit 2 readback |
| `taskpool_proof_gate.py`, orchestrator proof/ratification | evidence boundary | malformed fields, invalid budgets/hashes and unresolved ratification fail closed | 11 focused tests plus final manifest and live proof PASS |
| `taskpool_done_closeout_audit.py` | historical heuristic audit | report-only unless `--strict`; never rewrites tasks | 2 tests; historical debt classified separately |
| `kanban_bridge.py`, silent wrapper | one-way Local Brain -> Native Kanban observability projection | defaults DENIED without `--execute`; canonical note read-only by default; held cross-process `flock`; atomic state; unparseable IDs fail closed | 8 isolated bridge tests, including real subprocess crash-release |
| Native Kanban DB/tools/dashboard/worker watchers | local execution-plane store and APIs | DB transactions, worker lifecycle and prompt pinning | 604 passed, 1 skipped |
| Markdown task vault / proof JSONL / bridge state / Kanban SQLite | stores and projections | Markdown is canonical for Local Brain; projections cannot grant lifecycle authority | isolated canary, bridge transaction rollback test, Native Kanban suite |
| Lark/Telegram/external adapters | excluded external surfaces | remain authority/credential blocked; cannot contribute fabricated completion evidence | Agent OS readback explicitly blocked/degraded where applicable |

Known adjacent utilities (`taskpool_parent_evidence_aggregator.py`, validation-suite dry-run, standard task creator, tenant backfill dry-run, debt ledger and watch report) are included in the discovered task-oriented test manifest where tests exist. Live apply/create modes were not invoked.

## Evidence ledger / Converge matrix

| Claim | Required evidence | Final state |
|---|---|---|
| complete architecture inventory | production entrypoint/store/controller map and prior caller audit | PASS within local boundary; external adapters explicitly excluded/blocked |
| lifecycle correctness | transition, history, invalid path and isolated readback tests | PASS: final manifest + isolated canary |
| controller convergence | P0 packet + refreshed final tests | PASS: independently certified scoped P0; included in 570 manifest |
| recovery/idempotency | duplicate/retry/lease/orphan/partial-claim/lock fault tests | PASS: prior 45-test audit, parallel rollback tests, guardian/event suites, `flock` contention tests |
| proof/ratification correctness | malformed proof, strict ratification, live proof readback | PASS for current implementation/active gate; 92 historical terminal warnings explicitly debt-classified |
| store/projection consistency | temporary DB/vault, transaction rollback, readback | PASS: bridge 8 tests, Native Kanban 604/1, temporary-vault canary |
| local E2E | intake through done and cleanup-isolated readback | PASS: `1 passed, 117 deselected in 1.52s`; temporary directory owns cleanup and file-backed readback artifacts |
| full relevant suite | explicit command manifests and exit codes | PASS: local 570; Native Kanban 604 passed/1 skipped; py_compile and scoped diff checks exit 0 |
| runtime health | selfcheck/proof/claims/escape readback | PASS for active local boundary: 818 tasks, 0 dispatchable, 0 active/orphan, 0 proof failures, no current escape |
| historical outcome truth | proof/closeout audit for all old `done` records | EXCLUDED/NOT CERTIFIED: 92 proof-format warnings and 571 heuristic suspicious done records retained as debt |
| clean release/install baseline | clean commit and replay/install evidence | NOT CLAIMED: mixed-lineage dirty worktree; no commit/push performed |
| independent final verifier | fresh read-only PASS bound to final hashes/evidence | pending |
| multi-model review | configured Agent OS provider quorum | degraded/authority-blocked; independent same-runtime adversarial reviews may advise but cannot substitute for real multi-model authority |

## Stop and rollback

Continue while safe local/reversible work remains. Stop only for exact external authority, credentials, destructive historical cleanup, production/deploy/push, or evidence that cannot be obtained locally. Roll back only files changed by this certification slice; temporary vaults must be self-contained and removed by their own temp-directory cleanup. Preserve all historical/live task artifacts unless an exact repair is independently justified and read back.
