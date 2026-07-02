# Architecture Benchmark Scorecard

Generated: 2026-07-02T19:07:46+08:00

| Dimension | Target | Evidence now | Status |
|---|---|---|---|
| Core/adapter separation | Core has no platform imports | `test_core_has_no_platform_or_hardware_imports` | validated-local |
| Capability-driven routing | Actor/device capabilities drive decisions | `CapabilityRegistry` + mock adapters | validated-local |
| Evidence-first state | WorldState derived from ledger/reducer | planned P2 | planned |
| Safety gates | SafetyGate + ExternalControlGate before physical/external action | `validate_action_intent` executable gate tests | validated-contract |
| Workbench boundary | Web is operator surface only | architecture/PRD only; no UI code | planned |
| Competitor awareness | Sampled official sources and mapped patterns | competitor-source-samples + evaluation | accepted/advisory |
| Human stop gate | Stops before hardware/taskpool/external writes | no hardware/taskpool/external code touched | active |

## Current score

Planning/evidence maturity: 4/5.
P1 implementation maturity: 3/5 local contract slice.
Runtime/hardware maturity: 0/5 by design.

Do not claim runtime readiness until P2 replay and later Workbench tests pass.
