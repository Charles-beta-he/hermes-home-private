# Composable Capability Graph Workflow Coverage

Use this reference when a session turns a concrete workflow/demo/product pattern into reusable Hermes workflow architecture, or when asked to check whether an abstraction covers other workflow families.

## Core correction

Do not treat `module`, `workflow`, and `agent` as strict layers. They are different views over the same composable capability graph.

A capability can be:

- a workflow internally;
- a module externally;
- an agent-delegated task operationally;
- a subgraph inside a larger workflow;
- a feature when exposed through UI/API.

Preferred framing:

```text
CapabilityGraph = CapabilityNodes + I/O contracts + agents + gates + evidence + closure states
```

## CapabilityNode contract

Every reusable node should declare:

```yaml
id: string
kind: atomic_module | composite_module | workflow | agent_role | gate | adapter | artifact_template
responsibility: string
consumes: []
produces: []
preconditions: []
depends_on: []
subnodes: []          # required for composite nodes
gates: []
agent_wrappers: []
side_effects: none | local_write | external_read | external_write | physical_action | payment | publish | destructive
closure_states: []
can_be_used_as_module: true|false
can_be_used_as_workflow: true|false
can_be_delegated_to_agent: true|false
cannot_prove: []
```

## AgentWrapper contract

A named agent is not enough. Agent roles must wrap specific capabilities and declare authority.

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

Pitfall: if an agent has no `wraps`, `policy`, `authority`, and `produces`, it is only a label, not an executable workflow component.

## Coverage audit criteria

When checking whether an abstraction covers other workflow families, score each family against these criteria:

```yaml
C1_intent_router: route by requested deliverable/effect, not by the source demo/template
C2_input_asset_model: model inputs by role, authority, quality, and source boundary
C3_capability_graph: express work as capability nodes/subgraphs
C4_io_contract: reusable nodes have stable consumes/produces
C5_module_workflow_embedding: modules can contain workflows; workflows can be reused as modules
C6_agent_wrapper_policy: agents wrap capability nodes with execution/review policy
C7_gates_closure: nodes have pass/warn/fail/blocked and closure states
C8_evidence_ledger: claims and transitions cite evidence artifacts
C9_boundary_side_effects: permissions and external side effects are explicit
C10_composition_patterns: support linear, fan-out/fan-in, nested workflow, review-retry, and gate-fork patterns
```

Score: `1 = covered`, `0.5 = partial/domain-specific refinement needed`, `0 = absent`.

## Common transferable findings

Usually strong across domains:

- intent routing;
- input/source/asset modeling;
- gates and closure states;
- evidence ledgers.

Usually weak and worth auditing explicitly:

- agent wrapper policy;
- formal capability graph adoption;
- module/workflow mutual embedding with stable I/O;
- non-linear composition patterns.

## Composition patterns

Use these names consistently:

```text
linear_chain: A -> B -> C
fan_out_fan_in: A -> B1/B2/B3 -> C
nested_workflow_as_module: A -> [Workflow X as module] -> D
review_retry_loop: Generate -> Review -> Retry Delta -> Generate
gate_fork: pass/warn/fail/blocked routes
monitor_loop: observe -> threshold -> notify/act -> readback
```

## Landing guidance

When absorbing a concrete demo/video/product workflow:

1. Extract atomic capability nodes.
2. Identify composite modules that are internally workflows.
3. Give reusable workflows stable I/O and closure states so they can be used as modules elsewhere.
4. Define agents as wrappers over nodes/subgraphs, not free-floating role names.
5. Define gates with pass/warn/fail/blocked outcomes.
6. Run a cross-workflow coverage audit against at least 3 neighboring workflow families before promoting the abstraction.

## Smell checks

- A module with many hidden steps but no `subnodes` is a hidden workflow.
- A workflow that cannot be reused by another workflow lacks a stable I/O contract.
- An agent without wrapped capabilities/policy is only a label.
- A gate without pass/warn/fail/blocked is advice, not a gate.
- A composite node without closure state is not ready for orchestration.
- A demo chain copied end-to-end without partial routes will over-handle simple requests.
