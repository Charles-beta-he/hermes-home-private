# Taskpool parent/child flow governance — arguments and core works

Generated: 2026-06-26T00:29:07+08:00
Scope: explain and harden the scenario where a large parent task is split into many levels of child tasks and appears stuck because of concurrency, dependency, or evidence-consumption gaps.

## Core arguments

1. Parent-child decomposition is a dependency-structure problem, not merely a scheduling problem. If child completion evidence is not consumed by the parent closeout rule, more concurrency only increases WIP and stale proof.
2. Concurrency should follow true conflict boundaries. Coarse `parallel_boundary` values produce false contention; overly fine values produce unsafe simultaneous writes. The control plane needs explicit boundary keys plus readback.
3. Queueing/WIP theory predicts latency blow-up when many children are opened before the bottleneck resolver can certify and aggregate them.
4. Design Structure Matrix thinking predicts rework loops when child tasks depend cyclically or when parent criteria are not decomposed into mutually sufficient axes.
5. Theory-of-Constraints says the bottleneck here is usually not worker count; it is the parent evidence aggregator / certification gate.
6. SRE-style automation requires fail-closed lifecycle gates, observable receipts, and rollback paths rather than force-closing blocked parent tasks.
7. Product-development-flow literature favors small batches: one parent should generally split into a shallow, axis-complete child set with a deterministic aggregation step.

## Core works map

| # | Work | Author | Why it matters for taskpool |
|---:|---|---|---|
| 1 | The Mythical Man-Month | Frederick P. Brooks Jr. | coordination overhead grows nonlinearly with people and interfaces |
| 2 | The Goal | Eliyahu M. Goldratt | optimize the system bottleneck, not local activity |
| 3 | Critical Chain | Eliyahu M. Goldratt | shared resource contention and hidden buffers delay project flow |
| 4 | Managing the Design Factory | Donald G. Reinertsen | limit WIP and expose blocked flow |
| 5 | The Principles of Product Development Flow | Donald G. Reinertsen | small batches, queues, and economic WIP limits control latency |
| 6 | Design Structure Matrix Methods and Applications | Steven D. Eppinger and Tyson R. Browning | dependency structure predicts iteration, rework, and coordination loops |
| 7 | Out of the Tar Pit | Ben Moseley and Peter Marks | separate essential state/complexity from accidental control complexity |
| 8 | Team Topologies | Matthew Skelton and Manuel Pais | cognitive load and team/API boundaries constrain sustainable flow |
| 9 | Site Reliability Engineering | Betsy Beyer et al. | automation needs explicit SLOs, error budgets, and safe rollback |
| 10 | Accelerate | Nicole Forsgren, Jez Humble, and Gene Kim | fast flow requires deployment safety, feedback loops, and low-friction recovery |

## Landed local slice

Implemented read-only tool:
- `/Users/charles/.hermes/scripts/taskpool_parent_evidence_aggregator.py`

Tests:
- `/Users/charles/.hermes/scripts/test_taskpool_parent_evidence_aggregator.py`

Coverage evidence:
- `python3 -m coverage report -m taskpool_parent_evidence_aggregator.py` -> 100% statement coverage for the new slice.

Live dry-run report:
- `/Users/charles/.hermes/workflows/taskpool-governance/evidence/parent-evidence-aggregation-freeze-ssot-20260626.json`
- sha256: `c1ca45e8fd87a8ee411ba4bfc026cd0087974af408a32502d2fc2a3c3d4c5ad7`

## Live report interpretation

Parent: `2026-06-21-freeze-mobile-offline-avatar--travel-ssot`

- ready_for_parent: `True`
- action: `keep_blocked_certification_required`
- done_count/child_count: `3/3`
- axis_summary: `{'framing': 'done', 'patch_normalization': 'done', 'quota_observability': 'done'}`
- remaining_gate_reasons: `['architecture_target', 'evidence_bundle_contract', 'expected_participants_contract', 'explicit_multimodel_reason', 'explicit_requires_multimodel', 'loop_non_convergence', 'missing_required_model_consulted:mimo-v2.5-pro', 'missing_required_model_vote:mimo-v2.5-pro', 'mission_envelope', 'model_count_below_required:2/3', 'models_consulted_below_required:2/3', 'multimodel_gate:FAIL', 'truth_gate_contract']`
- stale_evidence count: `6`

Conclusion: child-axis evidence aggregation is complete enough to diagnose the parent, but the parent still should not be force-closed because remaining multimodel/certification gate reasons are explicit. The next safe step is a parent ratification refresh or a resolver path that consumes this report and reruns certification, not broader concurrency.


## 2026-06-26T00:39:13+08:00 blocked-resolve-step integration readback

Live command:
- `python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --task 2026-06-21-freeze-mobile-offline-avatar--travel-ssot --authority dispatch-hint --json`

Evidence:
- `/Users/charles/.hermes/workflows/taskpool-governance/evidence/blocked-resolve-parent-aggregation-freeze-ssot-20260626.json`
- sha256: `d95e658dee6ad0b145fb8f387133ea0718dfae01b08961122a41b8525c4edbaa`

Observed resolver output:
- status: `OK`
- resolved_count: `0`
- kept_blocked_count: `1`
- parent_aggregation.action: `keep_blocked_certification_required`
- parent_aggregation.suggested_next: `parent_ratification_refresh`

Interpretation: blocked-resolve-step now exposes child evidence aggregation directly in the keep-blocked row, proving the parent is not concurrency-stuck while preserving certification gate boundaries.
