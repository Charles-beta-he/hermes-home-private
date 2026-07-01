# Workflow Capability Graph Templates

Use these templates when modeling a new workflow family. Keep project-local paths, task IDs, and one-off evidence in scoped project docs rather than this reusable skill.

## Workflow family card

```yaml
workflow_family: string
version: 1
scope: string
anti_scope: []
primary_user_intents: []
common_partial_requests: []
full_chain_request: string
closure_targets: []
```

## Capability node

```yaml
capability_node:
  id: string
  kind: atomic_module | composite_module | workflow | agent_role | gate | adapter | artifact_template
  display_name: string
  responsibility: string
  consumes: []
  produces: []
  preconditions: []
  depends_on: []
  optional_depends_on: []
  subnodes: []
  gates: []
  agent_wrappers: []
  side_effects: none | local_write | external_read | external_write | physical_action | payment | publish | destructive
  closure_states: []
  can_be_used_as_module: true
  can_be_used_as_workflow: true
  can_be_delegated_to_agent: true
  cannot_prove: []
```

## Agent wrapper

```yaml
agent_wrapper:
  id: string
  wraps: []
  role: router | creator | reviewer | orchestrator | executor | monitor | verifier | publisher
  policy: []
  authority: read_only | local_write | external_read | external_write_requires_gate | physical_action_requires_gate | publish_requires_gate
  produces: []
  cannot_do: []
```

## Gate

```yaml
gate:
  id: string
  checks: []
  evidence_required: []
  outcomes:
    pass: string
    warn: string
    fail: string
    blocked: string
  retry_policy: string
  human_gate_when: []
```

## Evidence entry

```yaml
evidence_entry:
  stage_or_node: string
  input_refs: []
  output_refs: []
  review_refs: []
  claim_supported: string
  verdict: pass | warn | fail | blocked | assumption
  confidence: high | medium | low
```
