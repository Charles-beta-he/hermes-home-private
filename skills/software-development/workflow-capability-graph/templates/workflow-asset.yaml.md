---
schema: hermes_workflow_asset_v1
id: example-workflow-asset
title: Example governed workflow asset
version: 1
source:
  user_seed: "Original user seed or observed repeated pattern"
  source_refs: []
classification:
  workflow_type: hybrid
  scope: domain
  maturity: draft
  retention: domain_reusable
intent_model:
  user_goal: "What durable behavior this asset should produce"
  success_criteria:
    - "Safe local dry-run succeeds"
    - "Objective evidence is attached"
  non_goals:
    - "Do not execute external side effects without exact authority"
    - "Do not promote seed directly to canonical"
  assumptions: []
  ask_user_only_when:
    - "authority boundary"
    - "durable preference conflict"
    - "irreversible side effect"
routing:
  applies_when:
    - "Repeated or long-term process pattern with evidence/governance need"
  does_not_apply_when:
    - "One-off task"
    - "Simple answer"
    - "Keyword-only workflow request with weak reuse"
  neighbor_workflows: []
  forbidden_triggers:
    - "the word workflow alone"
    - "temporary task progress"
  examples_positive: []
  examples_negative:
    - "创建工作流：今天把这三个文件整理一下"
output_contract:
  allowed_formats: [json, markdown]
  default_format: json
  ordering_rule: "risk and reuse value before convenience"
  dedupe_rule: "merge same seed digest and same routing boundary"
  overlap_rule: "prefer existing narrower workflow; avoid broad umbrella steal"
  evidence_required: true
  confidence_required: true
  next_action_required: true
gates:
  - id: assetization_decision_gate
    pass: "reuse/risk/evidence/governability score justifies candidate"
    warn: "weak signal; keep as output fragment or project-scoped candidate"
    fail: "one-off or no durable value; no asset write"
    blocked: "retrieve context or evidence before promotion"
  - id: authority_boundary_gate
    pass: "local reversible read/write only or exact authority present"
    warn: "future automation mentioned but not authorized"
    fail: "external/destructive/publish/credential boundary without authority"
    blocked: "emit minimal authorization request; do not execute"
model_routing:
  default_tier: T1
  specialist_lanes: [architecture, verification]
  multimodel_required_when:
    - canonical promotion
    - global routing
    - external side effect
    - cron/taskpool/AgentOS enablement
evidence:
  required_refs: []
  verification_commands: []
lifecycle_policy:
  promote_when:
    - "route eval passes"
    - "real or dry-run evidence attached"
    - "negative/neighbor cases pass"
  demote_when:
    - "false trigger"
    - "stale evidence"
    - "user correction"
    - "validation failure"
  cleanup_when:
    - "no usage"
    - "superseded"
    - "low evidence"
    - "sprawl risk"
  protect_when:
    - "canonical with regression evidence"
    - "pinned by user"
  superseded_by: null
loop_policy:
  self_advance: true
  max_autonomous_iterations: 3
  stop_only_on:
    - authority_boundary
    - missing_evidence_after_attempt
    - destructive_or_external_side_effect
    - user_preference_conflict
---

# Workflow Asset Template

Use this template for governed Workflow Kernel Loop Engineering assets. A valid asset must define scope, negative routing space, output contract, evidence gates, model-routing boundary, and lifecycle/cleanup policy before it can be promoted beyond draft/candidate.

Do not use this template for one-off task progress, transient TODO state, or broad memory entries.
