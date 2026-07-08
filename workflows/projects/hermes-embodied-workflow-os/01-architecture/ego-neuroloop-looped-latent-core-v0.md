# Ego-NeuroLoop Looped Latent Core v0

Project: `hermes-embodied-workflow-os`
Status: architecture contract / productized absorption draft
Research input: `02-research/looped-world-models-absorption-20260708.md`
Boundary: local-only architecture and contract. No live model, no hardware action, no external dispatch.

## Goal

Turn the useful part of `Looped World Models` into an owned HEWOS/Ego-NeuroLoop product contract:

> A bounded looped-latent world-state core that refines action-conditioned predictions before decoding user-visible advice or operator projections.

## Non-goals

- No claim that Ego-NeuroLoop is in the paper.
- No claim of biological/neuroscience validity.
- No real-time wearable/fitness/travel/robot behavior until separate adapter evidence exists.
- No external side effects, hardware actuation, deploy/push, credential entry, payment, or destructive operations.
- No replacing EvidenceLedger/AuthorityGate with model-internal confidence.

## Core contract

```text
Adapter observation(s)
  -> EgoEncoder
  -> NeuroState projection from evidence
  -> LoopCore(shared update) x adaptive N
  -> ExitGate receipt
  -> DeferredDecoder
  -> Action advice / Workbench projection / voice cue / task candidate
  -> CorrectionGate when new evidence arrives
```

## Component boundaries

### EgoEncoder

Adapter-owned projection layer. It may normalize camera, glasses, phone, voice, UI, IMU, text, or taskpool observations into a common observation envelope.

Rules:

- Adapter-specific code stays outside the stable core.
- Raw camera/video should not leave local boundary by default.
- Encoder output is not durable memory unless explicitly recorded as evidence.

### NeuroState

Derived internal state for current task/world/risk context.

Rules:

- Derived from EvidenceLedger + current observations.
- Carries confidence/risk/unknowns.
- Must not overwrite source-of-truth state directly.
- Durable memory write is forbidden unless separately classified by abstraction governance.

### LoopCore

Shared update operator, repeated under an explicit loop budget.

Inputs:

- `neuro_state`
- `action_intent`
- `goal_context`
- `evidence_refs`
- `loop_budget`
- `risk_policy`

Outputs per iteration:

- `state_delta`
- `predicted_next_state`
- `risk_update`
- `confidence_update`
- `contradictions`

Rules:

- Must be deterministic/testable in the contract slice.
- Must expose loop count and exit reason.
- Must keep side-effect flags false.
- Must not import adapter/platform modules.

### AdaptiveExitGate

Stops, continues, or escalates the loop.

Exit reasons:

- `stable`: state delta low and confidence sufficient.
- `budget_exhausted`: no more safe compute budget.
- `risk_gate`: high-risk path requires stronger proof or human gate.
- `human_gate`: exact authority/readback needed.
- `error`: invalid input or contract violation.

Minimum gate checks:

- state delta threshold;
- confidence threshold;
- contradiction check;
- risk level;
- evidence sufficiency;
- side-effect authority boundary;
- latency/budget cap.

### DeferredDecoder

Converts final internal state into an external surface only after loop exit.

Allowed outputs:

- concise user advice;
- operator Workbench projection;
- local task candidate;
- voice cue;
- risk warning;
- `blocked` packet requiring exact target/authority.

Rules:

- Label predictions as predictions.
- Do not expose speculative latent rollout as verified fact.
- Attach evidence refs and known limits.

### CorrectionGate

Compares prediction with the next observation/evidence and corrects drift.

Rules:

- New observations append evidence; they do not mutate history.
- If prediction diverges from observation, mark contradiction and lower confidence.
- Long-horizon plans must refresh from evidence rather than recursively trusting prior predictions.

## Receipt schema

```json
{
  "schema": "ego_neuroloop_core_receipt_v0",
  "project": "hermes-embodied-workflow-os",
  "mode": "contract_only|runtime_mock|real_model",
  "input_refs": [],
  "action_intent_id": null,
  "loop_budget": 0,
  "loop_count": 0,
  "exit_reason": "stable|budget_exhausted|risk_gate|human_gate|error",
  "state_delta": null,
  "confidence": null,
  "risk_level": "low|medium|high|blocked",
  "predicted_next_state": {},
  "recommended_action": null,
  "deferred_decode_surface": "none|user_text|voice|workbench|task_candidate",
  "boundary_flags": {
    "external_dispatch": false,
    "hardware_actuation": false,
    "credential_entry": false,
    "payment": false,
    "destructive_operation": false
  },
  "evidence_refs": [],
  "known_limits": []
}
```

## Acceptance criteria for next local implementation slice

1. Contract helper can generate a valid receipt from fixture inputs.
2. Early exit occurs when state delta is below threshold and confidence is sufficient.
3. High-risk action intent exits as `risk_gate` or `human_gate` and keeps all side-effect flags false.
4. Deferred decoding output labels prediction vs evidence.
5. Tests prove no adapter/platform imports in core helper.
6. Tests cover negative cases: missing evidence, budget exhaustion, contradiction, side-effect request without exact authority.
7. Existing HEWOS tests continue to pass.

## Product integration map

- HEWOS stable core: owns `LoopCore`, `AdaptiveExitGate`, receipt schema, and evidence boundary.
- Workbench: read-only projection of receipts and risk/exit state.
- Fitness posture coach: possible future domain pack using the same receipt shape for low-risk posture cues only.
- Mobile/offline avatar travel: possible future adapter using looped latent planning for route/advice prediction only.
- Persona wake/glasses/voice: possible future interaction surface; no always-on authority implied.

## Current closure state

`contract-ready/advisory`: the research absorption and architecture contract are landed. Runtime implementation remains a safe local next slice, but it is not completed by this document.
