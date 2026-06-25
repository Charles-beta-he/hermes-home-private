# Parent/child taskpool stall scenarios — multi-model advisory synthesis

Generated: 2026-06-26T01:25:56+08:00

## Multi-model status

A live `consult_models.py` run was executed with Claude Opus 4.8, MiMo v2.5 Pro, and DeepSeek v4 Pro available in the discussion layer.

Result: `degraded_not_certified`.

Reason: planner fan-out was below min quorum (`2/3`, min `3`) and concrete implementation suggestions came from only one planner. Therefore this document treats model output as advisory scenario discovery, not as certification authority.

Evidence:
- prompt: `/Users/charles/.hermes/workflows/taskpool-governance/parent-child-stall-scenario-multimodel-prompt-20260626.md`
- state: `/Users/charles/.hermes/workflows/taskpool-governance/evidence/parent-child-stall-scenario-state-20260626.json`
- discussion: `/Users/charles/.hermes/workflows/taskpool-governance/evidence/parent-child-stall-scenario-discussion-20260626.json`
- discussion sha256: `714d8fba954a24497bc729b2404561341f5917266644b0fecb98b99ddf87c99c`

## Recommended next implementation order

P0 next:
1. S5 parent evidence backfill missing detector
2. S7 hidden blocked descendant detector
3. S4 missing child file contract

P1 next:
4. S2 stale claim occupancy report integration
5. S1 concurrency false contention grouping
6. S8 derived dashboard mismatch

P2:
7. S6 cyclic/depth guard
8. S9 durable certification artifact receipt
9. S10 degraded multi-model advisory classification hardening

## Scenario table

| ID | Scenario | Symptoms | Detection signal | Minimal safe resolver behavior | Test case |
|---|---|---|---|---|---|
| S1 | Concurrency false contention | Many unrelated children share one coarse parallel_boundary; dispatchable stays high while selected_count low and parallel_boundary_conflict/capacity skips repeat. | Emit boundary_collision_group with shared boundary, task ids, and independent evidence paths. | Read-only: keep tasks pending; recommend boundary split proposal; never override conflict lock. | Fixture with two child tasks under same parent, different workspaces/evidence axes but same boundary; assert diagnostic action=boundary_false_contention_possible. |
| S2 | Stale claim occupancy | claimed>0/running=0 or worker alive=0; task appears owned but no process can finish it. | Compare claim_expires_at/run_id with worker-jobs; emit stale_claim_detected and owning actor. | Read-only in resolver; dedicated claim reconciler may release only after TTL + worker absence proof. | Expired claim with no worker in fixture -> stale_claim_count=1 and no lifecycle mutation. |
| S3 | Stale child-status evidence | Parent evidence says child pending/claimed/running/review while child file is now done. | Current implementation: stale_evidence_count and stale_evidence child_id/evidence_status/current_status. | Keep parent blocked if certification still required; otherwise reopen only through parent ratification refresh. | Existing test asserts stale_evidence_count=1 when parent carries pending proof but child is done. |
| S4 | Missing child file | Parent auto_subtask_children includes ids that cannot be loaded from canonical task notes. | missing_children list plus file existence/readability error class. | Fail closed: keep parent blocked; suggest recover child note or mark split contract invalid. | Parent references child id with no markdown file -> action=missing_child_file, ready_for_parent=false. |
| S5 | Child done but parent evidence not backfilled | All child files are done but parent lacks proof:child-task:*:done / axis proof; auto-close gates reject parent. | children_done=true and missing_backfill_for axes list. | Read-only diagnostic first; optional backfill command writes only evidence receipts, not done status. | Done child with axis but parent evidence empty -> parent_evidence_backfill_required. |
| S6 | Cyclic or too-deep split tree | Parent A waits for B; B points back to A, or depth > configured max; resolver loops or keeps splitting. | DFS over auto_subtask_parent/children with visited set; emit cycle_path/depth_exceeded. | Keep blocked; stop auto-split; require human/project epic refactor. | A->B->A and A->B->C->D fixtures assert cycle/depth diagnostics. |
| S7 | Hidden blocked descendant | Direct children done/ready but a grandchild or descendant is blocked; parent appears ready falsely. | Recursive descendant scan with blocked/open descendant list. | Fail closed: keep parent blocked_hidden_child_required; suggest collapse/flatten child tree. | Child done with linked blocked grandchild -> ready_for_parent=false or hidden_blocked_descendant=true. |
| S8 | Derived dashboard mismatch | dashboard/control-center says blocked/review counts differ from canonical list/dispatch tick. | Compare canonical iter_tasks counts with derived view timestamps/checksums; emit derived_view_stale. | Refresh derived views only; do not change task lifecycle. | Mutate task after dashboard write; assert mismatch diagnostic and refresh-only suggested action. |
| S9 | Certification artifact pruned or inaccessible | blocked-resolve-step cannot load multimodel_last_discussion_artifact; taxonomy/ratification data unavailable. | taxonomy_warning already exists; add artifact_error_class and durable_receipt_missing. | Keep blocked_missing_taxonomy_artifact; regenerate/refresh certification evidence. | Existing missing artifact test asserts warning is non-fatal and task stays blocked. |
| S10 | Noop-vs-change multi-model ambiguity | One planner proposes concrete diagnostic patches while another votes noop; final result degraded_not_certified. | fanout_certification below_min_quorum + concrete_model_count + noop_only_model_count. | Downgrade to advisory; require re-fanout before claiming certification. | Use consult_models degraded fixture and assert scenario report labels advisory-only. |

## Certification boundary

Do not claim these scenarios as multi-model certified. The run produced useful advisory scenario candidates but remained `degraded_not_certified`. Any scenario promoted into code should be implemented as a small TDD slice with deterministic local tests and live dry-run readback.
