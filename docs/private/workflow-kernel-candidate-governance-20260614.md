# Workflow kernel candidate governance — 2026-06-14

- generated_at: `2026-06-14T19:09:45+08:00`
- scope: govern the 22 proposed workflow-kernel import candidates from `decision_brief_pack` / `run_preview_78eee6afcec1f12a`.
- hard boundary: no runtime executor enablement, no model/adapter call authority, no write-through, no external side effects; only taskpool candidate governance and creation of a bounded implementation slice.
- upstream import dry-run: `tpdry_a5678ba9e856a763`
- upstream import write: `tpwrite_f62e8067efc48f89`

## Decision

Approve the candidate set as a static workflow-kernel contract/registry tranche, not as runtime enablement. Close the 19 leaf import candidates as absorbed into the 3 consolidated decisions, close the 3 consolidated candidates as reviewed/approved, and create one bounded implementation slice for a local registry + static validator.

## Consolidation map

### Import guards
- `all_modules_have_evidence_required` → bounded slice prerequisites; task `2026-06-13-workflow-kernel-import-candidateall-modules-have-evidence-required`
- `all_modules_have_model_policy` → bounded slice prerequisites; task `2026-06-13-workflow-kernel-import-candidateall-modules-have-model-policy`
- `evidence_prefixes_valid` → bounded slice prerequisites; task `2026-06-13-workflow-kernel-import-candidateevidence-prefixes-valid`
- `human_gate_packet_fields_present` → bounded slice prerequisites; task `2026-06-13-workflow-kernel-import-candidatehuman-gate-packet-fields-present`
- `runtime_disabled_in_phase1` → bounded slice prerequisites; task `2026-06-13-workflow-kernel-import-candidateruntime-disabled-in-phase1`
- `workflow_contract_valid` → bounded slice prerequisites; task `2026-06-13-workflow-kernel-import-candidateworkflow-contract-valid`

### Model routes
- `model_route:acceptance_compiler.v1` → consolidated:model routes; task `2026-06-13-workflow-kernel-import-candidatemodel-route-acceptance-compilerv1`
- `model_route:decision_synthesizer.v1` → consolidated:model routes; task `2026-06-13-workflow-kernel-import-candidatemodel-route-decision-synthesizerv1`
- `model_route:evidence_verifier.v1` → consolidated:model routes; task `2026-06-13-workflow-kernel-import-candidatemodel-route-evidence-verifierv1`
- `model_route:goal_calibrator.v1` → consolidated:model routes; task `2026-06-13-workflow-kernel-import-candidatemodel-route-goal-calibratorv1`
- `model_route:source_research.v1` → consolidated:model routes; task `2026-06-13-workflow-kernel-import-candidatemodel-route-source-researchv1`

### Module contracts
- `module_contract:acceptance_compiler.v1` → consolidated:module contracts; task `2026-06-13-workflow-kernel-import-candidatemodule-contract-acceptance-compilerv1`
- `module_contract:decision_synthesizer.v1` → consolidated:module contracts; task `2026-06-13-workflow-kernel-import-candidatemodule-contract-decision-synthesizerv1`
- `module_contract:evidence_verifier.v1` → consolidated:module contracts; task `2026-06-13-workflow-kernel-import-candidatemodule-contract-evidence-verifierv1`
- `module_contract:goal_calibrator.v1` → consolidated:module contracts; task `2026-06-13-workflow-kernel-import-candidatemodule-contract-goal-calibratorv1`
- `module_contract:source_research.v1` → consolidated:module contracts; task `2026-06-13-workflow-kernel-import-candidatemodule-contract-source-researchv1`

### Safety flags
- `safety_flag:external_side_effects_enabled` → consolidated:safety flags; task `2026-06-13-workflow-kernel-import-candidatesafety-flag-external-side-effects-enabled`
- `safety_flag:runtime_enabled` → consolidated:safety flags; task `2026-06-13-workflow-kernel-import-candidatesafety-flag-runtime-enabled`
- `safety_flag:write_through_enabled` → consolidated:safety flags; task `2026-06-13-workflow-kernel-import-candidatesafety-flag-write-through-enabled`

