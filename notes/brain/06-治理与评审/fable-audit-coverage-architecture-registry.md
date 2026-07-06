---
status: current
stability_class: canonical
---

# Fable Audit Coverage Architecture Registry — current canonical source

Current source / canonical source for the local BrainConstraintGate preflight on the Fable audit coverage architecture registry.

This note records why `17-fable-audit-coverage-architecture-registry.json` is a valid local architecture evidence artifact:

- design_doc: the registry defines the declared 15-dimension audit coverage model for Fable 5 review of Hermes main assistant and ongoing project portfolio.
- gate_readback: local JSON validation returned `COVERAGE_REGISTRY_PASS 100 15`, proving every declared dimension has current readback status, verdict, evidence pointers, known gaps, and next action.
- evidence boundary: 100% means coverage-model completeness for the declared dimensions, not system health, production readiness, or absence of risk.
- rollback: local git reset/revert of the staged files restores the prior state.

Canonical terms for search: 17 fable audit coverage architecture registry readback current canonical knowledge source of truth ssot.
