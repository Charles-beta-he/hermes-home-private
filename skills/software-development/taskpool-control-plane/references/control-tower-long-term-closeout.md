# Control Tower long-term stable plan closeout

Use this reference when a Hermes-owned mission/workflow-kernel ladder has already reached runtime auto-enable or publication/manual-only terminal states, and the user asks whether the final long-term stable plan is complete or says to fill all remaining items.

Applicability: Hermes Control Tower / taskpool / workflow-kernel governance work where the remaining work is control-plane evidence, fail-closed contracts, and operator projections. Anti-conditions: do not use this as authority to send external messages, publish, mutate Lark/GitHub, enable unattended dispatch, read/write secrets, deploy, delete data, or enqueue Phase-G candidates without a fresh exact target and authorization.

## Closeout sequence

1. **Runtime freshness and mission state first**
   - Read mission board/status/doctor/signals.
   - Clear stale or pending mission flow signals only through the mission control-plane recovery path.
   - Refresh provider probe, cron provider gate, scheduler projection, run-outcome correlation, runtime readiness, drift watch, and post-auto-enable observation.
   - Required readback: no open decisions, no pending/stale signals, scheduler projection ready, readiness auto-enabled or explicitly classified, drift clear/read-only.

2. **Control Tower visibility**
   - The operator snapshot must expose runtime readiness, scheduler projection/correlation, post-auto-enable observation, mission flow signal counts, and no-external-side-effect flags.
   - Verify both Python snapshot (`build_snapshot`) and live dashboard API when the task claims UI/API completion.

3. **Conflicting-evidence override consumption**
   - Approved conflicting-evidence override is a consumable input to closeout authorization, not a direct closeout.
   - Preserve invariants: `override_allowed=true` only after admin approval; `closeout_allowed=false`; closeout authorization remains projection-only; task/adapters are not mutated.
   - Fail closed on evidence hash drift, missing/rejected/expired override, insufficient positive evidence, or insufficient actor role.

4. **Broader adapter contract**
   - Convert broad “more adapters/operations” into a read-only contract/index.
   - Explicitly list current narrow supported operations, candidate locked operations, required exact-target gates, and global invariants.
   - Safe default: no generic adapter write-through; current narrow taskpool/kanban-only surface remains the only implemented write-through.

5. **Remaining gates terminal index**
   - Compile a read-only terminal index for unattended dispatch, publication apply, and broader adapter operations.
   - Required gates: manual-only dispatch stays closed, publication stays closed-no-apply/human-gated-reopen-only, broader adapter operations stay fail-closed contract-only.

6. **Phase-G optimization/self-healing backlog projection**
   - Land candidate-only backlog projection for self-healing/optimization/completion-evidence work.
   - Required invariants: `read_only=true`, `taskpool_mutated=false`, `mission_mutated=false`, `executor_enabled=false`, `external_side_effects_executed=false`.
   - Candidate backlog is not implementation and not enqueue authority.

7. **Final closeout evidence**
   - Run focused tests spanning new scripts/projections, Control Tower snapshot, and dashboard plugin API.
   - Read back Control Tower Python snapshot and live dashboard API.
   - Read back mission status/doctor/signals.
   - Commit child repo scoped files first, then parent gitlink/skill updates.
   - Record a mission stage-report with evidence lines for tests, Control Tower states, live API states, and mission doctor.

## Expected final safe state

```text
workflow_kernel_status=ready
runtime_stability.status=RUNTIME_READINESS_SUMMARY_AUTO_ENABLED
remaining_gates_terminal_index.status=REMAINING_GATES_TERMINAL_INDEX_READY
phase_g_optimization_backlog.status=PHASE_G_OPTIMIZATION_BACKLOG_READY
broader_adapter_operation_contract.status=BROADER_ADAPTER_OPERATION_CONTRACT_READY
publication_terminal.status=PUBLICATION_GOVERNANCE_TERMINAL_SUMMARY_READY
mission.pending_flow_signals=0
mission.stale_flow_signals=0
mission.open_decisions=0
external_side_effects_enabled=false
unattended_dispatch_enabled=false
publication_apply_enabled=false
```

## Pitfalls

- Do not call a publication/manual-only ladder “the whole long-term plan” until runtime freshness, Control Tower visibility, broader adapter boundaries, and Phase-G candidate backlog are also checked.
- Do not turn a Phase-G candidate projection into taskpool enqueue or executor enablement without fresh authority.
- Do not interpret parent repo `m <submodule>` as failed scoped commit when the child repo has unrelated dirty files; verify the intended scoped files are clean and disclose unrelated dirtiness separately.
- Do not treat a local artifact or policy document as proof of external dispatch/publication; exact target/payload/rollback authority is still required.
