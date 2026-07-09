---
schema: hermes_capability_module_v1
id: example_capability_module
title: Example Capability Module
version: 1
kind: atomic_module
responsibility: "One stable reusable responsibility with clear input/output"
contracts:
  consumes:
    - seed
  produces:
    - evidence_refs
  input_contract:
    required:
      - seed
    optional: []
  output_contract:
    produces:
      - evidence_refs
    evidence_required: true
    confidence_required: true
  presentation_contract:
    surfaces:
      - cli
      - markdown
    style: concise_evidence_first
routing:
  applies_when:
    - "Repeated or long-term workflow needs this capability"
  does_not_apply_when:
    - "One-off simple answer"
    - "Keyword-only workflow request"
  positive_examples: []
  negative_examples:
    - "创建工作流：今天把这三个文件整理一下"
  neighbor_modules: []
  forbidden_triggers:
    - "the word workflow alone"
authority:
  side_effects: none
  required_authority: []
  can_run_autonomously: true
lifecycle:
  maturity: candidate
  retention: domain_reusable
metrics:
  usage_count: 0
  success_count: 0
  evidence_pass_rate: 0.0
  false_trigger_count: 0
  human_intervention_rate: 0.0
promotion_policy:
  promote_when:
    - "successful_runs >= 2"
    - "evidence_pass_rate >= 0.8"
    - "negative_cases_pass"
  demote_when:
    - false_trigger
    - stale_evidence
    - user_correction
  cleanup_when:
    - no_usage_for_ttl
    - superseded_by_better_module
---

# Capability Module Template

Use this template for the reusable module pool that powers Workflow Kernel Loop Engineering. Modules are smaller than workflow assets and must declare stable I/O, routing negative space, authority boundary, maturity, metrics, and promotion/cleanup policy.

Frequency is only a candidate signal. A high-frequency module combination must still pass evidence, negative/neighbor route, low-human-intervention, false-trigger, and cleanup gates before promotion.
