# Agent Template Profile

Scope: converting reusable agent templates, digital workers, role agents, or public agent-template claims into Hermes/AgentOS profiles. Applicability: Raven-style Agent Templates, digital workers, Mission templates, recurring personal/productivity/coding workers, and executor profiles. Anti-condition: one-off prompts, static documentation templates, or non-executing role descriptions do not need the full profile.

## Source pattern

Derived from Raven/EverOS absorption:

- SSOT: `/Users/charles/wechat_video_analysis/project_absorption/raven-everos-absorption-ssot/`
- Graph node: `agent_template_profile`
- Experience atom: `raven-everos-absorption-4e0e8b2f8d79`

## Profile contract

Represent an agent template as governed configuration, not as a free-form prompt:

```yaml
id: string
name: string
purpose: string
source_refs: []
capability_graph_refs: []
intent_routes: []
inputs:
  allowed_sources: []
  freshness_rules: []
  privacy_class: public | private | sensitive | secret
outputs:
  artifact_types: []
  delivery_targets: local_only | exact_allowlist_required
authority:
  read: none | local | external
  local_write: none | scoped
  external_write: none | exact_gate_required
  code_execution: none | sandbox_required | exact_target_required
  credentials: never_agent_typed
  publish_deploy_push: exact_gate_required
  destructive: exact_gate_required_with_backup
side_effect_matrix:
  S0_read_only: []
  S1_local_write: []
  S2_external_read: []
  S3_external_write: []
  S4_publish_deploy_push: []
  S5_destructive: []
  S6_payment_credentials: []
  S7_broad_fanout: []
gates:
  preflight: []
  evidence: []
  approval: []
  rollback: []
  receipt_readback: []
runtime:
  model_policy: string
  tool_policy: []
  budget_policy: string
  kill_switch: string
observability:
  receipts: []
  ledgers: []
  health_checks: []
cannot_do: []
```

## Projection rules

1. A template may become a Hermes project profile, Mission profile, or taskpool lane only after source refs and capability graph refs exist.
2. If it can act outside local files, it needs an authority matrix before execution.
3. If it can deliver messages, create tasks, push code, deploy, operate devices, or handle secrets/payment, require exact target + rollback + receipt + readback.
4. Agent templates should wrap CapabilityNodes; they should not invent tools or bypass gates.
5. A template is not a live worker until runtime readiness and side-effect gates are verified.

## Minimal local landing

When the user authorizes absorption but no runtime target is safe yet, land one of:

- profile schema draft;
- read-only checker for a candidate profile;
- capability graph node with authority matrix;
- project-doc proposal;
- experience-ratchet atom.

Do not stop at “needs approval” if one of those local artifacts can still be produced.
