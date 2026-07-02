# HEWOS Best-Practice Gate and Process Ladder

Status: local contract/process specification, no executor opened.
Updated: 2026-07-02T20:52:00+08:00

## Objective

Codify the next safe automation path so HEWOS can keep advancing without using "needs human intervention" as a generic interface. The process must still fail closed at real authority, evidence, or side-effect boundaries.

## Cost function

Prefer paths that maximize:

1. preserved core contract stability;
2. objective evidence before claims;
3. reversible local-only progress;
4. explicit side-effect class separation;
5. adapter/executor authority opened one rung at a time.

Minimize:

1. platform-specific branches in Core;
2. model-only certification;
3. hidden state mutation from UI/runtime;
4. skipped gates;
5. broad authority leakage into external/taskpool/hardware/deploy actions.

## Best-practice ladder

The canonical local ladder is implemented in:

`implementation/hewos_core/best_practice_gates.py`

Current phase order:

1. `contract_core`
   - Contract validators and registries.
   - Evidence: tests, contract readback, rollback.

2. `evidence_replay`
   - Append-only ledger and deterministic reducer/replay.
   - Evidence: tests, replay readback, append-only check, rollback.

3. `projection_fixtures`
   - DTO projection helpers, side-effect-free.
   - Evidence: tests, projection readback, side-effect scan, rollback.

4. `static_workbench`
   - Static local HTML artifact.
   - Evidence: tests, HTML readback, side-effect scan, rollback.

5. `local_runtime_smoke`
   - Local stdlib HTTP runtime, projection-only.
   - Evidence: tests, py_compile, HTTP/browser readback, rollback.

6. `ui_quality_audit`
   - UI/UX quality audit and screenshot/console evidence.
   - Evidence: tests, browser smoke, console readback, screenshot readback, rollback.
   - This is the first point where UI quality can be claimed, and only to the audited level.

7. `simulation_write_local_ledger`
   - Simulation-only local ledger write.
   - Evidence: tests, ledger receipt, idempotency readback, rollback.
   - No external adapter, no taskpool write, no hardware execution.

8. `approval_decision_local_ledger`
   - Local approval/rejection decisions as ledger facts.
   - Evidence: tests, decision receipt, single-use check, rollback.
   - Decisions still do not execute adapters.

9. `external_adapter_intent`
   - Intent projection for a specific adapter target.
   - Evidence: tests, intent digest, allowlist readback, rollback.
   - Still no write-through.

10. `harness_write_through`
    - Local fixture/harness write-through only.
    - Evidence: tests, harness receipt, post-action readback, rollback.

11. `real_adapter_write_through`
    - First real adapter mutation.
    - Requires exact target, exact authority, adapter receipt, post-action readback, rollback.

## Gate packet contract

A gate packet must include:

```yaml
gate_id: string
phase: one of BEST_PRACTICE_PHASES
risk_class: string
side_effect_class: string
required_evidence: [string]
provided_evidence: {evidence_class: evidence_ref_or_summary}
authority:
  scope: local-only
  expires_at: bounded string
  allowed_actions: [string]
  forbidden_actions:
    - external_dispatch
    - taskpool_write
    - hardware_execution
    - deploy
    - credential_entry
idempotency_key: string
rollback_plan: string
readback_plan: string
next_phase: phase|null
```

`validate_gate_packet()` returns `decision: pass` only when all required evidence classes are present and high-risk actions remain explicitly forbidden for local-only gates. It always returns `execution_enabled: false`; gate validation is not an executor.

## Process phase contract

A phase packet must include:

```yaml
phase: string
previous_phase: string|null
previous_receipt: string|null
allowed_side_effects: [string]
exit_criteria: [string]
```

Rules:

- If `previous_phase` is set, `phase` must be exactly the next rung.
- `previous_receipt` is mandatory for sequential advancement.
- `allowed_side_effects` must be a subset of the phase policy.
- Unknown or skipped phases fail closed.

## Authority ladder rules

`evaluate_authority_ladder()` blocks when:

- requested phase skips the next rung;
- requested phase is unknown;
- requested actions include external dispatch, taskpool write, hardware/robot execution, deploy/publish, credential/payment, destructive, or broad fanout.

## Multi-model role

Multi-model review is a safety/adversarial input. It can recommend amendments, but it is not completion evidence by itself. Completion still requires non-model evidence: tests, readback, receipts, screenshots/browser console when UI is claimed, and post-action readback for side effects.

If a model/provider is unavailable, the result is recorded as degraded/advisory and local-only reversible slices may continue if deterministic gates pass.

## Current safe next phase

After `local_runtime_smoke`, the next safe local phase is:

`ui_quality_audit`

Allowed work:

- improve local Workbench UI structure/copy/accessibility;
- run browser smoke;
- capture screenshot/readback;
- record UI audit findings;
- keep `/execute` absent and all side-effect routes closed.

Forbidden until later exact gates:

- taskpool lifecycle write;
- external adapter write;
- real hardware/robot control;
- deploy/push/publish;
- credential entry or token handling;
- production auth claims;
- UI A+ or uIMax completion claims without a real audit report.

## Verification

Current tests:

```bash
python3 -m unittest discover -s workflows/projects/hermes-embodied-workflow-os/implementation/tests -v
```

Best-practice gate tests live at:

`implementation/tests/test_best_practice_gates.py`
