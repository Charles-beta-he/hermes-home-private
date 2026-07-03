# Normal automation advance chain

Scope: class-level Hermes taskpool/control-plane operation pattern, not a record of one project, task, commit, provider incident, or session status.

Applicability: use when an operator is asked to continue advancing blocked/retry taskpool work without punting, and the live pool may contain stale child state, human-escape terminal envelopes, retry windows, active worker/multimodel ownership, certification loops, or ordinary-worker redispatch churn.

Anti-conditions: do not use this reference to mark tasks done, weaken certification, bypass permission/credential/external-write/destructive/payment/publish gates, or memorialize current task progress. If the remaining blocker is provider/quorum availability or an exact human authority gate, stop with a DecisionPacket.

## Objective model

Goal: restore the pool to honest normal flow by draining every safe reversible step and converting non-actionable loops into explicit gates.

Success evidence:
- worker and multimodel registries show no unaccounted live owner before mutation.
- Parallel dry-run either selects a genuinely eligible task or reports selected_count=0 for real gates.
- Ready parents have ready=true, open_children=[], and missing_children=[] without stale child-status proofs.
- Certification-required tasks are not ordinary-worker-dispatched after no discussion result or quorum failure.
- Final readback includes tests/selfcheck/proof-check/job liveness and allowlist leak status when code or policy changed.

Non-goals:
- no force-done;
- no certification downgrade from model agreement/advisory output;
- no bypass of human, credential, publish/deploy, external-dispatch, destructive, or payment boundaries;
- no repeated rerun of a parent/worker when the real blocker is certification economy/model availability.

## Capability graph

```yaml
normal_automation_advance_chain:
  kind: workflow
  consumes:
    - canonical_taskpool_state
    - worker_job_registry
    - multimodel_job_registry
    - escape_guard_state
    - task_notes_and_evidence
  produces:
    - repaired_control_plane_state
    - dispatch_or_gate_decision
    - committed_regression_fix_when_needed
    - continuation_packet_if_hard_gate_remains
  subnodes:
    - state_snapshot
    - deterministic_maintenance
    - live_owner_reconciliation
    - child_parent_sync
    - dispatch_selection_audit
    - multimodel_route_or_certification
    - loop_breaker_bugfix
    - final_readback
  gates:
    - no_live_owner_before_requeue
    - child_ready_not_parent_done
    - certification_not_worker_loop
    - proof_lifecycle_gate
    - scoped_commit_gate
```

## Normal chain

1. Snapshot before action.
   - Read canonical taskpool list.
   - Read worker job registry.
   - Read multimodel job registry.
   - Read human-escape guard state.
   - Run parallel dispatch dry-run.

2. Deterministic maintenance first.
   - Reconcile due retries.
   - Auto-close review tasks through normal lifecycle gates.
   - Sync auto-subtask parents.
   - Run blocked resolver.

3. Human-escape / terminal-envelope gate.
   - If the escape breaker is active, map every terminal envelope to canonical task status and live owner state.
   - Ack only when terminal rows are already represented as retry/blocked/pending and no worker/multimodel/process owner remains.
   - Never convert FAILED/TIMEOUT envelopes to done.

4. Live owner rule.
   - If a worker or multimodel job is alive for the task, wait and read logs; do not steal or transition.
   - If a task is running/claimed but job registry and process text prove no owner exists, reconcile or transition to pending/retry with structured evidence only.

5. Child-parent rule.
   - Finished children are evidence, not parent completion.
   - If children are terminal but a parent has stale open_children, run or repair sync/split logic so open/missing/ready are recomputed from actual child states.
   - If children are ready and parent still fails certification, stop child churn and run parent ratification/targeted multimodel path.

6. Dispatch selection audit.
   - Treat broad parallel dry-run selection as a candidate, not authority.
   - Run exact eligibility check before claim/allowlist.
   - If broad selection chooses a parent/task that exact eligibility denies, repair selection/dispatchability logic or run canonical reconciliation; do not add allowlist to force it.

7. Multimodel routing vs thinking.
   - Deterministic maintenance uses no model.
   - Routing-plan review is advisory: choose worker vs thinking vs gate; it cannot mark done.
   - Task-content thinking/certification uses governed durable background multimodel intervention for long T2/T3 work.
   - Wait for jobs and inspect gate, decision, models_consulted, missing votes, quota confidence, and discussion artifact.

8. Certification loop breaker.
   - If a certification-required task returns no discussion result, or FAIL/CONTINUE_LOOP with missing required votes/quorum, ordinary worker dispatch is not progress.
   - Convert the state into an explicit blocked gate or repair the dispatch predicate under TDD so the task is not selected for a worker loop.
   - Acceptable blocker text: required model votes missing, quorum not met, low quota confidence/provider health, no discussion result, or long-term alignment unresolved.

9. Code/policy repair discipline.
   - Reproduce the false loop with a targeted RED test.
   - Patch the smallest predicate/gate.
   - Run targeted test, then relevant taskpool/precommit regression.
   - Commit scoped files only after precommit passes.

10. Final readback.
   - Regression tests relevant to touched code.
   - Selfcheck and proof-check.
   - Worker and multimodel liveness.
   - Parallel dispatch dry-run.
   - Human-escape guard.
   - Allowlist/temp leak check if allowlists were touched.

## Multi-model thinking frame for operators

Use four lanes, even when not calling external models:

- Control-plane lane: what state transition or predicate is actually wrong?
- Runtime lane: who owns the task right now, and is the owner alive?
- Certification lane: is this a task-content truth/ratification problem, provider/quorum problem, or advisory-only result?
- Boundary lane: what side effects, completion claims, or durable writes are forbidden without authority?

When external models are available, map lanes to capability surfaces rather than simple majority voting. Model output remains advisory until tied to taskpool evidence and lifecycle gates.

## DecisionPacket shape for remaining gates

```text
Objective:
Completed evidence:
Pending action:
Requested authority:
Rollback / escape hatch:
Post-action verification:
Continuation state:
```

## Common pitfalls

- Treating selected_count>0 as permission to claim. Always run exact eligibility.
- Re-dispatching ordinary workers after certification no-discussion/FAIL. That is churn, not progress.
- Leaving a false running row after foreground timeout. Prove no owner, then requeue; never mark done.
- Creating more children when all axes are done and the parent needs ratification.
- Letting human-escape terminal envelopes block forever after they are already mapped to blocked/retry and no owner is alive.
- Reporting iteration/cycle exhaustion as final truth without fresh readback.
