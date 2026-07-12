# Portfolio Doctor and Registry/Profile Reconciliation

Use when auditing a Hermes project portfolio or when a model review flags project-status drift.

## Durable lessons

1. A portfolio doctor report can exist but still be a failure artifact. Check `ok`, `returncode`, and `stderr`, not just report presence or timestamp.
2. If the doctor script path recorded in the skill/profile is missing, treat portfolio project statuses as untrusted until the path is repaired and a fresh doctor run passes.
3. Registry/profile/SSOT must be reconciled as a set:
   - project in registry but missing profile/SSOT -> downgrade or restore evidence;
   - profile/SSOT exists but registry lacks the project -> add registry entry or mark intentionally excluded;
   - work/client projects may remain excluded unless the user explicitly switches context.
4. Do not infer project readiness from status strings like `contract-ready`, `validated`, or `ledgered` when the referenced files are missing.
5. Path roots may differ by project class (for example `workflows/product/` vs `workflows/projects/`). A missing result from a hardcoded root is a path-assumption defect until profile/SSOT paths are checked.

## Reconciliation checklist

- [ ] Read portfolio registry.
- [ ] Read all project profiles.
- [ ] For each project, check `ssot_root` and `progress_ledger` from the profile or registry, not from a hardcoded directory.
- [ ] Run or inspect portfolio doctor; require `ok: true` for status trust.
- [ ] Compare registry IDs, profile files, and SSOT directories.
- [ ] Downgrade any project whose state is stronger than evidence.
- [ ] Preserve explicit exclusions for work/client projects unless the user switches scope.

## A+/external-review closure checklist

When a model review (Fable, Claude, Codex, Gemini, etc.) flags portfolio drift, close the loop with evidence rather than status edits alone:

- Restore or repair the doctor/strict-verify scripts first, then rerun them; a stale report or missing path keeps all registry status strings untrusted.
- Reconcile registry IDs, profile files, SSOT roots, and progress ledgers as sets. Add missing registry entries only when a profile/SSOT is real; otherwise downgrade the claim to an evidence-seeking state.
- Reclassify stale blockers only when the same profile/ledger contains later lifecycle evidence (for example certified/done readback, scoped commits, or focused tests). Do not use reclassification as force-done.
- If selfcheck reports missing semantic control-plane policies, add scoped `backend_contract_policy`, `regression_coverage_policy`, `lark_task_execution_policy`, and `lark_evidence_policy` to the affected profiles while preserving WARN-only/fail-close posture unless separately ratified.
- Keep historical terminal proof/hash debt distinct from current portfolio blockers: if live `proof-check` has `status=PASS` and `failures=[]`, record the debt as P2/P3 burn-down work, not as a reason to distrust current portfolio reconciliation.
- After changes, require `portfolio_os_verify.py --json` with `ok=true`, `error=0`, `warning=0`, and a scoped git status/commit plan before claiming closure.

## Reporting wording

Use:
- “Status is untrusted until doctor path is repaired and fresh doctor passes.”
- “This is a registry/profile/SSOT reconciliation issue, not proof the project itself is broken.”

Avoid:
- “Project is contract-ready” when SSOT/ledger files are missing.
- “Project is missing” based only on a hardcoded root mismatch.
