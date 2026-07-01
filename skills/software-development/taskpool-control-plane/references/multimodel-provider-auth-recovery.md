# Multi-model provider auth recovery for blocked taskpool certifications

Applicability: use when taskpool blocked tasks have enough local evidence, but multi-model certification cannot pass because a required participant failed authentication (for example Claude CLI / `claude-opus-4-8` returns `401 Invalid authentication credentials`).

Anti-conditions:
- Do not use this to bypass `requires_multimodel`, quorum, or T3 economy gates.
- Do not use this when task evidence is actually weak, missing, or contradictory.
- Do not edit global quorum policy merely because one provider token expired.

Procedure:
1. Confirm provider-auth root cause with a direct smoke test, e.g. `claude -p --model claude-opus-4-8 'return CLAUDE_OK only'`.
2. If the user has asked for it, notify them on the configured channel to re-login. Treat auth expiry as recoverable setup state, not a durable tool limitation.
3. After re-authentication, rerun the same T3 discussion/certification against the task-specific state file; preserve the existing certification reasons and task scope.
4. Stamp the new `discussion_result.json` with task binding before gate evaluation. Missing target binding is a separate fail-closed gate failure.
5. Evaluate with `ratification_gate_result`; only `PASS` + `LOOP_DONE` may unblock the task.
6. Write the gate result back to the task note. Non-pass rounds should be recorded as latest state but must remain fail-closed.
7. Run blocked resolver to move `blocked -> review`, then use the governed review/auto-close path if acceptance evidence is complete.
8. Verify final state with selfcheck, proof-check/dispatch tick, and active-list counts. Success means no blocked/review/dispatchable stale work and proof/selfcheck pass.

Pitfalls:
- Do not store “model is broken” or “tool unavailable” as a persistent rule; store only the recovery pattern.
- Do not substitute another required model without explicit governance approval.
- Distinguish `discussion artifact missing` from `certification not PASS`: rebuild/stamp artifacts first, then inspect the real gate failures.
