# Review closeout with multimodel-claimed tasks

Applicability: use when a taskpool item is already claimed by `hermes-multimodel` or another worker, but the current session has produced the missing evidence and needs to move the task to review/closure. This is a lifecycle-control pattern, not a task-specific record.

Anti-conditions:
- Do not use this to bypass real missing proof.
- Do not force `done` merely because local tests pass if the lane requires ratification/certification.
- Do not save task IDs, commit hashes, or one-session outputs here.

## Pattern

1. Read the task file and identify claim owner, status, lane, completion gate, and required evidence.
2. Add structured evidence before lifecycle mutation. Prefer accepted prefixes such as:
   - `artifact:/absolute/path`
   - `command:<stable-command-or-proof-label>`
   - `proof:<stable-proof-label>`
3. If the task is claim-owned by another actor, a normal transition may fail with `task claim owned by ...`. Use `--force` only when:
   - the current session produced the evidence being recorded;
   - the force reason names the boundary crossed;
   - the transition is to `review`/`blocked`/`pending` as appropriate, not an unsafe direct `done`.
4. Run `auto-close-review` only after the task is in review and the lane allows it.
5. If `auto-close-review` returns `certification_triggered_skip` / `certification_task_mismatch` / `autorun_multimodel_disabled`, leave the task in `review` and report that certification is pending. Do not force `done` unless an explicit ratification artifact is present and the skill/policy allows it.
6. Re-run taskpool selfcheck or the relevant proof checker to ensure the control plane remains healthy.

## Good closeout phrasing

- "Evidence landed; task advanced to review. Auto-close skipped because multimodel certification is disabled, so done is intentionally not forced."
- "Claim owner was `hermes-multimodel`; used forced review transition with scoped evidence and reason, not direct done."

## Pitfalls

- Retrying `auto-close-review` without changing certification state usually repeats the same skip.
- A task reaching `review` can be the correct stopping point under fail-closed governance.
- Do not interpret `certification.status: SKIP` as success; it is a safe non-closure.
