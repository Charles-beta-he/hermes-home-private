# Product Workflow ↔ Taskpool Execution Flow Alignment

Scope: aligning `product-workflow-operating-system` workspaces and task candidates with the taskpool unified execution-flow gate. Applicability: use when product workflow candidates are ingested into taskpool and then dispatched, claimed, reviewed, or closed out. Anti-condition: do not create a second taskpool or bypass the canonical `daily_report_task_ingest.py` / `brain_task_orchestrator.py` path.

## Core relationship

Product workflow owns the upstream product lifecycle and workspace artifacts:

```text
product workflow workspace
  → tasks/task-candidates.json
  → product_workflow_taskpool_ingest.py
  → daily_report_task_ingest.py
  → brain_task_orchestrator.py add
```

Taskpool execution flow owns downstream safety and lifecycle gates:

```text
task note
  → execution-flow-dry-run
  → dispatch-dry-run
  → auto-claim-and-handoff
  → review/done closeout gate
```

The bridge should enrich task candidates so the execution-flow gate can decide safely; it should not claim, execute, close, or mutate task lifecycle directly.

## Field alignment target

The canonical taskpool add path now supports these fields. Product workflow candidates should carry them through to task frontmatter when downstream dispatch, claim, review, writeback, or closeout needs precise gates:

- `workflow_stage`: `evidence | execute | review | writeback | human_gate | done`
- `completion_boundary`: `document_only | taskpool_candidate | implementation_ready | shipping_packet | launched_observing`
- `harness_surfaces`: `command`, `ui`, `api`, `browser`, `security`, `performance`, `metrics`
- `required_artifacts`: concrete proof names such as `command_output`, `browser_screenshot`, `api_readback`, `security_audit`, `performance_audit`, `metric_readback`
- `external_side_effects`: boolean or scoped list; true should normally route to hold/human gate before writeback or launch

Until those are first-class CLI/frontmatter fields, encode the same intent inside `objective`, `acceptance_evidence`, `anti_drift_check`, `truth_gate`, and structured evidence lines.

## Product lifecycle → execution-flow mapping

- Stages 1-3 (`intake`, `discovery`, `market evidence`): `workflow_stage=evidence`; missing evidence is usually the work objective, so dispatch may be allowed as evidence-gathering.
- Stages 4-8 (`strategy`, `metrics`, `PRD`, `risk`, `planning`): `workflow_stage=evidence` or `execute`; require artifacts and acceptance evidence, but not necessarily UI/API proof.
- Stage 9 (`build / real verification`): `workflow_stage=execute`; require command proof and UI/API harness surfaces when the task mentions browser/frontend/API/backend.
- Stage 10 (`AI-code shipping`): `workflow_stage=review`; closeout must require command proof plus browser/API/security/performance evidence as applicable.
- Stage 11 (`launch / GTM / growth`): `workflow_stage=writeback`; set `external_side_effects=true` and hold for explicit authority before publish/deploy/send/closeout.
- Stage 12 (`measure / retro / ratchet`): `workflow_stage=done` or `writeback`; require metric/readback evidence before final closeout or ratchet writeback.

## Evidence projection pattern

Product workflow evidence bundles are useful provenance, but execution-flow closeout currently depends on structured task evidence. When ingesting candidates, project important evidence into task-readable lines:

```text
artifact:/absolute/path/to/evidence-bundle.json
proof:product_workflow_evidence_bundle claims=<N> verified=<M> blocked=<K>
command:<verification command> PASS
proof:browser <screenshot or browser harness evidence>
proof:api <curl/readback evidence>
```

Do not let `evidence_bundle` alone stand in for implementation, browser, API, or launch proof. It should link claims to sources; closeout proof should show the requested behavior actually happened.

## Dispatch and closeout expectations

- `dispatch-dry-run` may allow evidence-gathering tasks even when closeout evidence is missing.
- `auto-claim-and-handoff` must fail closed on hard boundaries: permission, external side effect, destructive action, credential/private access material, value judgement, safety/legal, or explicit human gate.
- `review → done` must fail closed for implementation/work/UI/API tasks without feature-specific structured evidence.
- A product workflow bridge should return normalized proposals and dry-run actions before write; write mode should still delegate to canonical ingest and taskpool gates.

## Pitfalls

1. **Bridge-as-executor mistake**: the product workflow bridge is an intake adapter, not a dispatcher or closeout executor.
2. **Evidence-bundle laundering**: a JSON bundle that says evidence exists is not equivalent to `command:`, `proof:browser`, or `proof:api` closeout proof.
3. **Stage loss**: if lifecycle stage is not carried into task frontmatter, execution-flow falls back to status/title/body heuristics. This is safe but less precise.
4. **Launch/GTM side effects**: publishing, sending, deploying, closing external tasks, or production writeback should be represented as writeback/human-gate work, not ordinary execute work.
