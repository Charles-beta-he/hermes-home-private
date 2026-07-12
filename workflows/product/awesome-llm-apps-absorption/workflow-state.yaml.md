# Workflow State

```yaml
schema: product_workflow_state_v1
workflow: awesome-llm-apps-absorption
state: ready_for_review
current_stage: temporary_workflow_built
source_commit: 426cfa66b5fd832090038c36e50a6aa1dab3119c
artifacts:
  spec: spec-packet.md
  catalog: module-pool/capability-catalog.json
  module_registry: module-pool/module_registry.json
  loop_runs: runs/
  temporary_workflow: temporary-workflows/awesome-functional-absorption.json
  report: report.md
  candidates: tasks/task-candidates.json
authority_boundary:
  external: false
  cron: false
  taskpool_write: false
  agentos: false
  publish: false
next_gate: "Select a concrete functional family for source-level review and owned runtime replication."
```
