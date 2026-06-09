---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1/4: Gate1 protocolization before runtime mechanisms"]
created: 2026-05-19T11:32:26+08:00
updated: 2026-05-20T00:00:00+08:00
expires_at: 2026-06-18T11:32:26+08:00
project: hermes
architecture_target: local-brain
capability_delta: "meta_synthesis_protocol_skill: workflow skill/reference can be loaded and used for multimodel/multibrain sessions"
anti_drift_check: Do not let 多模型同意 replace source/evidence; dissent ledger and handback remain mandatory
acceptance_evidence: skill exists; skill_view loads; protocol contains source_packet/dissent/handback/schema; one dry-run session record uses it
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: core-methodology absorption affects multi-brain governance
expected_participants: ["gpt-5.5", "mimo-v2.5-pro", "deepseek-v4-pro"]
truth_gate: source evidence + protocol artifact + skill load verification
evidence_bundle: brain/03-理论与元认知/系统工程协议/综合集成研讨厅协议.md; brain/06-治理与评审/reviews/2026-05-19-qian-xuesen-multimodel-synthesis.md
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: P2 evolution; evidence-first; existing Gate0 docs available; no immediate runtime side effect
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: May run in parallel with observer bus design; must precede qual_to_quant automation
evidence:
  - "artifact: /Users/charles/.hermes/profiles/brain-mirror/skills/autonomous-ai-agents/qian-meta-synthesis/SKILL.md"
  - "proof: runtime skill exists and skill_view(name='qian-meta-synthesis') loads successfully"
  - "artifact: /Users/charles/.hermes/profiles/brain-mirror/skills/autonomous-ai-agents/qian-meta-synthesis/templates/session.yaml.md"
  - "proof: linked template loads via skill_view(name='qian-meta-synthesis', file_path='templates/session.yaml.md')"
  - "artifact: /Users/charles/Code/personal-hermes-brain/hermes/skills/workflow/qian-meta-synthesis/SKILL.md"
  - "proof: repo copy preserves the original source/evidence/dissent/handback schema"
  - "artifact: /Users/charles/Code/personal-hermes-brain/brain/03-理论与元认知/系统工程协议/综合集成研讨厅协议.md"
  - "proof: protocol source packet defines source_packet/dissent/handback session schema"
  - "artifact: /Users/charles/Code/personal-hermes-brain/brain/06-治理与评审/reviews/2026-05-19-qian-xuesen-gate1-followup.md"
  - "proof: one dry-run session record uses the protocol and preserves dissent + handback boundaries"
  - "command: python3 hermes/scripts/qual_to_quant_task_contract.py --demo --json"
  - "proof: returns status OK plus required research->dev handback fields"
concepts: ["task"]
---

# Task - P1: 钱学森综合集成研讨厅协议沉淀为 Hermes workflow skill

## Objective

Turn Gate0 meta-synthesis protocol into reusable Hermes workflow skill/procedure

## Acceptance Criteria

- [x] Gate1 protocol executable

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `skill_view(name='qian-meta-synthesis')` | pass | runtime skill loads from `~/.hermes/profiles/brain-mirror/skills/autonomous-ai-agents/qian-meta-synthesis/SKILL.md` |
| `skill_view(name='qian-meta-synthesis', file_path='templates/session.yaml.md')` | pass | linked session template loads and preserves the meta_synthesis_session schema |
| `python3 hermes/scripts/qual_to_quant_task_contract.py --demo --json` | pass | returns `status: OK`, explicit `task_id`, and research->dev handback fields |
| Protocol source readback | pass | `综合集成研讨厅协议.md` contains `source_packet`, `dissent`, and `handback` sections |
| Dry-run session record readback | pass | `2026-05-19-qian-xuesen-gate1-followup.md` records one `meta_synthesis_session` with dissent + handback |

## Proof Log

- 2026-05-19T11:32:26+08:00: Task created from local-brain control point.
- 2026-05-19 Gate1/Gate2 bounded advancement: landed executable artifact slice and verification evidence. Truth gate grounded for deterministic claims; full 4/4 multi-model certification intentionally withheld because Gemini provider failed to sign best_within_constraints.
- 2026-05-20: Reconciled the gap between repo-only artifact and live Hermes runtime by creating the local `qian-meta-synthesis` skill plus linked template under `~/.hermes/profiles/brain-mirror/skills/autonomous-ai-agents/`, then read back both via `skill_view`.
- 2026-05-20: Re-verified protocol source and dry-run session record; acceptance evidence now covers runtime skill load, schema presence, and one concrete handback example.

## Blockers / Confusions

- Gemini provider/model signature failure remains as certification-only residual risk; deterministic evidence is grounded.
- Runtime dispatch hard-gate integration and core atom write integration are intentionally out of scope for this bounded slice.

## Final Handoff

- Status: done — the 钱学森综合集成研讨厅协议 is now available as a live Hermes skill and linked session template, not just a repo-side artifact.
- Runtime artifact: `~/.hermes/profiles/brain-mirror/skills/autonomous-ai-agents/qian-meta-synthesis/SKILL.md` and `templates/session.yaml.md` both load via `skill_view`.
- Evidence: protocol source, dry-run session record, and `qual_to_quant_task_contract.py --demo --json` collectively satisfy the original acceptance evidence without overclaiming runtime hard-gate integration.
- Residual boundary: dispatch hard-gate integration and core atom writes remain explicitly out of scope for this task.
