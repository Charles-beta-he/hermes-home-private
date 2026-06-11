# Product Workflow Taskpool Ingest Bridge

Scope: bridge a `product-workflow-operating-system` workspace into Hermes' existing governed taskpool ingest path. Applicability: use when a workflow workspace has deliberate task candidates under `tasks/task-candidates.json` and the user wants them routed into taskpool. Anti-condition: do not use for broad news/trend summaries, placeholder candidates, or unverified social-post claims.

## Bridge script

Use:

```bash
python3 ~/.hermes/scripts/product_workflow_taskpool_ingest.py --slug <workflow-slug> --json
```

Add `--write` only when the candidate JSON has been reviewed and taskpool mutation is intended:

```bash
python3 ~/.hermes/scripts/product_workflow_taskpool_ingest.py --slug <workflow-slug> --write --json
```

## Contract

The workspace must contain:

- `00-intake/intent-card.md`
- `workflow-state.yaml.md`
- `evidence/evidence-bundle.json`
- `tasks/task-candidates.json`

`tasks/task-candidates.json` must use schema `daily_report_task_candidates_v1` because the bridge delegates actual task creation to the canonical `daily_report_task_ingest.py` path.

## Safety behavior

- New workspaces start with `candidates: []`.
- Placeholder values such as `<project>` are rejected before ingest.
- Relative `evidence_bundle` paths are resolved against the workspace before delegating to the canonical ingest bridge.
- Empty candidate lists return `NO_CANDIDATES` unless `--allow-empty` is used.
- Actual task creation is still controlled by `daily_report_task_ingest.py`, including duplicate checks, multimodel normalization, evidence gates, and `brain_task_orchestrator.py add`.
- Product workflow execution-flow fields are validated and passed through when present: `workflow_stage`, `completion_boundary`, `harness_surfaces`, `required_artifacts`, and `external_side_effects`.

## Execution-flow field contract

Use these optional fields when downstream dispatch/claim/closeout needs precise gates:

```json
{
  "workflow_stage": "evidence|execute|review|writeback|human_gate|done",
  "completion_boundary": "document_only|taskpool_candidate|implementation_ready|shipping_packet|launched_observing",
  "harness_surfaces": ["command", "ui", "api", "browser", "security", "performance", "metrics"],
  "required_artifacts": ["command_output", "browser_screenshot", "api_readback", "security_audit", "performance_audit", "metric_readback"],
  "external_side_effects": false
}
```

These fields flow through:

```text
product_workflow_taskpool_ingest.py
  → daily_report_task_ingest.py
  → brain_task_orchestrator.py add
  → task frontmatter
  → execution_flow_evaluator.py / dispatch-dry-run / auto-claim / closeout gate
```

## Verification sequence

1. `python3 ~/.hermes/scripts/product_workflow_taskpool_ingest.py --slug <slug> --json`
2. If result is `NO_CANDIDATES`, either stop or edit `tasks/task-candidates.json` deliberately.
3. For a non-empty proposal, inspect dry-run actions and normalized proposal path.
4. Run with `--write --json` only after the candidate is concrete, evidence-backed, and authorized.
5. Read back the taskpool result and verify created/skipped/invalid counts.

## Pitfalls

1. Do not treat scaffolded template examples as real task candidates.
2. Do not bypass the canonical ingest script; that path owns dedupe and multimodel normalization.
3. Do not enqueue product ideas that lack acceptance evidence and anti-drift checks.