## Approved bounded slice

Title: `Workflow kernel bounded slice｜static registry and validator no-runtime`

Acceptance shape:
- Land a static workflow-kernel registry/manifest for modules, model route aliases, safety flags, and import guard criteria.
- Land a local deterministic validator or dry-run command that checks: evidence requirement, model policy presence, evidence prefixes, human gate packet fields, phase-1 runtime disabled, workflow contract validity, route aliases, module contracts, and safety flags.
- Verification must be local/read-only: syntax check + deterministic sample run + taskpool proof/selfcheck readback.
- Runtime executor, model calls, adapter write-through, and external side effects stay disabled and require a later explicit human gate.

## Rejected/forbidden now

- Do not enable `runtime_enabled`.
- Do not enable `write_through_enabled`.
- Do not enable `external_side_effects_enabled`.
- Do not claim implementation of a runtime executor or adapter.

## Candidate IDs

### import_guards_leaf
- `2026-06-13-workflow-kernel-import-candidateall-modules-have-evidence-required` — all_modules_have_evidence_required
- `2026-06-13-workflow-kernel-import-candidateall-modules-have-model-policy` — all_modules_have_model_policy
- `2026-06-13-workflow-kernel-import-candidateevidence-prefixes-valid` — evidence_prefixes_valid
- `2026-06-13-workflow-kernel-import-candidatehuman-gate-packet-fields-present` — human_gate_packet_fields_present
- `2026-06-13-workflow-kernel-import-candidateruntime-disabled-in-phase1` — runtime_disabled_in_phase1
- `2026-06-13-workflow-kernel-import-candidateworkflow-contract-valid` — workflow_contract_valid

### model_routes_leaf
- `2026-06-13-workflow-kernel-import-candidatemodel-route-acceptance-compilerv1` — model_route:acceptance_compiler.v1
- `2026-06-13-workflow-kernel-import-candidatemodel-route-decision-synthesizerv1` — model_route:decision_synthesizer.v1
- `2026-06-13-workflow-kernel-import-candidatemodel-route-evidence-verifierv1` — model_route:evidence_verifier.v1
- `2026-06-13-workflow-kernel-import-candidatemodel-route-goal-calibratorv1` — model_route:goal_calibrator.v1
- `2026-06-13-workflow-kernel-import-candidatemodel-route-source-researchv1` — model_route:source_research.v1

### module_contracts_leaf
- `2026-06-13-workflow-kernel-import-candidatemodule-contract-acceptance-compilerv1` — module_contract:acceptance_compiler.v1
- `2026-06-13-workflow-kernel-import-candidatemodule-contract-decision-synthesizerv1` — module_contract:decision_synthesizer.v1
- `2026-06-13-workflow-kernel-import-candidatemodule-contract-evidence-verifierv1` — module_contract:evidence_verifier.v1
- `2026-06-13-workflow-kernel-import-candidatemodule-contract-goal-calibratorv1` — module_contract:goal_calibrator.v1
- `2026-06-13-workflow-kernel-import-candidatemodule-contract-source-researchv1` — module_contract:source_research.v1

### safety_flags_leaf
- `2026-06-13-workflow-kernel-import-candidatesafety-flag-external-side-effects-enabled` — safety_flag:external_side_effects_enabled
- `2026-06-13-workflow-kernel-import-candidatesafety-flag-runtime-enabled` — safety_flag:runtime_enabled
- `2026-06-13-workflow-kernel-import-candidatesafety-flag-write-through-enabled` — safety_flag:write_through_enabled

### consolidated
- `2026-06-13-workflow-kernel-consolidated-candidatemodel-routes` — model routes
- `2026-06-13-workflow-kernel-consolidated-candidatemodule-contracts` — module contracts
- `2026-06-13-workflow-kernel-consolidated-candidatesafety-flags` — safety flags
