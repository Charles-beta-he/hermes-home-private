# Fable Audit Coverage Registry Readback — 2026-07-06

Scope: local, reversible coverage registry artifact for Fable 5 audit of Hermes main assistant and ongoing project portfolio.

Evidence labels for local BrainConstraintGate:

- design_doc: `17-fable-audit-coverage-registry.json` is the scoped design/projection document for the Fable audit coverage model. It defines 15 declared audit dimensions, coverage semantics, evidence pointers, known gaps, and next actions.
- gate_readback: `python3 - <<'PY' ...` parsed `17-fable-audit-coverage-registry.json` and returned `COVERAGE_REGISTRY_PASS 100 15`, proving all 15 dimensions have `coverage_status=covered_by_current_readback`, evidence, known gaps, and next action.
- exact_target: local Hermes home file write only under `/Users/charles/.hermes/workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/`; no external dispatch, lifecycle write, publish/deploy/push, destructive action, credential/payment action, or secret read.
- rollback: remove or revert `17-fable-audit-coverage-registry.json` and this readback note via `git revert <commit>` or `git reset` before commit.
- post_action_readback: Fable 5 final audit judged the registry PASS under the declared definition, while warning that 100% means coverage-model completeness, not system health or absence of risk.

Boundary:
- This artifact does not claim Hermes is 100% healthy.
- This artifact does not claim portfolio project states are trustworthy while portfolio doctor is broken.
- This artifact does not authorize external side effects, provider config changes, taskpool lifecycle writes, publish/deploy/push, secret handling, or destructive cleanup.
